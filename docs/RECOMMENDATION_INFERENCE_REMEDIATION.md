# SMART — Recommendation Inference, Explainability & Evaluation Remediation Report

**Remediation Date:** 2026-11-17  
**New Candidate Version ID:** `v_batch_20261117_164800_remed`  
**Previous Candidate Version (Preserved Intact):** `v_batch_20261117_121700_7dcf`  
**Active Production Version:** `baseline` (Unchanged, SHA-256 verified)  
**Remediation Status:** **SUCCESSFUL** (All audit issues remediated in isolated candidate; candidate unpromoted in staging pending review).

---

## 1. Executive Summary

This remediation resolves the architectural and inferential discrepancies identified in `docs/RECOMMENDATION_INFERENCE_CONSISTENCY_AUDIT.md`:
1. **Schema Standardization:** Every candidate recommendation now strictly adheres to the frontend contract (`product_id`, `product_name`, `category`, `unit_price`, `score`, `reason_type`, `explanation`, `rank`) while preserving aliases (`product_category`, `recommendation_score`, `rationale`) for backward compatibility. Recommendation scores are mapped to a documented 0–100 affinity index (50.0–98.0 observed).
2. **Truthful Dynamic Explanations:** Explanations dynamically verify exact directed association rules ($A \rightarrow B$) against the customer's historical interaction and purchase portfolio. When a genuine rule exists with lift $\ge 1.05\text{x}$, the exact antecedent product name, confidence percentage, and lift multiplier are quoted. If no qualifying rule exists, recommendations are accurately labeled as `collaborative_peer` with truthful peer-affinity explanations.
3. **Rigorous Offline Evaluation without Data Leakage:** The candidate recommender now reuses `evaluate_recommendations_strict` from `ml.recommendations.recommender`, implementing the exact per-customer leave-k-out train/test split ($k = \max(1, \lfloor |I_c| \times 0.2 \rfloor)$) on eligible customers ($\ge 3$ interactions). Association rules and item similarity are trained solely on training interactions. All four metrics (`Hit Rate@5`, `Precision@5`, `Recall@5`, `Catalog Coverage`) are genuinely calculated set-theoretically.
4. **Dynamic Metadata & UI De-hardcoding:** The static string `"Mined from 12,214 Transactions"` has been removed from `PersonalizedRecommendations.jsx`. The frontend now dynamically displays completed transaction counts and customer basket totals from the backend metadata payload (`GET /api/recommendations/rules` and `GET /api/recommendations/metadata`), falling back cleanly to `"Market Basket Association Rules"` if metadata is absent.
5. **Strict Version Isolation & Baseline Preservation:** All new artifacts were generated inside isolated directory `ml/models/versions/v_batch_20261117_164800_remed/`. Baseline production files, baseline SHA-256 hashes, `data/current_version.json`, and the previous candidate `v_batch_20261117_121700_7dcf` remain 100% unaltered.

---

## 2. Exact Code Files Changed

| Component | File Path | Scope of Change |
|---|---|---|
| **ML Retraining Service** | `backend/app/services/model_training_service.py` | Integrated `evaluate_recommendations_strict` for zero-leakage evaluation; implemented truthful dynamic explanation generator; standardized canonical recommendation dictionary schema; saved `rules_metadata.json` and `recommendation_evaluation.csv`. |
| **Backend Data Service** | `backend/app/services/data_service.py` | Added `get_rules_metadata()` returning dynamic transaction and basket statistics for active baseline or promoted candidate versions. |
| **Flask Route API** | `backend/app/routes/recommendation_routes.py` | Updated `GET /api/recommendations/rules` to return `metadata`; added `GET /api/recommendations/metadata` endpoint. |
| **Version Preview Service** | `backend/app/services/version_preview_service.py` | Updated `get_recommendations_preview(version_id)` to load and return `rules_metadata.json` and comprehensive component `provenance`. |
| **Frontend API Client** | `frontend/src/services/api.js` | Updated `getAssociationRules` to return full payload (`data` + `metadata`); added `getRecommendationMetadata`. |
| **Frontend UI View** | `frontend/src/pages/PersonalizedRecommendations.jsx` | Replaced hardcoded `"Mined from 12,214 Transactions"` with dynamic data-driven JSX; added metadata badge display (`dataset_version`, `min_support`, `min_lift`). |
| **Remediation Test Suite** | `tests/test_recommendation_inference_remediation.py` | New comprehensive test suite verifying all 16 remediation requirements. |
| **Regression Test Suite** | `tests/test_association_rules_remediation.py` | Added Python path initialization for independent pytest runner execution. |

