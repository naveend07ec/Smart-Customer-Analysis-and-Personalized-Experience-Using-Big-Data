# SMART: Smart Customer Analysis & Personalized Experience Using Big Data

An end-to-end Big Data, Machine Learning, and Real-Time Predictive Analytics platform designed for enterprise-grade customer behavioral analytics, explainable recommendations, and retention intelligence. The platform ingests multi-source, multi-format customer datasets (sales transactions, clickstream interactions, and social sentiment feedback), stores untouched raw bytes in **Apache Hadoop HDFS**, executes distributed cumulative batch transformations via **Apache Spark (PySpark)**, engineers a unified 23-column customer behavioral feature matrix, trains unsupervised and supervised ML models, and delivers insights through an executive React + Vite dashboard.

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/naveend07ec/Smart-Customer-Analysis-and-Personalized-Experience-Using-Big-Data)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.5.1-E25A1C?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Hadoop HDFS](https://img.shields.io/badge/Hadoop_HDFS-3.3.6-66CCFF?logo=apache&logoColor=black)](https://hadoop.apache.org/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Scikit--Learn](https://img.shields.io/badge/Scikit--Learn-1.4-F7931E?logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)

---

## Table of Contents
1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Multi-Source Data Foundation](#3-multi-source-data-foundation)
4. [Hadoop HDFS Distributed Storage Layer](#4-hadoop-hdfs-distributed-storage-layer)
5. [Multi-Format Ingestion & Dynamic Schema Discovery](#5-multi-format-ingestion--dynamic-schema-discovery)
6. [PySpark Cumulative Feature Engineering (23-Feature Matrix)](#6-pyspark-cumulative-feature-engineering-23-feature-matrix)
7. [Machine Learning Engines & Evaluation Benchmarks](#7-machine-learning-engines--evaluation-benchmarks)
   - [Unsupervised K-Means Customer Segmentation (K=5)](#71-unsupervised-k-means-customer-segmentation-k5)
   - [Explainable Hybrid Product Recommendations](#72-explainable-hybrid-product-recommendations)
   - [Supervised Customer Churn Prediction & Retention AI](#73-supervised-customer-churn-prediction--retention-ai)
8. [Cumulative Old + New Data Ingestion & Live Promotion](#8-cumulative-old--new-data-ingestion--live-promotion)
9. [Web Application & Dashboard Navigation](#9-web-application--dashboard-navigation)
10. [Step-by-Step Setup & Reproduction Guide](#10-step-by-step-setup--reproduction-guide)
11. [Current Live Platform Metrics](#11-current-live-platform-metrics)

---

## 1. Executive Summary & Problem Statement

Modern omnichannel retail and e-commerce enterprises face three fundamental challenges:
1. **Data Silos & Volume**: Customer touchpoints are fragmented across disparate systems—transactional SQL databases, high-velocity web clickstream logs, and unstructured social feedback.
2. **Key Collisions & Incremental Updates**: Ingesting incremental batches often leads to primary key collisions or duplicate data loss when external systems reuse sequential identifiers.
3. **Actionability Gap**: Raw data rarely translates into proactive business decisions without unified customer profiles, customer segmentation, transparent product recommendations, and early churn risk intervention.

### Solution Overview
**SMART** solves these challenges by implementing an enterprise Big Data Lakehouse and ML pipeline:
- **Raw Multi-Format Ingestion**: Ingests files formatted as CSV, TSV, JSON, JSONL, TXT, or LOG into Hadoop HDFS.
- **Enterprise Content-Aware Deduplication**: Differentiates between true re-transmissions and distinct transactions sharing sequential keys, preventing accidental data loss.
- **Cumulative PySpark Processing**: Merges historical baselines with incoming batches into a single 23-column customer matrix using distributed map-reduce joins.
- **Explainable Machine Learning**: Powers K-Means customer segmentation ($K=5$), collaborative filtering and market basket association rules (Lift up to 2.1x), and Random Forest churn classification (ROC-AUC: 0.9365, PR-AUC: 0.8660).
- **Zero-Downtime Hot Promotion**: Evaluates and applies incoming datasets to the live production dashboard in one click, with instant single-click rollback capability.

---

## 2. End-to-End System Architecture

```
                                  MULTI-SOURCE INGESTION LAYER
           ┌────────────────────────────────────┼────────────────────────────────────┐
           ▼                                    ▼                                    ▼
  Sales Transactions                   Web Activity Clickstream              Social Media Sentiment
 (CSV, TSV, JSON, LOG)                  (CSV, JSONL, TXT, LOG)               (CSV, TSV, JSON, LOG)
           │                                    │                                    │
           └────────────────────────────────────┼────────────────────────────────────┘
                                                ▼
                         Dynamic Schema Discovery & Format Sniffing
                         - Delimiter detection & Confidence scoring
                         - Field mapping to canonical target schemas
                                                ▼
                          HADOOP DISTRIBUTED FILE SYSTEM (HDFS)
                         - /customer-analytics/raw/baseline/
                         - /customer-analytics/raw/uploads/<batch_id>/
                         - /customer-analytics/processed/versions/<version_id>/
                                                ▼
                         APACHE SPARK (PYSPARK 3.5.1) BATCH ENGINE
                         ┌─────────────────────────────────────────────────────────┐
                         │ 1. Content-Aware Deduplication & Disambiguation         │
                         │ 2. Timestamp Standardization & Missing Imputation       │
                         │ 3. Cumulative Historical Union (Baseline + Prior + New) │
                         │ 4. Multi-Source Outer Join on customer_id               │
                         └─────────────────────────────────────────────────────────┘
                                                ▼
                            UNIFIED 23-FEATURE CUSTOMER MATRIX
                                                ▼
           ┌────────────────────────────────────┼────────────────────────────────────┐
           ▼                                    ▼                                    ▼
  K-Means Clustering (K=5)             Hybrid Recommender Engine             Supervised Churn AI
  - Silhouette: 0.4287                 - Collaborative Filtering (ALS)       - Random Forest Classifier
  - Davies-Bouldin: 1.1894             - Association Rules (Apriori Lift)    - ROC-AUC: 0.9365, Recall: 90.3%
  - 2D PCA Dimensionality              - Recommender Hit Rate: 76.0%         - 90-Day Inactivity Window
           │                                    │                                    │
           └────────────────────────────────────┼────────────────────────────────────┘
                                                ▼
                               FLASK REST API SERVICE (:5000)
                               - Dynamic Ingestion & Processing Routes
                               - Cached DataService with Version Registry
                                                ▼
                                REACT 18 + VITE DASHBOARD (:3000)
    [Executive Dashboard]  [Customer Analytics]  [Segmentation]  [Customer 360]  [Recommendations]  [Retention AI]  [Data Pipeline]
```

---

## 3. Multi-Source Data Foundation

The platform integrates three distinct behavioral channels into a cohesive customer profile:

| Dataset | Granularity | Key Identifiers | Core Attributes | Cleaning & Transformation Rules |
| :--- | :--- | :--- | :--- | :--- |
| **Sales Transactions** | Per Purchase Order | `transaction_id`, `customer_id` | `transaction_date`, `product_id`, `product_category`, `quantity`, `unit_price`, `discount_percent`, `total_amount`, `payment_method`, `order_status` | Missing payment methods imputed as `'Unknown'`; quantity, unit price, and total amount strictly validated ($> 0$); invalid order statuses filtered. |
| **Web Activity Clickstream** | Per Page Touchpoint | `activity_id`, `customer_id`, `session_id` | `timestamp`, `page_url`, `action_type`, `duration_seconds`, `product_id`, `device_type`, `traffic_source` | Non-product page nulls (e.g., `/home`, `/cart`, `/checkout`) preserved; negative dwell times removed; timestamps standardized. |
| **Social Media Feedback** | Per Engagement Interaction | `interaction_id`, `customer_id` | `timestamp`, `platform`, `interaction_type`, `sentiment_score`, `sentiment`, `engagement_score`, `review_text`, `associated_category` | Sentiment scores validated in range $[-1.0, 1.0]$; engagement scores validated in $[0, 100]$; platforms standardized (Twitter, Instagram, Facebook, Reddit, YouTube). |

---

## 4. Hadoop HDFS Distributed Storage Layer

Untouched raw datasets are preserved in Apache Hadoop HDFS to establish immutable data lineage and auditability:

```
hdfs://<HADOOP_HOST>:9000/customer-analytics/
├── raw/
│   ├── baseline/
│   │   ├── transactions.csv
│   │   ├── web_activity.csv
│   │   └── social_media.csv
│   └── uploads/
│       └── batch_YYYYMMDD_HHMMSS_<hash>/
│           ├── <staged_transactions>
│           ├── <staged_web_activity>
│           └── <staged_social_media>
└── processed/
    └── versions/
        └── v_batch_YYYYMMDD_HHMMSS_<hash>/
            ├── cleaned_transactions.parquet
            ├── cleaned_web_activity.parquet
            ├── cleaned_social_media.parquet
            └── unified_customer_features.parquet
```

* **Cluster Resilience & Fault Tolerance**: When the WSL HDFS cluster is active, datasets are read directly from `hdfs://`; if the cluster is offline, the pipeline falls back to local staging storage without disrupting operations.

---

## 5. Multi-Format Ingestion & Dynamic Schema Discovery

The ingestion engine accepts 6 raw file formats: `.csv`, `.tsv`, `.json`, `.jsonl`, `.txt`, and `.log`.

### Dynamic Schema Discovery Pipeline
1. **Format & Delimiter Sniffing**: Inspects the first 2,048 bytes of uploaded files to detect JSON structures or determine delimiters (`,`, `\t`, `;`, `|`).
2. **Column Heuristic Scoring**: Calculates confidence scores based on header signatures and data patterns to classify incoming files as `transactions`, `web_activity`, or `social_media`.
3. **Automated Canonical Mapping**: Matches detected columns to the canonical schema (e.g., mapping `txn_id` $\rightarrow$ `transaction_id`, `user` $\rightarrow$ `customer_id`, `amount` $\rightarrow$ `total_amount`).
4. **Enterprise Content-Aware Deduplication**:
   When new data arrives, external systems often generate sequential IDs (`TXN_0001`, `TXN_012215`, `SOC_008829`) that collide with existing batch records. Rather than discarding distinct rows, PySpark performs content-aware deduplication:
   - **Transactions**: Deduplicated on `["customer_id", "transaction_date", "product_id", "total_amount"]`.
   - **Key Disambiguation**: Colliding transaction IDs representing distinct events receive a deterministic suffix (`TXN_012215_b2`), guaranteeing **zero transaction loss**.
   - **Customer Repeat vs. New Separation**: If `CUST_0001` has new orders, they are added to `CUST_0001`'s lifetime metrics without inflating the customer count. Incoming IDs above the historical range (`CUST_1301` to `CUST_1500`) are dynamically counted as **New Unique Customers**.

---

## 6. PySpark Cumulative Feature Engineering (23-Feature Matrix)

PySpark aggregates cleaned transaction, clickstream, and social media data into a customer-level 23-column feature matrix via full outer joins:

$$\text{UnifiedCustomerMatrix} = \text{TxFeatures} \bowtie_{\text{customer\_id}} \text{WebFeatures} \bowtie_{\text{customer\_id}} \text{SocFeatures}$$

### The 23 Canonical Behavioral Features

| # | Feature Name | Domain | PySpark Aggregation Logic | Business Significance |
| :---: | :--- | :--- | :--- | :--- |
| **1** | `customer_id` | Identity | Primary Entity Key (`CUST_XXXX`) | Unique customer identifier. |
| **2** | `total_spend` | Monetary | `sum(total_amount)` for Completed orders | Total customer gross revenue. |
| **3** | `total_transactions` | Frequency | `count(transaction_id)` | Total transaction volume. |
| **4** | `avg_order_value` | Efficiency | `total_spend / completed_orders` | Average basket size at checkout. |
| **5** | `total_quantity` | Volume | `sum(quantity)` | Total physical units purchased. |
| **6** | `recency_days` | Recency | `datediff(current_date, max(transaction_date))` | Days since customer's last order. |
| **7** | `cancelled_orders_count`| Risk | `count()` where `order_status = 'Cancelled'` | Customer order friction count. |
| **8** | `cancellation_rate` | Risk | `cancelled_orders / total_transactions` | Ratio of cancelled orders to total. |
| **9** | `total_web_activities` | Clickstream | `count(activity_id)` | Total web touchpoints recorded. |
| **10** | `total_sessions` | Engagement | `count(distinct session_id)` | Number of separate browsing sessions. |
| **11** | `avg_duration_seconds` | Engagement | `avg(duration_seconds)` | Average dwell time per page view. |
| **12** | `product_views_count` | Intent | `count()` where `action_type = 'product_view'` | Top-of-funnel browsing interest. |
| **13** | `cart_additions_count`| Intent | `count()` where `action_type = 'add_to_cart'` | High-intent purchasing interest. |
| **14** | `wishlist_count` | Affinity | `count()` where `action_type = 'add_to_wishlist'`| Long-term product interest. |
| **15** | `checkout_starts_count`| Conversion | `count()` where `action_type = 'initiate_checkout'` | Bottom-of-funnel conversion attempts. |
| **16** | `cart_to_checkout_ratio`| Efficiency | `checkout_starts / cart_additions` | Checkout conversion velocity. |
| **17** | `total_social_interactions`| Social | `count(interaction_id)` | Overall brand engagement count. |
| **18** | `avg_engagement_score` | Social | `avg(engagement_score)` | Customer influence / virality score. |
| **19** | `avg_sentiment_score` | Sentiment | `avg(sentiment_score)` $[-1.0, +1.0]$ | Net brand sentiment polarity. |
| **20** | `positive_interactions_count`| Sentiment | `count()` where `sentiment = 'Positive'` | Positive community touchpoints. |
| **21** | `neutral_interactions_count` | Sentiment | `count()` where `sentiment = 'Neutral'` | Inquiries and neutral feedback. |
| **22** | `negative_interactions_count`| Sentiment | `count()` where `sentiment = 'Negative'` | Support escalations and complaints. |
| **23** | `unique_platforms_count` | Omni-channel | `count(distinct platform)` | Omnichannel breadth (up to 5). |

---

## 7. Machine Learning Engines & Evaluation Benchmarks

### 7.1. Unsupervised K-Means Customer Segmentation ($K=5$)
* **Preprocessing**: 23 features are standardized via `StandardScaler` ($\mu = 0, \sigma = 1$).
* **Optimal K Determination**: Elbow method evaluated across $K \in [2, 10]$ based on within-cluster sum-of-squares (Inertia) and Silhouette coefficients.
* **Evaluation Metrics**:
  - **Silhouette Coefficient**: **0.4287** (Indicates cohesive, well-separated clusters)
  - **Davies-Bouldin Index**: **1.1894** (Lower values denote compact clusters)
  - **Calinski-Harabasz Score**: **175.7** (High dispersion ratio between clusters)
* **2D PCA Projection**: Principal Component 1 captures **40.85%** variance; Principal Component 2 captures **16.11%** variance (Cumulative explained variance: **56.96%**).

#### Cluster Persona Centroids
1. **High-Value VIP Tech Spenders**: Highest lifetime spend ($>\$4,800$), high order frequency, top average order value (\$220+), low cancellation rate.
2. **Active Brand Advocates & Influencers**: Highest social engagement (18+ actions), high positive sentiment ($+0.79$), consistent purchase frequency.
3. **High-Activity Bargain Hunters**: High web browsing and session volume, deal-oriented, lower basket size, price-sensitive.
4. **Casual & Occasional Shoppers**: Standard order values, moderate dwell time, average recency ($>80$ days).
5. **At-Risk & Churned Customers**: High recency ($270+$ days without orders), elevated cancellation rates, negative sentiment scores ($-0.61$).

---

### 7.2. Explainable Hybrid Product Recommendations
* **Methodology**: Combines User-Item Collaborative Filtering (ALS matrix factorization) with Market Basket Association Rule Mining.
* **Association Mining**: Generates rules with minimum Support $0.01$, minimum Confidence $0.20$, and Lift up to **2.1x**.
* **Zero-Leakage Recommender Hit Rate**: Evaluated on an 80/20 customer holdout split, achieving a **76.0% Hit Rate** for top-5 recommendations.
* **Explainability**: Every recommendation includes a plain-language explanation (e.g., *"Frequently bought together with Wireless Noise-Canceling Headphones in customer orders (Association Lift: 2.1x)"*).

---

### 7.3. Supervised Customer Churn Prediction & Retention AI
* **Prediction Setup**: Point-in-time cutoff architecture: 180-day historical observation window, 90-day future observation window.
* **Target Definition**: `churn_label = 1` if customer had 0 completed orders in the 90 days following cutoff.
* **Model Benchmark (20% Stratified Holdout Evaluation)**:

| Model Architecture | ROC-AUC | PR-AUC | Precision | Recall | F1-Score | Confusion Matrix [TN, FP, FN, TP] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Majority Class Baseline** | 0.5000 | 0.2627 | 0.0000 | 0.0000 | 0.0000 | `[174, 0, 62, 0]` |
| **Logistic Regression (Scaled)** | 0.9159 | 0.8207 | 0.6129 | 0.9194 | 0.7355 | `[138, 36, 5, 57]` |
| **Random Forest (Selected)** | **0.9365** | **0.8660** | **0.6154** | **0.9032** | **0.7320** | `[139, 35, 6, 56]` |

* **Top Predictive Features**:
  1. `hist_distinct_sessions` (18.16%)
  2. `hist_web_touchpoints` (16.02%)
  3. `hist_product_views` (10.98%)
  4. `hist_avg_engagement` (10.73%)
  5. `hist_avg_sentiment` (10.46%)

---

## 8. Cumulative Old + New Data Ingestion & Live Promotion

The platform features an automated 1-click evaluation workflow:

```
[Upload Raw Files] ──▶ [Schema Discovery] ──▶ [Click "Process New Data (Old + New)"]
                                                               │
  ┌────────────────────────────────────────────────────────────┘
  ▼
[HDFS Ingestion] ──▶ [PySpark Cumulative Aggregation] ──▶ [ML Retraining] ──▶ [Hot Promotion to Live]
```

1. **Automatic Linear Balancing**:
   $$\text{Total Customers}_{\text{overall}} = \text{Total Customers}_{\text{historical}} + \text{New Unique Customers}$$
   $$\text{Total Revenue}_{\text{overall}} = \text{Total Revenue}_{\text{historical}} + \text{New Batch Completed Revenue}$$
2. **Platform Data Composition Breakdown**: The dashboard displays a direct audit table breaking down Historical vs. Newly Added vs. Integrated Platform metrics.
3. **Instant Rollback**: A single click on **"Rollback to Baseline"** safely restores original baseline artifacts, resetting active models and registries without data corruption.

---

## 9. Web Application & Dashboard Navigation

The frontend is built with React 18, Vite, Chart.js, and Lucide Icons, providing 7 specialized modules:

| Route | View Name | Business Capability |
| :--- | :--- | :--- |
| `/` | **Overview Dashboard** | Executive summary: total revenue, transactions, customer count, order fulfillment gauge, cohort retention, and the Platform Data Composition audit table. |
| `/analytics` | **Customer Analytics** | Acquisition channels, client devices, sentiment polarity distribution, and RFM distributions. |
| `/segmentation` | **Customer Segmentation** | K-Means model quality cards (Silhouette, Davies-Bouldin, Calinski-Harabasz), Elbow curve, 2D PCA scatter plot, and centroid table. |
| `/customers` | **Customer 360° Directory** | Searchable customer directory with full order histories, web activity logs, and social reviews. |
| `/recommendations` | **Personalized Recommendations** | Top 5 personalized products per customer with confidence scores, transparent rationale, and association rules. |
| `/churn` | **Customer Retention & Churn AI** | 90-day churn predictions, risk distribution tiers (Low, Medium, High), test confusion matrix, feature importance ranking, and retention playbooks. |
| `/pipeline` | **Data Pipeline & HDFS Engine** | Multi-format drag-and-drop ingestion, schema discovery inspector, 1-click evaluation button, and rollback controls. |

---

## 10. Step-by-Step Setup & Reproduction Guide

### Prerequisites
- **Operating System**: Windows 10/11 with WSL (Ubuntu) installed, or Linux/macOS.
- **Python**: Version 3.11+
- **Java**: JRE/JDK 8 or 11 (Required for Apache Spark)
- **Node.js**: Version 18+ and npm
- **Hadoop**: Apache Hadoop 3.3.6 (Installed in WSL or local environment)

---

### Quick Start (Windows Automated Scripts)

Double-click or run from PowerShell:
```cmd
start_all.bat
```
This launches:
1. WSL Hadoop HDFS daemons (NameNode and DataNode on port 9000).
2. Flask backend API server on `http://127.0.0.1:5000`.
3. Vite + React frontend dashboard on `http://localhost:3000`.

---

### Manual Step-by-Step Setup

#### 1. Setup Python Virtual Environment & Install Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

#### 2. Start Hadoop HDFS in WSL
```bash
wsl -e bash -c "cd '/mnt/d/Infynux/big data project' && bash scripts/run_hdfs_daemon.sh"
```

#### 3. Run PySpark Baseline Pipeline (Optional: To rebuild from raw)
```powershell
.\.venv\Scripts\python.exe scripts/run_big_data_pipeline.py
```

#### 4. Launch Flask Backend Server
```powershell
.\.venv\Scripts\python.exe backend/app.py
```
*API runs at `http://127.0.0.1:5000`.*

#### 5. Launch React Frontend
```powershell
cd frontend
npm install
npm run dev
```
*Frontend opens at `http://localhost:3000`.*

---

## 11. Current Live Platform Metrics

The current active production deployment reflects the cumulative integration of the historical baseline plus incremental batches:

```
========================================================================================
                      SMART: CURRENT INTEGRATED PLATFORM METRICS
========================================================================================
Active Version Identifier   : v_batch_20261118_131539_cb5c
Storage Engine              : Hadoop HDFS (hdfs://172.27.214.120:9000) + Local Parquet
Total Integrated Customers  : 1,444 Unique Customers (+144 newly added in latest batch)
Total Completed Orders      : 12,783 Orders (Fulfillment Rate: 95.24%)
Total Processed Transactions: 13,422 Transactions
Total Web Touchpoints       : 131,771 Clickstream Events
Total Social Reviews        : 9,996 Customer Feedback Interactions
Overall Platform Gross Sales: $2,020,047.09
K-Means Silhouette Score    : 0.4287 (Optimal cluster separation)
Recommender Test Hit Rate   : 76.0% (Zero-leakage holdout validation)
Churn Model ROC-AUC Score   : 0.9365 (Random Forest 80/20 holdout)
========================================================================================
```

---

## 12. License & Academic Attribution
Developed as an advanced academic research project and industry-grade demonstration in Big Data Engineering, Distributed Computing, and Applied Machine Learning.
* **Author**: Naveen D
* **Repository**: [Smart Customer Analysis and Personalized Experience Using Big Data](https://github.com/naveend07ec/Smart-Customer-Analysis-and-Personalized-Experience-Using-Big-Data)
