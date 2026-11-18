# SMART Project — Test Batch Results Audit Report (READ-ONLY)
**Audit Target:** Batch `batch_20261116_154011_ef38` / Version `v_batch_20261116_154011_ef38` (100 Customers)  
**Audit Mode:** READ-ONLY Verification (No modifications to code, data, models, or pointers)  
**Date of Audit:** 2026-11-16  
**Auditor:** Antigravity System Audit Engine  

---

## Executive Summary & Audit Dashboard Comparison

| Metric / Attribute | Dashboard Reported | Audited Actual | Variance | Audit Classification |
| :--- | :--- | :--- | :--- | :--- |
| **Batch ID** | `batch_20261116_154011_ef38` | `batch_20261116_154011_ef38` | Exact match | **PASS** |
| **Total Customers** | 100 | 100 | 0 | **PASS** |
| **Total Revenue** | $80,912.63 | $80,912.63 | $0.00 | **PASS** |
| **Order Fulfillment Rate** | 73.76% | 73.7562% (73.76%) | 0.00% | **PASS** |
| **K-Means Selected K** | K = 2 | K = 2 | 0 | **PASS** |
| **Cluster 0 Size & Stats** | 99 cust ($812.55, 5.94 ord, 32.2 web, 0 sent) | 99 cust ($812.55, 5.94 ord, 32.2 web, 0.0 sent) | Exact match | **PASS** |
| **Cluster 1 Size & Stats** | 1 cust ($470.60, 5.0 ord, 22.0 web, 0.85 sent) | 1 cust ($470.60, 5.0 ord, 22.0 web, 0.85 sent) | Exact match | **PASS** |
| **Association Rules Count** | 0 | 0 | 0 | **WARNING / FAIL** |
| **Churn Risk Distribution** | 2 High, 20 Medium, 78 Low | 2 High, 20 Medium, 78 Low | Exact match | **PASS** |
| **Churn Test ROC-AUC** | 0.3684 | 0.3684 | 0.00 | **PASS** |

---

## 1. Dataset & Ingestion Audit

### 1.1 Batch Identification & Staged Raw Files
- **Batch Identifier:** `batch_20261116_154011_ef38`
- **Creation Timestamp:** `2026-11-16T15:40:11.447473`
- **Staging Directory:** `data/uploads/batch_20261116_154011_ef38/`
- **Processed Version Directory:** `data/versions/v_batch_20261116_154011_ef38/`
- **Manifest File:** `data/uploads/batch_20261116_154011_ef38/manifest.json` (33,587 bytes)
- **Staged Raw Files:**
  1. `b81cb1_transactions.csv` (Original filename: `transactions.csv` | 111,963 bytes | SHA256: `18f707f154d23d8c1c469f69273c52a32c25390977a4a905a305f884a141a0e1`)
  2. `4d361f_web_activity.csv` (Original filename: `web_activity.csv` | 362,635 bytes | SHA256: `9550e70b79ca7226f3161c56b4f74d0360a7ad9a647dcfad6e2d83e2a0462058`)
  3. `9fcd0e_social_media_template.csv` (Original filename: `social_media_template.csv` | 271 bytes | SHA256: `c2086f8d1b855a509b299e35a6228f9a4ec769c128509dccb24fb0fcbd35d3aa`)

### 1.2 Multi-Source Processing & Record Counts
All three canonical customer channels were processed through PySpark batch execution:

| Source | Raw Records | Cleaned Records | Rejected Records | Customer Coverage | Audit Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Transactions** | 973 | 804 | 169 | 100 / 100 (100.0%) | **PASS** |
| **Web Activity** | 3,210 | 3,210 | 0 | 100 / 100 (100.0%) | **PASS** |
| **Social Media** | 1 | 1 | 0 | **1 / 100 (1.0%)** | **WARNING** |

#### Record Rejection Explanation:
- In `transactions.csv`, the 973 raw records have order status breakdown:
  - `Completed`: 593 records (60.9%)
  - `Cancelled`: 211 records (21.7%)
  - `Returned`: 169 records (17.4%)
