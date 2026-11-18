# SMART — Post-Promotion Cumulative Dataset Failure Audit

**Audit Date:** 2026-11-17  
**Auditor:** Antigravity Engineering & QA Agent  
**Investigation Mode:** STRICT READ-ONLY AUDIT  
**Audit Target Version:** `v_batch_20261117_171838_f825`  
**Current Active Version:** `baseline` (Rolled back at `2026-11-17T17:22:18.949096`)  

---

## Executive Summary

A severe data degradation incident occurred when version `v_batch_20261117_171838_f825` was promoted to the production dashboard:
- The production customer base collapsed from **1,200** to **8**.
- Transactions collapsed from **12,214** to **9**.
- Web activities collapsed from **120,944** to **10**.
- The Platform Data Composition card reported: **Historical: 8 | Newly Added: 0 | Overall: 8**.
- Machine learning performance severely degraded: K-Means silhouette fell to **0.2552**, Recommendation Hit Rate@5 fell to **0.0%**, and Churn training was skipped.

This strict read-only audit investigated the end-to-end data ingestion, PySpark batch processing, versioning, and promotion mechanisms. The baseline dataset remains **100% intact and uncorrupted** in both local backup and HDFS. The system was successfully rolled back to `baseline` at `17:22:18`.

The root causes have been isolated with forensic evidence:
1. **Primary Defect (Cumulative Pipeline Bypass):** An early-return prototype block in `backend/app/services/pipeline_execution_service.py` (`if is_multi_format:`, lines 285–364) intercepted all staged uploads (which are tagged `"batch_type": "MULTI_FORMAT"` by `ingestion_service.py`). This branch processed *only* the delta batch files in isolation and returned early, completely bypassing steps 2 through 18 of the cumulative pipeline (baseline loading, historical batch unioning, deduplication, and `data_composition.json` creation).
2. **Secondary Defect (Destructive Promotion):** `VersionPreviewService.promote_version()` unconditionally copied all files from `data/versions/<version_id>/` into `data/processed/`, overwriting the entire production dataset with the 8-customer isolated batch without any monotonic row count checks.
3. **Tertiary Defect (Data Composition Fallback):** Because `v_batch_20261117_171838_f825` lacked `data_composition.json`, `DataService.get_data_composition()` fell back to reading row counts from the currently loaded 8-customer `data/processed/` directory, computing Historical = 8, Newly Added = 0, Overall = 8.

---

## 1. Active Version Identification

| Property | Value | Evidence / Source |
|---|---|---|
| **Active Version in Pointer** | `baseline` | `data/current_version.json` |
| **Rolled Back At** | `2026-11-17T17:22:18.949096` | `data/current_version.json` |
| **Target Failed Version** | `v_batch_20261117_171838_f825` | `data/versions/v_batch_20261117_171838_f825/` |
| **Associated Batch ID** | `batch_20261117_171838_f825` | `data/uploads/batch_20261117_171838_f825/` |
| **Status in Index** | `EVALUATION_COMPLETED` | `data/versions/versions_index.json` |
| **Promotion Succeeded?** | YES (Promoted at ~17:18, then immediately rolled back at 17:22) | Confirmed via `_backup_prior_to_promotion` and `current_version.json` |

### Forensic Timeline
1. **17:18:38** — Incremental multi-format batch `batch_20261117_171838_f825` staged in `data/uploads/`.
2. **17:18:51** — PySpark batch pipeline finished. Due to `is_multi_format` short circuit, it generated `v_batch_20261117_171838_f825` containing only the 8 customers from the batch.
3. **17:18:52** — Model training evaluated K-Means (silhouette = 0.2552) and Recommender (Hit Rate@5 = 0.0) on 8 customers.
4. **~17:19:00** — User clicked **Promote Version to Production Dashboard**. `promote_version()` overwrote `data/processed/` with the 8-customer candidate.
5. **17:22:18** — User triggered **Rollback to Baseline**. `rollback_version()` restored `data/processed/` from `data/_baseline_backup/` and set `current_version.json` to `"baseline"`.

**Classification:** **PASS** (Status fully verified and documented).

---

## 2. Baseline Integrity Verification

The baseline was audited across three physical stores: Local Raw (`data/raw/`), Local Baseline Backup (`data/_baseline_backup/`), and Hadoop HDFS (`hdfs://172.27.214.120:9000/customer-analytics/raw/baseline/`).

### Local Datasets Integrity Table

