# SMART Project — Student Input & Batch Retraining Integration
## Stage A — Read-Only Repository Audit & System Design Specification

**Document Version:** 1.0.0  
**Date:** November 16, 2026  
**Auditor:** Antigravity Engineering Agent  
**Target Environment:** Windows 11 Host + WSL2 Debian (Hadoop 3.3.6 HDFS) + PySpark 3.5.1 + Flask 3.1 + React 18  
**Audit Scope:** Strictly Read-Only Architectural Inspection & Additive Integration Design (Zero source code, baseline datasets, models, or configurations modified)

---

## 1. Executive Summary & Objective

The **SMART Customer Analytics & Personalized Experience Platform** is an enterprise-grade big data and machine learning system combining:
1. Multi-source data ingestion (Transactions, Web Activity, Social Media).
2. Distributed storage on **Apache Hadoop 3.3.6 HDFS** (served via WSL2 Debian).
3. Distributed batch data cleaning, imputation, and feature engineering via **Apache PySpark 3.5.1 (`local[2]`)**.
4. Unsupervised customer behavioral segmentation (**K-Means with $K=5$, PCA 2D/3D projections**).
5. Personalized recommendation engine (**User-Item Collaborative Filtering + 394 Apriori Association Rules**, zero-leakage holdout hit rate = 76.0%).
6. Supervised churn prediction (**Random Forest with 180-day feature window / 90-day future observation window**, ROC-AUC = 0.9365, Recall = 90.32%).
7. REST API service layer (**Flask 3.1** with in-memory cached `DataService`).
8. High-performance interactive dashboard (**React 18 + Chart.js + Tailwind CSS** in an Apple-inspired minimal dark UI).

### Integration Objective
Extend the existing platform with a controlled, additive **Student Input & Batch Retraining Workflow**. This enables academic evaluators, students, and analysts to:
1. Securely upload custom or incremental CSV datasets (`transactions.csv`, `web_activity.csv`, `social_media.csv`).
2. Run strict pre-ingestion schema, type, and relational integrity validations.
3. Stage accepted raw datasets into Hadoop HDFS (`/customer-analytics/raw/uploads/<batch_id>/`).
4. Manually trigger PySpark batch processing to regenerate the unified 23-feature customer matrix.
5. Retrain the machine learning models (K-Means, CF/Apriori Recommender, and Churn Random Forest when temporal windows permit).
6. Atomically promote newly trained models and analytics to production with dynamic `DataService` cache refresh and one-click instant rollback.

### Protection Rules Enforced
- **Zero Modification to Baseline:** Baseline datasets (`data/raw/`, `data/processed/`), baseline models (`ml/models/`), and baseline HDFS directories remain immutable.
- **No Heavy Distributed Streaming:** Kafka, Spark Streaming, MongoDB, Docker, and external cloud services are strictly prohibited.
- **Hardware-Aware Execution:** PySpark runs in constrained `local[2]` mode within an 8 GB RAM physical memory boundary.
- **Dynamic Hot Reloading:** Flask REST API updates in memory without process termination or port renegotiation.
- **Backward Compatibility:** All existing 13+ REST endpoints and 7 dashboard pages remain 100% operational.

---

## 2. Existing System Architecture & Data Travel Flow

The complete data lifecycle currently flows sequentially through five major tiers:

```
[ Tier 1: Raw Multi-Source Data ]
  ├── data/raw/transactions.csv     (12,239 records, 12 columns)
  ├── data/raw/web_activity.csv     (120,979 records, 10 columns)
  └── data/raw/social_media.csv     (8,828 records, 10 columns)
                 │
                 ▼
[ Tier 2: Storage & Ingestion ]
  ├── HDFSManager (WebHDFS REST :9870 / IPC RPC :9000 inside WSL2)
  ├── HDFS Raw Store: /customer-analytics/raw/
  └── big_data/ingestion/schemas.py (Explicit PySpark StructTypes)
                 │
                 ▼
[ Tier 3: Distributed Processing Engine (PySpark 3.5.1 local[2]) ]
  ├── big_data/preprocessing/clean_data.py
  │     ├── clean_transactions()  -> Deduplicate (25 dups), impute payment_method (73 nulls)
  │     ├── clean_web_activity()  -> Deduplicate (35 dups), preserve meaningful null product_ids (60,540)
  │     └── clean_social_media()  -> Clamp sentiment [-1, 1], engagement [0, 100]
  ├── big_data/feature_engineering/extract_features.py
  │     ├── compute_transaction_features() (8 metrics: total_spend, order_count, AOV, recency, return_rate...)
  │     ├── compute_web_features()         (8 metrics: session_count, avg_duration, bounce_rate, channel shares...)
  │     ├── compute_social_features()      (7 metrics: interaction_count, avg_sentiment, positive_ratio...)
  │     └── build_unified_feature_matrix() -> Full Outer Join on customer_id (1,200 × 23 features)
  └── Export: data/processed/ (.parquet for ML & .csv for lightweight API access)
                 │
                 ▼
[ Tier 4: Machine Learning & Analytics ]
  ├── ml/segmentation/train_kmeans.py      -> StandardScaler, PCA (2D/3D), K=5 Clusters, silhouette=0.3451
  ├── ml/recommendations/recommender.py    -> Item-item cosine similarity + Apriori (394 rules), hit rate=76.0%
  └── ml/churn/ (build, train, predict)    -> Point-in-time RF (180d pre / 90d post cutoff), ROC-AUC=0.9365
                 │
                 ▼
[ Tier 5: Serving & Visualization ]
  ├── backend/app/services/data_service.py -> Singleton in-memory DataFrame & JSON cache
  ├── backend/app/routes/                  -> 13+ REST endpoints (/api/overview, /api/analytics, etc.)
  └── frontend/src/                        -> React 18 SPA (Apple Minimal Dark UI, Chart.js, Tailwind)
```

---

## 3. Inventory of Existing Logic & Exact Reusable Components

The existing codebase contains highly robust, battle-tested modular functions. To prevent code duplication, the new batch retraining system will reuse these functions directly:

### 3.1 Schemas & Ingestion Layer
- **Location:** `big_data/ingestion/schemas.py`
  - Reusable StructTypes: `TRANSACTIONS_SCHEMA`, `WEB_ACTIVITY_SCHEMA`, `SOCIAL_MEDIA_SCHEMA`.
  - Reusable validation constants: `VALID_ORDER_STATUSES`, `VALID_DEVICE_TYPES`, `VALID_TRAFFIC_SOURCES`, `VALID_PLATFORMS`, `VALID_INTERACTION_TYPES`, `VALID_SENTIMENTS`.
- **Location:** `big_data/ingestion/ingest_raw.py`
  - Reusable function: `load_raw_datasets(spark: SparkSession, data_dir: str) -> Tuple[DataFrame, DataFrame, DataFrame]`.
  - Timestamp parsing logic: Casts string ISO dates to Spark timestamps with format matching.
- **Location:** `big_data/ingestion/hdfs_client.py`
  - Reusable class: `HDFSManager`.
  - Reusable methods: `check_connectivity()`, `upload_file(local_path, hdfs_path)`, `list_directory(hdfs_path)`.
  - Dual-mode capability: Automatically falls back to local staging if WSL2 HDFS is not running or unreachable, ensuring zero crashes.

### 3.2 Preprocessing & Feature Engineering Layer
- **Location:** `big_data/preprocessing/clean_data.py`
  - Reusable functions:
    - `clean_transactions(df: DataFrame) -> DataFrame` (deduplication, payment method imputation to `"Unknown"`).
    - `clean_web_activity(df: DataFrame) -> DataFrame` (deduplication, product_id null preservation).
    - `clean_social_media(df: DataFrame) -> DataFrame` (score clamping, categorical validation).
- **Location:** `big_data/feature_engineering/extract_features.py`
  - Reusable functions:
    - `compute_transaction_features(df_tx: DataFrame) -> DataFrame`
    - `compute_web_features(df_web: DataFrame) -> DataFrame`
    - `compute_social_features(df_soc: DataFrame) -> DataFrame`
    - `build_unified_feature_matrix(df_tx_feat, df_web_feat, df_soc_feat) -> DataFrame`
  - Fixed 23-feature schema definition guarantees downstream ML input stability.

### 3.3 Pipeline Orchestration Layer
- **Location:** `big_data/run_pipeline.py`
  - Reusable function: `export_dataframe(df: DataFrame, output_base_dir: str, name: str)`.
  - Outputs both optimized Parquet files (partition-ready) and unified single-file CSVs with headers.

