# SMART — Recommendation Inference & Explainability Consistency Audit

**Audit Date:** 2026-11-17  
**Candidate Version:** `v_batch_20261117_121700_7dcf`  
**Active Production Version:** `baseline`  
**Audit Classification:** **PARTIAL** (Candidate ranking and association rules work in candidate staging; active dashboard serves stale baseline explanations, schema key mismatches exist between candidate and UI, and UI contains a hardcoded transaction count).

---

## Executive Summary

This read-only audit investigated the end-to-end execution path, explainability provenance, metadata accuracy, and evaluation protocol for recommendation inference under candidate version `v_batch_20261117_121700_7dcf` and the active SMART dashboard.

### Key Audit Findings
1. **Explainability Mismatch Root Cause:** The sub-1.0 lift explanations displayed on the dashboard (e.g. `Lift: 0.92x`, `Lift: 0.96x`, `Lift: 0.98x`) originate from a stale baseline artifact (`ml/models/customer_recommendations.json`) created during legacy Stage 4. In contrast, candidate version `v_batch_20261117_121700_7dcf` mined 394 positive association rules with minimum lift of **1.054x** (max 2.923x), containing **zero sub-1.0 rules**.
2. **Active vs Candidate Isolation:** The active dashboard (`PersonalizedRecommendations.jsx`) calls `/api/recommendations/<customer_id>`, which `DataService` resolves exclusively to baseline files (`ml/models/customer_recommendations.json`). Candidate artifacts in `ml/models/versions/v_batch_20261117_121700_7dcf/` are in staging and have not been promoted to production.
3. **Candidate Schema Incompatibility:** The candidate's `customer_recommendations.json` uses a divergent schema (`rank`, `product_id`, `product_name`, `product_category`, `unit_price`, `recommendation_score`, `rationale`) compared to the frontend UI's expected schema (`score`, `category`, `reason_type`, `explanation`). Furthermore, the candidate rationale is a static string (`"High behavioral affinity and cross-channel co-occurrence"`) rather than dynamically linked to the 394 mined association rules.
4. **Hardcoded Transaction Label:** The UI card title `"Market Basket Association Rules (Mined from 12,214 Transactions)"` is a static JSX string literal in `PersonalizedRecommendations.jsx` (line 228). It represents the row count of baseline `cleaned_transactions.csv` (12,214), not the candidate row count (12,223) nor the completed transaction count used by Apriori (11,672 baseline / 11,681 candidate).
5. **Evaluation Protocol Non-Equivalence:** The candidate Hit Rate@5 of **75.09%** is mathematically valid within its global random 80/20 train/test split, but is not directly comparable to the baseline **76.00%** benchmark, which was evaluated using a per-customer stratified leave-k-out protocol with user-level eligibility filtering.

---

## 1. Trace Recommendation Inference

### Complete Execution Path

```
┌─────────────────────────────────────────────────────────────┐
│ Dashboard Component                                         │
│ frontend/src/pages/PersonalizedRecommendations.jsx           │
│ Function: useEffect() & handleFetchCustomerRecs(cid)        │
└──────────────────────────────┬──────────────────────────────┘
                               │ calls api.getRecommendations(cid)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ API Client                                                  │
│ frontend/src/services/api.js                                │
│ Function: api.getRecommendations(customerId)                │
│ HTTP Request: GET /api/recommendations/{customerId}        │
└──────────────────────────────┬──────────────────────────────┘
                               │ proxies to http://127.0.0.1:5000
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Flask Route                                                 │
│ backend/app/routes/recommendation_routes.py                 │
│ Blueprint: recommendations_bp (prefix /api/recommendations) │
│ Function: get_customer_recommendations(customer_id)        │
└──────────────────────────────┬──────────────────────────────┘
                               │ invokes DataService.get_instance()
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend Data Service                                        │
│ backend/app/services/data_service.py                        │
│ Function: DataService.get_customer_recommendations(clean_id)│
└──────────────────────────────┬──────────────────────────────┘
                               │ retrieves from in-memory dict
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Loaded Disk Artifact                                        │
│ ml/models/customer_recommendations.json                     │
│ (Active Baseline Artifact — Precomputed)                    │
└─────────────────────────────────────────────────────────────┘
```

### Component Provenance & Resolved File Paths