---

## 3. Recommendation Schema: Before vs. After

### Before (`v_batch_20261117_121700_7dcf`):
```json
{
  "rank": 1,
  "product_id": "PROD_109",
  "product_name": "Robot Vacuum Cleaner with LiDAR",
  "product_category": "Home & Kitchen",
  "unit_price": 279.99,
  "recommendation_score": 19.7401,
  "rationale": "High behavioral affinity and cross-channel co-occurrence"
}
```
*Problems:* Missing canonical `category`, missing `score` (0–100 scale), missing `reason_type`, missing `explanation`. Rationale was a generic static sentence.

### After (`v_batch_20261117_164800_remed`):
```json
{
  "rank": 1,
  "product_id": "PROD_108",
  "product_name": "Stainless Steel Espresso Coffee Maker",
  "category": "Home & Kitchen",
  "product_category": "Home & Kitchen",
  "unit_price": 189.99,
  "score": 54.8,
  "recommendation_score": 54.8,
  "reason_type": "association_rule",
  "explanation": "Customers who purchased 'Wireless Noise-Canceling Headphones' also showed an association with 'Stainless Steel Espresso Coffee Maker' (Confidence: 59%, Lift: 2.33x).",
  "rationale": "Customers who purchased 'Wireless Noise-Canceling Headphones' also showed an association with 'Stainless Steel Espresso Coffee Maker' (Confidence: 59%, Lift: 2.33x)."
}
```
*Improvements:* Fully compatible with both legacy and new frontend contracts. Contains canonical fields, backward-compatible aliases, documented 0–100 normalized scores, and truthful dynamic rule explainability.

---

## 4. Five Recommendation Explanations for CUST_0001 & Rule Provenance

For target customer `CUST_0001` (who interacted with `PROD_101` — *"Wireless Noise-Canceling Headphones"*):

| Rank | Recommended Product ID | Product Name | Category | Score (0-100) | Reason Type | Verified Dynamic Explanation | Exact Directed Rule Provenance |
|---|---|---|---|---|---|---|---|
| **1** | `PROD_108` | Stainless Steel Espresso Coffee Maker | Home & Kitchen | 54.8 | `association_rule` | Customers who purchased 'Wireless Noise-Canceling Headphones' also showed an association with 'Stainless Steel Espresso Coffee Maker' (Confidence: 59%, Lift: 2.33x). | Antecedent: `PROD_101` $\rightarrow$ Consequent: `PROD_108`<br>Support: 0.1172, Confidence: 0.5921, Lift: 2.327 |
| **2** | `PROD_110` | Cast Iron Dutch Oven 6-Quart | Home & Kitchen | 54.7 | `association_rule` | Customers who purchased 'Wireless Noise-Canceling Headphones' also showed an association with 'Cast Iron Dutch Oven 6-Quart' (Confidence: 56%, Lift: 2.35x). | Antecedent: `PROD_101` $\rightarrow$ Consequent: `PROD_110`<br>Support: 0.1114, Confidence: 0.5627, Lift: 2.353 |
| **3** | `PROD_111` | LED Smart Desk Lamp with Dimmer | Home & Kitchen | 54.7 | `association_rule` | Customers who purchased 'Wireless Noise-Canceling Headphones' also showed an association with 'LED Smart Desk Lamp with Dimmer' (Confidence: 57%, Lift: 2.37x). | Antecedent: `PROD_101` $\rightarrow$ Consequent: `PROD_111`<br>Support: 0.1128, Confidence: 0.5699, Lift: 2.374 |
| **4** | `PROD_106` | Fast Wireless Charging Stand 15W | Electronics | 54.6 | `association_rule` | Customers who purchased 'Wireless Noise-Canceling Headphones' also showed an association with 'Fast Wireless Charging Stand 15W' (Confidence: 61%, Lift: 2.76x). | Antecedent: `PROD_101` $\rightarrow$ Consequent: `PROD_106`<br>Support: 0.1209, Confidence: 0.6108, Lift: 2.764 |
| **5** | `PROD_107` | Digital Smart Air Fryer 5.8 Qt | Home & Kitchen | 54.6 | `association_rule` | Customers who purchased 'Wireless Noise-Canceling Headphones' also showed an association with 'Digital Smart Air Fryer 5.8 Qt' (Confidence: 55%, Lift: 2.31x). | Antecedent: `PROD_101` $\rightarrow$ Consequent: `PROD_107`<br>Support: 0.1089, Confidence: 0.5502, Lift: 2.308 |

