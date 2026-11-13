# Academic Viva Voce & Defense Q&A Guide

## Project: Smart Customer Analysis and Personalized Experience Using Big Data

This document contains essential theoretical, architectural, and implementation questions and model answers commonly asked during academic project evaluations, external viva examinations, and project defense panels.

---

### 1. Big Data & Distributed Processing Architecture

#### Q1: Why did you choose Apache Spark (PySpark) instead of traditional Hadoop MapReduce?
**Answer:**
- **In-Memory Computation**: Traditional Hadoop MapReduce writes intermediate results to physical disk (HDFS) after every map and reduce phase, creating significant disk I/O bottlenecks. In contrast, Apache Spark performs resilient in-memory distributed computations via Directed Acyclic Graphs (DAG), executing batch transformations up to 100x faster.
- **Rich API & DataFrames**: PySpark provides the high-level `DataFrame` and Catalyst Optimizer API, which performs query optimization, projection pruning, and predicate pushdown automatically.
- **Unified Pipeline**: PySpark allows ingestion, cleaning, aggregation, and machine learning feature extraction in a single cohesive Python ecosystem.

#### Q2: How did you configure Apache Spark to run smoothly on standard computers with 8 GB RAM?
**Answer:**
We tailored Spark's runtime parameters specifically for constrained local environments:
1. **Master Core Allocation**: Configured `master("local[2]")` to restrict Spark to 2 worker threads, leaving remaining CPU cores free for the operating system, Flask API, and browser.
2. **Memory Throttling**: Set `spark.driver.memory = "2g"` and `spark.executor.memory = "1g"` to cap JVM memory usage below 3 GB total.
3. **Shuffle Partition Tuning**: Default Spark shuffle partitions are set to 200, which creates massive overhead for small-to-medium datasets. We tuned `spark.sql.shuffle.partitions = 4`, reducing task scheduling latency and memory fragmentation.
4. **UI Suppression**: Set `spark.ui.enabled = false` to eliminate memory consumed by Spark's background web server daemons.

#### Q3: What is the purpose of HDFS, and how does your project handle HDFS storage?
**Answer:**
- **Enterprise Role**: Hadoop Distributed File System (HDFS) provides fault-tolerant, horizontally scalable block storage across commodity server clusters with configurable replication factors (default: 3).
- **Dual-Mode Architecture in this Project**:
  - *Mode A (Genuine HDFS)*: If an Apache Hadoop cluster is running (`http://localhost:9870` / `hdfs://localhost:9000`), the `HDFSManager` in `big_data/ingestion/hdfs_client.py` can upload datasets and allow PySpark to read from genuine `hdfs://` URIs.
  - *Mode B (Local Staged Store Fallback)*: When running on student laptops without running Hadoop daemons (which require 4+ GB of background RAM for NameNode, DataNode, and ResourceManager), the pipeline stores verified datasets in partitioned **Parquet (Snappy-compressed)** format inside `data/processed/`.
  - We explicitly distinguish local filesystem storage from genuine HDFS to maintain academic transparency.

#### Q4: Why did you avoid directly joining the raw event tables together?
**Answer:**
Joining raw `transactions` (12,214 rows), `web_activity` (120,944 rows), and `social_media` (8,828 rows) directly on `customer_id` without prior aggregation would cause a **cartesian product explosion** (over $10^7$ joined records). This leads to:
1. Massive memory exhaustion and Out-Of-Memory (OOM) errors.
2. Metric duplication (e.g. summing transaction spend on repeated web activity rows would artificially multiply total spend thousands of times).
Instead, we aggregated each data source independently to the customer level ($N = 1,200$) before performing an outer join.

---

### 2. Machine Learning & Customer Segmentation

#### Q5: How did you select the optimal number of clusters ($K=5$) for K-Means?
**Answer:**
We evaluated cluster counts across $K \in [2, 8]$ using two complementary validation techniques:
1. **The Elbow Method (Within-Cluster Sum of Squares / Inertia)**: Identified the curve's inflection point where the rate of inertia reduction significantly levels off ($K=5$, Inertia = 9,784.31).
2. **Silhouette Analysis**: Silhouette coefficient measures how similar an object is to its own cluster compared to other clusters. $K=5$ achieved the global maximum Silhouette score of **0.3533** (compared to 0.3314 for $K=2$, 0.3194 for $K=3$, and 0.3365 for $K=4$).

