"""
Analytics Aggregation Service
Prepares data distributions, histograms, and summary statistics for Chart.js dashboard widgets.
"""

import numpy as np
import pandas as pd
from backend.app.services.data_service import data_service


def compute_customer_analytics():
    df = data_service.segments_df
    if df is None or df.empty:
        return {}

    # 1. Summary Statistics
    summary = {
        "total_revenue": round(float(df["total_spend"].sum()), 2),
        "avg_spend_per_customer": round(float(df["total_spend"].mean()), 2),
        "median_spend": round(float(df["total_spend"].median()), 2),
        "avg_orders_per_customer": round(float(df["total_transactions"].mean()), 2),
        "avg_order_value": round(float(df["avg_order_value"].mean()), 2),
        "avg_web_sessions": round(float(df["total_sessions"].mean()), 2),
        "avg_sentiment": round(float(df["avg_sentiment_score"].mean()), 3),
        "avg_engagement_score": round(float(df["avg_engagement_score"].mean()), 2),
        "overall_cancellation_rate": round(float(df["cancellation_rate"].mean()), 3)
    }

    # 2. Spending Distribution Bins
    spend_bins = [0, 500, 1000, 2000, 4000, float("inf")]
    spend_labels = ["$0 - $500", "$500 - $1,000", "$1,000 - $2,000", "$2,000 - $4,000", "$4,000+"]
    spend_cuts = pd.cut(df["total_spend"], bins=spend_bins, labels=spend_labels, right=False)
    spend_dist = spend_cuts.value_counts()[spend_labels].to_dict()

    # 3. Purchase Frequency Distribution Bins
    freq_bins = [0, 4, 8, 16, float("inf")]
    freq_labels = ["1 - 3 orders", "4 - 7 orders", "8 - 15 orders", "16+ orders"]
    freq_cuts = pd.cut(df["total_transactions"], bins=freq_bins, labels=freq_labels, right=False)
    freq_dist = freq_cuts.value_counts()[freq_labels].to_dict()

    # 4. Website Activity Distribution (Sessions)
    sess_bins = [0, 10, 20, 35, float("inf")]
    sess_labels = ["1 - 9 sessions", "10 - 19 sessions", "20 - 34 sessions", "35+ sessions"]
    sess_cuts = pd.cut(df["total_sessions"], bins=sess_bins, labels=sess_labels, right=False)
    sess_dist = sess_cuts.value_counts()[sess_labels].to_dict()

    # 5. Sentiment Polarity Breakdown
    sentiment_breakdown = {
        "positive_dominant": int((df["avg_sentiment_score"] > 0.2).sum()),
        "neutral_dominant": int(((df["avg_sentiment_score"] >= -0.2) & (df["avg_sentiment_score"] <= 0.2)).sum()),
        "negative_dominant": int((df["avg_sentiment_score"] < -0.2).sum())
    }

    # 6. Web Interaction Funnel Averages
    web_funnel = {
        "avg_product_views": round(float(df["product_views_count"].mean()), 1),
        "avg_cart_additions": round(float(df["cart_additions_count"].mean()), 1),
        "avg_wishlist_items": round(float(df["wishlist_count"].mean()), 1),
        "avg_checkout_starts": round(float(df["checkout_starts_count"].mean()), 1),
        "avg_cart_to_checkout_ratio": round(float(df["cart_to_checkout_ratio"].mean()), 3)
    }

    # 7. Segment Breakdown for Cross-filtering
    segment_counts = df["cluster_name"].value_counts().to_dict()

    return {
        "summary": summary,
        "spending_distribution": spend_dist,
        "frequency_distribution": freq_dist,
        "sessions_distribution": sess_dist,
        "sentiment_breakdown": sentiment_breakdown,
        "web_funnel": web_funnel,
        "segment_distribution": segment_counts
    }