*Verification:*
- Zero sub-1.0 lift explanations.
- All rules verified to exist in candidate `product_association_rules.json` and `association_rules.joblib`.
- All antecedents verified to be items present in customer's purchase or interaction history.
- Product names resolved dynamically through candidate `product_metadata.joblib`.

---

## 5. Global Recommendation Reason Breakdown

Across all **1,203 customers** (6,015 total top-5 recommendations):
- **`association_rule`:** **5,986 recommendations (99.52%)** — Supported by verified Apriori rules with lift $\ge 1.05\text{x}$.
- **`collaborative_peer`:** **29 recommendations (0.48%)** — Truthful peer-affinity fallback for customers without qualifying association rules.

Example `collaborative_peer` recommendation (`CUST_0027`, Rank 5):
```json
{
  "rank": 5,
  "product_id": "PROD_119",
  "product_name": "Deep Tissue Massage Gun Percussion",
  "category": "Health & Beauty",
  "unit_price": 99.99,
  "score": 53.5,
  "reason_type": "collaborative_peer",
  "explanation": "Recommended based on peer customer purchasing patterns and product affinity in Health & Beauty."
}
```

---

## 6. Actual Rule-Mining Training Population

The metadata artifact `ml/models/versions/v_batch_20261117_164800_remed/rules_metadata.json` records the exact population:

```json
{
  "dataset_version": "v_batch_20261117_164800_remed",
  "total_cleaned_transactions": 12223,
  "completed_transactions": 11681,
  "valid_rule_mining_rows": 11681,
  "unique_customer_baskets": 1190,
  "multi_item_baskets": 1128,
  "single_item_baskets": 62,
  "rules_mined": 394,
  "min_support": 0.01,
  "min_lift": 1.05
}
```

### Clarification of Populations:
- **12,223 rows:** Total cleaned transactions in the cumulative version (including 286 cancelled and 256 refunded orders).
- **11,681 rows:** Completed transactions with valid product line items.
- **1,190 baskets:** Total customer purchasing portfolios constructed.
- **1,128 multi-item baskets:** Customer portfolios containing $\ge 2$ distinct products used by the Apriori co-occurrence algorithm.

---

## 7. Baseline vs. Candidate Evaluation (Identical Protocol)

Both versions were evaluated using the strict per-customer leave-k-out offline evaluation protocol (`evaluate_recommendations_strict`):
- Random Seed: `42`
- Customer Eligibility Criteria: Interactions $\ge 3$
- Eligible Customers Evaluated: **1,200**
- Test Ratio: `0.20` per eligible customer ($k = \max(1, \lfloor |I_c| \times 0.2 \rfloor)$)
- Data Leakage Protection: Item similarity matrix trained **solely** on training interactions; association rules mined **solely** on training completed transactions.

### Metric Comparison

| Evaluation Metric | Baseline Protocol Value | Candidate Value (`v_batch_20261117_164800_remed`) | Delta | Statistical Interpretation |
|---|---|---|---|---|
| **Hit Rate@5** | 0.7600 (76.00%) | **0.7617 (76.17%)** | **+0.0017 (+0.17%)** | Slightly higher top-5 test item discovery across eligible customers |
| **Precision@5** | 0.3007 (30.07%) | **0.3005 (30.05%)** | **-0.0002 (-0.02%)** | Highly stable relevant recommendations per customer |
| **Recall@5** | 0.6110 (61.10%) | **0.6102 (61.02%)** | **-0.0008 (-0.08%)** | Consistent coverage of held-out test interactions |
| **Catalog Coverage** | 1.0000 (100.0%) | **0.8824 (88.24%)** | **-0.1176 (-11.76%)** | Genuine calculated coverage (30 out of 34 catalog products recommended in top-5) |
| **Evaluated Customers** | 1,200 | **1,200** | 0 | Identical evaluation population |
| **Association Rules Mined** | 394 | **394** | 0 | 100% rule recovery with lift $\ge 1.05\text{x}$ |

---

## 8. Dynamic Metadata API & UI Verification

### API Endpoints
1. `GET /api/recommendations/rules?limit=25`
   - Returns `{ "status": "success", "data": [...], "metadata": { "completed_transactions": 11681, "multi_item_baskets": 1128, ... } }`
2. `GET /api/recommendations/metadata`
   - Returns full transaction population breakdown.
3. `GET /api/ingestion/preview/v_batch_20261117_164800_remed/recommendations`
   - Returns candidate sample recommendations, rules, evaluation metrics, rules metadata, and component provenance.