#### Q6: Why did you standardize the features using `StandardScaler` before running K-Means?
**Answer:**
K-Means is a distance-based algorithm relying on **Euclidean distance**:
$$d(x, y) = \sqrt{\sum_{i=1}^d (x_i - y_i)^2}$$
Features with large raw numerical scales (e.g., `total_spend` spanning \$0 to \$6,000) would completely dominate features with small numerical ranges (e.g., `avg_sentiment_score` ranging between $-1.0$ and $+1.0$, or `cancellation_rate` from $0.0$ to $0.3$). `StandardScaler` converts each feature to zero mean ($\mu = 0$) and unit variance ($\sigma = 1$), ensuring all 23 behavioral dimensions contribute equally.

#### Q7: What are the 5 customer personas identified by the model?
**Answer:**
1. **High-Value VIP Tech Spenders (17.0%)**: Top spenders (mean \$4,634.37), highest average order value (\$223.13), lowest cancellation rate (1.9%), and positive sentiment (+0.75).
2. **Active Bargain Hunters (25.5%)**: Highest browsing dwell time and clickstream interactions (mean 190.0 touchpoints, 20.9 cart additions), moderate spend (\$1,399.53).
3. **Casual Occasional Shoppers (29.0%)**: Low transaction frequency (mean 2-5 purchases), modest spend (\$483.53), neutral sentiment (+0.35).
4. **Social Brand Advocates (14.5%)**: Highest social media engagement (mean 17.9 posts), highest positive sentiment (+0.82), frequent brand mentions.
5. **At-Risk / Dissatisfied Customers (14.0%)**: Longest recency lapse (mean 281.6 days without purchase), highest cancellation rate (25.6%), negative sentiment (-0.65).

#### Q8: How did you visualize high-dimensional clusters in a 2D scatter plot?
**Answer:**
We applied **Principal Component Analysis (PCA)** to reduce the 23-dimensional feature space to 2 orthogonal principal components:
- **PC1**: Captures $40.85\%$ of the total variance (primarily reflecting overall spending and interaction volume).
- **PC2**: Captures $16.11\%$ of the total variance (primarily reflecting sentiment polarity vs recency/churn risk).
- Combined, the 2 components preserve **$56.96\%$ of total dataset variance**, allowing meaningful 2D visual cluster boundaries on the dashboard.

---

### 3. Recommendation Engine & Explainability

#### Q9: How does your recommendation engine work?
**Answer:**
It is a **hybrid multi-strategy engine** combining:
1. **Implicit Feedback Interaction Matrix**: Quantifies interest by assigning weighted scores to customer actions:
   $$\text{Score} = 5.0 \times \text{Purchase Quantity} + 2.5 \times \text{Cart Addition} + 1.0 \times \text{Product View} + 1.5 \times \text{Wishlist}$$
2. **User-Based Collaborative Filtering**: Uses Cosine Similarity to find the top 15 most similar peer customers and computes peer-weighted product preference scores.
3. **Market Basket Association Rule Mining**: Mines 541 co-occurrence rules using Support, Confidence, and Lift metrics to detect cross-sell affinities.
4. **Segment Behavioral Affinity**: Incorporates top-performing items from the customer's cluster for cold-start mitigation.

#### Q10: What makes your recommendations "explainable"?
**Answer:**
Traditional recommendation systems act as "black boxes" outputting raw item IDs. Our engine attaches an explicit reason type (`association_rule`, `collaborative_peer`, `browsing_intent`, or `cluster_affinity`) and a human-readable explanation to each recommendation, for example:
- *"Frequently bought together with 'Hydrating Facial Moisturizer Cream' (Association confidence: 22%, Lift: 0.96x)."*
- *"Highly rated by peer customers with similar purchase patterns in your 'High-Value VIP' profile."*
- *"Picked based on your recent browsing interactions and active interest in Electronics."*

---

### 4. Full-Stack Web Architecture

#### Q11: How does the React dashboard communicate with the backend?
**Answer:**
- The React application utilizes **Axios** encapsulated in `frontend/src/services/api.js`.
- During development, Vite's dev server proxies requests from `/api/*` to `http://127.0.0.1:5000` to avoid CORS issues.
- In production, **Flask-CORS** is configured on the Flask app to permit cross-origin HTTP requests.
- All displayed metrics, charts, and customer tables originate from actual PySpark batch outputs and Scikit-Learn models, with zero hardcoded mock values.
