# SMART Customer Analytics — Dual Dataset Processing Modes Architecture & Verification Report

**Project:** Smart Customer Analysis and Personalized Experience Using Big Data  
**Scope:** Dual Dataset Processing Modes (Mode 1: Cumulative Analysis vs. Mode 2: New Batch Only)  
**Status:** IMPLEMENTED, AUDITED & VERIFIED  
**Date:** November 2026  

---

## 1. Executive Summary & Objective

In enterprise big data platforms and academic viva demonstrations, processing multi-gigabyte or cumulative historical datasets repeatedly just to evaluate a small incoming batch introduces unnecessary latency.

To address this without compromising data lineage or historical integrity, the SMART Customer Analytics Platform implements **Dual Dataset Processing Modes**:

1. **MODE 1: CUMULATIVE ANALYSIS (ENTERPRISE PRODUCTION)**
   - **Data Scope:** Original Academic Baseline (1,200 customers, 12,214 transactions, $1.8M revenue) + All Previously Accepted Batches + Current Validated Batch.
   - **Guarantees:** Full cross-batch primary-key deduplication, cumulative 23-column PySpark feature matrix generation, complete ML model retraining, versioned candidate generation, and production promotion/rollback controls.
   - **Active Production Integrity:** The active production pointer (`data/current_version.json`) and immutable baseline backup (`data/_baseline_backup/`, `ml/models/_baseline_backup/`) are permanently preserved.

2. **MODE 2: NEW BATCH ONLY (FAST DEMO & ISOLATED PREVIEW)**
   - **Data Scope:** Current Uploaded Batch Only (e.g. 100 new customers, 200 orders).
   - **Guarantees:** Reads only the 3 newly uploaded batch datasets. Runs PySpark cleaning, validation, and feature engineering strictly on batch data. Skips the expensive historical baseline union and baseline model retraining.
   - **Storage Isolation:** All batch-only outputs are saved into `data/versions/v_batch_only_<batch_id>/` and mirrored to `data/batch_previews/<batch_id>/`. The cumulative production pointer is never overwritten.
   - **Mathematical Honesty:** If the batch timespan is $< 270$ days (insufficient for the 180-day feature window + 90-day forward churn observation), churn is honestly recorded as `INSUFFICIENT_TEMPORAL_DATA` without fabricating synthetic labels.

---

## 2. Architecture & Data Processing Flow

```
                      +---------------------------------------+
                      | Raw Staged Batch (data/uploads/<id>/) |
                      +---------------------------------------+
                                          |
                     [ DATASET PROCESSING MODE SELECTOR ]
                                          |
                 +------------------------+------------------------+
                 |                                                 |
                 v                                                 v
   [ MODE 1: CUMULATIVE ANALYSIS ]                 [ MODE 2: NEW BATCH ONLY ]
                 |                                                 |
+------------------------------------+           +------------------------------------+
| 1. Load Baseline (1,200 customers) |           | 1. Load Current Batch Only         |
| 2. Union Accepted Prior Batches    |           | 2. Bypasses Historical Union       |
| 3. Append Current Validated Batch  |           | 3. Clean & Validate Batch PySpark  |
| 4. Cross-Batch Deduplication (PK)  |           | 4. Canonical 23-Col Feature Matrix |
| 5. Cumulative 23-Col Feature Matrix|           | 5. Retrain Models on Batch Only    |
| 6. Full ML Retraining              |           |    - K-Means (N >= 2)              |
| 7. Candidate Version Created       |           |    - Recs (Items >= 2)             |
|    data/versions/v_batch_<id>/     |           |    - Churn (Timeline >= 270d)      |
| 8. Optional Promotion to Live Prod |           | 6. Save Isolated Batch Preview     |
+------------------------------------+           |    data/batch_previews/<batch_id>/ |
                                                 +------------------------------------+
                                                                   |
                                                 +------------------------------------+
                                                 | DataService.switch_mode("batch")   |
                                                 | In-Memory Instant Live Context     |
                                                 | All 7 Website Modules Updated      |
                                                 +------------------------------------+
```

---

## 3. Storage Layout & Isolation Guarantees

Every mode operates within strictly partitioned storage paths:

| Mode | Data Directory | Model Artifacts Directory | Manifest & Composition |
| :--- | :--- | :--- | :--- |
| **Baseline** | `data/processed/` | `ml/models/` | `data/processed/data_composition.json` |
| **Cumulative Candidate** | `data/versions/v_batch_<id>/` | `ml/models/versions/v_batch_<id>/` | `data/versions/v_batch_<id>/data_composition.json` |
| **New Batch Only** | `data/versions/v_batch_only_<id>/` | `ml/models/versions/v_batch_only_<id>/` | `data/batch_previews/<id>/data_composition.json` |