- During PySpark batch cleaning (`clean_transactions` in `cleaners.py`), the filtering condition is `df.filter(col("order_status").isin(["Completed", "Cancelled"]))`.
- **Finding:** Exactly 169 records were rejected because their status was `Returned`. This is an intended Big Data pipeline business rule that excludes returned products from the active fulfillment denominator.

### 1.3 Data Quality & Customer Coverage
- **Duplicate Records:** 0 duplicate primary keys detected across all three files.
- **Missing Values:** Zero unexpected nulls in required fields (`transaction_id`, `customer_id`, `total_amount`, `order_status`, `event_id`, `action_type`).
- **Data Types:** Schema inference correctly assigned timestamps, numeric doubles, and categorical strings.
- **Customer Coverage Disparity:**
  - `transactions.csv` contains 100 unique customers (`CUST_0001` through `CUST_0100`).
  - `web_activity.csv` contains 100 unique customers (`CUST_0001` through `CUST_0100`).
  - `social_media_template.csv` contains **only 1 customer** (`CUST_0001`). The uploaded file was a single-row template rather than a full 100-customer dataset.

### 1.4 Revenue & Order Fulfillment Verification
- **Total Completed Orders:** 593 orders
- **Total Completed Revenue:** Sum of `total_amount` where `order_status == 'Completed'` = **$80,912.63** (Exact match with dashboard).
- **Total Cancelled Orders:** 211 orders
- **Fulfillment Calculation:**
  $$\text{Fulfillment Rate} = \frac{\text{Completed Orders}}{\text{Completed Orders} + \text{Cancelled Orders}} = \frac{593}{593 + 211} = \frac{593}{804} = 73.7562\% \rightarrow \mathbf{73.76\%}$$
- **Finding:** The revenue and fulfillment rate strictly use the verified transaction statuses. (Classification: **PASS**)

---

## 2. K-Means Segmentation & Cluster Imbalance Audit

### 2.1 Feature Set & Preprocessing
- **Feature Extraction:** 22 continuous numerical features generated in `unified_customer_features.csv` (excluding `customer_id`):
  `['total_spend', 'total_transactions', 'avg_order_value', 'total_quantity', 'recency_days', 'cancelled_orders_count', 'cancellation_rate', 'total_web_activities', 'total_sessions', 'avg_duration_seconds', 'product_views_count', 'cart_additions_count', 'wishlist_count', 'checkout_starts_count', 'cart_to_checkout_ratio', 'total_social_interactions', 'avg_engagement_score', 'avg_sentiment_score', 'positive_interactions_count', 'neutral_interactions_count', 'negative_interactions_count', 'unique_platforms_count']`.
- **Customer ID Exclusion:** Verified. `customer_id` is retained as an identifier and strictly excluded from the matrix fed into `StandardScaler`. (Classification: **PASS**)
- **Preprocessing:** `StandardScaler()` was fit on all 100 customer rows across all 22 feature columns.

### 2.2 Model Selection Metrics Across Tested K Values ($K=2..8$)
The pipeline retrained K-Means across candidate clusters $K \in [2, 8]$:

| $K$ | Inertia | Silhouette Score | Davies-Bouldin Index | Cluster Sizes |
| :---: | :---: | :---: | :---: | :--- |
| **K = 2** | **1285.43** | **0.7774** | **0.1537** | **[99, 1]** |
| $K = 3$ | 1070.75 | 0.1551 | 1.4784 | [55, 44, 1] |
| $K = 4$ | 904.01 | 0.1561 | 1.3671 | [24, 40, 1, 35] |
| $K = 5$ | 827.22 | 0.1372 | 1.4625 | [21, 20, 24, 34, 1] |
| $K = 6$ | 762.52 | 0.1326 | 1.4867 | [22, 17, 1, 21, 24, 15] |
| $K = 7$ | 723.96 | 0.1337 | 1.5733 | [12, 18, 21, 1, 10, 23, 15] |
| $K = 8$ | 676.75 | 0.1299 | 1.4584 | [5, 16, 1, 16, 13, 17, 12, 20] |

