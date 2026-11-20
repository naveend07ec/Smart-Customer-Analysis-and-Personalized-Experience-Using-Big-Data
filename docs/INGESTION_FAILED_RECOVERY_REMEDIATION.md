# SMART — INGESTION_FAILED Batch Recovery & PySpark Processing Remediation

**Date**: 2026-11-19  
**Engineer**: Antigravity Autonomous Engineering Agent  
**Environment**: SMART Big Data & Customer Analytics Platform  
**Target Failure**: `PySpark processing failed: Cannot process batch in status 'INGESTION_FAILED'. Batch must be VALIDATED, INGESTED, or UPLOADED.`  
**Status**: COMPLETE — 100% Verified with Automated Regression Tests  

---

## 1. Executive Summary & Problem Statement

During incremental data ingestion, batches uploaded while the Apache Hadoop HDFS cluster was offline entered the terminal-like state `INGESTION_FAILED`. When users subsequently clicked **Process New Data** or **Evaluate Old + New Data & Update Main Dashboard**, the execution was halted by the PySpark pipeline guard:

```text
PySpark processing failed: Cannot process batch in status 'INGESTION_FAILED'. Batch must be VALIDATED, INGESTED, or UPLOADED.
```

This forced users to either abandon the batch, manually manipulate status files, or re-upload datasets, risking duplicate files, state drift, and broken lineage.

### Remediation Objectives Achieved:
1. **Safe Idempotent Recovery**: Batches in `INGESTION_FAILED` can recover safely without re-uploading user files or losing batch data.
2. **HDFS File-Size & Checksum Verification**: Before status transitions to `INGESTED`, all raw files in HDFS (`/customer-analytics/raw/uploads/<batch_id>/`) are verified against local staged file sizes using `hdfs dfs -stat %b`.
3. **Same Batch ID Retry**: If files are missing in HDFS, retry ingestion uploads using the **same batch ID**, avoiding duplicate batches or orphaned files.
4. **Resilient State Machine**: Corrected the pipeline execution state machine in `pipeline_execution_service.py` and `ingestion_routes.py` to attempt safe verification/recovery and return actionable errors for invalid transitions.
5. **Cumulative Data Guarantees Preserved**: Cumulative lineage (`Baseline 1,200 customers + Prior Batches + Current Recovered Batch`) and primary-key deduplication remain strictly intact.
6. **Frontend Transparency**: Added an `INGESTION_FAILED` warning banner displaying the exact failure reason, retry history, and a dedicated **Retry HDFS Ingestion** button.

---

## 2. Root Cause Analysis

### The Failure Chain:
1. **HDFS NameNode/DataNode Shutdown**: In WSL2 Debian, background daemons terminated when previous shell sessions closed because no persistent keepalive process was running.
2. **Upload & Commit Attempt**: At 11:34–11:39, the user uploaded batch `batch_20261119_113909_a6a1`. The upload succeeded locally, but `commit_to_hdfs` detected NameNode RPC port 9000 was unreachable.
3. **Status Transition to `INGESTION_FAILED`**: The manifest recorded:
   ```json
   {
     "status": "INGESTION_FAILED",
     "message": "Hadoop HDFS cluster is OFFLINE. Cannot ingest to HDFS. Details: Hadoop NameNode not reachable at 127.0.0.1:9000 or localhost:9000. Start HDFS daemons in WSL.. Start Hadoop daemons in WSL2 and retry."
   }
   ```
4. **Hard Pipeline Rejection**: In `backend/app/services/pipeline_execution_service.py`:
   ```python
   # Line 279 (pre-remediation):
   status = manifest.get("status")
   if status not in ("INGESTED", "VALIDATED", "UPLOADED"):
       return False, f"Cannot process batch in status '{status}'. Batch must be VALIDATED, INGESTED, or UPLOADED.", {}
   ```
   Because `INGESTION_FAILED` was not an accepted processing state, the PySpark execution immediately halted with code 400.
5. **No Recovery Endpoint**: The application provided no mechanism to retry HDFS ingestion for an existing batch without re-uploading from scratch.

---

## 3. Safe Recovery Architecture & Implementation