### 3.4 Machine Learning Pipelines
- **Location:** `ml/segmentation/train_kmeans.py`
  - Reusable logic: `evaluate_kmeans()`, `train_production_kmeans()`, PCA projection generation, cluster profiling.
- **Location:** `ml/recommendations/recommender.py`
  - Reusable logic: `train_recommender()`, zero-leakage 80/20 train/test evaluation, Apriori rule generation, metadata serialization.
- **Location:** `ml/churn/`
  - Reusable modules: `build_churn_dataset.py`, `train_churn.py`, `predict_churn.py`.
  - Temporal cutoff logic: `CUTOFF_DATE = "2024-10-01"` (or dynamic point-in-time calculation).

### 3.5 API & Serving Layer
- **Location:** `backend/app/services/data_service.py`
  - Singleton `DataService`: Loads processed CSVs and JSON model artifacts into pandas DataFrames and dictionaries.
  - Reusable KPI, analytics, customer 360, and recommendation resolvers.
  - *Extension required:* Add an atomic `reload(version_id: Optional[str] = None)` method.

---

## 4. Ingestion & Validation Specifications

To protect production stability, uploaded student datasets must pass a rigorous two-tier validation engine (Header/Type Syntax Check + Relational Semantic Check) before any PySpark execution is scheduled.

### 4.1 Dataset Schemas & Strict Constraints

#### File 1: `transactions.csv`
| Column | Type | Nullable | Value Constraints / Validation Rules |
| :--- | :--- | :--- | :--- |
| `transaction_id` | String | NO | Primary Key. Unique regex `^TX_\d+$` or alphanumeric string. No duplicates allowed. |
| `customer_id` | String | NO | Foreign Key. Regex `^CUST_\d{4}$`. Must link to customer directory. |
| `transaction_date`| Timestamp| NO | Format `YYYY-MM-DD HH:MM:SS` or `YYYY-MM-DD`. Valid historical calendar date. |
| `product_id` | String | NO | Alphanumeric string `^PROD_\d+$`. Must not be empty. |
| `product_category`| String | NO | Standard categories (e.g., Electronics, Audio, Wearables, Accessories). |
| `product_name` | String | NO | Non-empty descriptive string. |
| `quantity` | Integer | NO | Strictly positive integer ($> 0$). Max limit: $1000$. |
| `unit_price` | Float | NO | Strictly positive float ($> 0.0$). |
| `discount_percent`| Float | NO | Range $[0.0, 100.0]$ or $[0.0, 1.0]$. Auto-normalized. |
| `total_amount` | Float | NO | Strictly positive ($> 0.0$). Approximately matches `quantity * unit_price * (1 - discount)`. |
| `payment_method` | String | YES | Allowed: Credit Card, Debit Card, PayPal, Bank Transfer, UPI, Cash. Nulls auto-imputed to `"Unknown"`. |
| `order_status` | String | NO | Allowed: `Completed`, `Pending`, `Cancelled`, `Refunded`. |

#### File 2: `web_activity.csv`
| Column | Type | Nullable | Value Constraints / Validation Rules |
| :--- | :--- | :--- | :--- |
| `activity_id` | String | NO | Primary Key. Unique regex `^ACT_\d+$`. |
| `customer_id` | String | NO | Foreign Key matching `CUST_\d{4}`. |
| `session_id` | String | NO | Session tracking identifier `^SESS_\d+$`. |
| `timestamp` | Timestamp| NO | ISO timestamp format. |
| `page_url` | String | NO | Non-empty URL path string (e.g., `/products/audio`, `/cart`). |
| `action_type` | String | NO | Allowed: `view`, `click`, `add_to_cart`, `purchase`, `search`, `scroll`. |
| `product_id` | String | **YES** | Nullable for home/category pages; non-empty for product-specific views. |
| `duration_seconds`| Integer | NO | Non-negative integer ($\ge 0$). Upper bound: $86,400$ s. |
| `device_type` | String | NO | Allowed: `Desktop`, `Mobile`, `Tablet`. |
| `traffic_source` | String | NO | Allowed: `Direct`, `Organic Search`, `Social Media`, `Referral`, `Email Newsletter`. |

