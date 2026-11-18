# SMART Project — Association Rule Regression Remediation Report

**Date:** 2026-11-17  
**Candidate Version Verified:** `v_batch_20261117_121700_7dcf`  
**Status:** Remediated, Isolated, and Verified (Candidate Not Promoted)

---

## 1. Executive Summary

Following the read-only audit in `docs/ASSOCIATION_RULE_REGRESSION_AUDIT.md`, a minimal, controlled remediation was implemented to resolve the association-rule regression where candidate retraining yielded 0 rules instead of the expected 394 rules.

### Core Remediation Highlights
1. **Fix A (Basket Construction):** Replaced line-item (`transaction_id`) grouping in `ModelTrainingService.train_recommender` with shared production customer-level basket grouping (`mine_association_rules` from `ml.recommendations.recommender`).
2. **Fix B (Artifact Safety & Fallback):** Added guardrails so that if a batch fails to meet minimum support/lift thresholds, baseline rules are retained for explainability rather than overwritten with an empty list (`[]`). Also added atomic temporary writes (`.tmp` $\rightarrow$ `os.replace`) to prevent file corruption.
3. **Fix C (Version Isolation):** All candidate artifacts remain strictly isolated under `ml/models/versions/<version_id>/`. Baseline models in `ml/models/` remained completely untouched with unchanged SHA-256 hashes. Active version pointer remains `baseline`.
4. **Validation:** All 10 mandatory regression test scenarios passed (10/10), existing backend tests passed (30/30), and frontend built cleanly in 6.68s.

---

## 2. Root Cause Summary

In the SMART canonical e-commerce schema, transactions represent individual purchased line items (`transaction_id` is unique per row).
- **Original Production Recommender (`ml/recommendations/recommender.py`):** Constructed customer baskets across completed transactions using `customer_id` grouping:
  ```python
  baskets = completed_tx_df.groupby("customer_id")["product_id"].unique()
  ```
  This captured multi-item co-occurrence across orders (1,128 multi-item customer baskets), discovering **394 association rules**.
- **Retraining Service (`backend/app/services/model_training_service.py`):** Grouped by `transaction_id`:
  ```python
  basket_df = completed_tx.groupby("transaction_id")["product_id"].apply(lambda p: list(set(p))).reset_index()
  ```
  Because every transaction row had only 1 product, 100% of baskets had length 1, and filtering for `len(b) >= 2` removed all 12,223 transactions, resulting in **0 rules mined**.

---

## 3. Exact Code Changes

### File: `backend/app/services/model_training_service.py`

#### A. Import Shared Basket Construction Helper
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from ml.recommendations.recommender import mine_association_rules
```

#### B. Customer Basket Construction & Safe Fallback
```python
        # Apriori Association Rules (from completed transactions grouped by customer_id)
        valid_completed_tx = completed_tx[
            completed_tx["customer_id"].notna() &
            completed_tx["product_id"].notna() &
            (completed_tx["product_id"].astype(str).str.strip() != "")
        ].copy()

        # Shared basket construction helper with exact baseline semantics (min_support=0.01, min_lift=1.05)
        mined_rules_df = mine_association_rules(valid_completed_tx, min_support=0.01, min_lift=1.05)

        rules = []
        rules_source = "MINED"
        rules_status = "MINED_SUCCESSFULLY"
        rules_note = f"Discovered {len(mined_rules_df) if mined_rules_df is not None else 0} association rules using customer-level co-purchasing baskets."

        if mined_rules_df is not None and not mined_rules_df.empty:
            for _, r in mined_rules_df.iterrows():
                ant = str(r["antecedent_id"])
                conq = str(r["consequent_id"])
                sup = float(r["support"])
                conf = float(r["confidence"])
                lift = float(r["lift"])
                rules.append({
                    "antecedent": ant,
                    "consequent": conq,
                    "antecedent_id": ant,
                    "consequent_id": conq,
                    "support": round(sup, 4),
                    "confidence": round(conf, 4),
                    "lift": round(lift, 3)
                })
        else:
            # Fallback: Load baseline association rules to preserve valid recommendation explainability
            rules_source = "RETAINED_BASELINE"
            rules_status = "RETAINED_BASELINE_FALLBACK"
            rules_note = "No association rules met minimum support/lift thresholds; safely retained baseline association rules."
            base_rules_path = os.path.join(self.baseline_models_dir, "product_association_rules.json")
            if os.path.exists(base_rules_path):
                try:
                    with open(base_rules_path, "r", encoding="utf-8") as f:
                        rules = json.load(f)
                except Exception:
                    rules = []
```

#### C. Atomic File Writing & Version Isolation
```python
        # Save artifacts strictly in candidate version directory (ml/models/versions/<version_id>/)
        # Using atomic temporary writes to prevent partial file corruption
        version_models_dir = os.path.join(self.models_versions_dir, version_id)
        version_data_dir = os.path.join(self.versions_dir, version_id)
        os.makedirs(version_models_dir, exist_ok=True)

        if mined_rules_df is not None and not mined_rules_df.empty:
            rules_df_to_save = mined_rules_df
        elif rules:
            rules_df_to_save = pd.DataFrame(rules)
        else:
            rules_df_to_save = pd.DataFrame(columns=["antecedent_id", "consequent_id", "support", "confidence", "lift"])

        def _atomic_dump_joblib(obj, target_path):
            tmp_path = f"{target_path}.tmp"
            joblib.dump(obj, tmp_path)
            os.replace(tmp_path, target_path)

        def _atomic_dump_json(obj, target_path):
            tmp_path = f"{target_path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(obj, f, indent=2)
            os.replace(tmp_path, target_path)

        _atomic_dump_joblib(sim_df, os.path.join(version_models_dir, "item_similarity_matrix.joblib"))
        _atomic_dump_joblib(prod_meta, os.path.join(version_models_dir, "product_metadata.joblib"))
        _atomic_dump_joblib(rules_df_to_save, os.path.join(version_models_dir, "association_rules.joblib"))
        _atomic_dump_json(customer_recommendations, os.path.join(version_models_dir, "customer_recommendations.json"))
        _atomic_dump_json(rules, os.path.join(version_models_dir, "product_association_rules.json"))
