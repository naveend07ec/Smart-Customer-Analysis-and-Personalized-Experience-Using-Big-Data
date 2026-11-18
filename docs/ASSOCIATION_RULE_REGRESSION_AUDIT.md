# SMART Project — Association Rule Regression Audit Report

**Date:** 2026-11-17  
**Version Audited:** `v_batch_20261117_121700_7dcf` (Cumulative 1,203 Customers)  
**Investigation Mode:** Strictly READ-ONLY (No code or models modified)

---

## Executive Summary

During cumulative model retraining of version `v_batch_20261117_121700_7dcf`, the recommendation engine reported:
> *"Top Association Rules Mined (0) — Single item transactions detected; minimum support threshold not exceeded."*

The baseline model previously discovered **394 association rules**.

### Core Finding
The regression is **NOT** caused by data loss, incomplete batch union, or missing historical data. The cumulative transactions dataset (`cleaned_transactions.parquet`) contains all **12,223 records** (12,214 historical + 9 new) across 1,203 customers.

The regression is caused by an **architectural grouping discrepancy** between the original production recommender (`ml/recommendations/recommender.py`) and the automated retraining service (`backend/app/services/model_training_service.py`):
1. **Original Recommender (`recommender.py`):** Grouped completed orders by **`customer_id`** (`completed_tx_df.groupby("customer_id")["product_id"].unique()`), analyzing customer co-purchasing affinity across transactions, producing **394 rules**.
2. **Retraining Service (`model_training_service.py`):** Grouped by **`transaction_id`** (`completed_tx.groupby("transaction_id")["product_id"]`). Because each canonical transaction row represents an individual line item with a unique `transaction_id`, **100% of transactions contain exactly 1 product**.
3. Filtering for baskets with $\ge 2$ items (`len(b) >= 2`) filtered out **all 12,223 transactions**, yielding 0 baskets and 0 rules.

---

## 1. Dataset & Provenance Verification

| Parameter | Baseline (`baseline`) | Cumulative Version (`v_batch_20261117_121700_7dcf`) | Status |
|---|:---:|:---:|:---:|
| **Source File** | `data/processed/cleaned_transactions.parquet` | `data/versions/v_batch_20261117_121700_7dcf/cleaned_transactions.parquet` | Verified |
| **Total Transactions** | 12,214 | 12,223 (+9 incoming) | Fully Cumulative |
| **Completed Transactions** | 11,673 | 11,681 (+8 incoming) | Fully Cumulative |
| **Distinct Customers** | 1,200 | 1,203 (+3 synthetic) | Fully Cumulative |
| **Distinct Products** | 30 | 34 (+4 incoming) | Preserved |
| **Null Product IDs** | 0 | 0 | Clean |

Historical data is **100% retained**. The PySpark cumulative union and primary-key deduplication succeeded completely.

---

## 2. Basket Construction Analysis & Discrepancy

### Schema Structure
In the SMART canonical schema:
- There is **no separate `order_id`** column.
- The schema is: `[transaction_id, customer_id, transaction_date, product_id, product_category, product_name, quantity, unit_price, discount_percent, total_amount, payment_method, order_status]`.
- Each record has a globally unique `transaction_id` representing a distinct line item purchase.

### Basket Grouping Comparison

| Grouping Strategy | Total Baskets | Baskets with $\ge 2$ Products | Multi-Item % | Association Rules Discovered |
|---|:---:|:---:|:---:|:---:|
| **By `transaction_id`** (`model_training_service.py`) | 11,681 | **0** | **0.00%** | **0** |
| **By `customer_id`** (`recommender.py`) | 1,202 | **1,128** | **93.84%** | **394** |

### Code Evidence

#### Baseline Production Recommender (`ml/recommendations/recommender.py`, Line 88)
```python
def mine_association_rules(completed_tx_df, min_support=0.01, min_lift=1.05):
    # Groups by customer_id to find products co-purchased across customer history
    baskets = completed_tx_df.groupby("customer_id")["product_id"].unique()
    total_baskets = len(baskets)
```

