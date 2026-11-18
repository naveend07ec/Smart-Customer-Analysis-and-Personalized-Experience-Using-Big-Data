"""
Build Point-in-Time Supervised Customer Churn Dataset
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Point-in-Time Specification:
- Prediction Cutoff: 2024-10-01 00:00:00
- Historical Feature Window: 180 days before cutoff (2024-04-04 to 2024-10-01)
- Future Observation Window: 90 days after cutoff (2024-10-01 to 2024-12-30)
- Target: churn_label = 1 (no completed purchase in next 90 days), 0 (at least 1 completed purchase)
- Eligibility: Customer must have at least 1 completed purchase before cutoff.

Zero-Leakage Assurance:
- No transaction, web activity, or social interaction occurring on or after 2024-10-01 00:00:00
  is used in predictor calculations.
"""

import os
import sys
import numpy as np
import pandas as pd

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAW_TX_PATH = os.path.join(BASE_DIR, "data", "raw", "transactions.csv")
RAW_WEB_PATH = os.path.join(BASE_DIR, "data", "raw", "web_activity.csv")
RAW_SOC_PATH = os.path.join(BASE_DIR, "data", "raw", "social_media.csv")
OUT_CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "churn_dataset.csv")
OUT_PARQUET_PATH = os.path.join(BASE_DIR, "data", "processed", "churn_dataset.parquet")

CUTOFF_DATE = pd.Timestamp("2024-10-01 00:00:00")
WINDOW_DAYS = 180
FEATURE_START = CUTOFF_DATE - pd.Timedelta(days=WINDOW_DAYS)