```

#### D. Comparison Report Metric Tracking
```python
                    {
                        "model": "Recommendation Engine",
                        "metric": "Association Rules Mined",
                        "baseline": 394,
                        "new_batch": rec_res.get("rules_mined", 0),
                        "difference": rec_res.get("rules_mined", 0) - 394,
                        "status": rec_res.get("rules_status", "COMPLETED")
                    },
```

---

## 4. Before & After Rule Counts

| Version | Customers | Total Transactions | Completed Transactions | Association Rules Mined | Status |
|---|:---:|:---:|:---:|:---:|:---:|
| **Baseline (`baseline`)** | 1,200 | 12,214 | 11,673 | **394** | Production Active |
| **Candidate Before Fix** | 1,203 | 12,223 | 11,681 | **0** | `REGRESSION` |
| **Candidate After Fix** | 1,203 | 12,223 | 11,681 | **394** | `MINED_SUCCESSFULLY` |

---

## 5. Baseline Hash Verification (Preservation Proof)

All production baseline files in `ml/models/` remain 100% untouched:

| File | SHA-256 Hash | Verification Status |
|---|---|:---:|
| `association_rules.joblib` | `d903ceb71c8ce255862068f787e67b11a2cee2b0cf8f3d4a1e79a1980f20f718` | **MATCH (UNTOUCHED)** |
| `product_association_rules.json` | `0e308072e55f5a8e4570d5272c7c956ec1553ca26d591861a061d482d4fab939` | **MATCH (UNTOUCHED)** |
| `customer_recommendations.json` | `8d585e0a8c0b4416e29e811dcece0ba662f352354b5d70654ad17caccf3ab2ef` | **MATCH (UNTOUCHED)** |
| `item_similarity_matrix.joblib` | `d8266d01d07bb227353f793c5142c352c52d26b429f6055d05defe8d707602e6` | **MATCH (UNTOUCHED)** |
| `product_metadata.joblib` | `ffaa9b37353bd3ef92b968d431aa1921076a3d2b378e5811b8812685f4ae76f3` | **MATCH (UNTOUCHED)** |
| `kmeans_model.joblib` | `560bbf6d2e33da1ab03f882f0251319ab188af1beea603d35d24388087c09e51` | **MATCH (UNTOUCHED)** |
| `scaler.joblib` | `ebc565252836329cf33db3533a4320631143520df12e611b84ff07269ea91814` | **MATCH (UNTOUCHED)** |
| `model_evaluation_report.json` | `25f515ce070ea58727b52bde417791114fb4d68e2f126fe1ea6b3216d5a90437` | **MATCH (UNTOUCHED)** |

---

## 6. Candidate Model Artifact Paths (Isolated)

Candidate artifacts for `v_batch_20261117_121700_7dcf` reside strictly under:
- `ml/models/versions/v_batch_20261117_121700_7dcf/`
  - `association_rules.joblib` (15,659 bytes — 394 rules DataFrame)
  - `product_association_rules.json` (83,015 bytes — 394 rules JSON)
  - `customer_recommendations.json` (1,942,493 bytes — 1,203 customers)
  - `item_similarity_matrix.joblib` (9,905 bytes)
  - `product_metadata.joblib` (3,321 bytes)
  - `model_evaluation_report.json` (1,401 bytes)
  - `evaluation_metrics.json` (685 bytes)

---

## 7. Test Results

### Remediation Test Suite (`tests/test_association_rules_remediation.py`)
- **10 passed in 23.59s (100% Pass Rate)**:
  1. `test_01_customer_level_basket_construction` &rarr; **PASSED**
  2. `test_02_multiple_line_items_for_one_customer` &rarr; **PASSED**
  3. `test_03_exclusion_of_invalid_product_ids` &rarr; **PASSED**
  4. `test_04_support_and_lift_calculation` &rarr; **PASSED**
  5. `test_05_cumulative_candidate_discovers_expected_rules` (394 rules asserted) &rarr; **PASSED**
  6. `test_06_empty_rule_generation_fallback` &rarr; **PASSED**
  7. `test_07_candidate_training_does_not_overwrite_baseline` (SHA-256 match) &rarr; **PASSED**
  8. `test_08_candidate_artifacts_are_version_isolated` &rarr; **PASSED**
  9. `test_09_failed_training_atomic_write_safety` (no `.tmp` pollution) &rarr; **PASSED**
  10. `test_10_recommendation_inference_continues_working` &rarr; **PASSED**

### Regression Test Suite
- `tests/test_api.py`, `tests/test_churn.py`, `tests/test_association_rules_remediation.py`: **30 passed in 25.29s (100% Pass Rate)**.
- Frontend Production Build: **built in 6.68s (0 errors)**.

---

## 8. Remaining Limitations

1. **Transaction Granularity:** Because the canonical dataset schema models orders as individual line-item transactions without an explicit `order_id` foreign key, market basket associations represent customer-level co-purchasing affinity across purchase history rather than simultaneous same-second cart checkout. This maintains 100% consistency with the baseline recommendation engine.
2. **Promotion Gating:** Candidate version `v_batch_20261117_121700_7dcf` has completed retraining and evaluation successfully, but has **not** been promoted. `data/current_version.json` remains pegged to `"baseline"`.