### 2.3 Why $K=2$ Was Selected
The model training service implements an objective mathematical criterion:
$$\text{optimal\_k} = \operatorname{argmax}_{k \in [2, 8]} (\text{silhouette\_score}_k)$$
Because $K=2$ achieved a silhouette score of **0.7774** compared to $\approx 0.13 - 0.15$ for all higher values of $K$, the algorithm strictly selected $K=2$. (Classification: **PASS**)

### 2.4 Investigation of the 99 / 1 Cluster Imbalance
- **Cluster 0 (99 Customers):**
  - Average spend: $812.55 | Orders: 5.94 | Recency: 68.2 days | Web activities: 32.2 | Social interactions: **0.00** | Sentiment: **0.00** | Engagement: **0.00**
- **Cluster 1 (1 Customer — `CUST_0001`):**
  - Average spend: $470.60 | Orders: 5.00 | Recency: 9.0 days | Web activities: 22.0 | Social interactions: **1.00** | Sentiment: **0.85** | Engagement: **65.00**

#### Unscaled Centroid Comparison Table:
| Feature Column | Cluster 0 (99 Customers) | Cluster 1 (`CUST_0001`) | Centroid Difference |
| :--- | :--- | :--- | :--- |
| `total_spend` | $812.55 | $470.60 | -$341.95 |
| `total_transactions` | 5.94 | 5.00 | -0.94 |
| `total_web_activities` | 32.20 | 22.00 | -10.20 |
| `total_social_interactions` | **0.00** | **1.00** | **+1.00** |
| `avg_engagement_score` | **0.00** | **65.00** | **+65.00** |
| `avg_sentiment_score` | **0.00** | **0.85** | **+0.85** |
| `positive_interactions_count`| **0.00** | **1.00** | **+1.00** |
| `unique_platforms_count` | **0.00** | **1.00** | **+1.00** |

#### Root Cause Analysis:
1. **Source of Imbalance:** The user uploaded `social_media_template.csv` containing only a single sample record for `CUST_0001`.
2. **StandardScaler Distortion:** Because 99 out of 100 values were zero, the population standard deviation for social features was near zero ($\sigma \approx 0.0995$). When `CUST_0001` was scaled:
   $$z_{\text{CUST\_0001}} = \frac{1 - 0.01}{0.0995} \approx \mathbf{+9.95}$$
   `CUST_0001` had a z-score of nearly $+10$ standard deviations across 5 orthogonal social media dimensions simultaneously.
3. **Outlier Topology:** In 22-dimensional Euclidean space, the squared distance of `CUST_0001` from the rest of the dataset is $5 \times (9.95)^2 \approx 495$. K-Means immediately isolates `CUST_0001` into a singleton cluster.
4. **Comparison with Baseline:** In the Academic Baseline (1,200 customers), all 1,200 customers have social interactions (8,828 total records), producing smooth, bell-shaped distributions and 5 balanced clusters (sizes 348, 306, 204, 174, 168).
5. **Verdict:** The 99/1 split is **supported by the actual data uploaded** and is a mathematically valid K-Means response to an extreme outlier caused by uploading a single-row template CSV. (Classification: **WARNING**)

---

## 3. Association Rules Audit

### 3.1 Order and Product Distribution
- Completed transactions: 593 records
- Distinct transaction IDs: 593
- Distinct product IDs: 8 (`PROD_101`, `PROD_102`, `PROD_201`, `PROD_202`, `PROD_301`, `PROD_302`, `PROD_401`, `PROD_402`)
- **Transactions containing $\ge 2$ distinct products:** **0 transactions** (Max items per `transaction_id` = 1)
- Distribution of items per `transaction_id`:
  - 1 item: 593 transactions (100.0%)
  - $\ge 2$ items: 0 transactions (0.0%)