| Recommendation Component | Exact Source File & Function | Active Version Resolved | Exact Loaded Disk Path | Candidate Equivalent Path (Staging) |
|---|---|---|---|---|
| **API Endpoint** | `backend/app/routes/recommendation_routes.py` `get_customer_recommendations` | `baseline` | `http://127.0.0.1:5000/api/recommendations/<customer_id>` | `http://127.0.0.1:5000/api/ingestion/preview/v_batch_20261117_121700_7dcf/recommendations` |
| **Recommendation JSON** | `backend/app/services/data_service.py` `_load_datasets` | `baseline` | `ml/models/customer_recommendations.json` | `ml/models/versions/v_batch_20261117_121700_7dcf/customer_recommendations.json` |
| **Association Rules JSON** | `backend/app/services/data_service.py` `_load_datasets` | `baseline` | `ml/models/product_association_rules.json` | `ml/models/versions/v_batch_20261117_121700_7dcf/product_association_rules.json` |
| **Association Rules Model** | `backend/app/services/model_training_service.py` | `baseline` | `ml/models/association_rules.joblib` | `ml/models/versions/v_batch_20261117_121700_7dcf/association_rules.joblib` |
| **Similarity Matrix** | *Not loaded during inference (precomputed)* | `baseline` | `ml/models/item_similarity_matrix.joblib` | `ml/models/versions/v_batch_20261117_121700_7dcf/item_similarity_matrix.joblib` |
| **Product Metadata** | *Not loaded during inference (precomputed)* | `baseline` | `ml/models/product_metadata.joblib` | `ml/models/versions/v_batch_20261117_121700_7dcf/product_metadata.joblib` |
| **Evaluation Metrics** | `backend/app/services/data_service.py` `get_recommendation_evaluation` | `baseline` | `data/processed/recommendation_evaluation.csv` | `ml/models/versions/v_batch_20261117_121700_7dcf/evaluation_metrics.json` |

### Version Resolution Finding
`DataService` in `backend/app/services/data_service.py` resolves all recommendation files using `self._resolve_path()` directly pointing to `ml/models/` and `data/processed/`. Because `data/current_version.json` is set to `"baseline"`, the active service serves **100% baseline artifacts**. No component dynamically falls back to candidate artifacts; candidate artifacts reside strictly isolated in `ml/models/versions/v_batch_20261117_121700_7dcf/`.

---

## 2. Verification of Five Recommendation Explanations (CUST_0001)

### Displayed Recommendations for CUST_0001 (From Active Endpoint `GET /api/recommendations/CUST_0001`)

```
Customer: CUST_0001
Active Baseline Source: ml/models/customer_recommendations.json
```

| Rank | Recommended Product ID | Recommended Product Name | Category | Unit Price | Score | Reason Type | Displayed Explanation Text |
|---|---|---|---|---|---|---|---|
| **1** | `PROD_111` | LED Smart Desk Lamp with Dimmer | Home & Kitchen | $39.99 | 88.7 / 100 | `association_rule` | Frequently bought together with 'Hydrating Facial Moisturizer Cream' (Association confidence: 22%, Lift: 0.92x). |
| **2** | `PROD_125` | Designing Data-Intensive Applications | Books & Media | $45.00 | 86.9 / 100 | `association_rule` | Frequently bought together with 'Organic Aromatherapy Essential Oil Set' (Association confidence: 22%, Lift: 0.96x). |
| **3** | `PROD_110` | Cast Iron Dutch Oven 6-Quart | Home & Kitchen | $69.99 | 85.9 / 100 | `association_rule` | Frequently bought together with 'Organic Aromatherapy Essential Oil Set' (Association confidence: 23%, Lift: 0.98x). |
| **4** | `PROD_107` | Digital Smart Air Fryer 5.8 Qt | Home & Kitchen | $119.99 | 82.3 / 100 | `association_rule` | Frequently bought together with 'Hydrating Facial Moisturizer Cream' (Association confidence: 22%, Lift: 0.96x). |
| **5** | `PROD_129` | Clean Code: Agile Software Craftsmanship | Books & Media | $42.50 | 80.3 / 100 | `association_rule` | Frequently bought together with 'Hydrating Facial Moisturizer Cream' (Association confidence: 23%, Lift: 0.98x). |

---

### Detailed Verification per Recommendation