#### File 3: `social_media.csv`
| Column | Type | Nullable | Value Constraints / Validation Rules |
| :--- | :--- | :--- | :--- |
| `interaction_id` | String | NO | Primary Key. Unique regex `^SOC_\d+$`. |
| `customer_id` | String | NO | Foreign Key matching `CUST_\d{4}`. |
| `timestamp` | Timestamp| NO | ISO timestamp format. |
| `platform` | String | NO | Allowed: `Twitter/X`, `Instagram`, `Facebook`, `LinkedIn`, `YouTube`. |
| `interaction_type`| String | NO | Allowed: `mention`, `review`, `comment`, `direct_message`, `share`, `like`. |
| `sentiment` | String | NO | Allowed: `Positive`, `Neutral`, `Negative`. |
| `sentiment_score` | Float | NO | Continuous range $[-1.0, 1.0]$. Clamped if slight float drift occurs. |
| `engagement_score`| Integer | NO | Bounded integer $[0, 100]$. |
| `feedback_content`| String | NO | Raw text feedback string. Non-empty. |
| `associated_category`| String | NO | Target product department or `General`. |

### 4.2 Structured Validation Response Format
The validation module will return a standardized JSON envelope:
```json
{
  "status": "success",
  "batch_id": "batch_20261116_143000_a1b2",
  "is_valid": true,
  "summary": {
    "transactions_count": 12500,
    "web_activity_count": 122000,
    "social_media_count": 9100,
    "unique_customers": 1200,
    "shared_customer_coverage": "100.0%",
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31",
      "span_days": 365
    }
  },
  "checks": {
    "headers_valid": true,
    "data_types_valid": true,
    "primary_keys_unique": true,
    "foreign_keys_aligned": true,
    "temporal_window_adequate": true
  },
  "warnings": [
    "75 transactions have missing payment_method; will be auto-imputed to 'Unknown'."
  ],
  "errors": []
}
```

---

## 5. HDFS Path Conventions & Storage Layout

All distributed datasets adhere to a clean, isolated directory structure in HDFS with a local fallback mirror:

### 5.1 HDFS Hierarchy (WSL2 Hadoop 3.3.6)
```
/customer-analytics/
  ├── raw/
  │    ├── baseline/                 <-- Permanent academic baseline (IMMUTABLE)
  │    │    ├── transactions.csv
  │    │    ├── web_activity.csv
  │    │    └── social_media.csv
  │    └── uploads/
  │         └── <batch_id>/          <-- Staged raw student uploads
  │              ├── transactions.csv
  │              ├── web_activity.csv
  │              ├── social_media.csv
  │              └── manifest.json
  └── processed/
       ├── baseline/                 <-- Baseline Parquet feature stores (IMMUTABLE)
       └── versions/
            └── <version_id>/        <-- Parquet outputs from batch retraining
                 ├── cleaned_transactions.parquet/
                 ├── cleaned_web_activity.parquet/
                 ├── cleaned_social_media.parquet/
                 └── unified_feature_matrix.parquet/
```

### 5.2 Local Storage Mirror
```
d:\Infynux\big data project\
  ├── data/
  │    ├── raw/                      <-- Local baseline raw files (IMMUTABLE)
  │    ├── processed/                <-- Active production files served by API
  │    ├── uploads/
  │    │    └── <batch_id>/          <-- Incoming raw uploads + validation reports
  │    └── versions/
  │         └── <version_id>/        <-- Archived versions of processed CSVs
  └── ml/models/
       ├── ...                       <-- Active production model artifacts
       └── versions/
            └── <version_id>/        <-- Versioned snapshots of joblib & JSON files
```

---

## 6. Staging, Isolation, and Execution Boundaries

To guarantee that incomplete or erroneous student submissions never corrupt the running system:
1. **Isolated Upload Staging:** Uploaded files are written exclusively to `data/uploads/<batch_id>/` and isolated with a cryptographic/timestamp manifest.
2. **Two-Stage Commit:**
   - **Stage 1 (Dry-Run Validation):** Performs syntax, type, schema, and relational checks. No HDFS writes or ML execution occur.
   - **Stage 2 (Batch Ingestion & Processing):** Triggered only when `is_valid == true` and explicitly confirmed by the user.
