# Academic Data Dictionary & Schema Documentation

> **IMPORTANT DISCLAIMER**: All datasets (`transactions.csv`, `web_activity.csv`, `social_media.csv`) stored in `data/raw/` and `data/sample/` are **purely synthetic academic benchmark datasets**. They were generated for educational research, distributed batch processing (PySpark), and machine learning experimentation. They do **not** represent real individuals, customer entities, or real-world transactions.

---

## 1. Multi-Source Integration Key: `customer_id`

All three datasets share a common foreign key: `customer_id`.
- **Format**: `CUST_0001` to `CUST_1200` (for full raw dataset) and `CUST_S_001` to `CUST_S_050` (for sample dataset).
- **Referential Integrity**: 100% cross-source linkage across Transactions, Web Activity, and Social Media interactions.
- **Behavioral Personas Simulated**:
  1. *VIP Tech Spenders*: High transaction amount, frequent purchases in Electronics and Home & Kitchen, positive social sentiment.
  2. *Active Bargain Hunters*: High web browsing and searches, price-sensitive discounts, apparel and books.
  3. *Casual Shoppers*: Low-frequency buyers, occasional direct browsing, neutral engagement.
  4. *Social Brand Advocates*: High social media post volume, high positive sentiment and engagement scores.
  5. *At-Risk / Dissatisfied*: Lapsed purchases (early in the year only), higher cancellation rate, negative feedback reviews.

---

## 2. Dataset Schemas

### Table 1: `transactions.csv`
Stored at: `data/raw/transactions.csv` and `data/sample/transactions.csv`

| Column Name | Data Type | Constraint / Format | Description & Academic Relevance |
| :--- | :--- | :--- | :--- |
| `transaction_id` | String | Unique Key (`TXN_xxxxxx`) | Primary identifier for the sales order event. |
| `customer_id` | String | Foreign Key (`CUST_xxxx`) | Links the transaction to the unified customer identity. |
| `transaction_date`| Timestamp | `YYYY-MM-DD HH:MM:SS` | Timestamp of the purchase, used for RFM Recency calculation. |
| `product_id` | String | Foreign Key (`PROD_xxx`) | Identifier of purchased product from the catalog (PROD_101 to PROD_130). |
| `product_category`| String | Categorical | Broad product grouping (Electronics, Home & Kitchen, Apparel, Health & Beauty, Sports & Fitness, Books & Media). |
| `product_name` | String | Text | Descriptive label of the catalog item. |
| `quantity` | Integer | $\ge 1$ | Units ordered in the line-item. |
| `unit_price` | Float | USD ($0.01 - $999.99) | Baseline price per unit item. |
| `discount_percent`| Float | Percentage ($0.0 - 15.0\%$) | Promotional discount applied to line item. |
| `total_amount` | Float | USD ($> 0.00$) | Net monetary amount after discount; used for RFM Monetary calculation. |
| `payment_method` | String | Categorical (Nullable) | Payment instrument (`Credit Card`, `Debit Card`, `PayPal`, `UPI`, `Net Banking`). Contains 0.6% missing values to benchmark PySpark data imputation/cleaning. |
| `order_status` | String | Categorical | Final state of order (`Completed`, `Pending`, `Cancelled`, `Refunded`). |

---

### Table 2: `web_activity.csv`
Stored at: `data/raw/web_activity.csv` and `data/sample/web_activity.csv`

| Column Name | Data Type | Constraint / Format | Description & Academic Relevance |
| :--- | :--- | :--- | :--- |
| `activity_id` | String | Unique Key (`WEB_xxxxxx`) | Primary identifier for the web interaction event. |
| `customer_id` | String | Foreign Key (`CUST_xxxx`) | Identified user performing digital browsing. |
| `session_id` | String | Key (`SESS_xxxxxx`) | Groups sequential clickstream activities within a visit. |
| `timestamp` | Timestamp | `YYYY-MM-DD HH:MM:SS` | Chronological log time of event. |
| `page_url` | String | URI Path | Navigated page path (e.g., `/home`, `/category/electronics`, `/product/prod_101`). |
| `action_type` | String | Categorical | Specific digital touchpoint (`page_view`, `product_view`, `search`, `add_to_cart`, `remove_from_cart`, `wishlist`, `checkout_start`). |
| `product_id` | String | Foreign Key (Nullable) | Associated catalog item for product-specific actions (e.g. `product_view`, `add_to_cart`). Null for generic pages like `/home` and `/category/*`. |
| `duration_seconds`| Integer | $\ge 0$ | Dwell time spent on page, used to measure engagement depth. |
| `device_type` | String | Categorical | Client device hardware (`Desktop`, `Mobile`, `Tablet`). |
| `traffic_source` | String | Categorical | Inbound marketing channel (`Organic Search`, `Direct`, `Social Media`, `Email Newsletter`, `Referral`). |

---

### Table 3: `social_media.csv`
Stored at: `data/raw/social_media.csv` and `data/sample/social_media.csv`

| Column Name | Data Type | Constraint / Format | Description & Academic Relevance |
| :--- | :--- | :--- | :--- |
| `interaction_id` | String | Unique Key (`SOC_xxxxxx`) | Primary identifier for the external social event. |
| `customer_id` | String | Foreign Key (`CUST_xxxx`) | Identified social profile linked to customer identity. |
| `timestamp` | Timestamp | `YYYY-MM-DD HH:MM:SS` | Creation timestamp of the review or engagement. |
| `platform` | String | Categorical | Social network origin (`Twitter/X`, `Instagram`, `Facebook`, `LinkedIn`, `YouTube`). |
| `interaction_type`| String | Categorical | Interaction style (`review`, `comment`, `mention`, `like`, `share`, `direct_message`). |
| `sentiment` | String | Categorical | Qualitative polarity (`Positive`, `Neutral`, `Negative`). |
| `sentiment_score` | Float | Range $[-1.000, +1.000]$ | Continuous sentiment polarity index computed from feedback text. |
| `engagement_score`| Integer | Range $[1, 100]$ | Normalized interaction reach / engagement impact metric. |
| `feedback_content`| Text | String | Realistic academic text feedback statement representing the user's opinion. |
| `associated_category` | String | Categorical | Related product category referenced in post. |

---

## 3. Deliberate Data Quality Test Cases for PySpark Processing

To ensure the Big Data preprocessing pipeline demonstrably performs data cleaning rather than passing pre-sanitized mock data:
1. **Deduplication**: 25 duplicate rows in `transactions.csv` and 35 duplicate rows in `web_activity.csv` were injected to test PySpark `dropDuplicates()` operations.
2. **Missing Field Imputation/Filtering**: 74 missing values (0.60%) in `transactions.csv: payment_method` to test null handling and categorization.
3. **Nullable Foreign Keys in Clickstream**: 50.06% of web activities lack `product_id` by nature (e.g., home and category searches) requiring conditional joining logic during PySpark feature aggregation.

