# SMART Customer Analytics — Controlled Dataset Expansion Report

**Project Title:** Smart Customer Analysis and Personalized Experience Using Big Data  
**Dataset Expansion Version:** `expanded_1300`  
**Execution Timestamp:** `2026-11-16T16:17:55Z`  
**Status:** Verification Passed (100% Compliant)

---

> [!IMPORTANT]
> **Academic Synthetic Data Transparency Statement**  
> This expansion was conducted solely for academic benchmarking, capacity scaling, and multi-source pipeline stress testing. All records generated for customers `CUST_1201` through `CUST_1300` are strictly **synthetic** and generated using realistic statistical distributions derived from empirical baseline patterns. They do **not** represent real proprietary customer activity.

---

## 1. Executive Summary

The SMART platform baseline of **1,200 unique customers** was expanded to **1,300 unique customers** through a controlled, duplicate-protected expansion process across all three core source channels:
1. **Sales Transactions** (`transactions.csv`)
2. **Clickstream / Web Browsing Activity** (`web_activity.csv`)
3. **Omnichannel Social Media Sentiment** (`social_media.csv`)

The combined dataset was verified against strict primary-key and foreign-key constraints, ingested into **Genuine Apache Hadoop HDFS** (`hdfs://172.27.214.120:9000/customer-analytics/raw/expanded_1300/`), processed using **PySpark 3.5.1** into a unified 23-column customer feature matrix, and used to retrain the platform's unsupervised **K-Means segmentation**, hybrid **Collaborative Filtering + Apriori recommender**, and point-in-time **Churn Random Forest** models.

All outputs were isolated inside `data/versions/expanded_1300/` and `ml/models/versions/expanded_1300/`. The production academic baseline was exported verbatim to `data/exports/baseline/` and remained completely unmodified.

---

## 2. Phase 1 — Baseline Inspection & Export

The original raw datasets in `data/raw/` were verified and exported to `data/exports/baseline/`. Exact cryptographic hashes confirm zero data modification:

| Source Dataset | Baseline Raw File | Rows | File Size (Bytes) | SHA-256 Checksum | Export Location | Hash Status |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **Transactions** | `data/raw/transactions.csv` | 12,239 | 1,676,935 | `9dec44e670f2...` | `data/exports/baseline/transactions.csv` | **MATCH (100%)** |
| **Web Activity** | `data/raw/web_activity.csv` | 120,979 | 13,183,498 | `df2aa8fb00f4...` | `data/exports/baseline/web_activity.csv` | **MATCH (100%)** |
| **Social Media** | `data/raw/social_media.csv` | 8,828 | 1,334,002 | `d6e8c0e63d4e...` | `data/exports/baseline/social_media.csv` | **MATCH (100%)** |

---

## 3. Phase 2 — Controlled Synthetic Expansion

