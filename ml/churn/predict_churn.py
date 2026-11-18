"""
Generate Customer-Level Churn Predictions and Risk Tiers
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Outputs:
- customer_id
- predicted_churn_class (0 or 1)
- churn_risk_score (0.0 - 100.0 uncalibrated model risk score)
- risk_category ('Low', 'Medium', 'High')
- model_version ('v1.0-rf')
- cluster_id, cluster_name (from existing K-Means segmentation for reference)
- suggested_retention_action

Saves to:
- data/processed/customer_churn_predictions.csv
- data/processed/customer_churn_predictions.parquet
- ml/models/churn/customer_churn_summary.json
"""

import os
import json
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATASET_PATH = os.path.join(BASE_DIR, "data", "processed", "churn_dataset.parquet")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "churn", "churn_model.joblib")
SEGMENTS_PATH = os.path.join(BASE_DIR, "data", "processed", "customer_segment_assignments.csv")
OUT_CSV = os.path.join(BASE_DIR, "data", "processed", "customer_churn_predictions.csv")
OUT_PARQUET = os.path.join(BASE_DIR, "data", "processed", "customer_churn_predictions.parquet")
OUT_SUMMARY_JSON = os.path.join(BASE_DIR, "ml", "models", "churn", "customer_churn_summary.json")

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


def assign_risk_category(score: float) -> str:
    if score < 35.0:
        return "Low"
    elif score < 65.0:
        return "Medium"
    else:
        return "High"


def assign_retention_action(category: str) -> str:
    if category == "High":
        return "Consider a personalized win-back offer. Review recent cancellation behaviour. Recommend relevant products based on existing recommendation results."
    elif category == "Medium":
        return "Consider targeted engagement campaigns. Monitor purchase frequency and website activity."
    else:
        return "Continue relevant product recommendations. Encourage repeat purchases and engagement."


def generate_predictions():
    print("=" * 60)
    print("Generating Customer-Level Churn Predictions")
    print("=" * 60)

    df_data = pd.read_parquet(DATASET_PATH)
    rf_model = joblib.load(MODEL_PATH)

    X = df_data[FEATURE_COLUMNS]
    probs = rf_model.predict_proba(X)[:, 1]
    preds = rf_model.predict(X)

    df_preds = df_data[["customer_id"] + FEATURE_COLUMNS].copy()
    df_preds["actual_churn_label"] = df_data["churn_label"]
    df_preds["predicted_churn_class"] = preds.astype(int)
    df_preds["churn_risk_score"] = np.round(probs * 100, 1)
    df_preds["risk_category"] = df_preds["churn_risk_score"].apply(assign_risk_category)
    df_preds["model_version"] = "v1.0-rf"
    df_preds["suggested_retention_action"] = df_preds["risk_category"].apply(assign_retention_action)

    # Attach existing K-Means segment labels if available without altering segmentation
    if os.path.exists(SEGMENTS_PATH):
        df_seg = pd.read_csv(SEGMENTS_PATH)
        df_preds = df_preds.merge(
            df_seg[["customer_id", "cluster_id", "cluster_name"]],
            on="customer_id",
            how="left"
        )
    else:
        df_preds["cluster_id"] = -1
        df_preds["cluster_name"] = "Unassigned"

    # Save CSV and Parquet
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    df_preds.to_csv(OUT_CSV, index=False)
    df_preds.to_parquet(OUT_PARQUET, index=False)

    # Calculate summary metrics
    risk_counts = df_preds["risk_category"].value_counts().to_dict()
    total_customers = len(df_preds)
    summary = {
        "model_name": "Random Forest Classifier",
        "model_version": "v1.0-rf",
        "prediction_cutoff": "2024-10-01 00:00:00",
        "total_customers_evaluated": total_customers,
        "risk_distribution": {
            "low_risk": {
                "count": int(risk_counts.get("Low", 0)),
                "percentage": round(risk_counts.get("Low", 0) / total_customers * 100, 1),
                "threshold": "Score < 35.0"
            },
            "medium_risk": {
                "count": int(risk_counts.get("Medium", 0)),
                "percentage": round(risk_counts.get("Medium", 0) / total_customers * 100, 1),
                "threshold": "35.0 <= Score < 65.0"
            },
            "high_risk": {
                "count": int(risk_counts.get("High", 0)),
                "percentage": round(risk_counts.get("High", 0) / total_customers * 100, 1),
                "threshold": "Score >= 65.0"
            }
        },
        "predicted_churn_counts": {
            "predicted_retained_0": int((df_preds["predicted_churn_class"] == 0).sum()),
            "predicted_churned_1": int((df_preds["predicted_churn_class"] == 1).sum())
        }
    }

    with open(OUT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Predictions successfully generated for {len(df_preds)} customers.")
    print(f"  CSV:     {OUT_CSV}")
    print(f"  Parquet: {OUT_PARQUET}")
    print(f"  Summary: {OUT_SUMMARY_JSON}")
    print("\nRisk Tier Distribution:")
    for tier, data in summary["risk_distribution"].items():
        print(f"  {tier.replace('_', ' ').title()}: {data['count']} ({data['percentage']}%) [{data['threshold']}]")

    return df_preds, summary


if __name__ == "__main__":
    generate_predictions()