3. **Atomic Execution:** If any failure occurs during PySpark processing or ML retraining, the active production pointers remain unchanged, the partial version is quarantined, and the user receives an actionable error trace.

---

## 7. Churn Model Temporal Window Limitations & Fallback Policy

### 7.1 Temporal Separation Constraint
The supervised Random Forest churn model adheres to strict point-in-time temporal cutoff logic to eliminate future information leakage:
- **Historical Observation Window:** 180 days prior to cutoff (used to compute behavioral predictors: spend velocity, frequency drop, complaint trends).
- **Future Observation Window:** 90 days after cutoff (used to observe whether the customer transacted; if $0$ orders, `churn_label = 1`).
- **Minimum Required Dataset Span:** At least $180 + 90 = 270$ continuous calendar days.

### 7.2 Safe Fallback Policy
When an uploaded batch represents a short academic sample (e.g., 30 days or 60 days of data):
1. **Unsupervised K-Means Segmentation:** Trains normally (requires no future window).
2. **Hybrid Collaborative Filtering & Association Rules:** Trains normally (co-occurrence and interaction-based).
3. **Supervised Churn Model:** The pipeline detects that the date span is $< 270$ days. Instead of failing the entire pipeline with an exception:
   - It gracefully skips churn model retraining.
   - It retains the previous validated churn model and predictions.
   - It logs an explicit notice in the batch execution summary: `"Notice: Uploaded dataset span (XX days) is below the 270-day requirement for point-in-time churn labeling. Retained previous production churn model."`
   - The dashboard and API reflect this status transparently with zero broken widgets.

---

## 8. Versioning, Atomic Promotion, and Rollback Strategy

### 8.1 Active Version Pointer
A lightweight JSON pointer `data/current_version.json` tracks the active deployment state:
```json
{
  "active_version": "version_20261116_143000",
  "batch_id": "batch_20261116_143000_a1b2",
  "promoted_at": "2026-11-16T14:35:10Z",
  "status": "active",
  "models": {
    "kmeans": "retrained",
    "recommender": "retrained",
    "churn": "retained_baseline"
  },
  "metrics": {
    "silhouette_score": 0.3482,
    "recommender_hit_rate": 0.764,
    "churn_roc_auc": 0.9365
  },
  "previous_version": "baseline"
}
```

### 8.2 In-Memory Hot Reloading (`DataService.reload`)
To avoid restarting the Flask server process and dropping frontend HTTP connections, `DataService` will be augmented with:
```python
def reload(self, version_id: Optional[str] = None) -> bool:
    """Reloads DataFrames and ML model artifacts in memory from the specified or active version."""
```
Calling `DataService.get_instance().reload()` instantly swaps the in-memory pandas DataFrames and JSON cache in a thread-safe manner within $< 200$ ms.

### 8.3 Instant One-Click Rollback
If an analyst or professor wishes to restore the baseline state or undo a retraining batch:
1. The rollback endpoint `POST /api/pipeline/rollback` accepts an optional target version (defaulting to `"baseline"`).
2. The active version pointer is updated.
3. Production files in `data/processed/` and `ml/models/` are restored from the version archive.
4. `DataService.get_instance().reload()` is invoked.
5. The dashboard updates immediately to show baseline metrics (1,200 customers, $1.8M sales, 76.0% hit rate).

---

## 9. Proposed Additive Architecture & Code Modifications

To adhere strictly to the principle of minimal disruption:

### 9.1 Proposed New Files
| File Path | Purpose |
| :--- | :--- |
| `big_data/ingestion/validator.py` | Standalone validation engine enforcing syntax, types, primary/foreign keys, and temporal windows. |
| `backend/app/services/ingestion_service.py` | Coordinates batch upload staging, validation execution, PySpark dispatch, version tracking, and rollback. |
| `backend/app/routes/ingestion_routes.py` | Exposes REST endpoints for upload, validation, execution triggering, batch status polling, and rollback. |
| `ml/retrain_all.py` | Orchestrates sequential retraining of K-Means, Recommender, and Churn models against newly processed feature matrices. |
| `frontend/src/components/DataIngestionModal.jsx` | Minimal, Apple-inspired modal tab inside the Data Pipeline page providing file drag-and-drop, validation summary, and progress bars. |

