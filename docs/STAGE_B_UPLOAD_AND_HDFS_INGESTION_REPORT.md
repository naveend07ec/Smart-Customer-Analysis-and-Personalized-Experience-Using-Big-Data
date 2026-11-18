# Stage B — Complete Dataset Upload & Raw HDFS Ingestion Report

**Project Title:** Smart Customer Analysis and Personalized Experience Using Big Data  
**Stage:** Stage B — Complete Dataset Upload (Full Replacement Batch) & Raw HDFS Ingestion  
**Environment:** Windows 11 Host + WSL2 Debian (Hadoop 3.3.6 HDFS) + PySpark 3.5.1 + Flask 3.1 + React 18  
**Date of Implementation:** November 16, 2026  
**Status:** **IMPLEMENTED, VERIFIED & PASSING (40/40 TESTS OK)**

---

## 1. Executive Summary

Stage B extends the SMART Customer Analytics Platform with an additive, student-friendly data upload and raw HDFS distributed ingestion workflow. Students, academic reviewers, and evaluators can upload complete replacement batches containing all three multi-source datasets:
1. `transactions.csv`
2. `web_activity.csv`
3. `social_media.csv`

Every upload is isolated under a unique batch directory (`data/uploads/<batch_id>/`), strictly validated for schema, syntax, ranges, primary keys, and customer coverage, and upon confirmation transferred directly into Apache Hadoop 3.3.6 HDFS (`/customer-analytics/raw/uploads/<batch_id>/`) with byte-size verification.

### Scope & Protection Rules Verified
- **Baseline Immutability:** Baseline raw datasets (`data/raw/`), processed feature matrices (`data/processed/`), machine learning models (`ml/models/`), and baseline HDFS directories (`/customer-analytics/raw/baseline/`, `/customer-analytics/processed/baseline/`) were **not modified, overwritten, or regenerated**.
- **No Heavy Infrastructure Creep:** No Kafka, Spark Streaming, MongoDB, Docker, or external cloud services introduced.
- **Fail-Safe HDFS Ingestion:** When Hadoop HDFS daemons are stopped or offline, the system halts with an informative error message (`HTTP 503: Hadoop HDFS cluster is OFFLINE. Cannot ingest to HDFS.`), preserves the validation report, and prevents silent local fallback.
- **Stage B Boundaries Preserved:** PySpark batch cleaning, feature matrix regeneration, model retraining, and active-version promotion have **not** been executed, cleanly preserving all boundaries for Stage C.

---

## 2. Codebase Inventory: Files Created and Modified

### 2.1 Files Created
| File Path | Description |
| :--- | :--- |
| `big_data/ingestion/validator.py` | Complete syntactic, schema, numeric range, categorical enum, primary-key uniqueness, and cross-source customer coverage validation engine. Reuses constants from `schemas.py`. |
| `backend/app/services/ingestion_service.py` | Coordinates multi-file staging, SHA-256 checksum generation, validation execution, manifest serialization, HDFS upload verification, and batch status lifecycle tracking. |
| `backend/app/routes/ingestion_routes.py` | Exposes REST endpoints (`/api/ingestion/upload`, `/validate/<id>`, `/commit/<id>`, `/status/<id>`, `/history`). |
| `frontend/src/components/StudentDatasetUpload.jsx` | Apple-inspired minimal dark UI upload component featuring 3-file dropzones, selection checklist, detailed validation metrics, warnings/errors accordions, HDFS commit action, and batch history table. |
| `tests/test_stage_b_ingestion.py` | Comprehensive test suite containing 20 automated test cases verifying upload, validation, null handling, HDFS failures, size mismatches, and backward compatibility. |
| `docs/STAGE_B_UPLOAD_AND_HDFS_INGESTION_REPORT.md` | This completion report and student demonstration guide. |

### 2.2 Files Modified (Minimal & Additive)
| File Path | Modifications Made |
| :--- | :--- |
| `big_data/ingestion/hdfs_client.py` | Enhanced `HDFSManager` with `get_wsl_ip()` dynamic resolution, `upload_batch_to_hdfs()`, and remote file-size verification (`hdfs dfs -stat %b`). No hardcoded IPs. |
| `backend/app/__init__.py` | Registered `ingestion_bp` under `/api/ingestion` and alias `/api/pipeline/ingest`. |
| `frontend/src/services/api.js` | Added API client helper methods (`uploadBatch`, `validateBatch`, `commitBatchToHDFS`, `getBatchStatus`, `getBatchHistory`). |
| `frontend/src/pages/DataProcessing.jsx` | Integrated `<StudentDatasetUpload />` component directly below environment architecture cards. |