### A. Dedicated Recovery Logic (`IngestionService.recover_failed_batch`)
Implemented in [backend/app/services/ingestion_service.py](file:///d:/Infynux/big%20data%20project/backend/app/services/ingestion_service.py):

```python
def recover_failed_batch(self, batch_id: str) -> Tuple[bool, str, Dict[str, Any]]:
```

#### Workflow Steps:
1. **Batch Preservation**: Retrieves the existing batch manifest. Preserves `batch_id`, creation timestamp, and local files under `data/uploads/<batch_id>/`.
2. **Local Staged File Integrity**: Verifies that all expected raw data files (`transactions`, `web_activity`, `social_media`, or multi-format files) exist on local disk with valid byte sizes.
3. **HDFS Cluster Health Check**: Calls `self.hdfs_manager.check_hdfs_status()`.
   - If offline: logs the failed attempt into `manifest["retry_history"]`, updates `last_retry_at`, keeps `status = INGESTION_FAILED`, and returns HTTP 503/400 with actionable instructions.
4. **Remote File Audit & Size Verification**:
   - Inspects target HDFS directory `/customer-analytics/raw/uploads/<batch_id>/`.
   - For every staged raw file, executes `hdfs dfs -stat %b <target_file>` to verify exact remote byte size against the local file size.
5. **Case 1: All Raw Files Verified in HDFS (Idempotent Recovery)**:
   - If all files exist and byte sizes match, the files were already written to HDFS.
   - Status transitions idempotently to `INGESTED` without re-uploading.
   - Logs `VERIFY_EXISTING_HDFS_FILES` in `retry_history`.
   - Uploads an updated manifest to HDFS and updates `batches_index.json`.
6. **Case 2: Missing or Incomplete Files in HDFS (Safe Retry)**:
   - If any file is missing or size-mismatched, triggers `upload_batch_to_hdfs` using the **exact same batch ID**.
   - Uses `hdfs dfs -put -f`, replacing any incomplete chunks without creating duplicate files.
   - Upon verified completion, updates status to `INGESTED` and records `RETRY_HDFS_UPLOAD` in `retry_history`.

---

### B. Corrected Processing State Machine (`PipelineExecutionService`)
Updated in [backend/app/services/pipeline_execution_service.py](file:///d:/Infynux/big%20data%20project/backend/app/services/pipeline_execution_service.py):

```python
# Check batch status and handle INGESTION_FAILED recovery
status = manifest.get("status")
if status == "INGESTION_FAILED":
    # Attempt safe recovery if raw files exist in HDFS or can be committed safely
    from backend.app.services.ingestion_service import IngestionService
    rec_ok, rec_msg, rec_manifest = IngestionService.get_instance().recover_failed_batch(batch_id)
    if rec_ok:
        manifest = rec_manifest
        status = manifest.get("status")
    else:
        return False, (
            f"Cannot process batch '{batch_id}' in status 'INGESTION_FAILED'. "
            f"Raw data could not be verified in HDFS ({rec_msg}). "
            f"Ensure Hadoop daemons are running in WSL and click 'Retry HDFS Ingestion'."
        ), {}

if status not in ("INGESTED", "VALIDATED", "UPLOADED"):
    if status == "VALIDATION_FAILED":
        err_detail = manifest.get("message") or "Schema validation errors detected."
        return False, f"Cannot process batch '{batch_id}' in status 'VALIDATION_FAILED'. {err_detail} Please fix errors before processing.", {}
    elif status in ("DISCOVERED", "MAPPING_PENDING"):
        return False, f"Cannot process batch '{batch_id}' in status '{status}'. Batch must be validated before processing.", {}
    else:
        return False, f"Cannot process batch '{batch_id}' in status '{status}'. Batch must be in 'INGESTED', 'VALIDATED', or 'UPLOADED' status.", {}
```

---

### C. API Routes Enhancement (`ingestion_routes.py`)
Updated in [backend/app/routes/ingestion_routes.py](file:///d:/Infynux/big%20data%20project/backend/app/routes/ingestion_routes.py):

- **New Recovery Routes**:
  - `POST /api/ingestion/retry-hdfs/<batch_id>`
  - `POST /api/ingestion/recover/<batch_id>`
- **`commit_batch` Route**: If called on an `INGESTION_FAILED` batch, automatically delegates to `recover_failed_batch`.
- **`evaluate_and_apply` Route**: Attempts safe recovery first when evaluating an `INGESTION_FAILED` batch. If HDFS is offline, returns HTTP 503 with the exact diagnostic message rather than proceeding to an invalid processing state.

---

### D. Frontend Data Pipeline UI Updates
Updated in [frontend/src/components/StudentDatasetUpload.jsx](file:///d:/Infynux/big%20data%20project/frontend/src/components/StudentDatasetUpload.jsx) and [frontend/src/services/api.js](file:///d:/Infynux/big%20data%20project/frontend/src/services/api.js):

1. **Recovery Banner**: When `activeBatch.status === 'INGESTION_FAILED'`, renders an alert card displaying:
   - Batch ID: `HDFS Ingestion Halted for Batch <batch_id>`
   - Detailed message from HDFS client explaining the failure.
   - Retry attempts logged count.
   - **Retry HDFS Ingestion** action button with spinning indicator during retry.
2. **5-Step Progress Bar**: Step 2 ("HDFS Raw Storage") shows a red warning indicator (`! Ingestion Failed`) when ingestion fails.
3. **Advanced Controls**:
   - Button 2 dynamically updates to `"2. Retry HDFS Ingestion"`.
   - Button 3 ("Run PySpark Batch") is disabled while in `INGESTION_FAILED`, preventing invalid transitions.
4. **Duplicate Prevention**: Keeps the existing batch selected throughout the failure and recovery flow, preventing users from creating redundant batches.

---

## 4. Cumulative Data & Lineage Guarantees

The recovery process strictly complies with cumulative big data guarantees:

1. **Academic Baseline Preserved**: All 1,200 original baseline customers and their transactions ($1,807,439.49 revenue) remain untouched in `data/_baseline_backup/` and baseline Parquet storage.
2. **Cumulative Batch Lineage**: Incoming records are merged using:
   $$\text{Dataset}_{\text{cumulative}} = \text{Baseline} \cup \bigcup_{i=1}^{k-1} \text{Batch}_i \cup \text{Batch}_k$$
3. **Primary-Key Deduplication**: PySpark enforces `dropDuplicates(["transaction_id"])`, `dropDuplicates(["activity_id"])`, and `dropDuplicates(["interaction_id"])`.
4. **HDFS File Idempotency**: Staging to `/customer-analytics/raw/uploads/<batch_id>/` overwrites in place via `hdfs dfs -put -f`, preventing file duplication.
5. **Active Dataset Isolation**: A failure in HDFS ingestion or recovery NEVER modifies `data/current_version.json` or the active production dataset.

---

## 5. Verification & Automated Test Results

A dedicated automated test suite was authored in [tests/test_ingestion_recovery.py](file:///d:/Infynux/big%20data%20project/tests/test_ingestion_recovery.py) covering all 10 required scenarios:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.2.1, pluggy-1.7.0
rootdir: D:\Infynux\big data project
collected 7 items

tests/test_ingestion_recovery.py::test_1_and_4_complete_hdfs_files_idempotent_recovery PASSED [ 14%]
tests/test_ingestion_recovery.py::test_2_and_3_incomplete_hdfs_upload_recovery_same_batch_id PASSED [ 28%]
tests/test_ingestion_recovery.py::test_5_hdfs_remaining_offline PASSED   [ 42%]
tests/test_ingestion_recovery.py::test_6_invalid_state_transitions PASSED [ 57%]
tests/test_ingestion_recovery.py::test_7_and_8_cumulative_pyspark_processing_after_recovery PASSED [ 71%]
tests/test_ingestion_recovery.py::test_9_failure_isolation_and_active_version_preservation PASSED [ 85%]
tests/test_ingestion_recovery.py::test_10_multi_format_ingestion_recovery PASSED [100%]

======================== 7 passed in 105.94s (0:01:45) ========================
```

### Regression Suites Verified:
- **K-Means Remediation Suite**: [tests/test_kmeans_remediation.py](file:///d:/Infynux/big%20data%20project/tests/test_kmeans_remediation.py) — **10/10 Passed** (5.38s).
- **Stage B Ingestion Suite**: [tests/test_stage_b_ingestion.py](file:///d:/Infynux/big%20data%20project/tests/test_stage_b_ingestion.py) — **20/20 Passed** (7.86s).
- **Backend REST API Suite**: [tests/test_api.py](file:///d:/Infynux/big%20data%20project/tests/test_api.py) — **11/11 Passed** (5.24s).
- **Frontend Production Build**: `npm run build` — **Built in 6.40s with 0 errors**.

### Live Batch Recovery Verification:
The user's halted batch `batch_20261119_113909_a6a1` was recovered live against Hadoop HDFS:
```text
Recovery Result ok: True
Message: Batch successfully ingested and verified in Hadoop HDFS (/customer-analytics/raw/uploads/batch_20261119_113909_a6a1) on retry.
New Status: INGESTED
HDFS Path: /customer-analytics/raw/uploads/batch_20261119_113909_a6a1
Retry History: [{'attempt': 1, 'status': 'SUCCESS', 'action': 'RETRY_HDFS_UPLOAD', 'message': 'Successfully uploaded and verified 4 files in HDFS.'}]
```

---

## 6. Operational Recommendations for Students & Demonstrators

1. **Keep HDFS Daemons Running**: When demonstrating Hadoop integration, start the WSL HDFS background daemon via:
   ```powershell
   wsl -d Debian bash /mnt/d/Infynux/big\ data\ project/scripts/run_hdfs_daemon.sh
   ```
2. **If HDFS is Temporarily Stopped**: If an upload occurs while HDFS is offline, the UI will clearly display the failure banner with the exact batch ID. Simply start the daemon and click **Retry HDFS Ingestion**. The platform will verify and resume without needing a new batch.
3. **Safe Promotion Guard**: Never promote a candidate batch automatically; preview candidate analytics in Stage 5 before promoting to the live dashboard.