### 9.2 Minimal Surgical Modifications to Existing Files
| File Path | Modification Required |
| :--- | :--- |
| `backend/app/services/data_service.py` | Add `reload(version_id)` method and version metadata resolver. No existing query logic modified. |
| `backend/app/__init__.py` | Register `ingestion_bp` under `/api/ingestion` (and alias `/api/pipeline/ingest`). Zero existing routes altered. |
| `frontend/src/pages/DataProcessing.jsx` | Add an "Upload & Retrain" trigger button and batch history table in the existing Apple-styled UI. |

### 9.3 Endpoint Conflict Guarantee
All new endpoints are strictly additive and prefixed under `/api/ingestion/`:
- `POST /api/ingestion/upload` — Upload CSV files to staging.
- `POST /api/ingestion/validate` — Validate staged batch and return validation report.
- `POST /api/ingestion/execute` — Trigger PySpark batch execution and model retraining.
- `GET  /api/ingestion/status/<batch_id>` — Poll batch execution progress.
- `GET  /api/ingestion/history` — List past batches and versions.
- `POST /api/ingestion/rollback` — Instant rollback to baseline or previous version.

Existing endpoints (`/api/overview/kpis`, `/api/pipeline/summary`, `/api/segmentation/clusters`, etc.) remain 100% untouched.

---

## 10. Comprehensive Verification & Test Plan

| Test Category | Target Component | Verification Criteria |
| :--- | :--- | :--- |
| **Unit: Schema Validation** | `validator.py` | Rejects malformed headers, negative quantities/prices, invalid enum values, and duplicate IDs with explicit line numbers. |
| **Unit: Foreign Key Integrity**| `validator.py` | Flags orphan transactions or web events lacking valid `customer_id`. |
| **Unit: Temporal Window** | `validator.py` | Correctly computes dataset date span and flags spans $< 270$ days for churn fallback. |
| **Integration: PySpark Batch**| `run_pipeline.py` | Generates identical 23-column schema in Parquet and CSV without unexpected nulls. |
| **Integration: Model Retrain**| `retrain_all.py` | Produces valid cluster profiles ($K=5$), association rules ($>0$ rules), and recommendations for all customers. |
| **Integration: Atomic Rollback**| `ingestion_service.py`| Confirms that rolling back restores baseline metrics ($1,200$ customers, $1.8M sales) with 0 numeric divergence. |
| **API Compliance** | `ingestion_routes.py`| All new endpoints return standard envelope `{"status": "success", "data": ...}` with appropriate HTTP 200, 400, and 500 codes. |
| **Frontend UI** | `DataProcessing.jsx` | Upload modal reflects Apple Minimal Dark styling with zero CSS regressions; builds cleanly with `npm run build`. |

---

## 11. Risks, System Constraints, and Mitigation Strategies

1. **Risk: Memory Exhaustion during PySpark Execution (8 GB RAM boundary)**  
   *Mitigation:* Configure `SparkConf` with `spark.driver.memory = "2g"`, `spark.executor.memory = "2g"`, and `spark.sql.shuffle.partitions = 4`. Clean up cached DataFrames via `unpersist()` after feature engineering.
2. **Risk: WSL2 HDFS Unavailability**  
   *Mitigation:* The `HDFSManager` connectivity probe automatically falls back to dual-mode local staging if WSL2 is asleep or NameNode is restarting, ensuring zero pipeline halts.
3. **Risk: Corrupted or Partial Uploads**  
   *Mitigation:* Uploads are validated against file hash and content length before staging; files failing validation are immediately purged from temporary buffers.
4. **Risk: Model Regression / Degradation**  
   *Mitigation:* Retrained models are evaluated against minimum quality thresholds (e.g., Silhouette score $\ge 0.25$, Recommender hit rate $\ge 50\%$). If quality degrades below thresholds, automatic promotion is blocked and an administrative warning is displayed.

---

## 12. Conclusion & Transition to Stage B

This Stage A audit confirms that the SMART platform possesses a highly modular, decoupled architecture that seamlessly supports additive batch ingestion and retraining. 

**Stage A Status:** **COMPLETED (Read-Only Audit & Design)**  
**Next Step:** Await explicit user approval before beginning **Stage B — Implementation**.