---

## 3. Upload & Ingestion Architecture

```
[ Student / Evaluator UI: React 18 Data Pipeline Page ]
                     │  (Drag & Drop / Select 3 CSVs)
                     ▼
[ Flask REST API: POST /api/ingestion/upload ]
                     │
                     ├──> 1. IngestionService.stage_batch()
                     │     ├── Verify all 3 required files present
                     │     ├── Generate batch_id: batch_YYYYMMDD_HHMMSS_<hex>
                     │     ├── Save original CSVs untouched to data/uploads/<batch_id>/
                     │     └── Compute SHA-256 checksums & file sizes in manifest.json
                     │
                     ├──> 2. DatasetValidator.validate_batch()
                     │     ├── Check headers against big_data/ingestion/schemas.py
                     │     ├── Validate data types & ISO timestamps
                     │     ├── Check numeric ranges (qty > 0, price > 0, duration >= 0, score [-1, 1])
                     │     ├── Check domain enums (order_status, action_type, sentiment)
                     │     ├── Check primary key uniqueness & report duplicate rows
                     │     ├── Compute cross-source customer coverage (all 3 vs 2 vs 1 source)
                     │     ├── Preserve meaningful nulls (product_id for navigation, payment_method for PySpark)
                     │     └── Status -> VALIDATED (or VALIDATION_FAILED)
                     │
                     ▼
[ Student Confirmation: POST /api/ingestion/commit/<batch_id> ]
                     │
                     ├──> 3. HDFSManager.check_hdfs_status()
                     │     └── If OFFLINE: Halt with HTTP 503 and clear WSL prompt
                     │
                     └──> 4. HDFSManager.upload_batch_to_hdfs()
                           ├── Create /customer-analytics/raw/uploads/<batch_id>/
                           ├── Put original untouched CSVs and manifest.json
                           ├── Verify file sizes: hdfs dfs -stat %b
                           └── Status -> INGESTED (Verified in HDFS)
```

---

## 4. Validation Rules Implemented

| Dataset | Column | Type | Validation Rules & Handling |
| :--- | :--- | :--- | :--- |
| **All** | Files | Files | All 3 files (`transactions.csv`, `web_activity.csv`, `social_media.csv`) must be submitted together. Reject partial batches. |
| **All** | Format | Encoding | UTF-8 compliant CSV. Rejects empty (0-byte) files or files exceeding 50 MB limit. |
| **All** | Headers | Strings | Must match exact schema columns in `big_data/ingestion/schemas.py`. |
| **Transactions** | `transaction_id` | String | Primary Key. Uniqueness checked; duplicates flagged with exact row numbers. |
| **Transactions** | `customer_id` | String | Pattern matching `CUST_\d+`. Cross-referenced against web and social sources. |
| **Transactions** | `transaction_date` | Timestamp | Valid ISO format (`YYYY-MM-DD HH:MM:SS` or `YYYY-MM-DD`). |
| **Transactions** | `quantity` | Integer | Strictly positive ($> 0$). |
| **Transactions** | `unit_price` | Float | Strictly positive ($> 0.0$). |
| **Transactions** | `discount_percent`| Float | Bounded range $[0.0, 100.0]$. |
| **Transactions** | `total_amount` | Float | Strictly positive ($> 0.0$). |
| **Transactions** | `payment_method` | String | Nullable. Missing values produce a non-blocking warning: *auto-imputed to 'Unknown' by PySpark*. |
| **Transactions** | `order_status` | String | Must be in `{"Completed", "Pending", "Cancelled", "Refunded"}`. |
| **Web Activity** | `activity_id` | String | Primary Key. Unique ID validation. |
| **Web Activity** | `timestamp` | Timestamp | Valid ISO timestamp. |
| **Web Activity** | `action_type` | String | Must be in `{"page_view", "product_view", "search", "add_to_cart", "remove_from_cart", "wishlist", "checkout_start"}`. |
| **Web Activity** | `product_id` | String | Nullable. Meaningful nulls on home/category navigation pages are preserved. |
| **Web Activity** | `duration_seconds`| Integer | Non-negative integer ($\ge 0$). |
| **Social Media** | `interaction_id` | String | Primary Key. Unique ID validation. |
| **Social Media** | `sentiment` | String | Must be in `{"Positive", "Neutral", "Negative"}`. |
| **Social Media** | `sentiment_score` | Float | Continuous range $[-1.0, 1.0]$. |
| **Social Media** | `engagement_score`| Integer | Bounded integer $[0, 100]$. |

