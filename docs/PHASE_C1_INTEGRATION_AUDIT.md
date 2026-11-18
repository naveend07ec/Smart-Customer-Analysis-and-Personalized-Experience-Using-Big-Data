# Phase C1 — Read-Only Integration Audit Report
**Project:** Smart Customer Analysis and Personalized Experience Using Big Data  
**Scope:** Stage C & Stage D End-to-End Student Demonstration Workflow  
**Date:** November 16, 2026  
**Status:** **AUDIT COMPLETED — IMPLEMENTATION READY**

---

## 1. Executive Summary

This read-only audit inspects the current repository state, Stage B implementations, PySpark pipeline modules, and machine learning training scripts to establish an exact, zero-regression roadmap for Stages C and D.

The SMART platform is currently 100% operational with:
- Genuine HDFS connectivity utilities (`big_data/ingestion/hdfs_client.py`).
- Strict schema & domain validation (`big_data/ingestion/validator.py`).
- Isolated upload staging in `data/uploads/<batch_id>/`.
- 40 passing tests across the test suite (`test_api.py`, `test_churn.py`, `test_stage_b_ingestion.py`).
- Apple-inspired Minimal Dark UI on React 18 + Vite.

---

## 2. Reusable Codebase Assets & Mapping

| Component | File Path | Reusable Logic | Adaptation for Stage C/D |
| :--- | :--- | :--- | :--- |
| **Spark Engine** | `big_data/spark_session.py` | `get_spark_session()` with 8.3 short paths, 2 GB driver, 1 GB executor, `local[2]` | Direct reuse without modification. |
| **Data Cleaning** | `big_data/preprocessing/cleaners.py` | `clean_transactions()`, `clean_web_activity()`, `clean_social_media()` | Direct reuse; captures raw vs clean row counts & imputation metrics. |
| **Feature Extraction** | `big_data/feature_engineering/aggregators.py` | `aggregate_transactions()`, `aggregate_web_activity()`, `aggregate_social_media()`, `build_unified_customer_features()` | Direct reuse; outputs standard 23-column unified customer feature matrix. |
| **Data Export** | `big_data/export_utils.py` | `export_spark_dataframe()` batch PyArrow streaming | Direct reuse; streams Parquet and CSV to versioned folders without `winutils.exe`. |
| **K-Means ML** | `ml/segmentation/train_kmeans.py` | Candidate evaluation $K=2..8$, StandardScaler, PCA 2D projection, cluster profiling | Refactored into parameterized function `train_version_kmeans(input_parquet, output_dir)`. |
| **Recommender ML** | `ml/recommendations/recommender.py` | Item-item cosine similarity, Apriori association rules, 80/20 holdout evaluation | Refactored into parameterized function `train_version_recommender(tx_parquet, web_parquet, output_dir)`. |
| **Churn ML** | `ml/churn/build_churn_dataset.py`, `train_churn.py` | Point-in-time Random Forest with 180d historical window and 90d future observation window | Enhanced with dynamic cutoff date and safe fallback (`SKIPPED_INSUFFICIENT_TEMPORAL_DATA`). |
| **API Serving** | `backend/app/services/data_service.py` | In-memory cached analytics resolvers | Augmented with `reload(version_id)` and version preview resolvers. |

---

## 3. Storage Hierarchy & Directory Isolation

```text
d:\Infynux\big data project\
├── data/
│   ├── raw/                              <-- Baseline Raw (IMMUTABLE)
│   ├── processed/                        <-- Baseline Processed (IMMUTABLE)
│   ├── uploads/
│   │   └── <batch_id>/                   <-- Stage B Staged Raw CSVs & manifest.json
│   └── versions/
│       └── <version_id>/                 <-- Stage C PySpark Processed Parquet & CSVs
│           ├── cleaned_transactions.parquet
│           ├── cleaned_web_activity.parquet
│           ├── cleaned_social_media.parquet
│           ├── unified_customer_features.parquet
│           └── processing_report.json
├── ml/models/
│   ├── ...                               <-- Baseline ML Models (IMMUTABLE)
│   └── versions/
│       └── <version_id>/                 <-- Stage C Retrained Versioned Models
│           ├── kmeans_model.joblib
│           ├── cluster_profiles.json
│           ├── customer_recommendations.json
│           ├── association_rules.json
│           ├── churn_model.joblib (or skip note)
│           └── model_evaluation_report.json
```

And in **HDFS**:
- Staged Raw: `/customer-analytics/raw/uploads/<batch_id>/`
- Staged Processed: `/customer-analytics/processed/versions/<version_id>/`

---

## 4. Planned Implementation Phases

1. **Phase C2:** PySpark Batch Processing Pipeline (`backend/app/services/pipeline_execution_service.py`).
2. **Phase C3:** ML Retraining Orchestrator (`backend/app/services/model_training_service.py`).
3. **Phase D1:** Version Preview Service & API Routes (`backend/app/routes/ingestion_routes.py`).
4. **Phase D2:** Version Promotion & Rollback with `DataService.reload()`.
5. **Phase D3:** Frontend Student Workflow UI (`StudentDatasetUpload.jsx`, `DataProcessing.jsx`).
6. **Documentation & Tests:** Full test suite & user demonstration guide.