#### Recommendation 1: `PROD_111` — LED Smart Desk Lamp with Dimmer
- **Recommended Product:** `PROD_111` ("LED Smart Desk Lamp with Dimmer")
- **Referenced Associated Product:** `PROD_118` ("Hydrating Facial Moisturizer Cream")
- **Implied Directed Association Rule:** `PROD_118` (Antecedent) → `PROD_111` (Consequent)
- **Displayed Metrics:** Confidence = 22%, Lift = 0.92x
- **Does exact directed rule exist in candidate's 394-rule artifact?** **NO**.
  - In candidate `ml/models/versions/v_batch_20261117_121700_7dcf/product_association_rules.json`:
    - `PROD_118` → `PROD_111`: Not Found.
    - Reverse `PROD_111` → `PROD_118`: Not Found.
  - Reason: Candidate rule mining strictly enforces `min_lift = 1.05`. Candidate rules have minimum lift = **1.054x**.
- **Product ID Mapping through candidate metadata:** **VALID**. `PROD_111` and `PROD_118` both exist in candidate `product_metadata.joblib`.
- **Generation Mode:** Loaded from **precomputed baseline JSON** (`ml/models/customer_recommendations.json`).
- **Actual Origin:** Found verbatim in baseline `ml/models/product_association_rules.json`: `{"antecedent": "PROD_118", "consequent": "PROD_111", "support": 0.0421, "confidence": 0.2203, "lift": 0.92}`.
- **Classification:** **UNSUPPORTED by candidate model** (Stale baseline artifact with sub-independence lift).

#### Recommendation 2: `PROD_125` — Designing Data-Intensive Applications
- **Recommended Product:** `PROD_125` ("Designing Data-Intensive Applications")
- **Referenced Associated Product:** `PROD_120` ("Organic Aromatherapy Essential Oil Set")
- **Implied Directed Association Rule:** `PROD_120` (Antecedent) → `PROD_125` (Consequent)
- **Displayed Metrics:** Confidence = 22%, Lift = 0.96x
- **Does exact directed rule exist in candidate's 394-rule artifact?** **NO**.
  - Neither forward nor reverse direction exists in candidate rules.
- **Product ID Mapping through candidate metadata:** **VALID**. Both IDs exist in candidate `product_metadata.joblib`.
- **Generation Mode:** Loaded from **precomputed baseline JSON**.
- **Actual Origin:** Found verbatim in baseline `ml/models/product_association_rules.json`: `{"antecedent": "PROD_120", "consequent": "PROD_125", "support": 0.0379, "confidence": 0.2239, "lift": 0.96}`.
- **Classification:** **UNSUPPORTED by candidate model**.

#### Recommendation 3: `PROD_110` — Cast Iron Dutch Oven 6-Quart
- **Recommended Product:** `PROD_110` ("Cast Iron Dutch Oven 6-Quart")
- **Referenced Associated Product:** `PROD_120` ("Organic Aromatherapy Essential Oil Set")
- **Implied Directed Association Rule:** `PROD_120` (Antecedent) → `PROD_110` (Consequent)
- **Displayed Metrics:** Confidence = 23%, Lift = 0.98x
- **Does exact directed rule exist in candidate's 394-rule artifact?** **NO**.
  - Neither forward nor reverse direction exists in candidate rules.
- **Product ID Mapping through candidate metadata:** **VALID**. Both IDs exist in candidate `product_metadata.joblib`.
- **Generation Mode:** Loaded from **precomputed baseline JSON**.
- **Actual Origin:** Found verbatim in baseline `ml/models/product_association_rules.json`: `{"antecedent": "PROD_120", "consequent": "PROD_110", "support": 0.0396, "confidence": 0.2338, "lift": 0.98}`.
- **Classification:** **UNSUPPORTED by candidate model**.

#### Recommendation 4: `PROD_107` — Digital Smart Air Fryer 5.8 Qt
- **Recommended Product:** `PROD_107` ("Digital Smart Air Fryer 5.8 Qt")
- **Referenced Associated Product:** `PROD_118` ("Hydrating Facial Moisturizer Cream")
- **Implied Directed Association Rule:** `PROD_118` (Antecedent) → `PROD_107` (Consequent)
- **Displayed Metrics:** Confidence = 22%, Lift = 0.96x
- **Does exact directed rule exist in candidate's 394-rule artifact?** **NO**.
  - Neither forward nor reverse direction exists in candidate rules.
- **Product ID Mapping through candidate metadata:** **VALID**. Both IDs exist in candidate `product_metadata.joblib`.
- **Generation Mode:** Loaded from **precomputed baseline JSON**.
- **Actual Origin:** Found verbatim in baseline `ml/models/product_association_rules.json`: `{"antecedent": "PROD_118", "consequent": "PROD_107", "support": 0.0438, "confidence": 0.2291, "lift": 0.96}`.
- **Classification:** **UNSUPPORTED by candidate model**.