### 3.2 Root Cause Analysis — Why Zero Rules Were Generated
The association rule mining function in `model_training_service.py` defines baskets as:
```python
basket_df = completed_tx.groupby("transaction_id")["product_id"].apply(lambda p: list(set(p))).reset_index()
baskets = [b for b in basket_df["product_id"] if len(b) >= 2]
```
- Because every transaction in `b81cb1_transactions.csv` has a unique `transaction_id` with exactly 1 product line, `baskets` is completely empty (`len(baskets) == 0`).
- The rule miner requires `len(baskets) >= 5` to compute pair-wise combinations. Hence, 0 rules were mined.

### 3.3 Implementation Discrepancy (Bug Identified)
- **Baseline Recommender Implementation (`ml/recommendations/recommender.py`):**
  ```python
  baskets = completed_tx_df.groupby("customer_id")["product_id"].unique()
  ```
- **Finding:** The baseline architecture uses **customer-level purchase baskets** (`groupby("customer_id")`), because e-commerce transaction logs often record multi-item carts across multiple single-item rows or repeat customer purchases.
- **Verification:** When grouping by `customer_id` on the test batch:
  - Total customer baskets: 100
  - Customers with $\ge 2$ distinct products: **100 / 100 (100%)**
  - Association rules generated (at `min_support=0.01`, `min_lift=1.05`): **7 association rules**.
- **Verdict:** Generating 0 rules is a **valid data outcome under the `transaction_id` grouping**, but represents an **implementation discrepancy (FAIL / CODE BUG)** compared to the baseline's `customer_id` basket definition.

---

## 4. Churn Prediction Audit

### 4.1 Model Artifact & Version Identification
- **Model File:** `ml/models/versions/v_batch_20261116_154011_ef38/churn/churn_model.joblib`
- **Scaler File:** `ml/models/versions/v_batch_20261116_154011_ef38/churn/scaler.joblib`
- **Evaluation File:** `ml/models/versions/v_batch_20261116_154011_ef38/churn/churn_evaluation_metrics.json`
- **Model Class:** `RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)`

### 4.2 Temporal Windows & Eligibility
- **Dataset Earliest Transaction:** `2025-01-01 15:30:00`
- **Dataset Latest Transaction:** `2026-01-25 11:18:00`
- **Batch Timeline Span:** **388 days**
- **Temporal Eligibility Check ($\ge 270$ days):** PASSED (388 days $\ge 270$ days).
- **Prediction Cutoff Date:** `2025-10-27 11:18:00` (Max date minus 90 days).
- **Historical Feature Window (180 days):** `2025-04-30 11:18:00` to `2025-10-27 11:18:00`.
- **Future Observation Window (90 days):** `2025-10-27 11:18:00` to `2026-01-25 11:18:00`.
- **Eligible Customers Evaluated:** **100 / 100 customers** (All 100 had events prior to cutoff).

### 4.3 Target Leakage Verification
- **Features Used:** `['recency_days_at_cutoff', 'spend_180d', 'orders_180d', 'web_activities_180d', 'web_duration_180d', 'avg_sentiment_180d']`.
- **Feature Extraction Rule:** Strictly restricted to events where `timestamp < cutoff_date` and `timestamp >= feature_start`.
- **Target Label Rule:** `churn_label = 1 if customer_id not in future_purchasers else 0`, where `future_purchasers` are customers with Completed orders strictly $\ge \text{cutoff\_date}$.
- **Finding:** ZERO target leakage detected. Features and labels are strictly segregated in time. (Classification: **PASS**)

### 4.4 Risk Score Distribution & Thresholds
- **Threshold Policy:**
  - High Risk: $\text{Probability} \ge 0.70$
  - Medium Risk: $0.40 \le \text{Probability} < 0.70$
  - Low Risk: $\text{Probability} < 0.40$