| Dataset | Location | File Size | Record Count | Distinct Customers | SHA-256 (First 16 chars) | Status |
|---|---|---|---|---|---|---|
| **raw/transactions.csv** | `data/raw/` | 1,676,935 bytes | 12,239 | 1,200 | `9dec44e670f2b048` | **INTACT** |
| **raw/web_activity.csv** | `data/raw/` | 13,183,498 bytes | 120,979 | 1,200 | `df2aa8fb00f4b3a7` | **INTACT** |
| **raw/social_media.csv** | `data/raw/` | 1,334,002 bytes | 8,828 | 1,200 | `d6e8c0e63d4e225e` | **INTACT** |
| **backup/cleaned_transactions.csv** | `data/_baseline_backup/` | 1,886,605 bytes | 12,214 | 1,200 | `41516758b314b3f1` | **INTACT** |
| **backup/cleaned_web_activity.csv** | `data/_baseline_backup/` | 15,719,408 bytes | 120,944 | 1,200 | `e7a5406d81e01f47` | **INTACT** |
| **backup/cleaned_social_media.csv** | `data/_baseline_backup/` | 1,505,098 bytes | 8,828 | 1,200 | `68a9ff6b9be5816c` | **INTACT** |
| **backup/customer_segments.csv** | `data/_baseline_backup/` | 163,123 bytes | 1,200 | 1,200 | `a05e74ff1dc7378f` | **INTACT** |
| **backup/unified_customer_features.csv** | `data/_baseline_backup/` | 104,643 bytes | 1,200 | 1,200 | `38afe622f6a21982` | **INTACT** |
| **backup/association_rules.csv** | `data/_baseline_backup/` | 15,314 bytes | 394 rules | N/A | `d4aecd01919def0f` | **INTACT** |
| **backup/customer_churn_predictions.csv**| `data/_baseline_backup/` | 262,189 bytes | 1,177 | 1,177 | `bf0a588b26e06175` | **INTACT** |

### HDFS Baseline Storage Verification
HDFS cluster is **ONLINE** (`hdfs://172.27.214.120:9000` on WSL2 Debian).

| HDFS Remote Path | File Size | Match Local Raw? |
|---|---|---|
| `/customer-analytics/raw/baseline/transactions.csv` | 1,676,935 bytes | **YES (Exact Match)** |
| `/customer-analytics/raw/baseline/web_activity.csv` | 13,183,498 bytes | **YES (Exact Match)** |
| `/customer-analytics/raw/baseline/social_media.csv` | 1,334,002 bytes | **YES (Exact Match)** |

**Finding:** The original 1,200-customer historical baseline is completely intact, unaltered, and verified.

**Classification:** **PASS**

---

## 3. Trace the 8-Customer Dataset

### Origin Batch: `batch_20261117_171838_f825`
Located at `data/uploads/batch_20261117_171838_f825/`:
- `b3442f_transactions.csv`: 9 transaction records
- `bc19a7_web_activity.csv`: 10 web activity records
- `60af9e_social_media.csv`: 8 social media records
- Customers involved: Exactly 8 unique customers (`CUST_0001`, `CUST_0002`, `CUST_0010`, `CUST_0100`, etc., including 3 new synthetic IDs).

### Code Path Tracing
1. Batch uploaded via `IngestionService.stage_batch_upload()`.
   - `manifest.json` set `"batch_type": "MULTI_FORMAT"`.
2. PySpark execution triggered in `PipelineExecutionService.execute_batch_pipeline()`.
3. In `pipeline_execution_service.py` (lines 285–364):
   ```python
   is_multi_format = (manifest.get("batch_type") == "MULTI_FORMAT")
   if is_multi_format:
       spark = get_spark_session(...)
       df_raw_tx = self._load_multiformat_source_df(...)
       ...
       export_spark_dataframe(df_tx_clean, version_dir, "cleaned_transactions")
       export_spark_dataframe(df_web_clean, version_dir, "cleaned_web_activity")
       export_spark_dataframe(df_soc_clean, version_dir, "cleaned_social_media")
       export_spark_dataframe(df_unified, version_dir, "unified_customer_features")
       ...
       return True, f"PySpark multi-format processing completed in {duration}s for {version_id}.", report
   ```
4. **Forensic Evidence:**
   - Did the service read the baseline? **NO.**
   - Did the service read previously accepted batches? **NO.**
   - Did the service read only the latest upload? **YES.**
   - Was the batch treated as a complete replacement dataset? **YES.**

