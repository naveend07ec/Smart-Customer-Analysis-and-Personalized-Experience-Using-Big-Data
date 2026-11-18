"""
Update README.md with Stage 7 Supervised Customer Churn Module Details
"""

with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update directory structure
old_ml_dir = """├── ml/
│   ├── segmentation/         # K-Means clustering, Elbow method, Silhouette & PCA scripts
│   ├── recommendations/      # Hybrid collaborative filtering & association rule mining
│   └── models/               # Serialized models, cluster profiles, and precomputed recommendations"""

new_ml_dir = """├── ml/
│   ├── churn/                # Supervised Churn: dataset builder, trainer, evaluator, predictor
│   ├── segmentation/         # K-Means clustering, Elbow method, Silhouette & PCA scripts
│   ├── recommendations/      # Hybrid collaborative filtering & association rule mining
│   └── models/               # Serialized models, cluster profiles, recs, and churn artifacts
│       └── churn/            # Fitted Random Forest model, scaler, and evaluation metrics"""

if old_ml_dir in content:
    content = content.replace(old_ml_dir, new_ml_dir)

# 2. Update Quick Start
old_qs = """# Run Explainable Recommendation Engine
.\\.venv\\Scripts\\python.exe ml\\recommendations\\recommender.py"""

new_qs = """# Run Explainable Recommendation Engine
.\\.venv\\Scripts\\python.exe ml\\recommendations\\recommender.py

# Run Supervised Customer Churn Prediction Module (Stage 7)
.\\.venv\\Scripts\\python.exe ml\\churn\\build_churn_dataset.py
.\\.venv\\Scripts\\python.exe ml\\churn\\train_churn.py
.\\.venv\\Scripts\\python.exe ml\\churn\\predict_churn.py"""

if old_qs in content:
    content = content.replace(old_qs, new_qs)

# 3. Add API endpoints
old_api_anchor = "| `/api/health` | `GET` | Service health status check | `status: \"healthy\"`, `service`, `version` |"
new_api_rows = """| `/api/churn/summary` | `GET` | Churn model evaluation metrics, risk tiers, and cutoff metadata | `total_customers_evaluated`, `risk_distribution`, `evaluation_metrics` (ROC-AUC, PR-AUC, F1, Confusion Matrix), `model_version` |
| `/api/churn/customers` | `GET` | Paginated customer churn predictions and risk categories | `total_records`, `customers` (`customer_id`, `cluster_name`, `churn_risk_score`, `risk_category`, `predicted_churn_class`, `suggested_retention_action`) |
| `/api/churn/customer/<id>` | `GET` | Individual customer point-in-time retention diagnostic factors | `customer_id`, `cluster_name`, `churn_risk_score`, `risk_category`, `historical_behavioural_factors`, `suggested_retention_action` |
| `/api/health` | `GET` | Service health status check | `status: \"healthy\"`, `service`, `version` |"""

if old_api_anchor in content:
    content = content.replace(old_api_anchor, new_api_rows)

# 4. Update Dashboard Pages list
old_p6 = "6. **Data Integration & Spark** (`/pipeline`): Detailed PySpark execution audit"
new_p6 = """6. **Customer Retention & Churn AI** (`/churn`): Supervised 90-day churn forecast, risk tier distributions (Low: 57.5%, Medium: 23.0%, High: 19.5%), test-set confusion matrix, feature importances, and individualized retention actions.
7. **Data Integration & Spark** (`/pipeline`): Detailed PySpark execution audit"""

if old_p6 in content:
    content = content.replace(old_p6, new_p6)

# 5. Add Dedicated Churn Section
if "## Supervised Customer Churn Prediction & Retention (Stage 7)" not in content:
    churn_section = """

---

## Supervised Customer Churn Prediction & Retention (Stage 7)

To satisfy the official Customer Retention requirement, a separate supervised machine learning module is implemented to estimate future purchase inactivity:

### 1. Point-in-Time Prediction Architecture
- **Prediction Cutoff**: `2024-10-01 00:00:00`
- **Historical Feature Window**: 180 days prior to cutoff (`2024-04-04` to `2024-10-01`).
- **Future Observation Window**: 90 days after cutoff (`2024-10-01` to `2024-12-30`).
- **Target Definition**:
  - `churn_label = 1`: Customer recorded 0 qualifying completed purchases during the next 90 days.
  - `churn_label = 0`: Customer made >= 1 qualifying completed purchases during the next 90 days.
- **Eligible Cohort**: 1,177 customers who established an active purchase history prior to the cutoff date.
- **Class Distribution**: 870 Retained (Class 0: 73.9%), 307 Churned (Class 1: 26.1%).

### 2. Historical Feature Engineering (Zero Future Leakage)
All 16 predictors are extracted strictly from transactions, clickstreams, and social media reviews occurring before `2024-10-01`:
1. `recency_days_at_cutoff`: Days since last completed purchase prior to cutoff.
2. `hist_completed_orders`, `hist_total_orders`, `hist_total_spend`, `hist_avg_order_value`, `hist_cancellation_rate` (180-day transactional RFM).
3. `hist_web_touchpoints`, `hist_distinct_sessions`, `hist_avg_dwell_time`, `hist_product_views`, `hist_cart_additions`, `hist_checkout_starts`, `hist_cart_abandon_ratio` (180-day web clickstream).
4. `hist_social_interactions`, `hist_avg_sentiment`, `hist_avg_engagement` (180-day social feedback).

### 3. Model Comparison & Test-Set Evaluation (20% Stratified Holdout)
Models were evaluated on 236 unseen test customers against a Majority-Class baseline:

| Model | ROC-AUC | PR-AUC | Precision | Recall | F1-Score | Confusion Matrix (TN, FP, FN, TP) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Majority Class Baseline** | 0.5000 | 0.2627 | 0.0000 | 0.0000 | 0.0000 | `[174, 0, 62, 0]` |
| **Logistic Regression (Scaled)** | 0.9159 | 0.8207 | 0.6129 | 0.9194 | 0.7355 | `[138, 36, 5, 57]` |
| **Random Forest (Selected)** | **0.9365** | **0.8660** | **0.6154** | **0.9032** | **0.7320** | `[139, 35, 6, 56]` |

*Key Findings*: Random Forest achieved the highest area under the precision-recall curve (`PR-AUC = 0.8660`) and detected >90% of actual churners (Recall: 90.32%). Top predictive features identified: `hist_distinct_sessions` (18.16%), `hist_web_touchpoints` (16.02%), `hist_product_views` (10.98%), `hist_avg_engagement` (10.73%), and `hist_avg_sentiment` (10.46%).

### 4. Documented Risk Tiers & Retention Playbooks
Predictions are categorized into 3 actionable tiers:
- **Low Risk (Score < 35.0)**: 677 customers (57.5%) — Continue standard recommendations and loyalty reinforcement.
- **Medium Risk (35.0 <= Score < 65.0)**: 271 customers (23.0%) — Target re-engagement campaigns and monitor clickstream dwell time.
- **High Risk (Score >= 65.0)**: 229 customers (19.5%) — Deliver personalized win-back offers and audit cancellation causes.

*Academic Disclaimer*: Model risk scores are uncalibrated ensemble rankings suitable for research prioritization rather than real-world commercial probabilities.
"""
    content += churn_section

with open("README.md", "w", encoding="utf-8") as f:
    f.write(content)

print("README.md updated with Stage 7 details.")