### Non-Negotiable Safety Safeguards:
1. **Never Overwrite Baseline:** Baseline datasets and models (`_baseline_backup/`) are read-only and immutable.
2. **Never Overwrite Production Pointer:** `data/current_version.json` is never updated by a New Batch Only execution.
3. **No Automatic Promotion:** Batch-only previews cannot be promoted to cumulative production.
4. **No Silent Fallback:** While in New Batch Only mode, every API endpoint resolves the batch's isolated datasets. No module falls back to baseline data.

---

## 4. API Endpoints & Contract

### 1. `GET /api/dataset-mode`
Returns active dataset mode and available batch previews:
```json
{
  "status": "success",
  "data": {
    "mode": "batch_only",
    "active_mode": "batch_only",
    "batch_id": "batch_20261119_113909_a6a1",
    "version_id": "v_batch_only_batch_20261119_113909_a6a1",
    "cumulative_version": "v_batch_20261118_131539_cb5c",
    "indicator_label": "NEW BATCH ONLY — batch_20261119_113909_a6a1",
    "available_batch_only": [
      {
        "version_id": "v_batch_only_batch_20261119_113909_a6a1",
        "batch_id": "batch_20261119_113909_a6a1",
        "customer_count": 80,
        "total_revenue": 7912.34
      }
    ]
  }
}
```

### 2. `POST /api/dataset-mode`
Switches the in-memory active dataset context across all 7 platform modules:
```json
// Request Body
{
  "mode": "cumulative" // or "batch_only"
  "batch_id": "batch_20261119_113909_a6a1" // required if mode == "batch_only"
}
```

### 3. `POST /api/ingestion/process-batch-only/<batch_id>`
Executes Mode 2 lightweight PySpark processing and ML retraining:
```json
{
  "status": "success",
  "message": "New Batch Only processed successfully in 28.4s. Switched active mode to NEW BATCH ONLY.",
  "data": {
    "version_id": "v_batch_only_batch_20261119_113909_a6a1",
    "batch_id": "batch_20261119_113909_a6a1",
    "processing_mode": "NEW_BATCH_ONLY",
    "pipeline_report": {
      "stage_timings": {
        "stage_1_ingestion_seconds": 0.05,
        "stage_2_cleaning_seconds": 12.34,
        "stage_3_feature_engineering_seconds": 15.82,
        "total_pipeline_seconds": 28.4
      }
    }
  }
}
```

---

## 5. UI Integration Across All 7 Modules

1. **Persistent Header Bar Pill:**
   - In Cumulative Mode: Displays `● CUMULATIVE ANALYSIS — [version_id]` with purple badge.
   - In New Batch Only Mode: Displays `⚡ NEW BATCH ONLY — [batch_id]` with vibrant cyan badge, accompanied by a quick-action "Switch to Cumulative" button.
2. **Data Pipeline Page:**
   - Includes the **Dataset Processing Mode Selector** card right above the processing action.
   - Allows users to choose between Mode 1 (Cumulative) and Mode 2 (Fast Demo).
   - Displays execution timings breakdown (Stage 1 Ingestion, Stage 2 Cleaning, Stage 3 Feature Engineering, Total Execution Time).
3. **Module Synchronization:**
   - **Dashboard (Overview):** Displays KPIs calculated strictly for the selected mode.
   - **Analytics:** Charts render traffic, revenue, and sentiment of the selected mode.
   - **Segmentation:** PCA scatter plot and segment profiles reflect the selected mode.
   - **Customer 360:** Customer registry lists customers belonging to the active dataset.
   - **Recommendations:** Association rules and collaborative filtering reflect active items.
   - **Retention AI:** Churn probabilities reflect active customers; displays honest timeline limitations if timespan $< 270$ days.
   - **Data Pipeline:** Displays data composition and execution reports for the active mode.

---

## 6. Mathematical & Academic Limitations (Mode 2)

When running **New Batch Only**:
1. **Sample Size Constraints:** If $N < 2$, K-Means cannot cluster; the platform reports `INSUFFICIENT_DATA` rather than throwing errors or inventing clusters.
2. **Interaction Sparsity:** If unique products $< 2$ or orders $< 2$, recommendation models report `INSUFFICIENT_DATA`.
3. **Temporal Incompleteness (Churn):** Forward 90-day churn prediction requires an observation window of $\ge 270$ days (180 days feature observation + 90 days future inactivity label). If a demo batch spans only 30 days, churn risk is marked as `INSUFFICIENT_TEMPORAL_DATA`.