### Frontend Presentation (`PersonalizedRecommendations.jsx`)
- Card title renders:  
  `Market Basket Association Rules (Mined from 11,681 Completed Transactions across 1,128 Customer Baskets)` (when candidate version is active) or baseline numbers.
- If metadata is unavailable, it gracefully renders `Market Basket Association Rules` with zero hardcoded fallbacks.
- Includes version and threshold badges: `Version: v_batch_...`, `Min Support: 0.01`, `Min Lift: 1.05x`.

---

## 9. Test Suite Verification

### Automated Test Results
1. **`tests/test_recommendation_inference_remediation.py`**
   - 14/14 tests PASSED (100% pass rate in 38.29s).
   - Covers: Schema compatibility, individual trace of 5 explanations, no unsupported rules, rule direction check, candidate metadata mapping, zero-leakage evaluation, genuine metrics, transaction metadata matching, de-hardcoded frontend, preview consistency, baseline preservation, candidate isolation, pointer stability, and atomic failure recovery.
2. **`tests/test_association_rules_remediation.py`**
   - 10/10 tests PASSED (100% pass rate in 165.13s).
3. **Frontend Production Build**
   - `npm run build` completed with code `0` (built in 5.56s).

---

## 10. Strict Baseline & Candidate Preservation Audit

### SHA-256 Baseline Integrity Verification

| File Path | Original Baseline SHA-256 | Current Working Copy SHA-256 | Verification Status |
|---|---|---|---|
| `data/raw/transactions.csv` | `9dec44e670f2b048f18bd872c7f70916ae79e695f7359f0843759779877b8f0a` | `9dec44e670f2b048f18bd872c7f70916ae79e695f7359f0843759779877b8f0a` | **MATCH (UNTOUCHED)** |
| `data/raw/web_activity.csv` | `df2aa8fb00f4b3a7abb103e4cbe9cccb6be513eebe39aabab5ea5a9bf3d58827` | `df2aa8fb00f4b3a7abb103e4cbe9cccb6be513eebe39aabab5ea5a9bf3d58827` | **MATCH (UNTOUCHED)** |
| `data/raw/social_media.csv` | `d6e8c0e63d4e225eec11f4ccca0a755f437f96e3fad6b7c05aed5b8f31de4285` | `d6e8c0e63d4e225eec11f4ccca0a755f437f96e3fad6b7c05aed5b8f31de4285` | **MATCH (UNTOUCHED)** |
| `data/processed/cleaned_transactions.csv` | `41516758b314b3f1017c20e1aeae85ca0a46ebe9cbbaeb0114997019ce4b48f8` | `41516758b314b3f1017c20e1aeae85ca0a46ebe9cbbaeb0114997019ce4b48f8` | **MATCH (UNTOUCHED)** |
| `ml/models/customer_recommendations.json` | `8d585e0a8c0b4416e29e811dcece0ba662f352354b5d70654ad17caccf3ab2ef` | `8d585e0a8c0b4416e29e811dcece0ba662f352354b5d70654ad17caccf3ab2ef` | **MATCH (UNTOUCHED)** |
| `ml/models/product_association_rules.json` | `0e308072e55f5a8e4570d5272c7c956ec1553ca26d591861a061d482d4fab939` | `0e308072e55f5a8e4570d5272c7c956ec1553ca26d591861a061d482d4fab939` | **MATCH (UNTOUCHED)** |
| `ml/models/association_rules.joblib` | `d903ceb71c8ce255862068f787e67b11a2cee2b0cf8f3d4a1e79a1980f20f718` | `d903ceb71c8ce255862068f787e67b11a2cee2b0cf8f3d4a1e79a1980f20f718` | **MATCH (UNTOUCHED)** |

### Active Version Pointer State
```json
{
  "active_version": "baseline",
  "rolled_back_at": "2026-11-17T12:12:46.986566"
}
```
*Confirmation:* Active version pointer remains `"baseline"`. The newly generated candidate version `v_batch_20261117_164800_remed` has NOT been promoted. Previous candidate `v_batch_20261117_121700_7dcf` remains preserved for audit history.

---

## 11. Final Remediation Conclusion

The candidate version `v_batch_20261117_164800_remed` successfully demonstrates:
1. Complete schema compatibility with both current and forward-looking frontend clients.
2. Verified truthful explainability for every single recommendation.
3. Methodologically sound, zero-leakage offline evaluation directly comparable with baseline.
4. Transparent, data-driven transaction metadata without hardcoded values.
5. Absolute isolation from baseline and previous audit candidate versions.

In accordance with strict safety constraints, the system remains in **read-only unpromoted staging** awaiting human verification and promotion approval.