**Classification:** **FAIL** (Service failed to read baseline or prior batches).

---

## 4. Inspection of Cumulative Integration Logic

### The Architecture Disconnect
`backend/app/services/pipeline_execution_service.py` contains two contradictory code paths:

1. **Path A (Early Exit - Multi-Format Prototype, Lines 285–364):**
   - Triggers when `manifest.get("batch_type") == "MULTI_FORMAT"`.
   - Loads *only* the current batch directory.
   - Cleans only the batch records (9 tx, 10 web, 8 soc).
   - Generates only 8 unified customer features.
   - **Does NOT emit `data_composition.json`**.
   - Returns early, bypassing all cumulative integration.

2. **Path B (Intended Cumulative Pipeline, Lines 366–625):**
   - Correctly determines lineage from `accepted_batches.json`.
   - Loads baseline via `_load_baseline_df()`.
   - Unions all prior accepted batches via `_load_batch_source_df()`.
   - Unions incoming batch via `unionByName()`.
   - Performs primary-key deduplication and cleaning on the combined dataset.
   - Computes Historical vs Newly Added mathematical delta.
   - Emits `data_composition.json`.
   - Mirrors artifacts to HDFS `/customer-analytics/processed/versions/<version_id>`.

Because `IngestionService.stage_batch_upload()` unconditionally tags all uploads as `"batch_type": "MULTI_FORMAT"`, **Path B was never executed**.

### Why the Dashboard Showed Historical = 8, Newly Added = 0, Overall = 8
When `v_batch_20261117_171838_f825` was active:
1. `data/processed/data_composition.json` did not exist (because Path A skipped generating it).
2. The frontend called `/api/overview/data-composition`.
3. In `backend/app/services/data_service.py` (lines 154–178):
   ```python
   # If data_composition.json is missing, fallback to active DataService state:
   base_cust = int(len(self.df_segments))      # 8
   base_tx   = int(len(self.df_transactions))  # 9
   base_web  = int(len(self.df_web))           # 10
   base_soc  = int(len(self.df_social))        # 8

   return {
       "historical": {"total_customers": base_cust, "total_transactions": base_tx, ...},
       "newly_added": {"new_unique_customers": 0, "valid_transactions": 0, ...},
       "overall": {"total_customers": base_cust, "total_transactions": base_tx, ...}
   }
   ```
4. As a result, the active 8-customer dataset was treated as the baseline, populating Historical with 8 and Newly Added with 0.

**Classification:** **FAIL** (Cumulative integration bypassed; data composition fallback produced misleading metrics).

---

## 5. Promotion Mechanism Inspection

`VersionPreviewService.promote_version()` in `backend/app/services/version_preview_service.py`:

```python
# Copy version datasets into data/processed/
for fname in os.listdir(v_data_dir):
    src = os.path.join(v_data_dir, fname)
    if os.path.isfile(src):
        shutil.copy2(src, os.path.join(self.processed_dir, fname))
```

### Analysis of the Promotion Failure
1. **Destructive Overwrite:** Promotion performs a whole-file copy (`shutil.copy2`) of candidate files directly into `data/processed/`.
2. **Missing Pre-flight Sanity Check:** The pre-flight validator only checks if files exist (`cleaned_transactions.csv`, etc.). It does **not** assert that the dataset is cumulative or that `len(candidate_customers) >= len(baseline_customers)` (>= 1,200).
3. **Did Promotion or Cumulative Processing Fail?**
   - **Both contributed:**
     - The **Cumulative Processing Mechanism** failed first by emitting an isolated delta instead of a cumulative dataset.
     - The **Promotion Mechanism** failed second by lacking safety guardrails, blindly copying the 8-customer delta over production.

**Classification:** **FAIL** (Missing safety guardrails in promotion service).

---

## 6. Machine Learning Degradation Analysis

When `ModelTrainingService.retrain_all_models("v_batch_20261117_171838_f825")` was called:

1. **K-Means Silhouette Score = 0.2552:**
   - K-Means was fitted on only **8 customer vectors** in `unified_customer_features.csv` rather than 1,200+.
   - Clustering 8 sparse points into 4 or 5 clusters forces clusters of size 1 or 2, severely degrading intra-cluster tightness and inter-cluster separation, driving the silhouette score down to 0.2552.