#### Retraining Service (`backend/app/services/model_training_service.py`, Line 266)
```python
# Apriori Association Rules (from completed transactions)
basket_df = completed_tx.groupby("transaction_id")["product_id"].apply(lambda p: list(set(p))).reset_index()
baskets = [b for b in basket_df["product_id"] if len(b) >= 2]
```
Because `len(b) == 1` for every single `transaction_id`, `baskets` evaluates to `[]` (`len(baskets) == 0`).  
At line 270, `if len(baskets) >= 5:` fails, and `rules` defaults to `[]`.

---

## 3. Support & Confidence Verification

Running the exact Apriori algorithm from `recommender.py` on the cumulative dataset (`data/versions/v_batch_20261117_121700_7dcf/cleaned_transactions.parquet`) using `customer_id` grouping:

- **Total Customer Baskets:** 1,202 completed buyer profiles
- **Multi-Item Customer Profiles:** 1,128 profiles (93.8%)
- **Item Frequencies Computed:** 34 products
- **Item Pairs Evaluated:** 561 unique pairs
- **Pairs with Support $\ge 0.01$ and Lift $\ge 1.05$:** **394 association rules**

The top rules match baseline exactly:
- `PROD_102` $\rightarrow$ `PROD_105` (Support: 0.0383, Confidence: 0.1825, Lift: 2.14)
- `PROD_105` $\rightarrow$ `PROD_102` (Support: 0.0383, Confidence: 0.2215, Lift: 2.14)

---

## 4. Fallback & Artifact Preservation Issue

When `len(baskets) < 5` occurred in `model_training_service.py`:
1. `rules` became `[]`.
2. `product_association_rules.json` was overwritten with `[]` (2 bytes).
3. `association_rules.joblib` was overwritten with pickled `[]` (5 bytes).

Rather than falling back to or retaining the existing baseline association rules (`ml/models/association_rules.joblib`), the system persisted the empty rule set.

---

## 5. Root Cause Classification

| Investigation Angle | Finding | Status |
|---|---|:---:|
| **Data Ingestion & Integration** | All baseline + new records present (12,223 rows). | **PASS** |
| **Primary Key Uniqueness** | `transaction_id` unique across all rows. | **PASS** |
| **Transaction Grouping Key** | Grouped by `transaction_id` (single line items) instead of `customer_id`. | **FAIL (ROOT CAUSE)** |
| **Support Thresholds** | Thresholds are valid; zero baskets reached the threshold. | **PASS** |
| **Model Fallback Handling** | Overwrote artifacts with `[]` instead of retaining baseline rules. | **SECONDARY DEFECT** |

---

## 6. Recommended Minimal Correction (For Future Implementation)

In `backend/app/services/model_training_service.py` (`train_recommender`):

1. **Align Grouping Key with `recommender.py`:**
   ```python
   # Group by customer_id to construct co-purchasing baskets
   baskets_series = completed_tx.groupby("customer_id")["product_id"].unique()
   baskets = [list(b) for b in baskets_series if len(b) >= 2]
   total_baskets = max(1, len(baskets_series))
   ```

2. **Artifact Preservation Guard:**
   If `len(rules) == 0`:
   - Load baseline rules from `ml/models/association_rules.joblib` or `ml/models/product_association_rules.json`.
   - Log a non-breaking warning and retain the baseline rules for explainability.

---

## 7. Required Regression Tests

1. `test_association_rules_retained_on_retraining`:
   - Asserts `len(report["models"]["recommender"]["rules_mined"]) >= 390` when retraining on cumulative data.
2. `test_customer_basket_construction`:
   - Verifies `completed_tx.groupby("customer_id")["product_id"].unique()` generates $>1,000$ multi-item baskets.
3. `test_empty_rules_fallback`:
   - Simulates a batch where no rules are discovered and asserts that baseline rules are retained rather than overwritten with `[]`.

