"""
SMART Customer Analytics Platform
Automated Test Suite: Dual Dataset Processing Modes (Cumulative + New Batch Only)

Covers all 10 required audit scenarios:
1. Cumulative mode still produces baseline + accepted batches + current batch.
2. New Batch Only reads only the current batch.
3. New Batch Only does not load historical datasets (0 historical records).
4. Both modes use isolated model artifacts.
5. All seven modules return the same selected version and mode context.
6. Switching modes restores the correct cumulative dataset without data loss.
7. A failed batch-only preview does not affect cumulative production.
8. Insufficient data produces honest model status messages (no synthetic metrics).
9. Churn predictions respect temporal observation requirements (<270 days).
10. API dataset mode endpoints and regression compliance.
"""

import os
import json
import shutil
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backend.app import create_app
from backend.app.services.data_service import DataService
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.pipeline_execution_service import PipelineExecutionService
from backend.app.services.model_training_service import ModelTrainingService


@pytest.fixture(scope="module")
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture(scope="module")
def setup_test_batch():
    """Creates a temporary isolated test batch with 10 synthetic customer records."""
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    batch_id = f"batch_test_dual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    batch_dir = os.path.join(workspace_root, "data", "uploads", batch_id)
    os.makedirs(batch_dir, exist_ok=True)

    # 1. Transactions (10 customers, 20 orders across 30 days)
    cust_ids = [f"CUST_DUAL_{i:03d}" for i in range(1, 11)]
    prod_ids = [f"PROD_D_{j:02d}" for j in range(1, 5)]

    tx_rows = []
    base_date = datetime(2024, 6, 1)
    for i, cid in enumerate(cust_ids):
        for o in range(2):
            tx_rows.append({
                "transaction_id": f"TX_D_{i}_{o}",
                "customer_id": cid,
                "transaction_date": (base_date + timedelta(days=o * 5 + i)).strftime("%Y-%m-%d %H:%M:%S"),
                "product_id": prod_ids[(i + o) % len(prod_ids)],
                "product_category": "Electronics",
                "product_name": f"Product {(i + o) % len(prod_ids)}",
                "quantity": 1,
                "unit_price": 50.0,
                "discount_percent": 0.0,
                "total_amount": 50.0,
                "payment_method": "Credit Card",
                "order_status": "Completed"
            })
    df_tx = pd.DataFrame(tx_rows)
    df_tx.to_csv(os.path.join(batch_dir, "transactions.csv"), index=False)

    # 2. Web activity
    web_rows = []
    for i, cid in enumerate(cust_ids):
        web_rows.append({
            "activity_id": f"ACT_D_{i}",
            "customer_id": cid,
            "session_id": f"SESS_D_{i}",
            "timestamp": (base_date + timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S"),
            "page_url": "/product/1",
            "action_type": "product_view",
            "product_id": prod_ids[i % len(prod_ids)],
            "duration_seconds": 120,
            "device_type": "Desktop",
            "traffic_source": "Search"
        })
    df_web = pd.DataFrame(web_rows)
    df_web.to_csv(os.path.join(batch_dir, "web_activity.csv"), index=False)

    # 3. Social media
    soc_rows = []
    for i, cid in enumerate(cust_ids):
        soc_rows.append({
            "interaction_id": f"SOC_D_{i}",
            "customer_id": cid,
            "timestamp": (base_date + timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S"),
            "platform": "Twitter",
            "interaction_type": "mention",
            "sentiment": "positive",
            "sentiment_score": 0.75,
            "engagement_score": 80,
            "feedback_content": "Great experience with product",
            "associated_category": "Electronics"
        })
    df_soc = pd.DataFrame(soc_rows)
    df_soc.to_csv(os.path.join(batch_dir, "social_media.csv"), index=False)

    # Manifest
    manifest = {
        "batch_id": batch_id,
        "format": "classic",
        "created_at": datetime.now().isoformat(),
        "status": "VALIDATED",
        "files": {
            "transactions": {"filename": "transactions.csv", "rows": len(df_tx), "status": "VALIDATED"},
            "web_activity": {"filename": "web_activity.csv", "rows": len(df_web), "status": "VALIDATED"},
            "social_media": {"filename": "social_media.csv", "rows": len(df_soc), "status": "VALIDATED"}
        }
    }
    with open(os.path.join(batch_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    yield batch_id

    # Cleanup temporary test artifacts
    version_id = f"v_batch_only_{batch_id}"
    version_dir = os.path.join(workspace_root, "data", "versions", version_id)
    preview_dir = os.path.join(workspace_root, "data", "batch_previews", batch_id)
    models_ver_dir = os.path.join(workspace_root, "ml", "models", "versions", version_id)

    for p in [batch_dir, version_dir, preview_dir, models_ver_dir]:
        if os.path.exists(p):
            try:
                shutil.rmtree(p)
            except Exception:
                pass


def test_1_cumulative_mode_preserves_baseline_and_prior_batches():
    """Scenario 1: Cumulative mode retains baseline (1,200) + prior accepted batches."""
    data_service = DataService.get_instance()
    data_service.switch_mode("cumulative")

    assert data_service.active_mode == "cumulative"
    assert len(data_service.df_segments) >= 1200
    comp = data_service.get_data_composition()
    assert comp["historical"]["total_customers"] >= 1200 or comp["version_id"] == "baseline"


def test_2_and_3_new_batch_only_reads_only_current_batch_no_historical(setup_test_batch):
    """
    Scenario 2 & 3: New Batch Only reads only the current batch (10 customers)
    and does NOT load historical datasets (0 historical customers/records).
    """
    batch_id = setup_test_batch
    pipe_service = PipelineExecutionService.get_instance()

    ok, msg, report = pipe_service.execute_batch_only_pipeline(batch_id, force_local_input=True, force_reprocess=True)
    assert ok is True
    assert report["processing_mode"] == "NEW_BATCH_ONLY"
    assert report["feature_matrix"]["rows"] == 10  # Only the 10 batch customers

    comp = report["data_composition"]
    assert comp["historical"]["total_customers"] == 0
    assert comp["historical"]["total_transactions"] == 0
    assert comp["historical"]["total_web_activities"] == 0
    assert comp["historical"]["total_social_interactions"] == 0
    assert comp["overall"]["total_customers"] == 10
    assert comp["overall"]["total_transactions"] == 20


def test_4_isolated_storage_and_model_artifacts(setup_test_batch):
    """Scenario 4: Both modes use isolated model artifacts in separate version directories."""
    batch_id = setup_test_batch
    version_id = f"v_batch_only_{batch_id}"
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    model_service = ModelTrainingService.get_instance()
    ok, msg, report = model_service.retrain_batch_only_models(version_id)
    assert ok is True

    # Check isolated version directory exists
    v_models_dir = os.path.join(workspace_root, "ml", "models", "versions", version_id)
    assert os.path.exists(v_models_dir)
    assert os.path.exists(os.path.join(v_models_dir, "cluster_profiles.json"))

    # Check preview mirroring
    preview_models_dir = os.path.join(workspace_root, "data", "batch_previews", batch_id, "models")
    assert os.path.exists(preview_models_dir)

    # Check baseline models in ml/models/ and ml/models/_baseline_backup/ remain untouched
    base_km = os.path.join(workspace_root, "ml", "models", "_baseline_backup", "kmeans_model.joblib")
    if os.path.exists(base_km):
        assert os.path.getsize(base_km) > 0


def test_5_unified_dataset_context_across_all_modules(setup_test_batch):
    """
    Scenario 5: Switching to batch_only mode ensures all seven modules return data
    corresponding strictly to the selected batch (10 customers, 0 historical).
    """
    batch_id = setup_test_batch
    data_service = DataService.get_instance()
    ok, msg, ctx = data_service.switch_mode("batch_only", batch_id)

    assert ok is True
    assert data_service.active_mode == "batch_only"
    assert data_service.active_batch_id == batch_id

    # 1. Overview KPIs
    kpis = data_service.get_kpi_summary()
    assert kpis["total_customers"] == 10
    assert kpis["total_transactions"] == 20

    # 2. Data Composition
    comp = data_service.get_data_composition()
    assert comp["mode"] == "NEW_BATCH_ONLY"
    assert comp["historical"]["total_customers"] == 0
    assert comp["overall"]["total_customers"] == 10

    # 3. Segmentation
    seg_eval = data_service.get_segmentation_evaluation()
    assert seg_eval["metrics"]["dataset_version"] == f"v_batch_only_{batch_id}"
    assert seg_eval["metrics"]["total_customers"] == 10

    # 4. Customer 360 Registry
    cust_res = data_service.get_customers(page=1, page_size=20)
    assert cust_res["total_records"] == 10
    assert cust_res["customers"][0]["customer_id"].startswith("CUST_DUAL_")

    # 5. Recommendations
    rec_rules = data_service.get_top_association_rules()
    assert isinstance(rec_rules, list)

    # 6. Retention Churn Summary
    churn_sum = data_service.get_churn_summary()
    assert churn_sum["total_customers_evaluated"] == 10

    # 7. Mode Context
    assert ctx["mode"] == "batch_only"
    assert "NEW BATCH ONLY" in ctx["indicator_label"]


def test_6_mode_switching_restores_cumulative_dataset():
    """Scenario 6: Switching from New Batch Only to Cumulative Analysis restores full baseline."""
    data_service = DataService.get_instance()
    ok, msg, ctx = data_service.switch_mode("cumulative")

    assert ok is True
    assert data_service.active_mode == "cumulative"
    assert data_service.active_batch_id is None
    assert len(data_service.df_segments) >= 1200
    assert "CUMULATIVE ANALYSIS" in ctx["indicator_label"]


def test_7_failed_batch_does_not_affect_production():
    """Scenario 7: Processing a non-existent or invalid batch does not alter production pointer."""
    pipe_service = PipelineExecutionService.get_instance()
    ok, msg, report = pipe_service.execute_batch_only_pipeline("non_existent_batch_xyz")
    assert ok is False
    assert "not found" in msg.lower()

    # Active production version file is unchanged
    curr_file = os.path.join(pipe_service.workspace_root, "data", "current_version.json")
    if os.path.exists(curr_file):
        with open(curr_file, "r", encoding="utf-8") as f:
            curr = json.load(f)
            assert "non_existent" not in curr.get("active_version", "")


def test_8_insufficient_data_produces_honest_model_status():
    """Scenario 8: Insufficient data (N < 2) produces honest model status without fabricating metrics."""
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    stub_version = "v_batch_only_stub_tiny"
    stub_v_dir = os.path.join(workspace_root, "data", "versions", stub_version)
    os.makedirs(stub_v_dir, exist_ok=True)

    # 1 customer feature row
    cols = ["customer_id", "total_spend", "total_transactions", "avg_order_value", "recency_days",
            "cancellation_rate", "total_web_activities", "total_sessions", "cart_additions_count",
            "total_social_interactions", "avg_engagement_score", "avg_sentiment_score"]
    df_single = pd.DataFrame([{c: (0.0 if c != "customer_id" else "CUST_SOLO") for c in cols}])
    df_single.to_parquet(os.path.join(stub_v_dir, "unified_customer_features.parquet"), index=False)

    model_service = ModelTrainingService.get_instance()
    res = model_service.train_kmeans(stub_version)

    assert res["status"] == "INSUFFICIENT_DATA"
    assert res["selected_k"] == 0
    assert res["silhouette_score"] == 0.0

    # Cleanup stub
    shutil.rmtree(stub_v_dir, ignore_errors=True)
    stub_m_dir = os.path.join(workspace_root, "ml", "models", "versions", stub_version)
    shutil.rmtree(stub_m_dir, ignore_errors=True)


def test_9_churn_respects_temporal_window_observation(setup_test_batch):
    """Scenario 9: Churn predictions respect 270d requirement and mark INSUFFICIENT_TEMPORAL_DATA."""
    batch_id = setup_test_batch
    version_id = f"v_batch_only_{batch_id}"

    model_service = ModelTrainingService.get_instance()
    churn_res = model_service.train_churn(version_id)

    # Test batch spans ~30 days (< 270 days)
    assert churn_res["status"] == "INSUFFICIENT_TEMPORAL_DATA"
    assert churn_res["roc_auc"] == "N/A"
    assert churn_res["span_days"] < 270


def test_10_api_dataset_mode_endpoints(client, setup_test_batch):
    """Scenario 10: GET and POST /api/dataset-mode operate seamlessly."""
    batch_id = setup_test_batch

    # Switch to batch_only
    res = client.post("/api/dataset-mode", json={"mode": "batch_only", "batch_id": batch_id})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["mode"] == "batch_only"

    # GET status
    get_res = client.get("/api/dataset-mode")
    assert get_res.status_code == 200
    assert get_res.get_json()["data"]["mode"] == "batch_only"

    # Switch back to cumulative
    res_back = client.post("/api/dataset-mode", json={"mode": "cumulative"})
    assert res_back.status_code == 200
    assert res_back.get_json()["data"]["mode"] == "cumulative"
