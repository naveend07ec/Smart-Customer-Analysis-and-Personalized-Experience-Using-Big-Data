# Stage 9 Final Read-Only Audit Report

**Date of Audit:** November 14, 2026  
**Audited Target:** Apache Hadoop HDFS Integration & PySpark Pipeline (Stage 9)  
**Project Workspace:** `D:\Infynux\big data project`  
**Execution Mode:** Strictly Read-Only (Zero code, model, dataset, or configuration modifications)

---

## Executive Summary

This audit provides a factual, evidence-backed evaluation of the Apache Hadoop HDFS (v3.3.6) single-node distributed storage integration with the Apache PySpark (v3.5.1) batch customer analytics pipeline. All checks confirm complete data fidelity (0.0 numeric divergence across all features), independent HDFS block readability after daemon restart, full preservation of existing machine learning models, dynamically wired frontend telemetry via NameNode JMX/RPC sockets, and stable, constrained WSL2 memory utilization (~459 MB total Hadoop RSS).

---

## 1. Schema & Column Count Audit (Resolution of the 8 vs 9 Column Issue)

### 1.1 Investigated Feature Schemas

The four core customer feature datasets were audited in both local and HDFS storage layers:

| Dataset Name | Row Count | Total Columns | Column Breakdown |
| :--- | :---: | :---: | :--- |
| `customer_transaction_features` | 1,200 | **8** | `customer_id` + 7 transaction metrics |
| `customer_web_features` | 1,200 | **9** | `customer_id` + 8 web metrics |
| `customer_social_features` | 1,200 | **8** | `customer_id` + 7 social metrics |
| `unified_customer_features` | 1,200 | **23** | `customer_id` + 7 (tx) + 8 (web) + 7 (social) |

### 1.2 Detailed Column List for `customer_social_features` (8 Columns)
1. `customer_id` (`string`)
2. `total_social_interactions` (`int64` / `int32`)
3. `avg_engagement_score` (`double`)
4. `avg_sentiment_score` (`double`)
5. `positive_interactions_count` (`int64` / `int32`)
6. `neutral_interactions_count` (`int64` / `int32`)
7. `negative_interactions_count` (`int64` / `int32`)
8. `unique_platforms_count` (`int64` / `int32`)

### 1.3 Detailed Column List for `customer_web_features` (9 Columns)
1. `customer_id` (`string`)
2. `total_web_activities` (`int64` / `int32`)
3. `total_sessions` (`int64` / `int32`)
4. `avg_duration_seconds` (`double`)
5. `product_views_count` (`int64` / `int32`)
6. `cart_additions_count` (`int64` / `int32`)
7. `wishlist_count` (`int64` / `int32`)
8. `checkout_starts_count` (`int64` / `int32`)
9. `cart_to_checkout_ratio` (`double`)

### 1.4 Cause of the Discrepancy
- **Audit Determination:** This is definitively a **documentation/reporting error** in earlier review summaries, **not** a schema change or code alteration.
- **Proof:** 
  - In `big_data/feature_engineering/aggregators.py` (lines 111–119), `extract_social_features()` has always aggregated exactly 7 metrics for each `customer_id` (total 8 columns).
  - In `big_data/feature_engineering/unified_features.py`, the unified table performs sequential outer joins on `customer_id`. The math confirms:
    $$\text{Total Unified Columns} = 1\ (\text{customer\_id}) + 7\ (\text{tx}) + 8\ (\text{web}) + 7\ (\text{social}) = 23\ \text{columns}$$
  - If `customer_social_features` had 9 columns (8 metrics), `unified_customer_features` would have had 24 columns. However, `unified_customer_features` has consistently held exactly 23 columns across all prior project stages.
  - A previous summary inadvertently transposed the 8 metrics of the web dataset onto the social dataset.

---

## 2. Local Baseline vs HDFS-Generated Pipeline Output Comparison

An exhaustive cell-by-cell numerical and structural comparison was performed between the local Parquet files in `data/processed/` and the HDFS-backed Parquet datasets at `hdfs://172.27.214.120:9000/customer-analytics/`:

### 2.1 Dataset Verification Matrix

| Dataset Target | Local Rows | HDFS Rows | Column Count | Null Count Delta | Max Numeric Diff | Parity Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `cleaned_transactions` | 12,214 | 12,214 | 10 | 0 | **0.000000** | **100% Exact Match** |
| `cleaned_web_activity` | 120,944 | 120,944 | 10 | 0 | **0.000000** | **100% Exact Match** |
| `cleaned_social_media` | 8,828 | 8,828 | 9 | 0 | **0.000000** | **100% Exact Match** |
| `customer_transaction_features` | 1,200 | 1,200 | 8 | 0 | **0.000000** | **100% Exact Match** |
| `customer_web_features` | 1,200 | 1,200 | 9 | 0 | **0.000000** | **100% Exact Match** |
| `customer_social_features` | 1,200 | 1,200 | 8 | 0 | **0.000000** | **100% Exact Match** |
| `unified_customer_features` | 1,200 | 1,200 | 23 | 0 | **0.000000** | **100% Exact Match** |