def build_churn_dataset() -> pd.DataFrame:
    print("=" * 60)
    print("Building Supervised Customer Churn Dataset")
    print(f"Prediction Cutoff Date:     {CUTOFF_DATE}")
    print(f"Historical Feature Window:  {FEATURE_START} to {CUTOFF_DATE} ({WINDOW_DAYS} days)")
    print(f"Future Observation Window:  {CUTOFF_DATE} to 2024-12-30 (90 days)")
    print("=" * 60)

    # 1. Load Raw Datasets
    print("Loading raw datasets...")
    df_tx = pd.read_csv(RAW_TX_PATH)
    df_tx["transaction_date"] = pd.to_datetime(df_tx["transaction_date"])

    df_web = pd.read_csv(RAW_WEB_PATH)
    df_web["timestamp"] = pd.to_datetime(df_web["timestamp"])

    df_soc = pd.read_csv(RAW_SOC_PATH)
    df_soc["timestamp"] = pd.to_datetime(df_soc["timestamp"])

    # 2. Strict Point-in-Time Temporal Splits
    # All historical records strictly before cutoff
    hist_tx_all = df_tx[df_tx["transaction_date"] < CUTOFF_DATE].copy()
    hist_tx_180 = hist_tx_all[hist_tx_all["transaction_date"] >= FEATURE_START].copy()
    hist_web_180 = df_web[(df_web["timestamp"] >= FEATURE_START) & (df_web["timestamp"] < CUTOFF_DATE)].copy()
    hist_soc_180 = df_soc[(df_soc["timestamp"] >= FEATURE_START) & (df_soc["timestamp"] < CUTOFF_DATE)].copy()

    # Future transactions strictly on or after cutoff for ground truth label
    future_tx = df_tx[(df_tx["transaction_date"] >= CUTOFF_DATE) & (df_tx["order_status"] == "Completed")]
    future_purchasers = set(future_tx["customer_id"].unique())

    # 3. Determine Eligible Customers
    # Eligibility: Customer had established an active purchase history prior to cutoff
    eligible_custs = hist_tx_all[hist_tx_all["order_status"] == "Completed"]["customer_id"].unique()
    eligible_custs = sorted(eligible_custs)
    print(f"Eligible customers identified: {len(eligible_custs)} / {df_tx['customer_id'].nunique()}")

    df_dataset = pd.DataFrame({"customer_id": eligible_custs})

    # 4. Extract Historical Behavioral Features (Strictly < Cutoff)
    print("Extracting point-in-time historical features...")

    # A. Lifetime Recency at Cutoff
    tx_last = hist_tx_all[hist_tx_all["order_status"] == "Completed"].groupby("customer_id")["transaction_date"].max().reset_index()
    tx_last["recency_days_at_cutoff"] = (CUTOFF_DATE - tx_last["transaction_date"]).dt.total_seconds() / 86400.0
    df_dataset = df_dataset.merge(tx_last[["customer_id", "recency_days_at_cutoff"]], on="customer_id", how="left")

    # B. 180-Day Transactional RFM
    tx_comp = hist_tx_180[hist_tx_180["order_status"] == "Completed"].groupby("customer_id").agg(
        hist_completed_orders=("transaction_id", "count"),
        hist_total_spend=("total_amount", "sum")
    ).reset_index()
    tx_comp["hist_avg_order_value"] = tx_comp["hist_total_spend"] / tx_comp["hist_completed_orders"]

    tx_tot = hist_tx_180.groupby("customer_id").agg(
        hist_total_orders=("transaction_id", "count"),
        hist_cancelled_orders=("order_status", lambda s: (s == "Cancelled").sum())
    ).reset_index()
    tx_tot["hist_cancellation_rate"] = tx_tot["hist_cancelled_orders"] / tx_tot["hist_total_orders"]

    df_dataset = df_dataset.merge(tx_comp, on="customer_id", how="left")
    df_dataset = df_dataset.merge(tx_tot[["customer_id", "hist_total_orders", "hist_cancellation_rate"]], on="customer_id", how="left")

    # C. 180-Day Clickstream Activity
    web_agg = hist_web_180.groupby("customer_id").agg(
        hist_web_touchpoints=("activity_id", "count"),
        hist_distinct_sessions=("session_id", "nunique"),
        hist_avg_dwell_time=("duration_seconds", "mean"),
        hist_product_views=("action_type", lambda s: (s == "product_view").sum()),
        hist_cart_additions=("action_type", lambda s: (s == "add_to_cart").sum()),
        hist_checkout_starts=("action_type", lambda s: (s == "checkout_start").sum())
    ).reset_index()
    web_agg["hist_cart_abandon_ratio"] = np.where(
        web_agg["hist_cart_additions"] > 0,
        (web_agg["hist_cart_additions"] - web_agg["hist_checkout_starts"]) / web_agg["hist_cart_additions"],
        0.0
    )
    df_dataset = df_dataset.merge(web_agg, on="customer_id", how="left")

    # D. 180-Day Social Sentiment & Engagement
    soc_agg = hist_soc_180.groupby("customer_id").agg(
        hist_social_interactions=("interaction_id", "count"),
        hist_avg_sentiment=("sentiment_score", "mean"),
        hist_avg_engagement=("engagement_score", "mean")
    ).reset_index()
    df_dataset = df_dataset.merge(soc_agg, on="customer_id", how="left")

    # E. Neutral Default Imputation for Inactive Channels
    df_dataset["recency_days_at_cutoff"] = df_dataset["recency_days_at_cutoff"].round(1)
    df_dataset["hist_completed_orders"] = df_dataset["hist_completed_orders"].fillna(0).astype(int)
    df_dataset["hist_total_orders"] = df_dataset["hist_total_orders"].fillna(0).astype(int)
    df_dataset["hist_total_spend"] = df_dataset["hist_total_spend"].fillna(0.0).round(2)
    df_dataset["hist_avg_order_value"] = df_dataset["hist_avg_order_value"].fillna(0.0).round(2)
    df_dataset["hist_cancellation_rate"] = df_dataset["hist_cancellation_rate"].fillna(0.0).round(4)
    df_dataset["hist_web_touchpoints"] = df_dataset["hist_web_touchpoints"].fillna(0).astype(int)
    df_dataset["hist_distinct_sessions"] = df_dataset["hist_distinct_sessions"].fillna(0).astype(int)
    df_dataset["hist_avg_dwell_time"] = df_dataset["hist_avg_dwell_time"].fillna(0.0).round(1)
    df_dataset["hist_product_views"] = df_dataset["hist_product_views"].fillna(0).astype(int)
    df_dataset["hist_cart_additions"] = df_dataset["hist_cart_additions"].fillna(0).astype(int)
    df_dataset["hist_checkout_starts"] = df_dataset["hist_checkout_starts"].fillna(0).astype(int)
    df_dataset["hist_cart_abandon_ratio"] = df_dataset["hist_cart_abandon_ratio"].fillna(0.0).round(4)
    df_dataset["hist_social_interactions"] = df_dataset["hist_social_interactions"].fillna(0).astype(int)
    df_dataset["hist_avg_sentiment"] = df_dataset["hist_avg_sentiment"].fillna(0.0).round(3)
    df_dataset["hist_avg_engagement"] = df_dataset["hist_avg_engagement"].fillna(0.0).round(1)

    # 5. Assign Ground-Truth Target Label (Next 90 Days)
    df_dataset["churn_label"] = df_dataset["customer_id"].apply(lambda c: 0 if c in future_purchasers else 1)

    # 6. Save Outputs
    os.makedirs(os.path.dirname(OUT_CSV_PATH), exist_ok=True)
    df_dataset.to_csv(OUT_CSV_PATH, index=False)
    df_dataset.to_parquet(OUT_PARQUET_PATH, index=False)

    print("Dataset generation complete!")
    print(f"Shape:               {df_dataset.shape}")
    print(f"CSV saved to:        {OUT_CSV_PATH}")
    print(f"Parquet saved to:    {OUT_PARQUET_PATH}")
    print("\nTarget Class Distribution:")
    val_counts = df_dataset["churn_label"].value_counts()
    for label, count in val_counts.items():
        name = "Retained (Class 0)" if label == 0 else "Churned (Class 1)"
        pct = (count / len(df_dataset)) * 100
        print(f"  {name}: {count} customers ({pct:.1f}%)")

    return df_dataset


if __name__ == "__main__":
    build_churn_dataset()

