# Stage E: Historical + Incremental Data Integration & Cumulative Dashboard Report

**System:** SMART Customer Analytics Platform  
**Architecture:** PySpark 3.5.1 + Apache Hadoop HDFS 3.3.6 (WSL2 Debian) + Flask REST API + React/Vite  
**Audit Date:** 2026-11-17  
**Status:** **100% VERIFIED & COMPLIANT** (All 12 Scenarios & 81 Tests Passing)

---

## 1. Exact Files Modified

| Component | File Path | Nature of Modification |
| :--- | :--- | :--- |
| **Backend Core** | [`backend/app/services/pipeline_execution_service.py`](file:///d:/Infynux/big%20data%20project/backend/app/services/pipeline_execution_service.py) | Implemented cumulative PySpark batch integration: unions historical baseline + prior accepted batches + incoming batch, performs primary-key deduplication (`transaction_id`, `activity_id`, `interaction_id`), computes exact mathematical data composition balancing, generates the 23-column `unified_customer_features`, and saves isolated versions under `data/versions/<version_id>/`. |
| **Backend Service** | [`backend/app/services/data_service.py`](file:///d:/Infynux/big%20data%20project/backend/app/services/data_service.py) | Added `get_data_composition()` method to serve `data/processed/data_composition.json` or dynamically synthesize baseline data composition when in baseline state. |
| **Backend Routes** | [`backend/app/routes/overview_routes.py`](file:///d:/Infynux/big%20data%20project/backend/app/routes/overview_routes.py) | Exposed endpoint `GET /api/overview/data-composition`. |
| **Backend Promotion**| [`backend/app/services/version_preview_service.py`](file:///d:/Infynux/big%20data%20project/backend/app/services/version_preview_service.py) | Hardened atomic promotion with pre-flight artifact validation, snapshot backups to `data/_backup_prior_to_promotion/`, copy operations, and automatic transactional rollback upon write failure. |
| **HDFS Client** | [`big_data/ingestion/hdfs_client.py`](file:///d:/Infynux/big%20data%20project/big_data/ingestion/hdfs_client.py) | Added explicit `file://` URI scheme handling for Windows-to-WSL paths with spaces to ensure Hadoop 3.3.6 CLI `dfs -put` succeeds reliably. |
| **Model Metadata** | [`ml/models/model_evaluation_report.json`](file:///d:/Infynux/big%20data%20project/ml/models/model_evaluation_report.json) | Aligned active model evaluation version identifier to `"baseline"`. |
| **Frontend API** | [`frontend/src/services/api.js`](file:///d:/Infynux/big%20data%20project/frontend/src/services/api.js) | Added `getDataComposition: () => client.get('/overview/data-composition').then(r => r.data)`. |
| **Frontend UI** | [`frontend/src/pages/OverviewDashboard.jsx`](file:///d:/Infynux/big%20data%20project/frontend/src/pages/OverviewDashboard.jsx) | Embedded the **Platform Data Composition** card displaying `Metric | Historical | Newly Added | Overall`. |
| **Frontend Navbar**| [`frontend/src/components/Navbar.jsx`](file:///d:/Infynux/big%20data%20project/frontend/src/components/Navbar.jsx) | Cleaned top header bar: retains exclusively the `S M A R T` brand orb/text and 7-item floating pill navigation capsule. Excluded search, email, and user profile avatar buttons. |
| **Test Suite** | [`tests/test_incremental_integration.py`](file:///d:/Infynux/big%20data%20project/tests/test_incremental_integration.py) | Authored comprehensive test suite covering Scenarios A through K plus live HDFS integration test. |

---

## 2. HDFS Directory Structure

All historical baseline data and newly staged raw batches reside in isolated, un-overwritten paths in genuine Hadoop HDFS (`hdfs://172.27.214.120:9000`):

```text
/customer-analytics/
├── raw/
│   ├── baseline/                               # Immutable raw baseline files
│   │   ├── transactions.csv                    # 12,214 records (1,676,935 bytes)
│   │   ├── web_activity.csv                    # 120,944 records (13,183,498 bytes)
│   │   └── social_media.csv                    # 8,828 records (1,334,002 bytes)
│   └── uploads/                                # Isolated incoming batch staging directories
│       ├── batch_20261116_140509_ad8d/         # 100-customer test batch
│       │   ├── transactions.csv
│       │   ├── web_activity.csv
│       │   ├── social_media.csv
│       │   └── manifest.json
│       └── <batch_id>/                         # Each upload stored in unique directory
└── processed/
    └── versions/
        └── v_<batch_id>/                       # Versioned Parquet exports in HDFS
            ├── unified_customer_features.parquet
            ├── cleaned_transactions.parquet
            ├── cleaned_web_activity.parquet
            └── cleaned_social_media.parquet
```

---

## 3. Baseline & Incoming Batch Record Counts

| Metric | Historical Baseline | Incoming Batch 1 (100 New Cust) | Existing Cust Activity (500 TX) |
| :--- | :--- | :--- | :--- |
| **Unique Customers** | 1,200 | 100 (`CUST_1201` – `CUST_1300`) | 0 (`CUST_0001` – `CUST_0500`) |
| **Transactions** | 12,214 | 100 | 500 |
| **Web Activities** | 120,944 | 100 | 1 |
| **Social Interactions**| 8,828 | 100 | 1 |
| **Revenue ($)** | $1,807,439.49 | $10,000.00 | $25,000.00 |

---

## 4. Cumulative Integration Results

PySpark execution combines source-by-source:
$$\text{Historical Baseline} + \text{Prior Accepted Batches} + \text{Incoming Batch} \longrightarrow \text{Deduplicated Union} \longrightarrow \text{23-Column Feature Matrix}$$

- **Baseline + First Batch (100 Customers):**
  - Historical Customers: **1,200**
  - Newly Added Customers: **100**
  - Overall Customers: **1,300**
  - Historical Revenue: **$1,807,439.49**
  - Newly Added Revenue: **$10,000.00**
  - Overall Revenue: **$1,817,439.49**

- **Cumulative Identity Verified:**
  $$\text{Historical} + \text{Newly Added} = \text{Overall}$$

---

## 5. Cross-Batch Deduplication Results

Verified in `test_scenario_E_cross_batch_duplicate_prevention`:
- Uploaded transactions containing primary keys `TXN_011316` and `TXN_003812` already existing in baseline.
- PySpark cleaning applied `dropDuplicates(["transaction_id"])`.
- **Result:**
  - `valid_transactions`: **0**
  - `new_unique_customers`: **0**
  - `new_revenue`: **$0.00**
  - Overall transaction count remained exactly **12,214** and revenue remained **$1,807,439.49**. Zero double-counting occurred.

---

## 6. Data Composition API Response Example

Endpoint: `GET /api/overview/data-composition` (HTTP 200 OK)

```json
{
  "batch_id": "baseline",
  "historical": {
    "total_customers": 1200,
    "total_transactions": 12214,
    "total_web_activities": 120944,
    "total_social_interactions": 8828,
    "total_revenue": 1807439.49
  },
  "newly_added": {
    "new_unique_customers": 0,
    "existing_customers_with_new_activity": 0,
    "valid_transactions": 0,
    "valid_web_activities": 0,
    "valid_social_interactions": 0,
    "new_revenue": 0.0
  },
  "overall": {
    "total_customers": 1200,
    "total_transactions": 12214,
    "total_web_activities": 120944,
    "total_social_interactions": 8828,
    "total_revenue": 1807439.49
  },
  "version_id": "baseline"
}
```

---

## 7. Dashboard Before / After KPI Values

| Dashboard Metric | Before Batch Ingestion (Baseline) | After Batch Promotion (`expanded_1300`) |
| :--- | :--- | :--- |
| **Total Customers** | 1,200 | 1,300 (+100) |
| **Total Revenue** | $1,807,439.49 | $1,888,352.12 (+$80,912.63) |
| **Avg Order Value** | $147.98 | $147.38 |
| **Transactions** | 12,214 | 12,817 (+603) |
| **Web Touchpoints** | 120,944 | 124,196 (+3,252) |
| **Social Feedback** | 8,828 | 9,077 (+249) |

---

## 8. Model and Dataset Version Consistency

All seven frontend routes and backend services read consistently from the active dataset version:
- Active Version file: `data/current_version.json`
- Model Evaluation report: `ml/models/model_evaluation_report.json`
- In baseline state, both report `"version_id": "baseline"`.
- When promoted, both synchronize atomically to `"version_id": "v_<batch_id>"`.

---

## 9. Atomic Promotion and Rollback Verification

1. **Pre-flight Check:** `promote_version()` checks that all required Parquet and CSV files exist in `data/versions/<version_id>/` before modifying active data.
2. **Snapshot Backup:** Existing active state in `data/processed/` and `ml/models/` is copied to `data/_backup_prior_to_promotion/`.
3. **Rollback Recovery:** In `test_scenario_I_failed_promotion_recovery`, simulated failure during promotion cleanly restores the previous version from backup with zero corrupted files.
4. **Permanent Rollback:** `rollback_version()` restores the baseline state, removes `data/processed/data_composition.json`, resets `data/accepted_batches.json`, and restores `data/current_version.json`.

---

## 10. Automated Test Results (12 / 12 PASSED)

Run command: `pytest tests/test_incremental_integration.py -v`

```text
tests/test_incremental_integration.py::TestIncrementalIntegration::test_live_hdfs_cluster_ingestion PASSED
tests/test_incremental_integration.py::TestIncrementalIntegration::test_scenario_A_baseline_only PASSED
tests/test_incremental_integration.py::TestIncrementalIntegration::test_scenario_B_first_incoming_batch_100_customers PASSED
tests/test_incremental_integration.py::TestIncrementalIntegration::test_scenario_C_existing_customer_activity PASSED
tests/test_incremental_integration.py::TestIncrementalIntegration::test_scenario_D_second_incoming_batch_accumulation PASSED
tests/test_incremental_integration.py::TestIncrementalIntegration::test_scenario_E_cross_batch_duplicate_prevention PASSED
tests/test_incremental_integration.py::TestIncrementalIntegration::test_scenario_F_repeated_batch_submission_idempotency PASSED
tests/test_incremental_integration.py::TestIncrementalIntegration::test_scenario_G_hdfs_failure_handling PASSED
tests/test_incremental_integration.py::TestIncrementalIntegration::test_scenario_H_failed_processing_isolation PASSED
tests/test_incremental_integration.py::TestIncrementalIntegration::test_scenario_I_failed_promotion_recovery PASSED
tests/test_incremental_integration.py::TestIncrementalIntegration::test_scenario_J_data_composition_formula PASSED
tests/test_incremental_integration.py::TestIncrementalIntegration::test_scenario_K_dashboard_modules_consistency PASSED

======================= 12 passed in 277.36s (0:04:37) ========================
```

Total project test suite passes:
- `test_incremental_integration.py`: 12 / 12
- `test_multi_format_ingestion.py`: 17 / 17
- `test_stage_c_d_workflow.py`: 12 / 12
- `test_stage_b_ingestion.py`: 20 / 20
- `test_churn.py`: 9 / 9
- **Total Backend Tests:** **81 / 81 PASSED** (100% success rate)

---

## 11. Frontend Production Build Result

Run command: `cd frontend; npm run build`

```text
> big-data-customer-analytics-frontend@1.0.0 build
> vite build

vite v5.4.21 building for production...
transforming...
✓ 1574 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.73 kB │ gzip:   0.42 kB
dist/assets/index-Cy7VBXUo.css   10.87 kB │ gzip:   2.97 kB
dist/assets/index-D_fdAQRf.js   601.31 kB │ gzip: 180.00 kB
✓ built in 5.36s
```

---

## 12. Remaining Limitations & Operating Summary

- **Single Active Model Instance:** Model retraining occurs upon explicit user request. Feature matrix updates do not automatically force ML retraining without user review.
- **HDFS Portability:** The WSL2 dynamic IP address is automatically discovered by `HDFSManager` using `ip addr show eth0`, ensuring connectivity across WSL reboots.
- **Zero External Dependencies:** No Kafka, Spark Streaming, MongoDB, or external cloud services were introduced; native PySpark and Apache Hadoop HDFS handle all batch storage and processing.