---

## 5. HDFS Directory Hierarchy

```text
hdfs://<WSL_IP>:9000/customer-analytics/
├── raw/
│   ├── baseline/                          <-- Permanent Academic Baseline (IMMUTABLE)
│   │   ├── transactions/transactions.csv  (12,239 records)
│   │   ├── web_activity/web_activity.csv  (120,979 records)
│   │   └── social_media/social_media.csv  (8,828 records)
│   └── uploads/
│       └── <batch_id>/                    <-- Isolated Student Upload Batches (Stage B)
│           ├── transactions.csv           (Original untouched uploaded CSV)
│           ├── web_activity.csv           (Original untouched uploaded CSV)
│           ├── social_media.csv           (Original untouched uploaded CSV)
│           └── manifest.json              (Audit manifest with sizes, SHA-256 & validation)
└── processed/
    └── baseline/                          <-- Active Parquet Feature Matrices (IMMUTABLE)
```

---

## 6. Additive REST API Endpoints

All endpoints are prefixed under `/api/ingestion/` (with `/api/pipeline/ingest` alias):

| HTTP Method | Route | Description | HTTP Codes |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/ingestion/upload` | Multipart upload for all 3 CSVs (`transactions`, `web_activity`, `social_media`). Stages files locally and optionally auto-validates. | `201 Created`, `400 Bad Request` |
| `POST` | `/api/ingestion/validate/<batch_id>` | Runs validation on staged batch. | `200 OK`, `422 Validation Error`, `404 Not Found` |
| `POST` | `/api/ingestion/commit/<batch_id>` | Commits valid batch to HDFS `/customer-analytics/raw/uploads/<batch_id>/` and verifies sizes. | `200 OK`, `503 HDFS Offline`, `400 Error`, `404 Not Found` |
| `GET` | `/api/ingestion/status/<batch_id>` | Polls batch state, manifest, validation report, and HDFS target path (without exposing host internal paths). | `200 OK`, `404 Not Found` |
| `GET` | `/api/ingestion/history` | Returns registered batch history sorted by timestamp descending. | `200 OK` |

---

## 7. Verification & Automated Test Results

### 7.1 Stage B Dedicated Test Suite (`tests/test_stage_b_ingestion.py`)
Ran all 20 required Stage B tests:
```text
test_01_successful_upload_and_validation ... ok
test_02_missing_one_required_csv ... ok
test_03_incorrect_file_extension_api ... ok
test_04_incorrect_headers ... ok
test_05_empty_csv ... ok
test_06_invalid_data_types ... ok
test_07_duplicate_primary_keys ... ok
test_08_invalid_numeric_values ... ok
test_09_invalid_categorical_values ... ok
test_10_invalid_timestamps ... ok
test_11_customer_coverage_reporting ... ok
test_12_meaningful_null_product_ids ... ok
test_13_missing_payment_method_handling ... ok
test_14_hdfs_unavailable_handling ... ok
test_15_hdfs_upload_failure ... ok
test_16_hdfs_size_mismatch ... ok
test_17_successful_hdfs_ingestion ... ok
test_18_batch_isolation ... ok
test_19_existing_api_backward_compatibility ... ok
test_20_history_and_status_polling ... ok

Ran 20 tests in 5.508s — OK (100% Pass)
```

### 7.2 Full Repository Regression Test Suite
Ran all test suites across the repository:
```text
tests/test_api.py (11 tests) .................... ok
tests/test_churn.py (9 tests) ................... ok
tests/test_stage_b_ingestion.py (20 tests) ...... ok

Total: Ran 40 tests in 7.328s — OK (100% Pass)
```

### 7.3 Frontend Production Build Verification
```text
> big-data-customer-analytics-frontend@1.0.0 build
> vite build

