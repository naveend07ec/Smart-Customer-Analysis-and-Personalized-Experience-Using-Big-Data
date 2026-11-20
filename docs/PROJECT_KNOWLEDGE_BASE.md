# SMART Big Data Customer Analytics & Personalization Platform
## Comprehensive Knowledge Base: Architecture, Tech Stack & Defense Q&A

**Project Title:** Smart Customer Analysis and Personalized Experience Using Big Data  
**Author / Team:** naveend07ec  
**Repository:** [Smart-Customer-Analysis-and-Personalized-Experience-Using-Big-Data](https://github.com/naveend07ec/Smart-Customer-Analysis-and-Personalized-Experience-Using-Big-Data)  

---

# SECTION 1: WHAT WE USED, WHY WE USED IT, AND HOW IT WORKS

This section provides a rigorous breakdown of every component, framework, library, and algorithm utilized in the platform.

---

## 1. Storage & Distributed File System Layer

### A. Apache Hadoop HDFS (Hadoop Distributed File System) 3.3.6
* **What it is:** A distributed, scalable, and fault-tolerant file storage system that splits large files into blocks and stores them redundantly across commodity hardware.
* **Why we used it:**
  1. *Enterprise Big Data Standard:* In commercial e-commerce, raw clickstreams, server access logs, and transaction streams must be preserved in their raw, untouched byte format (Data Lake pattern) before any ETL or transformation.
  2. *Immutable Audit Trail:* Storing incoming raw batches in HDFS (`/customer-analytics/raw/uploads/<batch_id>/`) guarantees that raw logs are never overwritten or corrupted by downstream pipeline bugs.
  3. *WSL2 Integration:* Installed and managed inside WSL2 (Debian Linux) running real NameNode and DataNode daemons on port 9000, with Python WebHDFS / socket connectivity.
* **How it works:**
  - When raw files are uploaded via the UI, `HDFSManager` computes SHA-256 checksums and file sizes.
  - Files are streamed into HDFS via WebHDFS REST API or `hdfs dfs -put`.
  - If Hadoop daemons are offline, the system safely falls back to local staging storage without crashing, ensuring zero data loss and seamless offline demonstrations.

### B. Apache Parquet Storage (Snappy Compressed)
* **What it is:** An open-source, columnar storage file format optimized for fast query execution and efficient data compression.
* **Why we used it:**
  1. *Columnar vs Row-oriented:* Traditional CSV stores data row by row. If an algorithm only needs `total_spend` and `recency_days`, CSV still reads all 23 columns from disk. Parquet reads only the requested columns (Projection Pruning).
  2. *Drastic Storage Savings:* Snappy compression reduces file sizes by **70% to 85%** compared to uncompressed CSV.
  3. *Type Safety:* Preserves exact data schemas (e.g., timestamps, floats, integer arrays) without CSV parsing ambiguity.
* **How it works:**
  - After PySpark cleans and deduplicates records, it writes the processed datasets to `data/processed/*.parquet` and `data/versions/<version_id>/*.parquet`.
  - Both CSV and Parquet copies are maintained so users can view data in Excel or query high-speed Parquet via PySpark/Pandas.

---

## 2. Distributed Processing & Feature Engineering Layer

### Apache PySpark 3.5.1
* **What it is:** The Python API for Apache Spark, a lightning-fast distributed in-memory computing engine using Directed Acyclic Graphs (DAGs) and Catalyst Query Optimization.
* **Why we used it:**
  1. *In-Memory Computing:* PySpark executes data transformations in RAM, performing up to 100x faster than legacy Hadoop MapReduce which continually writes intermediate state to physical disk.
  2. *Avoiding Cartesian Product Explosion:* E-commerce datasets contain multiple tables at different granularities (transactions, web logs, social sentiment). A naive SQL join across 12,000 transactions, 120,000 web clicks, and 8,800 social posts produces over $10^7$ rows. PySpark aggregates each source independently to the customer level ($N = 1,200$) before performing an outer join.
  3. *Cross-Batch Primary-Key Deduplication:* When new batches arrive, PySpark uses `dropDuplicates(['transaction_id'])` and window ranking functions (`row_number().over(Window.partitionBy('customer_id').orderBy(desc('timestamp')))` to replace obsolete customer profiles with fresh incoming data.
* **How it works:**
  - PySpark spins up with `local[2]` (2 CPU cores, 2 GB RAM limit) to run smoothly on standard laptops.
  - It reads raw files from HDFS or local staging.
  - Executes cleaning: null imputation, timestamp parsing, regex URL cleaning, and out-of-range filtering.
  - Computes the **Unified 23-Column Customer Feature Matrix** (monetary spend, average order value, browsing duration, cart additions, positive/negative sentiment, recency lapse, and cancellation rates).

---

## 3. Machine Learning Suite

The project implements three distinct machine learning systems covering unsupervised learning, hybrid recommendation, and supervised classification.

### A. Customer Segmentation: K-Means Clustering + 2D PCA
* **What it is:** Unsupervised clustering algorithm that partitions $N$ customer vectors into $K$ distinct behavioral cohorts based on feature similarity.
* **Why we used it:**
  - E-commerce stores cannot treat all customers identically. Automated segmentation groups customers with shared habits (e.g. VIP spenders vs at-risk lapse shoppers) for hyper-targeted marketing.
* **How it works:**
  1. *Standardization:* All 22 numerical features are transformed using `StandardScaler` ($\mu = 0, \sigma = 1$) so large metrics (like \$5,000 spend) do not overpower small metrics (like sentiment from -1 to +1).
  2. *Elbow & Silhouette Optimization:* Evaluated $K \in [2, 8]$. $K=5$ achieved the highest silhouette score (**0.3533**), representing optimal cluster separation.
  3. *Principal Component Analysis (PCA):* Reduces the 22-dimensional space into 2 principal components ($PC1$ explains 40.85% variance, $PC2$ explains 16.11% variance, totaling **56.96%**), enabling 2D visual cluster boundaries on the dashboard.
  4. *Five Identified Personas:*
     - **High-Value VIP Spenders:** Highest average spend (\$4,634.37), top AOV (\$223.13), lowest cancellation (1.9%).
     - **Active Bargain Hunters:** Highest web clickstream (190 touchpoints), high cart activity (20.9 additions), moderate spend (\$1,399.53).
     - **Casual Occasional Shoppers:** Low frequency (2–5 purchases), modest spend (\$483.53), neutral sentiment.
     - **Social Brand Advocates:** Highest social engagement (17.9 interactions), strong positive sentiment (+0.82).
     - **At-Risk / Dissatisfied Customers:** Long recency lapse (281.6 days without purchase), highest cancellation rate (25.6%), negative sentiment (-0.65).

---

### B. Personalized Experience: Explainable Hybrid Recommender
* **What it is:** A multi-strategy recommendation engine combining Item-Item Collaborative Filtering, Market Basket Association Rules (Apriori), and Segment Affinity.
* **Why we used it:**
  - Pure collaborative filtering suffers from "cold-start" (new users or items have no history). Pure association rules only work when an item is already in the cart. A hybrid architecture ensures 100% catalog coverage and explainable recommendations.
* **How it works:**
  1. *Implicit Interaction Matrix:* Combines actions into an interest score:
     $$\text{Score} = 5.0 \times \text{Purchases} + 2.5 \times \text{Cart Adds} + 1.0 \times \text{Product Views} + 1.5 \times \text{Wishlist}$$
  2. *Cosine Similarity:* Measures product co-engagement across all customer profiles.
  3. *Association Rule Mining:* Evaluates rules using Support ($\ge 0.01$), Confidence ($\ge 0.15$), and Lift ($\ge 0.85x$).
  4. *Explainability Engine:* Every recommendation outputs a human-readable reason (e.g., *"Frequently bought together with Hydrating Facial Moisturizer Cream (Confidence: 22%, Lift: 1.12x)"*).

---

### C. Retention AI: Supervised Churn Prediction (Random Forest Classifier)
* **What it is:** A supervised ensemble classification model that predicts the exact probability that a customer will churn (stop buying) in the subsequent 90 days.
* **Why we used it:**
  - Retaining an existing customer is 5x cheaper than acquiring a new one. Identifying at-risk customers *before* they leave allows proactive discount offers and customer support intervention.
* **How it works:**
  1. *Observation vs Outcome Window (Point-in-Time Integrity):* Splits customer history into a 180-day observation window (for features) and a 90-day future outcome window (for binary churn label $y \in \{0, 1\}$). This eliminates data leakage.
  2. *Algorithm:* Random Forest Classifier (100 estimators, max depth 5).
  3. *Evaluation on 20% Unseen Test Set:*
     - **ROC-AUC:** `0.9365` (outstanding discrimination between churners and non-churners)
     - **Recall:** `90.32%` (identifies 9 out of 10 customers who are about to churn)
     - **F1 Score:** `0.732`
  4. *Top Predictive Features:* Days since last purchase (recency lapse), number of web sessions, product views, and negative social media sentiment.

---

## 4. Dual Processing Modes & Versioning Architecture

To accommodate both comprehensive enterprise batch processing and rapid live classroom demonstrations, the platform features **Dual Dataset Processing Modes**:

| Feature | Mode 1: Cumulative Analysis (Production) | Mode 2: New Batch Only (Fast Demo) |
| :--- | :--- | :--- |
| **Data Scope** | 1,200 Baseline + Historical Batches + New Batch | Only the newly uploaded batch records |
| **Typical Customer Count** | 1,200 to 1,500+ Customers | 50 to 200 Customers |
| **Pipeline Duration** | 2 to 3 minutes (full PySpark merge & ML retraining) | 8 to 15 seconds (isolated lightweight demo) |
| **Lineage & Storage** | Saves candidate version `v_<batch_id>`, promotes to prod | Saves isolated version `v_batch_only_<batch_id>` |
| **Academic Safeguards** | Retrains full K-Means, Recommender, and Churn models | If time span < 270 days, safely flags churn limitation |
| **1-Click Rollback** | Restores original 1,200 customer baseline instantly | Switching mode instantly switches back to baseline |

---

## 5. Web Application Layer

### A. Backend: Python Flask REST API
* **Why we used it:** Flask is lightweight, highly customizable, and natively integrates with Python's scientific ecosystem (NumPy, Pandas, Scikit-Learn, PySpark).
* **Role:**
  - Exposes 20+ REST endpoints (`/api/overview/*`, `/api/segmentation/*`, `/api/recommendations/*`, `/api/churn/*`, `/api/ingestion/*`).
  - Holds the in-memory singleton `DataService` for microsecond dashboard responses.
  - Handles multi-part file uploads, schema discovery, batch job execution, and rollback.

### B. Frontend: React 18 + Vite + Chart.js + Lucide Icons
* **Why we used it:**
  - *React 18 & Vite:* Instant Hot Module Replacement (HMR), component-driven UI, sub-second build times.
  - *Chart.js & React-Chartjs-2:* Renders smooth, interactive scatter plots (PCA clusters), bar charts (monthly trends), and doughnut charts (segment breakdown).
  - *Lucide Icons:* Modern icon set for clean enterprise analytics aesthetics.
  - *Server-Side Pagination:* Customer 360 table paginates 15 rows at a time, allowing the browser to remain responsive even if millions of rows exist in the database.

---

# SECTION 2: TOP 25+ DEFENSE & VIVA VOCE QUESTIONS & ANSWERS

---

### Category 1: Project Scope & Big Data Concepts

#### Q1: What is the core objective of this project?
**Answer:** The objective is to build an end-to-end Big Data analytics and machine learning platform that ingests raw, multi-source e-commerce activity (transactions, web clickstreams, social sentiment), stores them in a Hadoop HDFS data lake, processes them using Apache PySpark to create a unified 23-column customer feature matrix, and powers three machine learning models for customer segmentation, personalized product recommendations, and churn risk prediction.

#### Q2: What are the 3 'V's of Big Data in this project?
**Answer:**
1. **Volume:** Aggregates thousands of transactions, hundreds of thousands of clickstream events, and social reviews, scaling smoothly up to millions of rows.
2. **Velocity:** Batch ingestion handles incremental daily/weekly batch updates without re-architecting the system.
3. **Variety:** Ingests structured (CSV, TSV, XLSX transactions), semi-structured (JSON, JSONL product catalogs and web events), and unstructured/text data (social media sentiment logs).

#### Q3: Why didn't you use traditional relational SQL databases (like MySQL) for everything?
**Answer:** Relational databases struggle with unstructured clickstreams and large-scale joins across millions of event logs. Rigid schemas reject unmapped fields, and vertical scaling becomes cost-prohibitive. Hadoop HDFS and PySpark provide schema-on-read flexibility, horizontal scalability across distributed nodes, and in-memory parallel computation.

---

### Category 2: Hadoop HDFS & Storage Layer

#### Q4: What is HDFS, and why is it used instead of storing files in a standard local directory?
**Answer:** Hadoop Distributed File System (HDFS) is a distributed file system designed to run on commodity hardware. It provides:
1. **High Fault Tolerance:** Files are broken into blocks (typically 128 MB) and replicated across multiple DataNodes. If a server hardware fails, data remains intact.
2. **High Throughput:** Designed for streaming access to large datasets rather than random low-latency reads.
3. **Data Lake Architecture:** In this project, raw files uploaded by users are saved directly into `/customer-analytics/raw/uploads/<batch_id>/`, preserving raw bytes for compliance and auditing.

#### Q5: What is the NameNode and DataNode in Hadoop?
**Answer:**
- **NameNode (Master Node):** Manages the file system namespace, maintains directory trees, and records metadata (which blocks belong to which file and which DataNodes host them).
- **DataNode (Worker Node):** Stores the actual data blocks on local disk and periodically sends heartbeats and block reports to the NameNode.
- In our project, these run as daemons inside WSL2 Debian on port 9000.

#### Q6: What happens if Hadoop HDFS is offline when a user uploads data?
**Answer:** The system features a non-blocking graceful fallback (`HDFSManager`). If HDFS socket connections fail, the batch is safely staged in the local filesystem (`data/uploads/<batch_id>/`) with an `INGESTION_FAILED` or `LOCAL_FALLBACK` status. The user can view the issue on the UI and click **"Retry HDFS Ingestion"** without re-uploading the file.

#### Q7: Why did you store processed data in Parquet format in addition to CSV?
**Answer:** Parquet is a columnar file format that uses dictionary encoding and Snappy compression. It reduces disk footprint by 70–85%, enables projection pruning (reading only needed columns), and predicate pushdown (filtering rows at the storage layer before reading into memory).

---

### Category 3: Apache PySpark & Data Processing Pipeline

#### Q8: Why did you choose Apache Spark (PySpark) over traditional Hadoop MapReduce?
**Answer:**
1. **Speed:** Spark uses in-memory Resilient Distributed Datasets (RDDs) and Directed Acyclic Graph (DAG) execution, running up to 100x faster than MapReduce, which writes intermediate results to disk after every Map and Reduce phase.
2. **API Usability:** PySpark provides high-level DataFrames and SQL expressions, drastically simplifying complex aggregations.
3. **Catalyst Optimizer:** Automatically optimizes execution plans, reordering operations and pruning unused columns.

#### Q9: How did you configure Spark to run efficiently on an 8 GB / 16 GB laptop?
**Answer:**
1. `master("local[2]")`: Limits Spark to 2 CPU threads, leaving remaining cores for the OS and browser.
2. `spark.driver.memory = "2g"` and `spark.executor.memory = "1g"`: Prevents JVM memory crashes.
3. `spark.sql.shuffle.partitions = 4`: Default Spark shuffle partitions are 200, which creates massive task overhead for medium datasets. Capping it at 4 reduces task scheduling latency by 80%.

#### Q10: Why did you aggregate transactions, web logs, and social media separately before joining them?
**Answer:** Joining raw transaction rows (12k) directly to raw web touchpoints (120k) and social media (8.8k) by `customer_id` produces a **Cartesian explosion** exceeding $10^7$ rows, exhausting memory and duplicating metrics (e.g., total spend would be multiplied hundreds of times). By aggregating each source to 1 row per customer ($N=1,200$) first, the join remains a clean 1:1 merge.

#### Q11: How does cross-batch primary key deduplication work?
**Answer:** When an incoming batch contains transactions or customer updates that already exist in historical storage, PySpark performs deduplication:
- Transaction level: `dropDuplicates(['transaction_id'])` retains the unique transaction.
- Customer level: Window ranking (`row_number().over(Window.partitionBy('customer_id').orderBy(col('timestamp').desc()))`) retains the most recent record, updating recency, lifetime spend, and sentiment accurately.

---

### Category 4: Machine Learning Suite

#### Q12: Why was K-Means chosen for customer segmentation, and how did you determine $K=5$?
**Answer:** K-Means is fast, computationally efficient ($O(N \cdot K \cdot I)$), and segments continuous multivariate customer vectors cleanly.
We determined $K=5$ using two techniques:
1. **Elbow Method:** Plotting Within-Cluster Sum of Squares (Inertia) against $K \in [2, 8]$ revealed an elbow bend at $K=5$ (Inertia = 9,784.31).
2. **Silhouette Analysis:** Measures how well-separated clusters are (-1 to +1). $K=5$ achieved the global maximum Silhouette score of **0.3533** (compared to 0.33 for $K=2$ and 0.31 for $K=3$).

#### Q13: Why is feature standardization (`StandardScaler`) essential before K-Means?
**Answer:** K-Means uses Euclidean distance ($d = \sqrt{\sum (x_i - y_i)^2}$). If `total_spend` is measured in thousands of dollars (\$0 to \$6,000) while `avg_sentiment_score` ranges between $-1.0$ and $+1.0$, the spend feature will dominate the distance calculation by a factor of 1,000x. `StandardScaler` centers all features to mean 0 and variance 1, giving all 22 dimensions equal weighting.

#### Q14: How does Principal Component Analysis (PCA) work in this project?
**Answer:** PCA is a linear dimensionality reduction technique that finds orthogonal eigenvectors with maximal variance in the covariance matrix. We reduce the 22 features down to 2 principal components:
- **PC1 (40.85% variance):** Primarily represents spend magnitude and transaction frequency.
- **PC2 (16.11% variance):** Represents engagement sentiment and recency.
Together, they retain **56.96% of total dataset variance**, allowing 2D visualization of high-dimensional clusters on the dashboard.

#### Q15: How does your hybrid recommendation engine operate?
**Answer:** It combines four complementary strategies:
1. **Implicit Interaction Matrix:** Translates user behavior into weighted interest: Purchase (5.0), Cart Add (2.5), Wishlist (1.5), Product View (1.0).
2. **Item-Item Collaborative Filtering:** Computes cosine similarity between product engagement vectors.
3. **Association Rule Mining (Apriori):** Discovers cross-sell patterns (e.g., item A $\rightarrow$ item B) evaluated by Support, Confidence, and Lift.
4. **Segment Fallback (Cold-Start):** For brand new customers with no history, recommends top-selling items from their demographic cluster.

#### Q16: What is the meaning of Support, Confidence, and Lift in Association Rules?
**Answer:**
- **Support:** Proportion of transactions containing both Item A and Item B: $P(A \cap B)$.
- **Confidence:** Probability that Item B is purchased given that Item A was purchased: $P(B|A) = \frac{P(A \cap B)}{P(A)}$.
- **Lift:** Ratio of observed joint purchase to expected purchase if they were statistically independent: $\frac{P(A \cap B)}{P(A) \times P(B)}$. A lift $> 1.0$ confirms that buying Item A significantly increases the probability of buying Item B.

#### Q17: How did you formulate Churn Prediction without data leakage?
**Answer:** We implemented a **Point-in-Time Temporal Split**:
- Split customer history into a **180-day Observation Window** (used to calculate features like transactions, clicks, and sentiment).
- Followed by a **90-day Outcome Window** (used strictly to define the ground-truth label: $y=1$ if no purchases occurred, $y=0$ if retained).
Features are computed strictly from the observation window, preventing target leakage.

#### Q18: What machine learning algorithm was used for Churn Prediction, and what were the results?
**Answer:** We trained a **Random Forest Classifier** (100 trees, max depth 5) evaluated on a 20% holdout test set:
- **ROC-AUC:** `0.9365` (distinguishes churners from retained customers with high confidence).
- **Recall:** `90.32%` (identifies 9 out of 10 real churners).
- **F1 Score:** `0.732`.
- **Top Features:** Days since last purchase (recency lapse), number of web sessions, and negative social sentiment.

---

### Category 5: Multi-Format Ingestion & Field Mapping

#### Q19: What formats does your ingestion pipeline support, and how does it detect them?
**Answer:** The pipeline supports `.csv`, `.tsv`, `.json`, `.jsonl`, `.txt`, `.log`, and `.xlsx`. The `SchemaDiscoveryEngine`:
1. Inspects file extension and magic bytes.
2. Infers structure (delimiters like comma, tab, pipe, or JSON objects).
3. Detects column types (integer, float, timestamp, string).
4. Automatically classifies the source (`transactions`, `web_activity`, `social_media`) based on keyword heuristics.

#### Q20: What is Intelligent Canonical Field Mapping?
**Answer:** Incoming files from third-party systems rarely match standard database column names (e.g., `user_id` instead of `customer_id`, `amount` instead of `price`, `timestamp` instead of `transaction_date`).
Our Schema Discovery Engine suggests canonical mappings with confidence scores. Users can adjust mappings via a slide-out drawer on the UI before PySpark runs, eliminating schema mismatch crashes.

---

### Category 6: Dual Processing Modes & Rollback

#### Q21: What is the difference between "Cumulative Analysis" and "New Batch Only" modes?
**Answer:**
- **Mode 1 (Cumulative Analysis):** Enterprise production mode. Merges historical baseline (1,200) with incoming batches, executes cross-batch deduplication, retrains all 3 ML models, and saves candidate versions. Takes ~2–3 minutes.
- **Mode 2 (New Batch Only):** Lightweight classroom demonstration mode. Isolates the newly uploaded batch (e.g., 100 rows), processes features in 8–15 seconds, and switches the live dashboard to visualize only that batch without touching production baseline files.

#### Q22: What happens when you click "Rollback to Baseline"?
**Answer:** Rollback restores the system to the original academic baseline:
1. Copies clean baseline datasets from `data/_baseline_backup/` to `data/processed/`.
2. Copies original baseline ML models from `ml/models/_baseline_backup/` to `ml/models/`.
3. Resets `data/current_version.json` to `"active_version": "baseline"`.
4. Resets the in-memory singleton `DataService` (`active_mode = "cumulative"`).
5. Dispatches `smart-dataset-mode-changed` to the frontend, updating all 7 modules and the top-right navbar pill back to `CUMULATIVE ANALYSIS — baseline`.

---

### Category 7: Full-Stack Architecture & Production Readiness

#### Q23: How do the React frontend and Flask backend communicate?
**Answer:** The frontend communicates with Flask via asynchronous HTTP REST calls using **Axios** (`frontend/src/services/api.js`). In development, Vite's dev server proxies `/api/*` to `http://127.0.0.1:5000`. In production, **Flask-CORS** enables secure cross-origin resource sharing.

#### Q24: How does the dashboard achieve microsecond response times despite running on Big Data?
**Answer:** The frontend does not run heavy PySpark queries on page load. Instead, the architecture separates **batch compute** from **serving**:
- PySpark and ML training run asynchronously during batch ingestion, writing pre-aggregated Parquet/JSON artifacts.
- Flask loads these artifacts into an in-memory singleton (`DataService`).
- REST endpoints serve pre-computed KPIs, scatter points, and paginated customer profiles instantly in < 20 milliseconds.

#### Q25: If a customer clones this repository on a new machine, how do they run it?
**Answer:** We created automated single-command setup and launch scripts:
- **Windows:** Run `setup.bat` (creates virtualenv, installs pip packages, runs `npm install`), then `start.bat` (launches Flask backend, Vite frontend, and checks HDFS).
- **macOS / Linux:** Run `chmod +x setup.sh start.sh && ./setup.sh && ./start.sh`.
- The system includes a default `.env.example` with zero-configuration local fallbacks.
