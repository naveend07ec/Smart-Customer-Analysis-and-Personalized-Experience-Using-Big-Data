# SMART Project — Student Demonstration & Operations Guide
**Project Title:** Smart Customer Analysis and Personalized Experience Using Big Data  
**Target Audience:** Students, Evaluators, Academic Reviewers  
**Platform Architecture:** React 18 + Vite | Flask 3.1 REST API | PySpark 3.5.1 (`local[2]`) | Hadoop 3.3.6 HDFS | Scikit-Learn

---

## 1. Executive Summary & Purpose

The SMART Customer Analytics Platform is a complete Big Data and Machine Learning system engineered for customer intelligence. It addresses the end-to-end data lifecycle:
1. **Multi-Format Ingestion:** Ingestion across supported raw data formats including **CSV, TSV, JSON, JSON Lines (.jsonl), Text (.txt), and Server Logs (.log)**.
2. **HDFS Storage:** Commits raw datasets to Hadoop Distributed File System (`/customer-analytics/raw/uploads/<batch_id>/`) with strict byte preservation and SHA-256 verification.
3. **Automated Schema Discovery & Field Mapping:** Inspects file structures, infers data types, detects customer identifiers (`CUST_\d+`), and provides interactive field mapping to canonical schemas.
4. **PySpark Batch Processing:** Distributed PySpark batch jobs perform cleaning, deduplication, missing value imputation, multi-source aggregations, and outer joins to produce the unified 23-column customer feature matrix.
5. **Machine Learning Retraining & Evaluation:**
   - **K-Means Clustering:** Evaluates optimal $K \in [2, 8]$ using Silhouette Scores and Davies-Bouldin index; generates 2D/3D PCA coordinates and behavioral personas.
   - **Hybrid Recommender:** Blends Item-Item Collaborative Filtering (cosine similarity) and Apriori association rules, validated against zero-leakage 80/20 train/test holdouts.
   - **Supervised Churn Forecast:** Random Forest classifier with point-in-time temporal cutoff logic (requires $\ge 270$ days history, safely handles insufficient spans without crashing).
6. **Data Export & Templates:** Downloads canonical CSV templates, raw batch files, processed Parquet/CSV datasets, and JSON analytics reports.
7. **Version-Isolated Preview, Atomic Promotion & Instant Rollback:** Students can inspect batch analytics side-by-side in a modal preview, promote to production, or immediately roll back to the academic baseline.

---

## 2. Quick-Start Demonstration Workflow (7 Steps)

Follow this sequence during your project evaluation:

```
[ Step 1: Upload Raw Files ] ──► [ Step 2: HDFS Storage ] ──► [ Step 3: Schema Discovery & Mapping ]
                                                                             │
[ Step 6: Preview & Export ] ◄── [ Step 5: Retrain ML ] ◄── [ Step 4: PySpark Batch Processing ]
           │
[ Step 7: Promote / Rollback ]
```

### Step 1: Access the Data Pipeline Hub
1. Launch the application:
   - Backend: `http://localhost:5000`
   - Frontend: `http://localhost:3000`
2. Navigate to **Data Pipeline** (`/pipeline`) in the top navigation bar.
3. Observe the **Multi-Format Big Data Ingestion & Analytics Pipeline** workspace.

### Step 2: Select Mode & Upload Raw Files
Students can demonstrate in either:
- **Multi-Format Mode (Default):** Upload mixed files (e.g. `transactions.json`, `web_activity.csv`, or server logs).
- **Classic 3-CSV Mode:** Upload the 3 fixed CSV files (`transactions.csv`, `web_activity.csv`, `social_media.csv`).

Drag and drop or browse files and click **Stage & Discover Batch**:
- The backend assigns a unique batch ID (e.g. `batch_20261116_...`).
- Computes SHA-256 checksums and registers byte counts.
- Executes automated schema discovery and source classification.

### Step 3: Inspect Schema & Map Custom Columns
1. In the **Active Batch Files Registry**, review the uploaded files:
   - Filename, Format badge (`CSV`, `JSON`, `JSONL`, `TXT`, `LOG`), Size, and Schema Status.
2. Click **Map Fields** on any file:
   - Inspect discovered column names, inferred scalar types (`string`, `double`, `integer`, `timestamp`), and sample data.
   - Verify or adjust the target analytical source (`transactions`, `web_activity`, `social_media`, or `other`).
   - Map custom columns to canonical project fields (e.g. `client_code` $\to$ `customer_id`).
   - Click **Save & Apply Mapping**: The registry updates analytics eligibility to `✓ ELIGIBLE`.

### Step 4: Store Raw Data in Hadoop HDFS
1. Click **2. Commit to HDFS**:
   - The backend checks NameNode health on port 9000.
   - Uploads untouched raw files into `/customer-analytics/raw/uploads/<batch_id>/`.
   - Verifies remote file sizes using `hdfs dfs -stat %b`.

### Step 5: Execute PySpark Distributed Batch Processing
1. Click **3. Run PySpark Batch**:
   - Spawns PySpark in constrained `local[2]` mode within an 8 GB RAM boundary.
   - Standardizes heterogeneous formats into structured DataFrames.
   - Cleans records: removes duplicates, imputes missing payment methods, validates positive monetary values.
   - Computes behavioral feature aggregations.
   - Outer-joins into the canonical 23-column customer feature matrix (`unified_customer_features.parquet` & `.csv`).
   - Execution finishes in ~15-30 seconds with a full processing audit.

### Step 6: Retrain ML Models & Compare Against Baseline
1. Click **4. Retrain Models**:
   - Retrains K-Means clustering across $K=2..8$ and outputs silhouette scores.
   - Rebuilds Collaborative Filtering item-similarity matrix and mines Apriori association rules.
   - Evaluates churn temporal eligibility ($\ge 270$ days) and fits Random Forest.
   - Outputs side-by-side performance benchmarks against the Academic Baseline in the comparison table.

### Step 7: Preview Analytics, Export Data & Instant Rollback
1. Click **5. Preview Analytics**:
   - Opens the isolated preview modal without affecting production users.
   - Inspect **Overview KPIs**, **Segment Distribution**, **Association Rules**, and **Churn Risk Tiers**.
2. **Export Center:**
   - Download canonical CSV templates.
   - Export raw staged files.
   - Export cleaned Parquet/CSV datasets.
   - Download JSON execution and evaluation reports.
3. **Promotion & Rollback:**
   - Click **Promote Version to Production**: Hot-reloads production dashboards to the new batch version.
   - Click **Rollback to Baseline**: Instantly restores the original verified 1,200-customer academic baseline.

---

## 3. Academic Evaluation FAQ

**Q: Where are the original baseline files stored?**  
A: Raw baselines reside in `data/raw/`, processed baselines in `data/processed/`, and models in `ml/models/`. Student batches are strictly isolated in `data/versions/<id>/` and `ml/models/versions/<id>/`.

**Q: How does HDFS fail-safe protection work?**  
A: If WSL2 or Hadoop NameNode is stopped, ingestion immediately halts with `HTTP 503 Service Unavailable: HDFS service is offline`. The system never silently falls back to local storage.

**Q: What happens if an upload only has 2 sources instead of 3?**  
A: PySpark standardizes the missing source as an empty schema. `build_unified_customer_features` outer joins with 0/neutral defaults, safely producing the exact canonical 23-column matrix without pipeline crashes.
