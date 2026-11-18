"""
Evaluate Customer Churn Prediction Models
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Generates machine-readable evaluation results and test-set reports:
- ROC-AUC, PR-AUC, Precision, Recall, F1
- Confusion Matrix
- Class distribution & Baseline comparison
- Academic limitation commentary
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    precision_score, recall_score, f1_score,
    confusion_matrix
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATASET_PATH = os.path.join(BASE_DIR, "data", "processed", "churn_dataset.parquet")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "churn", "churn_model.joblib")
SCALER_PATH = os.path.join(BASE_DIR, "ml", "models", "churn", "scaler.joblib")
OUT_JSON = os.path.join(BASE_DIR, "ml", "models", "churn", "churn_evaluation_metrics.json")
OUT_CSV = os.path.join(BASE_DIR, "data", "processed", "churn_evaluation_metrics.csv")

FEATURE_COLUMNS = [
    "recency_days_at_cutoff",
    "hist_completed_orders",
    "hist_total_orders",
    "hist_total_spend",
    "hist_avg_order_value",
    "hist_cancellation_rate",
    "hist_web_touchpoints",
    "hist_distinct_sessions",
    "hist_avg_dwell_time",
    "hist_product_views",
    "hist_cart_additions",
    "hist_checkout_starts",
    "hist_cart_abandon_ratio",
    "hist_social_interactions",
    "hist_avg_sentiment",
    "hist_avg_engagement"
]


def evaluate_models():
    print("=" * 60)
    print("Evaluating Customer Churn Prediction Models")
    print("=" * 60)

    df = pd.read_parquet(DATASET_PATH)
    rf_model = joblib.load(MODEL_PATH)

    X = df[FEATURE_COLUMNS]
    y = df["churn_label"]

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    y_prob = rf_model.predict_proba(X_test)[:, 1]
    y_pred = rf_model.predict(X_test)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    metrics = {
        "evaluation_protocol": "Holdout Test Set (20% Stratified Split)",
        "test_samples_total": len(y_test),
        "test_actual_retained_class_0": int((y_test == 0).sum()),
        "test_actual_churned_class_1": int((y_test == 1).sum()),
        "class_imbalance_ratio": f"1 : {(y_test == 0).sum() / (y_test == 1).sum():.2f} (26.3% Churn rate)",
        "models_evaluated": [
            {
                "model_name": "Random Forest Classifier (Selected)",
                "algorithm": "RandomForestClassifier(n_estimators=100, max_depth=5)",
                "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
                "pr_auc": round(float(average_precision_score(y_test, y_prob)), 4),
                "precision": round(float(precision_score(y_test, y_pred)), 4),
                "recall": round(float(recall_score(y_test, y_pred)), 4),
                "f1_score": round(float(f1_score(y_test, y_pred)), 4),
                "confusion_matrix": {
                    "true_negatives": int(tn),
                    "false_positives": int(fp),
                    "false_negatives": int(fn),
                    "true_positives": int(tp)
                }
            },
            {
                "model_name": "Majority Class Baseline",
                "algorithm": "ZeroRule (Predict Class 0)",
                "roc_auc": 0.5000,
                "pr_auc": round(float((y_test == 1).mean()), 4),
                "precision": 0.0000,
                "recall": 0.0000,
                "f1_score": 0.0000,
                "confusion_matrix": {
                    "true_negatives": int((y_test == 0).sum()),
                    "false_positives": 0,
                    "false_negatives": int((y_test == 1).sum()),
                    "true_positives": 0
                }
            }
        ],
        "top_features": [
            {"feature": k, "importance_percent": round(v * 100, 2)}
            for k, v in sorted(
                zip(FEATURE_COLUMNS, rf_model.feature_importances_),
                key=lambda x: x[1],
                reverse=True
            )[:6]
        ],
        "academic_limitations": [
            "Dataset is synthetically generated with fixed random seeds for academic reproducibility; metrics reflect synthetic statistical relationships rather than commercial e-commerce churn.",
            "Sample size is constrained to 1,200 customers (1,177 eligible) to ensure lightweight local execution on 8 GB RAM hardware.",
            "Model risk scores are uncalibrated tree ensemble probabilities, suitable for ordinal risk ranking rather than true actuarial probabilities."
        ]
    }

    # Save JSON
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Save CSV
    df_metrics = pd.DataFrame([
        {
            "model": "Random Forest",
            "roc_auc": metrics["models_evaluated"][0]["roc_auc"],
            "pr_auc": metrics["models_evaluated"][0]["pr_auc"],
            "precision": metrics["models_evaluated"][0]["precision"],
            "recall": metrics["models_evaluated"][0]["recall"],
            "f1_score": metrics["models_evaluated"][0]["f1_score"],
            "tn": tn, "fp": fp, "fn": fn, "tp": tp
        },
        {
            "model": "Majority Baseline",
            "roc_auc": 0.5000,
            "pr_auc": round(float((y_test == 1).mean()), 4),
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "tn": int((y_test == 0).sum()), "fp": 0, "fn": int((y_test == 1).sum()), "tp": 0
        }
    ])
    df_metrics.to_csv(OUT_CSV, index=False)

    print("Evaluation completed and artifacts saved:")
    print(f"  JSON: {OUT_JSON}")
    print(f"  CSV:  {OUT_CSV}")
    print(f"\nRandom Forest Test Performance: ROC-AUC={metrics['models_evaluated'][0]['roc_auc']}, Recall={metrics['models_evaluated'][0]['recall']}, Precision={metrics['models_evaluated'][0]['precision']}, F1={metrics['models_evaluated'][0]['f1_score']}")

    return metrics


if __name__ == "__main__":
    evaluate_models()

