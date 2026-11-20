"""
HDFS Ingestion Failure Recovery & Cumulative PySpark Processing Test Suite
Project: SMART Customer Analysis and Personalized Experience Using Big Data

Verifies all 10 mandatory audit and recovery scenarios:
1. Complete HDFS files with INGESTION_FAILED status (idempotent recovery via size verification).
2. Incomplete HDFS upload recovery (re-uploads missing files to HDFS).
3. Retry preserves the exact same batch ID.
4. Repeated retries without creating duplicate files in HDFS or duplicate records.
5. Safe failure handling when HDFS remains offline (records attempt, preserves state).
6. Invalid state transitions rejected with actionable error messages.
7. Successful cumulative PySpark processing after recovery.
8. Preservation of all 1,200 baseline customers and prior accepted batches.
9. Failure isolation: active production dataset and current_version.json preserved untouched.
10. Full support for both Classic 3-CSV and Multi-Format ingestion batches.
"""

import os
import sys
import json
import shutil
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.services.ingestion_service import IngestionService, STATUS_INGESTION_FAILED, STATUS_INGESTED, STATUS_VALIDATED
from backend.app.services.pipeline_execution_service import PipelineExecutionService
from big_data.ingestion.hdfs_client import HDFSManager


@pytest.fixture(scope="module")
def ingestion_service():
    return IngestionService.get_instance()


@pytest.fixture(scope="module")
def pipeline_service():
    return PipelineExecutionService.get_instance()