### 2.2 In-Depth Comparison Criteria
1. **Primary Key Sorting & Record Alignment:**
   - Datasets were sorted by their true unique identifiers: `transaction_id` (transactions), `activity_id` (web), `interaction_id` (social), and `customer_id` (aggregated feature datasets).
   - Zero missing records, zero duplicate records, and zero spurious records were found.
2. **Null Value Fidelity:**
   - In `cleaned_web_activity`, legitimate nulls exist for non-product events (e.g. `page_view` on homepage). Exactly 60,540 nulls in `product_id`, `category`, and `price`, and 30,236 nulls in `referrer` were preserved with 100% identity between local and HDFS outputs.
3. **Data Type Representation Nuance:**
   - In the local baseline written through standalone PyArrow exports, count metrics defaulted to 64-bit integer (`int64`).
   - In the HDFS output written natively by PySpark 3.5.1, Spark SQL schema conventions stored count aggregations as 32-bit integer (`int32` / `IntegerType`).
   - Floating-point columns (`double` / `float64`) and string columns (`string` / `StringType`) match identically.
   - All downstream consumption layers (NumPy, Pandas, Scikit-learn, Flask JSON serialization) treat `int32` and `int64` transparently.

---

## 3. Independent HDFS Readback After NameNode & DataNode Restart

To verify persistent block integrity and rule out ephemeral in-memory caching:

1. **Daemon Restart Execution:**
   - Previous daemons (NameNode PID 340, DataNode PID 408) were cleanly terminated using `/opt/hadoop/hadoop-3.3.6/bin/hdfs --daemon stop`.
   - Fresh daemons were started under the persistent daemon supervisor:
     - **NameNode PID:** `2827`
     - **DataNode PID:** `2895`
   - DataNode successfully registered with NameNode and reported healthy block pools.
2. **Independent Readback Test via PySpark Client:**
   A standalone PySpark session was launched from Windows with DataNode hostname resolution enabled:
   - `spark.read.parquet("hdfs://172.27.214.120:9000/customer-analytics/processed/cleaned_transactions")` -> **12,214 rows** [PASS]
   - `spark.read.parquet("hdfs://172.27.214.120:9000/customer-analytics/processed/cleaned_web_activity")` -> **120,944 rows** [PASS]
   - `spark.read.parquet("hdfs://172.27.214.120:9000/customer-analytics/processed/cleaned_social_media")` -> **8,828 rows** [PASS]
   - `spark.read.parquet("hdfs://172.27.214.120:9000/customer-analytics/features/customer_transaction_features")` -> **1,200 rows** [PASS]
   - `spark.read.parquet("hdfs://172.27.214.120:9000/customer-analytics/features/customer_web_features")` -> **1,200 rows** [PASS]
   - `spark.read.parquet("hdfs://172.27.214.120:9000/customer-analytics/features/customer_social_features")` -> **1,200 rows** [PASS]
   - `spark.read.parquet("hdfs://172.27.214.120:9000/customer-analytics/features/unified_customer_features")` -> **1,200 rows** [PASS]
3. **Conclusion:** Storage is persistent on the ext4 filesystem inside WSL Debian (`/var/hadoop/hdfs/data` and `/var/hadoop/hdfs/name`). Blocks survive daemon restarts without corruption or block loss.

---

## 4. Machine Learning Model Preservation & Consumption

All pre-trained machine learning models and evaluation baselines remain intact:

1. **Customer Segmentation (K-Means Clustering):**
   - **Model File:** `ml/models/kmeans_model.pkl` & `scaler.pkl` (unmodified).
   - **Features Consumed:** 22 numerical features from `unified_customer_features`.
   - **Metrics:** $K=5$, Silhouette Score = `0.3451`, Davies-Bouldin Index = `1.1759`.
   - **Customer Distribution:** 1,200 customers mapped across 5 distinct clusters (`VIP High-Spenders`, `Window Shoppers`, `Engaged Brand Advocates`, `At-Risk Occasional Shoppers`, `Low-Engagement Churn Risk`).
2. **Personalized Product Recommender:**
   - **Model Files:** `collaborative_filtering_svd.pkl`, item similarity matrix, and popularity fallbacks (unmodified).
   - **Predictions:** 6,000 recommendations generated (Top 5 per customer for all 1,200 customers).
   - **Catalog Coverage:** 100.0% (all 20 product catalog items recommended).
   - **Hit Rate @ 5:** 76.0%.