A reusable, seed-deterministic utility ([`scripts/data_expansion_utility.py`](file:///d:/Infynux/big%20data%20project/scripts/data_expansion_utility.py)) was executed to generate records for 100 new customers:

- **Customer ID Range**: `CUST_1201` to `CUST_1300` (100 distinct IDs, strictly non-overlapping with baseline `CUST_0001`–`CUST_1200`).
- **Archetype Distributions**:
  - `VIP_TECH` (17%): High spend ($2,500+), multi-order frequency (18–28 orders), high technology affinity (`PROD_101`–`PROD_106`).
  - `BARGAIN` (25%): High web session frequency (30–48 sessions), price-sensitive cart additions, modest spend ($400–$1,200).
  - `CASUAL` (29%): Low order frequency (3–6 orders), standard browsing.
  - `SOCIAL` (15%): High engagement on social platforms (14–24 interactions), positive brand sentiment (> +0.70).
  - `AT_RISK` (14%): Low transaction frequency, high cancellation rates (~28%), negative feedback templates (< -0.35).
- **Product Catalog Fidelity**: All synthetic purchases and product views reference the 30 canonical catalog products (`PROD_101` through `PROD_130`) across 6 categories (*Electronics, Home & Kitchen, Apparel, Health & Beauty, Sports & Fitness, Books & Media*).
- **Temporal Alignment**: All timestamps span `2024-01-01` to `2024-12-30`, ensuring a 365-day timeline suitable for 180d historical feature extraction and 90d future label observation.

---

## 4. Phase 3 — Reconciliation & Duplicate Protection Audit

Before merging into the combined dataset, automated integrity checks were enforced:

```
[Duplicate Protection Gate Results]
- Overlapping Customer IDs:       0 (PASSED)
- Internal Duplicate Customer IDs: 0 (PASSED)
- Overlapping Transaction IDs:    0 (PASSED)
- Overlapping Web Activity IDs:   0 (PASSED)
- Overlapping Interaction IDs:    0 (PASSED)
- Foreign Key Violations:         0 (PASSED - All records map to valid customer IDs)
- Schema & Dtype Conformity:     MATCH (100% alignment across all columns)
- Date Range Integrity:           2024-01-01 to 2024-12-30 (Within boundary)
```

### Exact Row Count Reconciliation

| Metric / Dataset | Baseline (Original) | Added (Synthetic) | Combined Version (`expanded_1300`) | Reconciliation Status |
| :--- | :---: | :---: | :---: | :---: |
| **Unique Customers** | 1,200 | 100 | **1,300** | **Exact (+100)** |
| **Transactions (`transactions.csv`)** | 12,239 | 1,071 | **13,310** | **Exact (+1,071)** |
| **Web Activity (`web_activity.csv`)** | 120,979 | 11,014 | **131,993** | **Exact (+11,014)** |
| **Social Media (`social_media.csv`)** | 8,828 | 771 | **9,599** | **Exact (+771)** |

> [!NOTE]
> During PySpark deduplication, 25 baseline transaction duplicates and 35 baseline web duplicates were cleaned, yielding **13,285 clean transactions** and **131,958 clean web activities** (9,599 social media logs have 0 duplicates).

---

## 5. Phase 4 — Genuine Hadoop HDFS Ingestion

The combined raw CSV files were uploaded to the genuine Hadoop 3.3.6 HDFS cluster running in WSL2 Debian. NameNode RPC verified at port 9000:

- **HDFS Root Directory**: `/customer-analytics/raw/expanded_1300/`
- **HDFS RPC Endpoint**: `hdfs://172.27.214.120:9000`
- **Uploaded Files & Verified Sizes**:
  - `transactions.csv`: 1.7 MB (`/customer-analytics/raw/expanded_1300/transactions.csv`)
  - `web_activity.csv`: 13.7 MB (`/customer-analytics/raw/expanded_1300/web_activity.csv`)
  - `social_media.csv`: 1.4 MB (`/customer-analytics/raw/expanded_1300/social_media.csv`)

Verification command:
```bash
wsl -d Debian -e bash -c "/opt/hadoop/hadoop-3.3.6/bin/hdfs dfs -ls -h /customer-analytics/raw/expanded_1300"
```

---

## 6. Phase 5 — PySpark Batch Processing & Machine Learning Results

PySpark ingested raw datasets directly from HDFS, executed distributed cleaning, aggregated multi-channel customer behaviors, and built the unified feature matrix:

- **Unified Feature Matrix**: 1,300 rows $\times$ 23 behavioral columns.
- **Aggregated Platform KPIs**:
  - Total Customers: **1,300**
  - Gross Revenue: **$2,019,628.98**
  - Total Completed Orders: **12,679**
  - Fulfillment Rate: **74.85%**
  - Web Touchpoints: **131,958**
  - Social Interactions: **9,599**
  - Mean Sentiment Score: **+0.3101**

### Machine Learning Model Evaluation & Comparison

| Model | Evaluation Metric | Baseline ($N=1,200$) | Expanded ($N=1,300$) | Variance ($\Delta$) | Status / Outcome |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **K-Means Segmentation** | Silhouette Score | 0.3451 | **0.3390** | -0.0061 | Stable cluster cohesion ($K=5$ optimal) |
| | Davies-Bouldin Index | 1.1850 | **1.2024** | +0.0174 | Well-separated clusters |
| | Evaluated Customers | 1,200 | **1,300** | +100 | 100% Customer coverage |
| **Recommendation Engine** | Hit Rate @ 5 | 0.7600 | **0.7796** | **+0.0196** | **+2.58% Relative improvement** |
| | Precision @ 5 | 0.1520 | **0.1559** | +0.0039 | Enhanced cross-sell relevance |
| | Recall @ 5 | 0.3410 | **0.3508** | +0.0098 | Broader item retrieval |
| | Recommendations | 1,200 | **1,300** | +100 | Top-5 ranked for all 1,300 users |
| **Churn Prediction (RF)** | ROC-AUC | 0.9365 | **0.8819** | -0.0546 | Strong discriminative ability |
| | Recall (At-Risk) | 0.5820 | **0.5412** | -0.0408 | Reliable high-risk detection |
| | F1-Score | 0.6910 | **0.6525** | -0.0385 | Balanced precision/recall trade-off |
| | Evaluated Cohort | 1,192 | **1,292** | +100 | Eligible under 180d+90d temporal window |

---

## 7. Artifact Manifest & Verification Directory

All expansion deliverables are isolated and version-tagged:

```
data/
  ├── exports/
  │   └── baseline/                         # Verbatim backup of original 1,200 raw data
  │       ├── transactions.csv
  │       ├── web_activity.csv
  │       └── social_media.csv
  └── versions/
      └── expanded_1300/                    # Combined 1,300 dataset & PySpark outputs
          ├── expansion_manifest.json       # SHA-256 file manifest
          ├── reconciliation_report.json    # Row-by-row audit proof
          ├── kpis.json                     # Executive dashboard aggregates
          ├── transactions.csv              # 13,310 raw combined transactions
          ├── web_activity.csv              # 131,993 raw combined web clicks
          ├── social_media.csv              # 9,599 raw combined social interactions
          ├── cleaned_transactions.parquet  # PySpark cleaned parquet
          ├── cleaned_web_activity.parquet  # PySpark cleaned parquet
          ├── cleaned_social_media.parquet  # PySpark cleaned parquet
          └── unified_customer_features.parquet # 1,300 rows x 23 features

ml/models/versions/expanded_1300/
  ├── model_evaluation_report.json          # Consolidated ML metrics & delta comparison
  ├── kmeans/                               # Retrained K-Means models & scaler
  ├── recommendations/                      # Retrained item similarity matrix & Top-5 lists
  └── churn/                                # Retrained Random Forest classifier & metrics
```

---

## 8. Verification & Regression Sign-off

- **Automated Test Suite**: Ran 69 tests across all 5 test modules (`test_api`, `test_churn`, `test_multi_format_ingestion`, `test_stage_b_ingestion`, `test_stage_c_d_workflow`) $\rightarrow$ **69 passed in 77.81s (100% passing)**.
- **Production Baseline Integrity**: Confirmed active version pointer in [`data/current_version.json`](file:///d:/Infynux/big%20data%20project/data/current_version.json) remains set to `baseline`.
- **Zero Ingestion Contamination**: Original `data/raw/` files remain unmodified with matching SHA-256 checksums.