vite v5.4.21 building for production...
✓ 1574 modules transformed.
dist/index.html                   0.73 kB │ gzip:   0.42 kB
dist/assets/index-gJOqQj2e.css   10.12 kB │ gzip:   2.82 kB
dist/assets/index-f7t_cRci.js   557.44 kB │ gzip: 172.03 kB
✓ built in 5.13s (0 Errors, 0 Warnings)
```

---

## 8. Confirmation of Baseline Protection

- `data/raw/transactions.csv` (12,239 records, 1,676,935 bytes): **Untouched**
- `data/raw/web_activity.csv` (120,979 records, 13,183,498 bytes): **Untouched**
- `data/raw/social_media.csv` (8,828 records, 1,334,002 bytes): **Untouched**
- `data/processed/unified_feature_matrix.parquet` (1,200 × 23 features): **Untouched**
- `ml/models/` (K-Means, PCA, Scaler, Recommender, Churn): **Untouched**
- Active REST API `/api/overview` reports exact baseline figures: **1,200 Customers, $1.8M Sales, 76.0% Recommender Hit Rate**.

---

## 9. Student Demonstration Procedure

To demonstrate Stage B during an academic review or viva defense:

### Step 1: Start Services
1. **Start Hadoop HDFS (in WSL2 Debian):**
   ```bash
   wsl -d Debian bash -c "export JAVA_HOME=/opt/java/jdk8 && /opt/hadoop/run_hdfs.sh"
   ```
2. **Start Flask REST API (Windows PowerShell):**
   ```powershell
   .venv\Scripts\python.exe backend\app.py
   ```
3. **Start React Frontend (Windows PowerShell):**
   ```powershell
   npm --prefix frontend run dev
   ```

### Step 2: Open Data Pipeline Interface
- Navigate in browser to `http://localhost:3000/pipeline`.
- Observe the **Stage B: Complete Dataset Upload & Raw HDFS Ingestion** interface at the top of the page.

### Step 3: Select Three CSV Files
- In the 3-card dropzone, select:
  1. `data/sample/transactions.csv` (or student CSV)
  2. `data/sample/web_activity.csv`
  3. `data/sample/social_media.csv`
- Observe that each card displays the filename, size in KB/MB, and green readiness badge.
- Notice that the **"Submit Batch for Validation"** button activates only when all 3 files are present.

### Step 4: Submit Batch for Validation
- Click **"Submit Batch for Validation"**.
- View the structured validation report:
  - **Batch ID:** Displayed with unique timestamped identifier (e.g. `batch_20261116_125643_0d82`).
  - **Status:** `VALIDATED` in Apple-styled soft green badge.
  - **Total Records:** Shows transaction, web, and social breakdown.
  - **Customer Coverage:** Shows unique customers and multi-source overlap percentage.
  - **Data Quality:** Green checkmarks for schema, types, primary keys, and ranges.
  - **Warnings:** Displays non-blocking notices (e.g. PySpark auto-imputation of missing payments).

### Step 5: Commit Batch to Hadoop HDFS
- Click **"Commit Batch to Hadoop HDFS"**.
- The frontend transfers the original CSV files into HDFS and verifies their byte sizes.
- The status updates to **`INGESTED TO HDFS`** with verified remote path:
  `/customer-analytics/raw/uploads/<batch_id>`

### Step 6: Verify in HDFS (Terminal Proof for Evaluators)
Run in terminal to inspect the files stored inside Hadoop HDFS:
```powershell
wsl -d Debian bash -c "export JAVA_HOME=/opt/java/jdk8 && /opt/hadoop/hadoop-3.3.6/bin/hdfs dfs -ls /customer-analytics/raw/uploads/<batch_id>"
```
Evaluators will see:
- `transactions.csv`
- `web_activity.csv`
- `social_media.csv`
- `manifest.json`

### Step 7: Explain Stage Boundary to Reviewers
Inform the faculty panel:
> *"Stage B successfully stages and validates the student's multi-source CSV files and stores the original raw copies directly inside Hadoop HDFS. PySpark has not modified the baseline models yet; PySpark batch cleaning, feature extraction, and ML retraining will be executed in Stage C."*

---

## 10. Conclusion & Readiness for Stage C

Stage B is **100% complete, fully verified, and tested**.

The system is ready to proceed to **Stage C — PySpark Batch Processing & Model Retraining** upon user approval.