- **Evaluated Distribution across 100 Customers:**
  - **High Risk:** 2 customers (2.0%)
  - **Medium Risk:** 20 customers (20.0%)
  - **Low Risk:** 78 customers (78.0%)
  - Exact match with dashboard display. (Classification: **PASS**)
- **Probability Summary:**
  - Mean: $0.2377$ | Median: $0.1598$ | Std: $0.2095$ | Min: $0.0015$ | Max: $0.7694$

### 4.5 Model Evaluation Metrics & Accuracy Claim Audit
- **Ground Truth Distribution:** 76 Retained (0), 24 Churned (1)
- **Train/Test Partition:** 75 Train / 25 Test (Stratified 25% holdout)
- **Holdout Test Set Metrics:**
  - Test Accuracy: **0.7600 (76.0%)**
  - Test Recall: **0.1667 (16.7%)**
  - Test F1-Score: **0.2500**
  - Test ROC-AUC: **0.3684**
- **Evaluation Finding:** On this small 100-customer test batch (only 6 churners in the test holdout), the Random Forest model exhibited low ranking power ($\text{ROC-AUC} = 0.3684$).
- **Integrity Verification:** The system truthfully recorded and presented $\text{ROC-AUC} = 0.3684$ in `model_evaluation_report.json` without falsifying or inflating model performance metrics. (Classification: **PASS**)

---

## 5. Consolidated Audit Findings & Classifications

| # | Audit Item | Finding Summary | Classification |
| :---: | :--- | :--- | :---: |
| **1** | Batch Identity & File Staging | Batch `batch_20261116_154011_ef38` staged 3 files with verified SHA-256 hashes. | **PASS** |
| **2** | Pipeline Ingestion Record Counts | Raw transactions (973), Web (3210), Social (1). Cleaned counts verified. | **PASS** |
| **3** | Order Status Rejection Logic | 169 "Returned" transactions excluded by pipeline business rule. | **PASS** |
| **4** | Revenue & Fulfillment Calculation | Revenue ($80,912.63) and fulfillment (73.76%) strictly match completed/cancelled orders. | **PASS** |
| **5** | Social Media Customer Coverage | Uploaded file was `social_media_template.csv` with 1 record, giving 1% coverage. | **WARNING** |
| **6** | Customer ID Feature Exclusion | `customer_id` strictly excluded from K-Means feature matrix. | **PASS** |
| **7** | K-Means Model Selection ($K=2$) | $K=2$ selected by `argmax(silhouette)` due to high silhouette score (0.7774). | **PASS** |
| **8** | 99/1 Cluster Imbalance | Caused by single-customer social media record creating a $z \approx +9.95$ outlier. Valid math response to data. | **WARNING** |
| **9** | Association Rules Count (0 rules) | Caused by `groupby("transaction_id")` on single-item order data (`len(baskets)==0`). | **FAIL** |
| **10** | Churn Temporal Eligibility | 388-day batch timeline exceeds 270-day requirement; eligibility confirmed. | **PASS** |
| **11** | Churn Target Leakage | Zero leakage; feature window strictly precedes 90-day future observation window. | **PASS** |
| **12** | Churn Risk Distribution | 2 High, 20 Medium, 78 Low verified from model inference probabilities. | **PASS** |
| **13** | Churn Metric Reporting Integrity | True holdout ROC-AUC of 0.3684 accurately recorded without false claims. | **PASS** |

---

## 6. Recommendations for Future Batch Uploads

1. **Upload Complete Social Media Files:** Avoid uploading sample template CSVs (`social_media_template.csv`) with full transaction and web activity files. Ensure all 100 customers have representative social media records to avoid single-customer outlier clustering.
2. **Harmonize Association Rule Grouping:** In `model_training_service.py`, update basket grouping to `completed_tx.groupby("customer_id")["product_id"].unique()` (matching `ml/recommendations/recommender.py`) to support single-item transaction schemas.
3. **Expand Churn Training Samples:** Churn models require $\ge 500$ customers for robust Random Forest tree splits; 100 customers with 6 test churners produces high sample variance.

