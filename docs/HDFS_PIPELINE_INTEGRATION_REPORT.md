# Apache Hadoop HDFS Integration Report (Stage 9)
**Project:** Smart Customer Analysis and Personalized Experience Using Big Data  
**Environment:** Windows 11 Host + WSL2 Debian (Hadoop 3.3.6) + PySpark 3.5.1 (`local[2]`)  
**Date:** November 14, 2026  
**Status:** **VERIFIED & OPERATIONAL**

---

## 1. Executive Summary

In Stage 9, genuine distributed storage capabilities via **Apache Hadoop 3.3.6 HDFS** were fully integrated into the existing PySpark customer analytics processing pipeline.

- **Storage Architecture:** Local single-node HDFS cluster inside isolated WSL2 Debian Linux.
- **Compute Architecture:** PySpark 3.5.1 executing in `local[2]` batch mode on Windows 11 host.
- **Client Protocol:** Hadoop IPC / RPC client (port 9000) and DataNode Block Transfer (port 9866) communicating over WSL virtual network interface (`172.27.x.x`).
- **Data Ingestion:** Master PySpark pipeline (`scripts/run_big_data_pipeline.py`) ingests raw CSV datasets directly from HDFS URI paths (`hdfs://<WSL_IP>:9000/customer-analytics/raw/...`).
- **Data Storage:** Cleaned records and customer feature matrices are written directly to HDFS in compressed Parquet format and mirrored locally for zero-regression compatibility with downstream ML models and REST API endpoints.

---

## 2. Hadoop HDFS Architecture & Environment

| Parameter | Configuration | Verification Status |
| :--- | :--- | :--- |
| **Hadoop Version** | Apache Hadoop 3.3.6 | Verified (`/opt/hadoop/hadoop-3.3.6`) |
| **Java Runtime (WSL)** | Eclipse Temurin OpenJDK 8u432 (64-Bit) | Verified (`/opt/java/jdk8`) |
| **Java Runtime (Windows)** | Oracle JRE 1.8.0_471 (64-Bit) | Untouched & Isolated |
| **HDFS Cluster ID** | `CID-CUSTOMER-ANALYTICS-2024` | Verified format |
| **NameNode RPC** | `0.0.0.0:9000` (Advertised to Windows client) | **Pass** (TCP ping & RPC handshake) |
| **NameNode Web UI** | `0.0.0.0:9870` | **Pass** (HTTP JMX healthy) |
| **DataNode Block Transfer** | `172.27.214.120:9866` | **Pass** (Direct block write/read) |
| **DataNode Web UI** | `172.27.214.120:9864` | **Pass** (HTTP status healthy) |
| **Configured DFS Capacity** | 1,006.85 GB (DFS Remaining: 949.55 GB) | 1 Live DataNode active |
| **Replication Factor** | 1 (Single-Node standalone) | Verified (`dfs.replication = 1`) |

---

## 3. HDFS Directory Hierarchy

The complete customer analytics storage hierarchy was created and verified under `/customer-analytics/`:

```text
hdfs://<WSL_IP>:9000/customer-analytics/
├── raw/
│   ├── transactions/
│   │   └── transactions.csv                      [1,676,935 bytes]
│   ├── web_activity/
│   │   └── web_activity.csv                      [13,183,498 bytes]
│   └── social_media/
│       └── social_media.csv                      [1,334,002 bytes]
├── processed/
│   ├── cleaned_transactions/                     [12,214 Parquet records]
│   ├── cleaned_web_activity/                     [120,944 Parquet records]
│   └── cleaned_social_media/                     [8,828 Parquet records]
├── features/
│   ├── customer_transaction_features/            [1,200 records x 8 columns]
│   ├── customer_web_features/                    [1,200 records x 9 columns]
│   ├── customer_social_features/                 [1,200 records x 8 columns]
│   └── unified_customer_features/                [1,200 records x 23 columns]
└── analytics/
    ├── customer_segments/
    │   └── customer_segments.parquet             [1,200 records x 5 clusters]
    ├── recommendations/
    │   └── customer_recommendations.parquet      [6,000 records (Top-5 per customer)]
    └── churn_predictions/
        └── customer_churn_predictions.parquet    [1,177 eligible customer predictions]
```

---

## 4. End-to-End Pipeline Execution & Data Integrity Audit

Master pipeline (`scripts/run_big_data_pipeline.py`) executed against genuine HDFS storage:

### Ingestion & Cleaning Verification
- **Raw Transactions Ingested:** 12,239 records directly from HDFS CSV.
  - Duplicates Removed: 25
  - Missing Payment Methods Handled: 73 (imputed with `'Unknown'`)
  - Cleaned Records Stored: **12,214 records** (Exact baseline match)
- **Raw Web Activity Ingested:** 120,979 records directly from HDFS CSV.
  - Duplicates Removed: 35
  - Legitimate Non-Product Touchpoints Preserved: 60,540
  - Cleaned Records Stored: **120,944 records** (Exact baseline match)
- **Raw Social Media Ingested:** 8,828 records directly from HDFS CSV.
  - Cleaned Records Stored: **8,828 records** (Exact baseline match)

### Customer-Level Feature Aggregation & Multi-Source Join
- **Customer Dimension:** Exactly 1,200 unique customers (1 row per customer verified).
- **Feature Dimension:** 23 numerical & categorical features.
- **Null Value Audit:** **0 unexpected nulls** across all 23 columns.
- **HDFS Write & Immediate Readback:**
  - All 7 datasets written directly to HDFS in Parquet format.
  - Immediate PySpark readback confirmed 100% schema and row count identity.
- **Local Mirroring:** Mirrored to `data/processed/` using PyArrow for seamless ML & Flask REST API zero-downtime consumption.

---

## 5. Downstream Machine Learning & REST API Verification

1. **Unsupervised K-Means Customer Segmentation:**
   - Evaluated $K \in [2, 8]$; confirmed optimal $K=5$ (Silhouette Coefficient = `0.3451`, Davies-Bouldin = `1.1759`).
   - 1,200 customers segmented into 5 distinct behavioural clusters.
2. **Personalized Recommendation Engine:**
   - Item-item collaborative filtering with 394 association rules.
   - 6,000 top-5 explainable recommendations generated (Hit Rate@5 = `76.0%`, Catalog Coverage = `100%`).
3. **Supervised Customer Churn Prediction:**
   - Point-in-time observation with zero data leakage.
   - 1,177 eligible customer predictions (ROC-AUC = `0.782`, Average Precision = `0.704`).
4. **Flask REST API Test Suite (`pytest tests/`):**
   - **20 out of 20 tests passed** cleanly in 13.49 seconds.

---

## 6. Storage Operational Safeguards

- **Explicit Fallback Mode:** The pipeline defaults strictly to genuine HDFS (`--storage hdfs`). If HDFS NameNode or DataNode is offline or unreachable, the pipeline raises an immediate `RuntimeError` and refuses to proceed. It **never silently falls back** to local storage. An explicit `--storage local` flag is required for local execution.
- **Memory Footprint:** NameNode and DataNode JVM heaps are constrained to `-Xms128m -Xmx256m` each, consuming ≤ 512 MB total memory within WSL2 to guarantee system stability on 8 GB RAM machines.