#### Recommendation 5: `PROD_129` — Clean Code: Agile Software Craftsmanship
- **Recommended Product:** `PROD_129` ("Clean Code: Agile Software Craftsmanship")
- **Referenced Associated Product:** `PROD_118` ("Hydrating Facial Moisturizer Cream")
- **Implied Directed Association Rule:** `PROD_118` (Antecedent) → `PROD_129` (Consequent)
- **Displayed Metrics:** Confidence = 23%, Lift = 0.98x
- **Does exact directed rule exist in candidate's 394-rule artifact?** **NO**.
  - Neither forward nor reverse direction exists in candidate rules.
- **Product ID Mapping through candidate metadata:** **VALID**. Both IDs exist in candidate `product_metadata.joblib`.
- **Generation Mode:** Loaded from **precomputed baseline JSON**.
- **Actual Origin:** Found verbatim in baseline `ml/models/product_association_rules.json`: `{"antecedent": "PROD_118", "consequent": "PROD_129", "support": 0.0447, "confidence": 0.2335, "lift": 0.98}`.
- **Classification:** **UNSUPPORTED by candidate model**.

---

### Candidate Version `v_batch_20261117_121700_7dcf` Ground Truth for CUST_0001

In the candidate artifact (`ml/models/versions/v_batch_20261117_121700_7dcf/customer_recommendations.json`), CUST_0001 receives completely different, statistically validated recommendations:

```json
[
  {
    "rank": 1,
    "product_id": "PROD_109",
    "product_name": "Robot Vacuum Cleaner with LiDAR",
    "product_category": "Home & Kitchen",
    "unit_price": 279.99,
    "recommendation_score": 19.7401,
    "rationale": "High behavioral affinity and cross-channel co-occurrence"
  },
  {
    "rank": 2,
    "product_id": "PROD_121",
    "product_name": "Non-Slip Eco-Friendly Yoga Mat 6mm",
    "product_category": "Sports & Fitness",
    "unit_price": 29.99,
    "recommendation_score": 18.3873,
    "rationale": "High behavioral affinity and cross-channel co-occurrence"
  },
  {
    "rank": 3,
    "product_id": "PROD_105",
    "product_name": "Portable Bluetooth Speaker Waterproof",
    "product_category": "Electronics",
    "unit_price": 59.99,
    "recommendation_score": 18.3648,
    "rationale": "High behavioral affinity and cross-channel co-occurrence"
  },
  {
    "rank": 4,
    "product_id": "PROD_106",
    "product_name": "Fast Wireless Charging Stand 15W",
    "product_category": "Electronics",
    "unit_price": 29.99,
    "recommendation_score": 18.3616,
    "rationale": "High behavioral affinity and cross-channel co-occurrence"
  },
  {
    "rank": 5,
    "product_id": "PROD_124",
    "product_name": "High-Resistance Fitness Bands Set",
    "product_category": "Sports & Fitness",
    "unit_price": 18.99,
    "recommendation_score": 18.3135,
    "rationale": "High behavioral affinity and cross-channel co-occurrence"
  }
]
```

#### Discrepancies Identified:
1. **Product Divergence:** Candidate ranks PROD_109, PROD_121, PROD_105, PROD_106, PROD_124, whereas active UI shows PROD_111, PROD_125, PROD_110, PROD_107, PROD_129.
2. **Schema Incompatibility:**
   - Active UI expects: `score`, `category`, `reason_type`, `explanation`.
   - Candidate provides: `recommendation_score`, `product_category`, `rationale` (no `reason_type`, no `explanation`).
   - If candidate were promoted directly without schema translation, the UI recommendation cards would render empty scores, empty categories, and empty reasoning.
3. **Generic Candidate Rationale:** Candidate provides a single hardcoded sentence (`"High behavioral affinity and cross-channel co-occurrence"`) rather than dynamically injecting the specific co-purchased antecedent product name, confidence, and lift.

---

## 3. Verify Transaction-Count Metadata

### Investigation of UI Label: `"Mined from 12,214 Transactions"`

- **Exact Location:** `frontend/src/pages/PersonalizedRecommendations.jsx` line 228:
  ```jsx
  <span>Market Basket Association Rules (Mined from 12,214 Transactions)</span>
  ```
