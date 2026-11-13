# Final-Year Academic Project Defense Presentation

## Title: Smart Customer Analysis and Personalized Experience Using Big Data

---

### Slide 1: Title & Project Identity
- **Project Title**: Smart Customer Analysis and Personalized Experience Using Big Data
- **Domain**: Big Data Analytics, Distributed Computing, Machine Learning, Full-Stack Web Engineering
- **Target Platform**: Apache Spark (PySpark), Scikit-Learn, Flask REST API, React 18, Chart.js
- **Repository**: [https://github.com/naveend07ec/Smart-Customer-Analysis-and-Personalized-Experience-Using-Big-Data](https://github.com/naveend07ec/Smart-Customer-Analysis-and-Personalized-Experience-Using-Big-Data)

---

### Slide 2: Problem Statement & Motivation
- **The Challenge**: Modern e-commerce enterprises generate fragmented, high-velocity data across disconnected channels (point-of-sale transactions, web browsing clickstreams, and social media sentiment).
- **The Limitation of Traditional Systems**: Traditional relational databases (RDBMS) suffer from scaling bottlenecks, schema rigidity, and performance degradation when extracting cross-channel behavioral features.
- **The Research Goal**: Design and implement a scalable, distributed, batch-processing architecture using open-source big data tools to unify multi-source data, perform unsupervised customer segmentation, and deliver explainable product recommendations.

---

### Slide 3: Project Objectives
1. **Multi-Source Data Ingestion**: Ingest and unify sales transactions, website logs, and social reviews using a common `customer_id`.
2. **Distributed Data Processing**: Clean, deduplicate, and transform high-volume datasets using Apache Spark / PySpark.
3. **Behavioral Feature Store**: Extract 24 explainable customer-level behavioral metrics (RFM, dwell time, funnel conversion, sentiment polarity).
4. **Customer Segmentation**: Train an optimal K-Means clustering model evaluated by Elbow and Silhouette metrics.
5. **Personalized Recommendations**: Develop a hybrid recommendation engine combining collaborative filtering and Market Basket association rules.
6. **Transparent Explainability**: Provide human-understandable reasoning for every product recommendation.
7. **Interactive Dashboard**: Build a React 18 + Chart.js web dashboard served by a lightweight Flask REST API.

---

### Slide 4: System Architecture & Data Pipeline
```
 Multi-Source Raw Data (Transactions, Clickstream, Social)
                          │
                          ▼
        Storage Layer (Staged Parquet / HDFS)
                          │
                          ▼
     Distributed PySpark 3.5.1 Processing Layer
      - Primary Key Deduplication
      - Missing Value Imputation
      - Domain-Level Customer Aggregations
      - Multi-Source Outer Join on customer_id
                          │
                          ▼
       Unified Feature Matrix (1,200 x 24 Columns)
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
  K-Means Clustering (K=5)    Explainable Recommender
   - Optimal Silhouette: 0.3533- Collaborative Filtering
   - 2D PCA Visualization      - 541 Association Rules
            │                           │
            └─────────────┬─────────────┘
                          ▼
              Flask REST API Server (:5000)
                          │
                          ▼
              React + Vite Dashboard (:3000)
```

---

### Slide 5: Multi-Source Dataset Architecture
- **Common Identity Key**: `customer_id` (`CUST_0001` through `CUST_1200`).
- **Referential Integrity**: 100% overlap across all three data sources (1,200 unique customers).
- **Dataset Dimensions**:
  1. **Sales Transactions** (`transactions.csv`): 12,239 records, 12 features (sales value, item quantities, discounts, order statuses).
  2. **Website Clickstream** (`web_activity.csv`): 120,979 records, 10 features (sessions, page paths, action types, dwell time, devices).
  3. **Social Media Feedback** (`social_media.csv`): 8,828 records, 10 features (platforms, interaction types, continuous sentiment polarity $[-1.0, +1.0]$, engagement score $[1, 100]$).

---

### Slide 6: PySpark Big Data Processing & Cleaning Audit
- **Lightweight Configuration for 8 GB RAM**: Restricting Spark to `local[2]` with a 2 GB driver memory cap and 4 shuffle partitions prevents memory exhaustion.
- **Data Quality Transformations**:
  - **Deduplication**: 25 duplicate sales rows and 35 duplicate web activity events identified and eliminated via `dropDuplicates()`.
  - **Missing Value Handling**: 73 missing payment methods imputed to an explicit `'Unknown'` category.
  - **Meaningful Null Preservation**: 60,540 null product IDs safely preserved on generic navigation pages (`/home`, category listings).
  - **Zero Unexpected Nulls**: Applied coalesce fill policies to ensure 100% complete feature matrices.

---

### Slide 7: Behavioral Feature Matrix (24 Columns)
- **Transactional Metrics (RFM)**:
  - Total Spend ($M$), Total Transactions ($F$), Completed Orders, Cancelled Orders, Cancellation Rate, Average Order Value ($AOV$), Recency Days ($R$).
- **Clickstream Engagement Metrics**:
  - Total Web Touchpoints, Distinct Sessions, Average Dwell Time (seconds), Product Views Count, Cart Additions Count, Wishlist Count, Checkout Starts Count, Cart-to-Checkout Funnel Ratio.
- **Social Sentiment Metrics**:
  - Total Social Interactions, Average Engagement Score ($0-100$), Average Sentiment Polarity ($-1.0$ to $+1.0$), Positive/Neutral/Negative Interaction Counts, Unique Platforms Utilized.
- **Output**: Exactly **1 row per customer** (1,200 rows $\times$ 24 columns).

---

### Slide 8: K-Means Clustering & Optimal $K$ Selection
- **Feature Scaling**: Standardized all 23 numerical features using `StandardScaler` ($\mu = 0, \sigma = 1$) to prevent high-scale monetary features from dominating unit-bound sentiment scores.
- **Evaluation Across $K \in [2, 8]$**:
  - **Inertia (WCSS)**: Demonstrated clear inflection point (Elbow) at $K=5$ (Inertia = 9,784.31).
  - **Silhouette Score**: Peaked at $K=5$ (**0.3533**), validating optimal cluster separation.
  - **Davies-Bouldin Index**: **1.1554** (compact cluster density).
  - **Calinski-Harabasz Score**: **543.98** (high between-cluster variance).

---

### Slide 9: 2D PCA Dimensionality Reduction
- **Mathematical Projection**: Reduced the 23-dimensional feature space to 2 principal components ($PC1, PC2$) via orthogonal linear transformation.
- **Variance Retention**:
  - **PC1 (40.85%)**: Primarily captures overall spending and interaction volume.
  - **PC2 (16.11%)**: Primarily reflects sentiment polarity vs churn/lapse risk.
  - **Total Variance Explained**: **56.96%**.
- **Dashboard Application**: Powers the interactive 2D scatter plot with hover tooltips and segment color coding.

---

### Slide 10: Discovered Customer Personas (K=5)
1. **High-Value VIP Tech Spenders (17.0%, 204 customers)**:
   - Mean Spend: **\$4,634.37** | Mean AOV: **\$223.13** | Recency: **18.4 days** | Sentiment: **+0.75**.
   - Strategy: Exclusive VIP loyalty rewards, early access to flagship electronics.
2. **Active Bargain Hunters (25.5%, 306 customers)**:
   - Mean Web Actions: **190.0** | Mean Cart Additions: **20.9** | Mean Spend: **\$1,399.53**.
   - Strategy: Flash discount campaigns, cart abandonment recovery alerts.
3. **Casual Occasional Shoppers (29.0%, 348 customers)**:
   - Mean Spend: **\$483.53** | Purchases: **2-5 orders** | Recency: **80.4 days**.
   - Strategy: Cross-sell recommendations, seasonal newsletter engagement.
4. **Social Brand Advocates (14.5%, 174 customers)**:
   - Mean Social Interactions: **17.9 posts** | Mean Sentiment: **+0.82** (Highest).
   - Strategy: Referral affiliate incentives, user-generated content amplification.
5. **At-Risk / Dissatisfied Customers (14.0%, 168 customers)**:
   - Mean Recency: **281.6 days** | Cancellation Rate: **25.6%** | Sentiment: **-0.65**.
   - Strategy: Re-engagement surveys, targeted win-back discounts.

---

### Slide 11: Explainable Recommendation Engine
- **Hybrid Architecture**:
  1. **User-Item Interaction Matrix**: Implicit interest scored by:
     $$\text{Score} = 5.0 \times \text{Purchase Qty} + 2.5 \times \text{Cart Adds} + 1.0 \times \text{Views} + 1.5 \times \text{Wishlist}$$
  2. **Collaborative Filtering**: Cosine similarity across customer preference vectors.
  3. **Market Basket Association Rules**: 541 mined co-occurrence rules with Support, Confidence, and Lift.
  4. **Explainability Narrative**: Outputs plain-language reasoning for every product suggestion.

---

### Slide 12: Sample Explainable Output
- **Customer**: `CUST_0001` (Casual Occasional Shopper)
- **Recommendations Generated**:
  1. **LED Smart Desk Lamp with Dimmer** (\$39.99, Home & Kitchen) — **Match: 88.7%**
     * *Reason*: Frequently bought together with *Hydrating Facial Moisturizer Cream* (Association confidence: 22%, Lift: 0.92x).
  2. **Designing Data-Intensive Applications** (\$45.00, Books & Media) — **Match: 86.9%**
     * *Reason*: Frequently bought together with *Organic Aromatherapy Essential Oil Set* (Association confidence: 22%, Lift: 0.96x).
  3. **Cast Iron Dutch Oven 6-Quart** (\$69.99, Home & Kitchen) — **Match: 85.9%**
     * *Reason*: Frequently bought together with *Organic Aromatherapy Essential Oil Set* (Association confidence: 23%, Lift: 0.98x).

---

### Slide 13: Full-Stack Web Architecture
- **Flask REST API (Port 5000)**:
  - 15 endpoints organized into 6 modular blueprints (`overview`, `analytics`, `segmentation`, `customers`, `recommendations`, `pipeline`).
  - Cached in-memory `DataService` layer eliminates repetitive disk I/O.
  - Automated test suite achieves a **100% pass rate** across all 15 endpoints.
- **React 18 + Vite Frontend (Port 3000)**:
  - 6 dedicated analytics views with Chart.js:
    1. Overview Dashboard
    2. Customer Analytics
    3. Customer Segmentation
    4. Customer Details (360° Profile Drawer)
    5. Personalized Recommendations & Association Mining
    6. Data Integration & PySpark Diagnostics

---

### Slide 14: Engineering Challenges Overcome
1. **Cartesian Product Explosion Prevention**: Avoided raw table joins by pre-aggregating transactions, clickstream, and social data to the customer level.
2. **Resource Constraints (8 GB RAM)**: Tuned PySpark configuration to `local[2]` with a 2 GB driver memory ceiling and suppressed Spark UI daemons.
3. **Windows Hadoop Environment Compatibility**: Embedded project-local WinUtils binaries, eliminating global environment variable modifications.
4. **HDFS Dual-Mode Storage**: Provided seamless dual-mode capability supporting both genuine Hadoop clusters and lightweight local staged Parquet storage.

---

### Slide 15: Conclusion & Future Scope
- **Key Contributions**:
  - Successfully demonstrated an end-to-end Big Data & Machine Learning pipeline running on standard developer hardware.
  - Formulated a 24-feature customer behavioral matrix combining sales, clickstreams, and social media reviews.
  - Validated K-Means clustering ($K=5$) and developed an explainable hybrid recommendation engine.
  - Deployed an interactive React dashboard backed by a verified Flask REST API.
- **Future Enhancements**:
  - Spark Structured Streaming via Apache Kafka for real-time clickstream recommendation updates.
  - Two-Tower Neural Recommender Models for higher-order user-item feature interactions.
  - Distributed multi-node deployment on an Apache Hadoop YARN cloud cluster.
