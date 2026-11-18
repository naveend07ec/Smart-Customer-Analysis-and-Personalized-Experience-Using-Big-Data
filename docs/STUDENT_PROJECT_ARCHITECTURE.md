# SMART Customer Analytics — System Architecture & Data Flow
**Project Title:** Smart Customer Analysis and Personalized Experience Using Big Data  
**Document Code:** SMART-ARCH-V2.0  
**Compliance Standard:** ISO/IEC/IEEE 42010 Architecture Description

---

## 1. System Architecture Overview

```
 +-------------------------------------------------------------------------+
 |                            CLIENT LAYER                                 |
 |  React 18 + Vite | Apple Minimal Dark UI | Chart.js | Lucide Icons      |
 +------------------------------------+------------------------------------+
                                      | HTTP REST (JSON)
                                      v
 +-------------------------------------------------------------------------+
 |                           API & LOGIC LAYER                             |
 |  Flask 3.1 REST Server (WSGI)                                           |
 |  - IngestionRoutes (/api/ingest/*, /api/process/*, /api/train/*)        |
 |  - IngestionService, PipelineExecutionService, ModelTrainingService     |
 |  - VersionPreviewService & DataService (In-Memory Hot Reloading)        |
 +-------------------+---------------------------------+-------------------+
                     |                                 |
                     v                                 v
 +-----------------------------------+ +-----------------------------------+
 |         STORAGE SUBSYSTEM         | |       DISTRIBUTED COMPUTING       |
 |  Apache Hadoop 3.3.6 HDFS         | |  Apache PySpark 3.5.1 (local[2])  |
 |  - hdfs://localhost:9000          | |  - In-Memory DataFrames           |
 |  - /customer-analytics/raw/       | |  - Cleaning & Deduplication       |
 |  - /customer-analytics/processed/ | |  - Multi-Source Aggregations      |
 |  - WSL2 Debian Environment        | |  - 23-Feature Matrix Generation   |
 +-----------------------------------+ +-----------------------------------+
                     |                                 |
                     v                                 v
 +-------------------------------------------------------------------------+
 |                         MACHINE LEARNING ENGINE                         |
 |  - Unsupervised K-Means ($K=2..8$) with Silhouette Optimization         |
 |  - PCA Dimensionality Reduction (2D/3D Coordinates)                     |
 |  - Item-Item Collaborative Filtering (Cosine Similarity)                |
 |  - Apriori Association Rule Mining (Support, Confidence, Lift)          |
 |  - Supervised Random Forest Churn Classifier (90-Day Horizon)           |
 +------------------------------------+------------------------------------+
                                      |
                                      v
 +-------------------------------------------------------------------------+
 |                       VERSION ISOLATION & STORAGE                       |
 |  - Active Pointer: data/current_version.json (baseline vs version_id)   |
 |  - Versioned Storage: data/versions/<id>/ & ml/models/versions/<id>/    |
 |  - Protected Baseline: data/_baseline_backup/ & ml/models/_baseline_... |
 +-------------------------------------------------------------------------+
```

---

## 2. End-to-End Pipeline Data Flow

```
[ transactions.csv ]
[ web_activity.csv ] ──► [ Stage B Validator ] ──► [ Hadoop HDFS ]
[ social_media.csv ]       - Schema validation       - /raw/uploads/<batch_id>/
                           - PK & Range checks       - Direct byte streaming
                           - Coverage reports
                                                            │
                                                            ▼
                                                   [ PySpark local[2] ]
                                                   - Order deduplication
                                                   - Payment imputation
                                                   - Customer aggregations
                                                            │
                                                            ▼
                                                   [ 23-Feature Matrix ]
                                                   - Customer ID PK
                                                   - Zero unexpected nulls
                                                            │
                                                            ▼
                                                   [ ML Retraining Engine ]
                                                   - K-Means (K=2..8)
                                                   - CF + Apriori Rules
                                                   - Churn RF (if >=270d)
                                                            │
                                                            ▼
                                                   [ Version Directory ]
                                                   - data/versions/<id>/
                                                   - ml/models/versions/<id>/
                                                   - Evaluation report
                                                            │
                                                            ▼
                                                   [ Modal Preview / Swap ]
                                                   - Preview analytics
                                                   - Atomic promotion
                                                   - 1-Click Rollback
```

---

## 3. Storage Hierarchy & Version Directory Structure

```
d:\Infynux\big data project\
├── data/
│   ├── raw/                           <-- Immutable baseline raw files
│   │   ├── transactions.csv
│   │   ├── web_activity.csv
│   │   └── social_media.csv
│   ├── processed/                     <-- Active production data (1,200 cust)
│   │   ├── unified_customer_features.csv & .parquet
│   │   ├── customer_segments.csv & .parquet
│   │   └── customer_recommendations.csv & .parquet
│   ├── current_version.json           <-- Active version pointer
│   ├── _baseline_backup/              <-- Permanent copy of baseline datasets
│   └── versions/                      <-- Isolated student batch datasets
│       └── <version_id>/
│           ├── unified_customer_features.csv & .parquet
│           ├── customer_segments.csv
│           └── processing_report.json
├── ml/
│   └── models/
│       ├── kmeans_model.joblib        <-- Active production models
│       ├── scaler.joblib
│       ├── pca_model.joblib
│       ├── item_similarity_matrix.joblib
│       ├── cluster_profiles.json
│       ├── _baseline_backup/          <-- Permanent copy of baseline models
│       └── versions/                  <-- Isolated student batch models
│           └── <version_id>/
│               ├── kmeans_model.joblib
│               ├── cluster_profiles.json
│               ├── pca_model.joblib
│               ├── item_similarity_matrix.joblib
│               └── model_evaluation_report.json
```

---

## 4. Key Security & Performance Guarantees

1. **Zero Baseline Mutation:** Baseline files in `data/raw/`, `data/processed/`, and `ml/models/` are never overwritten during upload, processing, or retraining.
2. **Safe Fallbacks:** Churn training checks date span ($\ge 270$ days); insufficient batches fallback gracefully without aborting the batch.
3. **Hardware Boundaries:** PySpark operates strictly in `local[2]` mode under an 8 GB memory ceiling, preventing memory leaks and swapping.
4. **HDFS Enforced:** Ingestion requires live HDFS service (`HTTP 503` if offline), ensuring student demonstrations prove true distributed storage.