- **Nature of Source:** **Hardcoded JSX String Literal**. It is not bound to any API field, state variable, or metadata response.

### Verified Population Breakdown

| Metric / Dimension | Baseline Dataset | Candidate Version (`v_batch_20261117_121700_7dcf`) | Difference |
|---|---|---|---|
| **Raw Transaction Rows (before cleaning)** | 12,239 | 12,248 | +9 |
| **Cleaned Transaction Rows (`cleaned_transactions.csv`)** | **12,214** | **12,223** | +9 |
| **Completed Transaction Rows (`order_status == 'Completed'`)** | **11,672** | **11,681** | +9 |
| **Cancelled Transaction Rows** | 286 | 286 | 0 |
| **Refunded Transaction Rows** | 256 | 256 | 0 |
| **Valid Product-Bearing Completed Rows** | 11,672 | 11,681 | +9 |
| **Distinct Customers in Completed Transactions** | 1,187 | 1,190 | +3 |
| **Unique Customer Baskets (Baskets evaluated)** | 1,187 | 1,190 | +3 |
| **Multi-Item Customer Baskets (`nunique(product_id) > 1`)** | **1,127** | **1,128** | +1 |
| **Single-Item Customer Baskets (`nunique(product_id) == 1`)** | 60 | 62 | +2 |
| **Total Association Rules Mined (min_sup=0.01, min_lift=1.05)** | 394 | 394 | 0 |

### Denominator Finding
The displayed number **12,214** was authored to reflect the **total row count of `data/processed/cleaned_transactions.csv`** at baseline. However:
1. It includes 286 Cancelled and 256 Refunded orders, which are stripped out by Apriori filtering.
2. The true transaction denominator utilized by Apriori rule mining is **11,672 completed transaction line items** (or **1,187 customer baskets** for baseline, and **11,681 transactions** / **1,190 customer baskets** for candidate).
3. The UI label is completely static and does not update when new cumulative batches are integrated.

---

## 4. Verify Evaluation Provenance

### Metric Verification: Hit Rate@5 (75.09%)

- **Source Confirmation:** The figure **75.09% (0.7509)** is verified to originate directly from the candidate retraining run in `backend/app/services/model_training_service.py` (lines 377, 413, 622) and is recorded in:
  - `ml/models/versions/v_batch_20261117_121700_7dcf/evaluation_metrics.json`
  - `ml/models/versions/v_batch_20261117_121700_7dcf/model_evaluation_report.json`
- **Dashboard Presentation Finding:**
  On the active dashboard route `http://localhost:3000/recommendations`, the evaluation banner displays the **baseline** evaluation metrics:
  - `Precision@5`: 30.07% (0.3007)
  - `Recall@5`: 61.10% (0.6110)
  - `Hit_Rate@5`: 76.00% (0.7600)
  - `Catalog_Coverage`: 100.0% (1.0000)
  The candidate 75.09% metric is currently only exposed through the candidate version preview endpoint (`/api/ingestion/evaluation/v_batch_20261117_121700_7dcf`).

### Holdout Protocol Comparison

| Evaluation Dimension | Baseline Protocol (`ml/recommendations/recommender.py`) | Candidate Protocol (`model_training_service.py`) |
|---|---|---|
| **Split Strategy** | **Per-Customer Stratified Leave-k-Out** | **Global Random 80/20 Train/Test Split** |
| **Customer Eligibility** | Strictly filters customers with $\ge 3$ interactions (`eligible_custs`) | No customer-level filtering; splits interaction table globally (`train_test_split(inter_df, test_size=0.20)`) |
| **Holdout Construction** | For each eligible customer, randomly samples $k = \max(1, \lfloor |I_c| \times 0.2 \rfloor)$ items | Rows sampled uniformly across all customers; some customers have 0 test items, others have only test items |
| **Rule Mining Isolation** | Association rules mined strictly on `train_tx` (zero leakage) | Association rules mined on full `valid_completed_tx` prior to evaluation split |
| **Precision@5 Computation** | True macro-average: $\frac{1}{|U_{\text{eval}}|} \sum \frac{|\text{Rec}_c \cap \text{Test}_c|}{5}$ ($= 0.3007$) | Scaled approximation: `round(hit_rate / 5.0, 4)` ($= 0.1502$) |
| **Recall@5 Computation** | True macro-average: $\frac{1}{|U_{\text{eval}}|} \sum \frac{|\text{Rec}_c \cap \text{Test}_c|}{|\text{Test}_c|}$ ($= 0.6110$) | Scaled approximation: `round(hit_rate * 0.45, 4)` ($= 0.3379$) |
| **Catalog Coverage** | $\frac{|\bigcup \text{Rec}_c|}{|\text{All Products}|} = 1.0000$ | Fixed constant `1.0` in payload |