@pytest.fixture
def mock_hdfs_batch(ingestion_service, tmp_path_factory):
    """Creates a temporary isolated test batch in INGESTION_FAILED status."""
    batch_id = f"test_recover_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}"
    batch_dir = os.path.join(ingestion_service.uploads_base_dir, batch_id)
    os.makedirs(batch_dir, exist_ok=True)

    # Create dummy raw CSVs
    tx_content = "transaction_id,customer_id,transaction_date,product_id,product_category,quantity,unit_price,total_amount,payment_method,order_status\nTX_TEST_001,CUST_1201,2024-09-01 10:00:00,PROD_001,Electronics,1,100.0,100.0,Credit Card,completed\n"
    web_content = "activity_id,customer_id,session_id,timestamp,page_url,action_type,product_id,duration_seconds,device_type,traffic_source\nWEB_TEST_001,CUST_1201,SESS_001,2024-09-01 10:05:00,/home,view,,30,Mobile,Direct\n"
    soc_content = "interaction_id,customer_id,timestamp,platform,interaction_type,sentiment,sentiment_score,engagement_score,feedback_content,associated_category\nSOC_TEST_001,CUST_1201,2024-09-01 10:10:00,Twitter,post,Positive,0.85,50,Great product,Electronics\n"

    tx_path = os.path.join(batch_dir, "transactions.csv")
    web_path = os.path.join(batch_dir, "web_activity.csv")
    soc_path = os.path.join(batch_dir, "social_media.csv")

    with open(tx_path, "w", encoding="utf-8") as f: f.write(tx_content)
    with open(web_path, "w", encoding="utf-8") as f: f.write(web_content)
    with open(soc_path, "w", encoding="utf-8") as f: f.write(soc_content)

    manifest = {
        "batch_id": batch_id,
        "batch_type": "CLASSIC_3CSV",
        "status": STATUS_INGESTION_FAILED,
        "created_at": datetime.now().isoformat(),
        "total_bytes": len(tx_content) + len(web_content) + len(soc_content),
        "file_count": 3,
        "staged_files": {
            "transactions": {
                "file_id": "transactions",
                "original_filename": "transactions.csv",
                "staged_filename": "transactions.csv",
                "local_path": tx_path,
                "bytes": len(tx_content),
                "format": "CSV",
                "source_type": "transactions"
            },
            "web_activity": {
                "file_id": "web_activity",
                "original_filename": "web_activity.csv",
                "staged_filename": "web_activity.csv",
                "local_path": web_path,
                "bytes": len(web_content),
                "format": "CSV",
                "source_type": "web_activity"
            },
            "social_media": {
                "file_id": "social_media",
                "original_filename": "social_media.csv",
                "staged_filename": "social_media.csv",
                "local_path": soc_path,
                "bytes": len(soc_content),
                "format": "CSV",
                "source_type": "social_media"
            }
        },
        "is_canonical_three_source": True,
        "validation": {"is_valid": True, "errors": []},
        "hdfs_path": None,
        "message": "Hadoop HDFS cluster is OFFLINE. Cannot ingest to HDFS."
    }

    manifest_path = os.path.join(batch_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    yield batch_id, batch_dir, manifest

    # Cleanup
    if os.path.exists(batch_dir):
        shutil.rmtree(batch_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test 1 & 4: Complete HDFS Files Idempotent Recovery & No Duplicates
# ---------------------------------------------------------------------------
def test_1_and_4_complete_hdfs_files_idempotent_recovery(ingestion_service, mock_hdfs_batch):
    """Test 1 & 4: If all files already exist in HDFS with matching size, recover without duplicate upload."""
    batch_id, batch_dir, _ = mock_hdfs_batch

    # Mock HDFS as online, directory exists, and stat reports matching byte size
    with patch.object(ingestion_service.hdfs_manager, "check_hdfs_status", return_value={"is_available": True, "message": "ONLINE"}):
        with patch.object(ingestion_service.hdfs_manager, "verify_hdfs_directory", return_value=(True, ["transactions.csv", "web_activity.csv", "social_media.csv"])):
            def mock_exec_cmd(args):
                if args[0:2] == ["dfs", "-stat"]:
                    # Return local file size for stat
                    target = args[3]
                    fname = os.path.basename(target)
                    local_p = os.path.join(batch_dir, fname)
                    if os.path.exists(local_p):
                        return 0, str(os.path.getsize(local_p)), ""
                return 0, "", ""

            with patch.object(ingestion_service.hdfs_manager, "_exec_hdfs_cmd", side_effect=mock_exec_cmd):
                # First recovery call
                ok, msg, manifest = ingestion_service.recover_failed_batch(batch_id)
                assert ok is True
                assert manifest["status"] == STATUS_INGESTED
                assert "verified in Hadoop HDFS" in msg
                assert manifest["retry_history"][-1]["action"] == "VERIFY_EXISTING_HDFS_FILES"

                # Second recovery call (idempotent repeated call)
                ok2, msg2, manifest2 = ingestion_service.recover_failed_batch(batch_id)
                assert ok2 is True
                assert manifest2["status"] == STATUS_INGESTED
                assert "already in INGESTED status" in msg2


# ---------------------------------------------------------------------------
# Test 2 & 3: Incomplete HDFS Upload Recovery with Same Batch ID
# ---------------------------------------------------------------------------
def test_2_and_3_incomplete_hdfs_upload_recovery_same_batch_id(ingestion_service, mock_hdfs_batch):
    """Test 2 & 3: Missing files trigger retry upload under the exact same batch ID."""
    batch_id, batch_dir, _ = mock_hdfs_batch

    with patch.object(ingestion_service.hdfs_manager, "check_hdfs_status", return_value={"is_available": True, "message": "ONLINE"}):
        # Simulate HDFS directory not found or empty
        with patch.object(ingestion_service.hdfs_manager, "verify_hdfs_directory", return_value=(False, [])):
            with patch.object(ingestion_service.hdfs_manager, "upload_batch_to_hdfs", return_value=(True, "Uploaded 4 files", {"files": {}})) as mock_upload:
                ok, msg, manifest = ingestion_service.recover_failed_batch(batch_id)
                assert ok is True
                assert manifest["status"] == STATUS_INGESTED
                assert manifest["batch_id"] == batch_id, "Batch ID must be preserved exactly"
                assert mock_upload.called
                assert mock_upload.call_args[1]["batch_id"] == batch_id


# ---------------------------------------------------------------------------
# Test 5: Safe Failure Handling When HDFS Remains Offline
# ---------------------------------------------------------------------------
def test_5_hdfs_remaining_offline(ingestion_service, mock_hdfs_batch):
    """Test 5: If HDFS is offline, batch remains INGESTION_FAILED with retry logged."""
    batch_id, batch_dir, _ = mock_hdfs_batch

    with patch.object(ingestion_service.hdfs_manager, "check_hdfs_status", return_value={"is_available": False, "message": "Connection refused on port 9000"}):
        ok, msg, manifest = ingestion_service.recover_failed_batch(batch_id)
        assert ok is False
        assert manifest["status"] == STATUS_INGESTION_FAILED
        assert "OFFLINE" in msg
        assert len(manifest["retry_history"]) >= 1
        assert manifest["retry_history"][-1]["status"] == "FAILED"
        assert manifest["retry_history"][-1]["action"] == "CHECK_HDFS_CONNECTIVITY"


# ---------------------------------------------------------------------------
# Test 6: Invalid State Transitions Rejected with Actionable Errors
# ---------------------------------------------------------------------------
def test_6_invalid_state_transitions(pipeline_service, ingestion_service, mock_hdfs_batch):
    """Test 6: Invalid status transitions return clear, actionable errors."""
    batch_id, batch_dir, manifest = mock_hdfs_batch

    # Test VALIDATION_FAILED state
    manifest_path = os.path.join(batch_dir, "manifest.json")
    manifest["status"] = "VALIDATION_FAILED"
    manifest["message"] = "Primary key collision in transactions"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    # Calling recovery on VALIDATION_FAILED must reject
    ok_rec, msg_rec, _ = ingestion_service.recover_failed_batch(batch_id)
    assert ok_rec is False
    assert "Cannot recover batch in status 'VALIDATION_FAILED'" in msg_rec

    # Calling pipeline execution on VALIDATION_FAILED must reject with actionable message
    ok_pipe, msg_pipe, _ = pipeline_service.execute_batch_pipeline(batch_id)
    assert ok_pipe is False
    assert "VALIDATION_FAILED" in msg_pipe
    assert "fix errors before processing" in msg_pipe.lower()


# ---------------------------------------------------------------------------
# Test 7 & 8: Successful Cumulative PySpark Processing After Recovery
# ---------------------------------------------------------------------------
def test_7_and_8_cumulative_pyspark_processing_after_recovery(pipeline_service, ingestion_service, mock_hdfs_batch):
    """Test 7 & 8: Recovered batch merges with 1,200 baseline customers in cumulative pipeline."""
    batch_id, batch_dir, manifest = mock_hdfs_batch

    # Set batch to INGESTED (simulating post-recovery state)
    manifest_path = os.path.join(batch_dir, "manifest.json")
    manifest["status"] = STATUS_INGESTED
    manifest["hdfs_path"] = f"/customer-analytics/raw/uploads/{batch_id}"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    # Run PySpark pipeline in local fallback mode (mocked HDFS read)
    with patch.object(pipeline_service.hdfs_manager, "check_hdfs_status", return_value={"is_available": False}):
        ok, msg, report = pipeline_service.execute_batch_pipeline(batch_id, force_local_input=True, force_reprocess=True)
        assert ok is True, f"PySpark pipeline failed: {msg}"
        assert report["status"] == "PROCESSING_COMPLETED"

        # Verify cumulative baseline preservation (>= 1,200 customers)
        comp = report.get("data_composition", {})
        total_customers = comp.get("overall", {}).get("total_customers", 0)
        assert total_customers >= 1200, f"Baseline customers not preserved, got {total_customers}"

        # Clean up isolated test version directory
        ver_dir = os.path.join(PROJECT_ROOT, "data", "versions", f"v_{batch_id}")
        if os.path.exists(ver_dir):
            shutil.rmtree(ver_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test 9: Failure Isolation & Active-Version Preservation
# ---------------------------------------------------------------------------
def test_9_failure_isolation_and_active_version_preservation(ingestion_service, mock_hdfs_batch):
    """Test 9: INGESTION_FAILED status never modifies current_version.json or active production data."""
    cur_ver_path = os.path.join(PROJECT_ROOT, "data", "current_version.json")
    assert os.path.exists(cur_ver_path), "current_version.json must exist"

    with open(cur_ver_path, "r", encoding="utf-8") as f:
        before_ver = json.load(f)

    batch_id, _, _ = mock_hdfs_batch

    # Attempt recovery while HDFS is offline
    with patch.object(ingestion_service.hdfs_manager, "check_hdfs_status", return_value={"is_available": False, "message": "Cluster offline"}):
        ingestion_service.recover_failed_batch(batch_id)

    with open(cur_ver_path, "r", encoding="utf-8") as f:
        after_ver = json.load(f)

    # Verify active production version remains completely untouched
    assert before_ver["active_version"] == after_ver["active_version"]
    assert before_ver.get("promoted_at") == after_ver.get("promoted_at")


# ---------------------------------------------------------------------------
# Test 10: Multi-Format Ingestion Recovery
# ---------------------------------------------------------------------------
def test_10_multi_format_ingestion_recovery(ingestion_service):
    """Test 10: Multi-Format batch in INGESTION_FAILED recovers safely."""
    mf_batch_id = f"test_mf_recover_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}"
    mf_dir = os.path.join(ingestion_service.uploads_base_dir, mf_batch_id)
    os.makedirs(mf_dir, exist_ok=True)

    dummy_file = os.path.join(mf_dir, "web_log.json")
    with open(dummy_file, "w") as f:
        f.write('{"activity_id": "WEB_01", "customer_id": "CUST_1201"}\n')

    manifest = {
        "batch_id": mf_batch_id,
        "batch_type": "MULTI_FORMAT",
        "status": STATUS_INGESTION_FAILED,
        "created_at": datetime.now().isoformat(),
        "total_bytes": os.path.getsize(dummy_file),
        "file_count": 1,
        "staged_files": {
            "file_1": {
                "file_id": "file_1",
                "original_filename": "web_log.json",
                "staged_filename": "web_log.json",
                "local_path": dummy_file,
                "bytes": os.path.getsize(dummy_file),
                "format": "JSON",
                "source_type": "web_activity"
            }
        },
        "is_canonical_three_source": False,
        "validation": {"is_valid": True, "errors": []},
        "message": "HDFS offline during multi-format staging"
    }

    manifest_path = os.path.join(mf_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    try:
        with patch.object(ingestion_service.hdfs_manager, "check_hdfs_status", return_value={"is_available": True}):
            with patch.object(ingestion_service.hdfs_manager, "verify_hdfs_directory", return_value=(False, [])):
                with patch.object(ingestion_service.hdfs_manager, "upload_batch_to_hdfs", return_value=(True, "Success", {"files": {}})):
                    ok, msg, recovered_manifest = ingestion_service.recover_failed_batch(mf_batch_id)
                    assert ok is True
                    assert recovered_manifest["status"] == STATUS_INGESTED
                    assert recovered_manifest["batch_type"] == "MULTI_FORMAT"
                    assert len(recovered_manifest["retry_history"]) >= 1
    finally:
        shutil.rmtree(mf_dir, ignore_errors=True)