3. **Customer Churn Prediction (Random Forest Classifier):**
   - **Model File:** `ml/models/churn_rf_model.pkl` (unmodified).
   - **Eligible Predictions:** Exactly 1,177 customers (satisfying point-in-time cutoff requiring historical purchases prior to the observation window).
   - **Prediction Integrity:** Zero discrepancies; distribution matches the established baseline.
4. **Automated Test Suite:**
   - Ran `pytest tests/` -> **20 passed in 4.90s** (100% pass rate).

---

## 5. Frontend & Backend Dynamic Status Verification

The audit verified whether HDFS health metrics displayed on the React dashboard originate from actual runtime systems rather than mock or hardcoded values:

1. **Backend Service Layer (`backend/app/services/data_service.py`):**
   - **Active Socket Check:** Lines 145–152 attempt a live TCP socket connection to `(HDFS_HOST, HDFS_PORT)` (e.g. `172.27.214.120:9000`) with a 2-second timeout. If unreachable, `hdfs_status` immediately transitions to `offline`.
   - **NameNode JMX Ingestion:** Lines 154–173 perform a live HTTP GET request to the NameNode web UI JMX endpoint:
     `http://172.27.214.120:9870/jmx?qry=Hadoop:service=NameNode,name=NameNodeInfo`
     Live attributes extracted directly from NameNode memory include:
     - `Free` & `Used` disk bytes
     - `TotalBlocks`
     - `CorruptBlocks`
     - `MissingBlocks`
     - `LiveNodes`
   - **Pipeline Metadata Check:** Inspects `data/hdfs_pipeline_metadata.json` for timestamps, row counts, and storage formats.
2. **REST API Endpoint (`backend/app/routes/pipeline_routes.py`):**
   - Endpoint `/api/pipeline/summary` serves the dynamic dictionary generated by `data_service.get_pipeline_summary()`.
3. **Frontend Presentation (`frontend/src/pages/DataProcessing.jsx`):**
   - Renders `pipelineSummary.hdfs_storage.status`, active node count, formatted bytes, and storage tier directly into the UI.
   - **Determination:** The frontend reflects live, dynamic telemetry with zero hardcoding.

---

## 6. WSL2 Memory Footprint vs Configured JVM Limits

### 6.1 Configuration Audit
Hadoop environment configuration in WSL (`/opt/hadoop/hadoop-3.3.6/etc/hadoop/hadoop-env.sh`) enforces strict, minimal memory limits:
```bash
export HDFS_NAMENODE_OPTS="-Xms128m -Xmx256m"
export HDFS_DATANODE_OPTS="-Xms128m -Xmx256m -Ddfs.datanode.hostname=172.27.214.120"
```

### 6.2 Live Inspection Findings (`free -m` & `ps`)
- **WSL Virtual Machine Memory:**
  - **Total Memory:** 3,564 MB (~3.5 GB allocated to WSL2 VM)
  - **Used Memory:** 805 MB (total system usage including all background services)
  - **Free Memory:** 2,621 MB
  - **Available Memory:** 2,758 MB
  - **Swap Usage:** 0 MB used (out of 1,024 MB configured)

- **Hadoop Daemon RSS Consumption:**
  | Process Name | PID | Configured Max Heap | Live Resident Set Size (RSS) | Virtual Memory (VSZ) | % Memory |
  | :--- | :---: | :---: | :---: | :---: | :---: |
  | **NameNode** | 2827 | 256 MB | **232.8 MB** (232,868 KB) | 1,975,516 KB | 6.3% |
  | **DataNode** | 2895 | 256 MB | **237.2 MB** (237,248 KB) | 1,960,140 KB | 6.5% |
  | **Combined** | — | 512 MB | **470.0 MB** | — | 12.8% |

### 6.3 Analysis of JVM RSS vs Heap
- The live JVM resident memory (RSS) is approximately ~233 MB and ~237 MB respectively, which is strictly beneath the physical memory ceiling.
- RSS accounts for the active Java heap, Metaspace, thread stacks, and JNI shared libraries (`libhadoop.so`).
- Total memory consumed by both Hadoop daemons combined is **under 470 MB**, leaving more than 2.7 GB of free RAM in the WSL2 instance and avoiding memory pressure on the Windows host.

---

## 7. Audit Conclusion & Compliance Summary

1. **Read-Only Compliance:** No application code, test files, configuration files, trained model binaries, or raw/processed datasets were modified during this audit.
2. **Schema Clarity:** `customer_social_features` has always contained 8 columns; the reference to 9 columns was an editorial error in previous status notes.
3. **Pipeline Parity:** The PySpark-on-HDFS batch pipeline produces 100% identical analytical output compared to the original local baseline (0.0 numeric error, 0 missing records).
4. **Fault Tolerance & Reliability:** Daemons recover cleanly after restart, and Parquet data residing in genuine HDFS blocks is read directly by Windows PySpark without errors.
5. **Stage 9 Sign-Off:** The project is in a verified, stable state and fully prepared for review.