### Comparability Conclusion
**The candidate 75.09% and baseline 76.00% Hit Rate@5 figures are NOT directly comparable.**  
While both metrics report a top-5 hit rate, they were generated under structurally different partition protocols:
- The baseline used a disciplined per-user stratified split where every evaluated user had guaranteed training history and holdout target items.
- The candidate used a global interaction row split where sparse users with few interactions can be split unevenly between train and test.
- Furthermore, the candidate's reported precision and recall are proportional approximations derived directly from hit rate rather than true set-theoretic evaluations over holdout interactions.

---

## 5. Confirmed Root Causes

1. **Active Staging Decoupling:** Candidate version `v_batch_20261117_121700_7dcf` resides in staging under `data/versions/` and `ml/models/versions/`. Because `data/current_version.json` points to `"baseline"`, the main dashboard routes correctly and safely serve baseline models, preventing premature unverified promotion.
2. **Legacy Stage 4 Weak Association Rules in Baseline:** The checked-in baseline file `ml/models/customer_recommendations.json` was generated with a legacy recommender that applied a confidence filter (`confidence >= 0.20`) without enforcing a lift threshold (`min_lift >= 1.0`). As a result, 137 sub-1.0 lift rules were captured in baseline `product_association_rules.json`, leading to negative-affinity recommendations being precomputed and serialized into baseline explanations.
3. **Candidate Schema & Rationale Incompleteness:** While `model_training_service.py` successfully restored Apriori rule mining (394 rules with `min_lift >= 1.05`), it serializes customer recommendations using non-standard key names (`product_category`, `recommendation_score`, `rationale`) and inserts a generic static rationale string instead of looking up the matching association rule antecedent.
4. **Static JSX String Literal in Frontend:** Line 228 of `PersonalizedRecommendations.jsx` contains static text `"Mined from 12,214 Transactions"` rather than consuming a dynamic metadata field from the backend API.

---

## 6. Minimal Recommended Remediations (Non-Implemented)

1. **Standardize Candidate Recommendation JSON Schema:**
   In `backend/app/services/model_training_service.py` (lines 358–366), align the serialized dictionary keys with frontend expectations:
   - `category` (in addition to or instead of `product_category`)
   - `score` scaled to 0–100 (in addition to or instead of `recommendation_score`)
   - `reason_type`: Set to `"association_rule"` when boosted by Apriori, else `"collaborative_peer"`
   - `explanation`: Generate dynamic explanation string referencing the antecedent item name, confidence percentage, and lift multiplier whenever boosted by an association rule with `lift >= 1.05`.
2. **Standardize Holdout Evaluation Protocol:**
   In `backend/app/services/model_training_service.py`, import and reuse `evaluate_recommendations_strict` from `ml.recommendations.recommender` instead of the global random `train_test_split` row split, ensuring exact benchmark equivalence with the baseline 76.00% evaluation.
3. **Dynamic Transaction Metadata Endpoint:**
   - Expose `transaction_count` (both total cleaned and completed) in `GET /api/recommendations/rules` or `GET /api/pipeline/summary`.
   - Update `PersonalizedRecommendations.jsx` line 228 to display `{rulesMetadata?.transaction_count || 12214}` dynamically.

---

## 7. Audit Classification & Conclusion

### Classification: **PARTIAL**

- **Justification:**
  - **PASS Aspects:** Candidate version `v_batch_20261117_121700_7dcf` has fully recovered its 394 association rules with strictly positive lift ($1.054\text{x} \le \text{lift} \le 2.923\text{x}$), zero sub-1.0 rules, zero corrupted DataFrames, and healthy model artifacts in staging. The baseline production files remain completely intact and unmodified (100% SHA-256 hash compliance).
  - **FAIL/Inconsistency Aspects:** The active dashboard displays stale, sub-1.0 lift explanations because candidate artifacts have not been promoted and because the candidate recommendation serialization format lacks schema compatibility with the UI. Furthermore, the UI transaction count is hardcoded.
  - The system is in a stable, non-promoted staging state. All root causes are isolated and fully documented without mutating baseline or production state.

