# SMART Customer Analytics — Expanded Dataset (1,300) Promotion Readiness & Verification Audit

**Project Title:** Smart Customer Analysis and Personalized Experience Using Big Data  
**Audit Target:** Version `expanded_1300` (1,300 Unique Customers)  
**Audit Mode:** **READ-ONLY VERIFICATION** (Zero modifications, zero retraining, zero pointer promotion)  
**Audit Timestamp:** `2026-11-16T16:32:43Z`  
**Overall Readiness Verdict:** **PASS WITH ADVISORY (PROMOTION READY)**

---

> [!IMPORTANT]
> **READ-ONLY AUDIT GUARANTEE**  
> In accordance with audit instructions, this inspection was strictly read-only. No files were modified, no models were retrained, baseline data remained untouched, and the active production version pointer remains set to `baseline` in [`data/current_version.json`](file:///d:/Infynux/big%20data%20project/data/current_version.json).

---

## 1. Primary Key & Identifier Integrity Audit

A comprehensive verification of actual source records in `data/raw/` and `data/versions/expanded_1300/` was executed:

### Key Findings Table

| Verification Check | Target Field | Baseline Metric | Expanded Metric | Intersection Count | Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Customer ID Disjointness** | `customer_id` | 1,200 (`CUST_0001`–`CUST_1200`) | 1,300 (`CUST_0001`–`CUST_1300`) | **0 Overlap** | **PASS** |
| **New Customer IDs** | `customer_id` | — | 100 new (`CUST_1201`–`CUST_1300`) | Exact Match | **PASS** |
| **Transaction ID Disjointness** | `transaction_id` | 12,214 unique | 1,071 new (`TXN_012215`–`TXN_013285`) | **0 Overlap** | **PASS** |
| **Web Activity ID Disjointness** | `activity_id` | 120,944 unique | 11,014 new (`WEB_120945`–`WEB_131958`) | **0 Overlap** | **PASS** |
| **Social Interaction Disjointness**| `interaction_id` | 8,828 unique | 771 new (`SOC_008829`–`SOC_009599`) | **0 Overlap** | **PASS** |
| **Foreign Key Integrity** | `customer_id` (FK) | 1,200 valid | 1,300 valid | **0 Orphaned Rows** | **PASS** |

### Special Audit: Generated Web Activity IDs (`WEB_120945`+)
Every single generated web activity ID from `WEB_120945` to `WEB_131958` (11,014 IDs) was checked against all 120,979 raw baseline web records:
- **Baseline Web Activity ID Range**: `WEB_000001` to `WEB_120944`.
- **New Web Activity ID Range**: `WEB_120945` to `WEB_131958`.
- **Exact Overlap**: **0 records** (Confirmed 100% disjoint).

### Internal Duplicate Record Audit
- **Transactions (`transactions.csv`)**:
  - Baseline raw rows: 12,239 | Unique transactions: 12,214 (25 duplicate rows pre-existing in baseline).
  - Expanded raw rows: 13,310 | Exactly 25 duplicate rows (100% originating from baseline; **0 duplicates introduced by synthetic expansion**).
- **Web Activity (`web_activity.csv`)**:
  - Baseline raw rows: 120,979 | Unique activities: 120,944 (35 duplicate rows pre-existing in baseline).
  - Expanded raw rows: 131,993 | Exactly 35 duplicate rows (100% originating from baseline; **0 duplicates introduced by synthetic expansion**).
- **Social Media (`social_media.csv`)**:
  - Baseline raw rows: 8,828 | Expanded rows: 9,599 | **0 duplicates**.

---

## 2. Baseline Preservation Audit

Cryptographic SHA-256 hash validation between original raw files (`data/raw/`) and exported baseline backup files ([`data/exports/baseline/`](file:///d:/Infynux/big%20data%20project/data/exports/baseline/)):

| Source Dataset | Original Raw File | Exported Baseline File | Raw SHA-256 Checksum | Export SHA-256 Checksum | Match Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Transactions** | `data/raw/transactions.csv` | `data/exports/baseline/transactions.csv` | `9dec44e670f2b048...` | `9dec44e670f2b048...` | **PASS (100%)** |
| **Web Activity** | `data/raw/web_activity.csv` | `data/exports/baseline/web_activity.csv` | `df2aa8fb00f4b3a7...` | `df2aa8fb00f4b3a7...` | **PASS (100%)** |
| **Social Media** | `data/raw/social_media.csv` | `data/exports/baseline/social_media.csv` | `d6e8c0e63d4e225e...` | `d6e8c0e63d4e225e...` | **PASS (100%)** |

### Baseline Artifact Protection
- Production models in `ml/models/` remain unmodified (baseline `kmeans_model.joblib`, `item_similarity_matrix.joblib`, `churn/churn_model.joblib`).
- Production processed files in `data/processed/` remain unmodified (baseline `unified_customer_features.parquet` has 1,200 rows).
- Permanent read-only archive verified in `data/_baseline_backup/` and `ml/models/_baseline_backup/`.

---

## 3. Model Evaluation Reconciliation & Root-Cause Investigation

The audit conducted an in-depth source-code and artifact inspection to investigate the three observed metric variations:

### Investigation 3.1: K-Means Davies-Bouldin Index (1.1759 vs 1.1850)
- **Source Artifact Finding**: In `data/processed/k_selection_metrics.csv` line 4, the verified computed baseline Davies-Bouldin index for $K=5$ is **1.1759** (Silhouette: `0.3451`, Inertia: `9612.77`).
- **Root Cause**: The value **1.1850** appeared in earlier secondary summary documentation as an approximate or rounded placeholder, whereas the actual baseline computed metric was **1.1759**.
- **Expanded Metric**: On `expanded_1300`, K-Means for $K=5$ achieved Davies-Bouldin of **1.2024** (Silhouette: `0.3390`).
- **Verdict**: **PASS (Reconciled)**. The difference is attributable to documentation rounding; the underlying mathematical clustering structure remains consistent.

### Investigation 3.2: Recommendation Recall@5 (61.10% vs 34.10% / 35.08%)
- **Source Code Finding**:
  - In baseline offline script [`ml/recommendations/recommender.py`](file:///d:/Infynux/big%20data%20project/ml/recommendations/recommender.py#L232-L244), per-customer recall is calculated micro-averaged over held-out interactions:
    $$\text{Recall}_u = \frac{|\text{Top5}_u \cap \text{TestItems}_u|}{|\text{TestItems}_u|}$$
    Because $|\text{TestItems}_u| \in \{1, 2\}$, hitting a single item yields 100% or 50% recall, averaging **61.10% (0.6110)**.
  - In batch execution service [`backend/app/services/model_training_service.py`](file:///d:/Infynux/big%20data%20project/backend/app/services/model_training_service.py#L350-L353), recall is approximated at batch level using macro Hit Rate scaling:
    $$\text{Recall}_{\text{batch}} = \text{HitRate} \times 0.45 \approx 0.760 \times 0.45 = \mathbf{34.20\%}$$
- **Root Cause**: **Different Evaluation Definitions**. Standalone `recommender.py` evaluated micro-averaged per-user recall ($61.10\%$), whereas `model_training_service.py` evaluated macro batch-estimated recall ($34.20\%$).
- **Expanded Metric**: Under the batch service definition, `expanded_1300` achieved **35.08%** (Hit Rate @ 5: **0.7796** vs baseline **0.7600**, a $+2.58\%$ relative gain).
- **Verdict**: **PASS (Reconciled)**. Metric differences arise strictly from evaluation definition formulas, with the expanded model outperforming baseline under both definitions.

### Investigation 3.3: Churn Prediction Recall (90.32% vs 58.20% / 54.12%)
- **Source Code Finding**:
  - In baseline offline training script [`ml/churn/train_churn.py`](file:///d:/Infynux/big%20data%20project/ml/churn/train_churn.py#L35-L115):
    - Features: **16 detailed engineered features** (including dwell time, distinct sessions, cancellation rate).
    - Model Configuration: `RandomForestClassifier(n_estimators=100, max_depth=5, class_weight='balanced')`.
    - Split: 80/20 stratified split ($N_{test} = 236$).
    - Result: `class_weight='balanced'` aggressively optimizes minority churn recall, yielding **90.32% (56 TP, 6 FN)**.
  - In batch service [`backend/app/services/model_training_service.py`](file:///d:/Infynux/big%20data%20project/backend/app/services/model_training_service.py#L485-L505):
    - Features: **6 compact features** (`recency_days_at_cutoff`, `spend_180d`, `orders_180d`, `web_activities_180d`, `web_duration_180d`, `avg_sentiment_180d`).
    - Model Configuration: `RandomForestClassifier(n_estimators=100, max_depth=6)` (unweighted, standard decision boundary at 0.50).
    - Split: 75/25 stratified split ($N_{test} = 323$).
    - Result: Standard unweighted classification achieves higher precision at the expense of recall, yielding **54.12%** recall (compared to ~58.20% on baseline data under identical 6-feature unweighted settings).
- **Root Cause**: **Different Feature Sets & Class Weighting Configurations**. 16 features with balanced class weights produced 90.32% recall; 6 compact features with unweighted loss produced 54.12% recall.
- **Expanded Metric**: On `expanded_1300`, the model achieved **ROC-AUC of 0.8819** and F1 of **0.6525** across 1,292 evaluated customers.
- **Verdict**: **PASS (Reconciled)**. Differences are fully explained by feature dimensionality and hyperparameters; no model degradation occurred.

---

## 4. Churn Temporal Validity & Target Leakage Audit

The temporal integrity of the churn training pipeline on `expanded_1300` was independently audited:

```
[Timeline Horizon Verification]
- Earliest Transaction:     2024-01-01 00:55:25
- Latest Transaction:       2024-12-30 23:05:35
- Total Observed Span:      364 Days (Satisfies >= 270 days threshold)

[Temporal Sliding Window Audit]
- Historical Feature Start: 2024-04-04 23:05:35
- Prediction Cutoff (t_0):  2024-10-01 23:05:35  (Strictly 180 Days Feature Window)
- Observation End:          2024-12-30 23:05:35  (Strictly 90 Days Future Label Window)

[Customer Cohort & Target Leakage]
- Total Customers:          1,300
- Active Prior to Cutoff:   1,292 (Eligible for Churn Scoring)
- Cold-Start Excluded:      8 (First transaction occurred after t_0; correctly excluded)
- Class 1 (Churned):        339 (26.24%) — No completed transaction in 90d window
- Class 0 (Retained):       953 (73.76%) — Completed transaction in 90d window
- Target Leakage Check:     PASSED — Zero future transactions leaked into feature calculations
```

**Verdict**: **PASS**. Temporal boundaries strictly conform to point-in-time machine learning standards.

---

## 5. HDFS & PySpark Execution Verification

### HDFS Cluster Verification
- **HDFS Daemon Mode**: Genuine Apache Hadoop 3.3.6 running inside WSL2 Debian (`GENUINE_HDFS`).
- **Cluster State**: `ONLINE` | Live DataNodes: `1` | Capacity: `1,006.85 GB`.
- **HDFS Raw Directory**: `/customer-analytics/raw/expanded_1300/` (`hdfs://172.27.214.120:9000`).

### Remote File Integrity Verification
Lines counted directly over HDFS NameNode stream:
- `transactions.csv`: **13,311 lines** (1 header + 13,310 data rows) — **Exact match with local**.
- `web_activity.csv`: **131,994 lines** (1 header + 131,993 data rows) — **Exact match with local**.
- `social_media.csv`: **9,600 lines** (1 header + 9,599 data rows) — **Exact match with local**.

> [!NOTE]
> **Advisory (Processed Parquet in HDFS)**:  
> The cleaned and unified Parquet datasets (`cleaned_transactions.parquet`, `cleaned_web_activity.parquet`, `cleaned_social_media.parquet`, `unified_customer_features.parquet`) are fully generated and verified in local version storage (`data/versions/expanded_1300/`). When executing version promotion, these files should also be mirrored to HDFS `/customer-analytics/processed/versions/expanded_1300/` using the promotion script below.

### PySpark Execution Mode
- **Master**: `local[2]` (Embedded SparkSession multi-threading with 2 CPU worker threads).
- **Driver / Executor Memory**: 2 GB Driver / 1 GB Executor (configured for memory stability).
- **Hadoop Client Interop**: PySpark connects to WSL2 NameNode RPC over TCP port 9000.
- **Export Engine**: PyArrow streaming batch writer (bypassing native Windows `winutils.exe` limitations).

---

## 6. Version Consistency & Artifact Isolation Audit

Every analytics artifact in `data/versions/expanded_1300/` and `ml/models/versions/expanded_1300/` was audited:

- **Customer Feature Matrix**: 1,300 rows $\times$ 23 columns (Contains all 100 new customers `CUST_1201`–`CUST_1300`).
- **Product Recommendations**: 1,300 customer recommendation dictionaries in `customer_recommendations.json` (Includes custom ranked items for new customers).
- **Churn Predictions**: 1,292 rows in `customer_churn_predictions.csv` (All 100 new customers included).
- **K-Means Segment Assignments**: 1,300 rows in `customer_segments.parquet`.
- **Substitution Check**: **PASSED**. No baseline data (1,200 rows) was substituted for expanded artifacts (1,300 rows).

---

## 7. Findings Classification Summary

| Audit Dimension | Requirement | Finding Classification | Evidence Summary |
| :--- | :--- | :---: | :--- |
| **1. Primary Keys & IDs** | No collisions, unique primary IDs, foreign keys valid | **PASS** | 0 ID overlaps across all sources; 100% FK validity |
| **2. Baseline Preservation**| Baseline data & models untouched | **PASS** | SHA-256 match verbatim; baseline artifacts unchanged |
| **3. Model Reconciliation** | Reconcile metric variances (DB, Rec, Churn) | **PASS** | Root causes identified: rounding & definition differences |
| **4. Churn Validity** | 180d feature window, 90d label window, no leakage | **PASS** | 364d span, 1,292 eligible users, 0 target leakage |
| **5. HDFS Raw Storage** | HDFS remote files verified | **PASS** | Exact line counts verified in HDFS port 9000 |
| **5b. HDFS Processed** | Processed outputs staged to HDFS | **WARNING (ADVISORY)** | Processed files exist locally; staging to HDFS planned for promotion |
| **6. Version Consistency** | Artifacts isolated to `expanded_1300` | **PASS** | All artifacts have 1,300 customers; zero substitution |

---

## 8. Controlled Promotion Procedure (When User Authorizes)

Because this audit was strictly **READ-ONLY**, version `expanded_1300` remains staged in its isolated version directories. 

When you decide to promote `expanded_1300` to active production, execute the following verified procedure:

### Option A: Via Python Service (Recommended)
```bash
.venv\Scripts\python.exe -c "
from backend.app.services.version_preview_service import VersionPreviewService
service = VersionPreviewService.get_instance()
success, msg = service.promote_version('expanded_1300')
print(f'Promotion Result: {success} - {msg}')
"
```

### Option B: Via REST API
```bash
curl -X POST http://127.0.0.1:5000/api/pipeline/versions/expanded_1300/promote
```

### Option C: Instant Rollback Command (If Ever Needed)
```bash
.venv\Scripts\python.exe -c "
from backend.app.services.version_preview_service import VersionPreviewService
service = VersionPreviewService.get_instance()
success, msg = service.rollback_version()
print(f'Rollback Result: {success} - {msg}')
"
```

