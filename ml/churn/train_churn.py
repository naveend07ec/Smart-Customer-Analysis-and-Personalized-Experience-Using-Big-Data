"""
Train Supervised Customer Churn Prediction Models
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Compares:
1. Majority Class Baseline
2. Logistic Regression (StandardScaler + Balanced Class Weight)
3. Random Forest Classifier (Depth-controlled + Balanced Class Weight)

Validation Protocol:
- Stratified Customer-Level Train/Test Split (80/20)
- Preprocessing and scaling fitted strictly on training data
- Artifacts saved under ml/models/churn/
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    precision_score, recall_score, f1_score,
    confusion_matrix
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATASET_PATH = os.path.join(BASE_DIR, "data", "processed", "churn_dataset.parquet")
MODEL_DIR = os.path.join(BASE_DIR, "ml", "models", "churn")

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


def train_churn_models():
    print("=" * 60)
    print("Training Supervised Customer Churn Models")
    print("=" * 60)

    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}. Run build_churn_dataset.py first.")

    df = pd.read_parquet(DATASET_PATH)
    print(f"Loaded dataset: {len(df)} eligible customers, {len(FEATURE_COLUMNS)} predictive features.")

    X = df[FEATURE_COLUMNS]
    y = df["churn_label"]

    # Customer-level Stratified Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Train split: {len(X_train)} samples (Churned: {y_train.sum()}, Retained: {len(y_train) - y_train.sum()})")
    print(f"Test split:  {len(X_test)} samples (Churned: {y_test.sum()}, Retained: {len(y_test) - y_test.sum()})")

    # 1. Baseline: Majority Class Classifier (Predicts 0)
    y_pred_base = np.zeros_like(y_test)
    base_acc = float(np.mean(y_pred_base == y_test))
    base_rec = float(recall_score(y_test, y_pred_base, zero_division=0))
    base_f1 = float(f1_score(y_test, y_pred_base, zero_division=0))

    # 2. Logistic Regression (Scaled)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    lr_model = LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
    lr_model.fit(X_train_scaled, y_train)
    y_pred_lr = lr_model.predict(X_test_scaled)
    y_prob_lr = lr_model.predict_proba(X_test_scaled)[:, 1]

    lr_roc = float(roc_auc_score(y_test, y_prob_lr))
    lr_pr = float(average_precision_score(y_test, y_prob_lr))
    lr_prec = float(precision_score(y_test, y_pred_lr))
    lr_rec = float(recall_score(y_test, y_pred_lr))
    lr_f1 = float(f1_score(y_test, y_pred_lr))
    lr_cm = confusion_matrix(y_test, y_pred_lr).tolist()

    # 3. Random Forest Classifier
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        min_samples_split=6,
        class_weight="balanced",
        random_state=42
    )
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)
    y_prob_rf = rf_model.predict_proba(X_test)[:, 1]

    rf_roc = float(roc_auc_score(y_test, y_prob_rf))
    rf_pr = float(average_precision_score(y_test, y_prob_rf))
    rf_prec = float(precision_score(y_test, y_pred_rf))
    rf_rec = float(recall_score(y_test, y_pred_rf))
    rf_f1 = float(f1_score(y_test, y_pred_rf))
    rf_cm = confusion_matrix(y_test, y_pred_rf).tolist()

    print("\n" + "-" * 50)
    print("TEST-SET MODEL COMPARISON RESULTS:")
    print("-" * 50)
    print(f"1. Majority Class Baseline : Accuracy={base_acc:.4f}, Recall={base_rec:.4f}, F1={base_f1:.4f}")
    print(f"2. Logistic Regression     : ROC-AUC={lr_roc:.4f}, PR-AUC={lr_pr:.4f}, Precision={lr_prec:.4f}, Recall={lr_rec:.4f}, F1={lr_f1:.4f}")
    print(f"3. Random Forest (Selected): ROC-AUC={rf_roc:.4f}, PR-AUC={rf_pr:.4f}, Precision={rf_prec:.4f}, Recall={rf_rec:.4f}, F1={rf_f1:.4f}")

    # Feature Importances
    importances = dict(zip(FEATURE_COLUMNS, [round(float(x), 4) for x in rf_model.feature_importances_]))
    sorted_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    print("\nTop 5 Predictive Features (Random Forest):")
    for feat, imp in sorted_importances[:5]:
        print(f"  - {feat}: {imp * 100:.2f}%")

    # Save artifacts
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_save_path = os.path.join(MODEL_DIR, "churn_model.joblib")
    scaler_save_path = os.path.join(MODEL_DIR, "scaler.joblib")
    metadata_path = os.path.join(MODEL_DIR, "model_metadata.json")

    joblib.dump(rf_model, model_save_path)
    joblib.dump(scaler, scaler_save_path)

    metadata = {
        "model_name": "Random Forest Classifier",
        "model_version": "v1.0-rf",
        "algorithm": "RandomForestClassifier",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 5,
            "min_samples_split": 6,
            "class_weight": "balanced",
            "random_state": 42
        },
        "feature_columns": FEATURE_COLUMNS,
        "feature_importances": dict(sorted_importances),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "prediction_cutoff": "2024-10-01 00:00:00",
        "future_window_days": 90,
        "test_metrics": {
            "roc_auc": round(rf_roc, 4),
            "pr_auc": round(rf_pr, 4),
            "precision": round(rf_prec, 4),
            "recall": round(rf_rec, 4),
            "f1_score": round(rf_f1, 4),
            "confusion_matrix": rf_cm
        },
        "baseline_metrics": {
            "model": "Majority Class",
            "accuracy": round(base_acc, 4),
            "recall": round(base_rec, 4),
            "f1_score": round(base_f1, 4)
        },
        "logistic_regression_metrics": {
            "roc_auc": round(lr_roc, 4),
            "pr_auc": round(lr_pr, 4),
            "precision": round(lr_prec, 4),
            "recall": round(lr_rec, 4),
            "f1_score": round(lr_f1, 4),
            "confusion_matrix": lr_cm
        }
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\nTrained artifacts saved:")
    print(f"  Model:    {model_save_path}")
    print(f"  Scaler:   {scaler_save_path}")
    print(f"  Metadata: {metadata_path}")

    return metadata


if __name__ == "__main__":
    train_churn_models()