2. **Recommendation Hit Rate@5 = 0.0%:**
   - Recommender evaluated on only **9 transaction lines**.
   - With 8 users and 9 purchases, collaborative filtering / co-occurrence matrices have virtually zero overlap, yielding zero test-set hits in top-5 recommendations.
3. **Churn Training Skipped:**
   - The temporal churn observation window requires multi-month activity logs. An isolated batch containing 8 customer rows lacks sufficient historical observation depth, correctly triggering the temporal safety guard and skipping churn training.

**Finding:** All three ML anomalies directly resulted from training on an isolated 8-customer dataset rather than a cumulative 1,200+ customer dataset.

**Classification:** **PASS** (Degradation mechanism fully understood and verified).

---

## 7. HDFS Raw Batch Inventory

- **HDFS Baseline Path:** `/customer-analytics/raw/baseline/` (3 canonical CSVs, all matching local baseline raw files).
- **HDFS Processed Store:** `/customer-analytics/processed/versions/`.
- **HDFS Uploads Path:** `/customer-analytics/raw/uploads/`:
  - `batch_20261117_115113_f894`
  - `batch_20261117_115827_b7df`
  - `batch_20261117_170415_2762`
- **Local Staging Directory:** `data/uploads/` holds **158 batch staging directories**, all preserved without deletion.

**Classification:** **PASS**

---

## 8. Expected vs Actual Record Counts

| Entity | Baseline (Expected Historical) | Promoted Candidate (`171838_f825`) | Expected Cumulative (`Baseline + Batch`) | Active Rolled Back |
|---|---:|---:|---:|---:|
| **Customers** | 1,200 | **8** | **1,203** | 1,200 |
| **Cleaned Transactions** | 12,214 | **9** | **12,223** | 12,214 |
| **Cleaned Web Activities** | 120,944 | **10** | **120,954** | 120,944 |
| **Cleaned Social Media** | 8,828 | **8** | **8,836** | 8,828 |
| **Association Rules** | 394 | **0** | **394** | 394 |
| **K-Means Silhouette** | 0.2952 | **0.2552** | **~0.295** | 0.2952 |
| **Recommendation Hit Rate@5**| 75.09% | **0.0%** | **~75%** | 75.09% |

---

## 9. Baseline Restoration Status

- **Status:** **RESTORED & VERIFIED**.
- The active version pointer in `data/current_version.json` is `"active_version": "baseline"`.
- All production CSVs in `data/processed/` match the bit-level SHA-256 hashes of `data/_baseline_backup/`.
- The live dashboard is currently serving the authentic 1,200-customer historical dataset.

---

## 10. Remediation Plan & Required Test Suite

### Remediation Steps
1. **Refactor `pipeline_execution_service.py`:**
   - Remove the early-return block `if is_multi_format:` (lines 285–364).
   - Ensure that multi-format batches route through the cumulative pipeline (Steps 2–18). Note that `_load_batch_source_df()` already has multi-format support implemented via `_load_multiformat_source_df()`.
   - Ensure `data_composition.json` is always computed and saved in `data/versions/<version_id>/data_composition.json`.
2. **Add Promotion Pre-Flight Monotonicity Guard in `version_preview_service.py`:**
   - In `promote_version()`, before copying files, inspect candidate `unified_customer_features` or `customer_segments`.
   - Reject promotion with an explicit error if candidate customer count < 1,200 (or < active version customer count).
3. **Ensure Data Composition Persistence:**
   - Verify that `data_composition.json` is atomically copied to `data/processed/data_composition.json` on promotion so `get_data_composition()` never falls back to un-segmented approximations.

### Required Tests to Prove the Fix
1. `test_cumulative_multi_format_pipeline_includes_baseline`:
   - Execute batch pipeline for a multi-format batch.
   - Assert `unified_customer_features` row count is `>= 1200`.
   - Assert `data_composition.json` exists with `historical.total_customers == 1200`, `newly_added.new_unique_customers >= 0`, and `overall.total_customers >= 1200`.
2. `test_promotion_preflight_blocks_non_cumulative_versions`:
   - Mock a candidate version directory containing only 8 customers.
   - Call `promote_version()`.
   - Assert promotion returns `False` and leaves production untouched.
3. `test_end_to_end_ml_metrics_on_remediated_cumulative_candidate`:
   - Verify K-Means silhouette remains `>= 0.28`, Hit Rate@5 remains `>= 70%`, and Association Rules discover `>= 390` rules.

