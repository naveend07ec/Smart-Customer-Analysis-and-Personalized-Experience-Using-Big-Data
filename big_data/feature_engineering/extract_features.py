"""
Feature Engineering and Multi-Source Integration Module
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Implements customer-level aggregation across transactions, website activity,
and social media, followed by multi-source integration into a unified feature matrix.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, count, countDistinct, sum as _sum, avg, max as _max,
    when, round as _round, lit, coalesce, datediff, to_date
)


def compute_transaction_features(df_tx: DataFrame, reference_date_str: str = "2025-01-01") -> DataFrame:
    """
    Computes RFM and transaction metrics per customer:
    - total_spend
    - total_transactions
    - completed_transactions
    - cancelled_transactions
    - cancellation_rate
    - avg_order_value
    - total_quantity
    - recency_days
    """
    ref_date = to_date(lit(reference_date_str), "yyyy-MM-dd")

    features = (
        df_tx.groupBy("customer_id")
        .agg(
            _round(coalesce(_sum(when(col("order_status") == "Completed", col("total_amount"))), lit(0.0)), 2).alias("total_spend"),
            count("transaction_id").alias("total_transactions"),
            coalesce(count(when(col("order_status") == "Completed", 1)), lit(0)).alias("completed_transactions"),
            coalesce(count(when(col("order_status").isin("Cancelled", "Refunded"), 1)), lit(0)).alias("cancelled_transactions"),
            _round(
                coalesce(count(when(col("order_status").isin("Cancelled", "Refunded"), 1)), lit(0)) /
                when(count("transaction_id") > 0, count("transaction_id")).otherwise(lit(1)),
                4
            ).alias("cancellation_rate"),
            _round(
                coalesce(avg(when(col("order_status") == "Completed", col("total_amount"))), lit(0.0)),
                2
            ).alias("avg_order_value"),
            coalesce(_sum(when(col("order_status") == "Completed", col("quantity"))), lit(0)).alias("total_quantity"),
            datediff(ref_date, to_date(_max("transaction_date"))).alias("recency_days")
        )
    )
    return features


def compute_web_features(df_web: DataFrame) -> DataFrame:
    """
    Computes browsing engagement metrics per customer:
    - total_web_activities
    - total_sessions
    - avg_duration_seconds
    - product_views_count
    - cart_additions_count
    - wishlist_count
    - checkout_starts_count
    - cart_to_checkout_ratio
    """
    features = (
        df_web.groupBy("customer_id")
        .agg(
            count("activity_id").alias("total_web_activities"),
            countDistinct("session_id").alias("total_sessions"),
            _round(coalesce(avg("duration_seconds"), lit(0.0)), 2).alias("avg_duration_seconds"),
            coalesce(count(when(col("action_type") == "product_view", 1)), lit(0)).alias("product_views_count"),
            coalesce(count(when(col("action_type") == "add_to_cart", 1)), lit(0)).alias("cart_additions_count"),
            coalesce(count(when(col("action_type") == "wishlist", 1)), lit(0)).alias("wishlist_count"),
            coalesce(count(when(col("action_type") == "checkout_start", 1)), lit(0)).alias("checkout_starts_count")
        )
        .withColumn(
            "cart_to_checkout_ratio",
            _round(
                col("checkout_starts_count") /
                when(col("cart_additions_count") > 0, col("cart_additions_count")).otherwise(lit(1.0)),
                4
            )
        )
    )
    return features


def compute_social_features(df_soc: DataFrame) -> DataFrame:
    """
    Computes social engagement and sentiment polarity metrics per customer:
    - total_social_interactions
    - avg_engagement_score
    - avg_sentiment_score
    - positive_interactions_count
    - neutral_interactions_count
    - negative_interactions_count
    - unique_platforms_count
    """
    features = (
        df_soc.groupBy("customer_id")
        .agg(
            count("interaction_id").alias("total_social_interactions"),
            _round(coalesce(avg("engagement_score"), lit(0.0)), 2).alias("avg_engagement_score"),
            _round(coalesce(avg("sentiment_score"), lit(0.0)), 4).alias("avg_sentiment_score"),
            coalesce(count(when(col("sentiment") == "Positive", 1)), lit(0)).alias("positive_interactions_count"),
            coalesce(count(when(col("sentiment") == "Neutral", 1)), lit(0)).alias("neutral_interactions_count"),
            coalesce(count(when(col("sentiment") == "Negative", 1)), lit(0)).alias("negative_interactions_count"),
            countDistinct("platform").alias("unique_platforms_count")
        )
    )
    return features


def build_unified_feature_matrix(
    df_tx_feat: DataFrame,
    df_web_feat: DataFrame,
    df_soc_feat: DataFrame
) -> DataFrame:
    """
    Joins the three customer-level feature sets on customer_id into a single unified matrix.
    Uses outer join to guarantee zero record loss, then applies coalescing for zero-fill safety.
    """
    # Join transactions and web features
    unified = df_tx_feat.join(df_web_feat, on="customer_id", how="outer")

    # Join with social features
    unified = unified.join(df_soc_feat, on="customer_id", how="outer")

    # Fill any missing metrics with 0.0 / 0 to guarantee non-null feature matrix
    numeric_defaults = {
        "total_spend": 0.0,
        "total_transactions": 0,
        "completed_transactions": 0,
        "cancelled_transactions": 0,
        "cancellation_rate": 0.0,
        "avg_order_value": 0.0,
        "total_quantity": 0,
        "recency_days": 365,
        "total_web_activities": 0,
        "total_sessions": 0,
        "avg_duration_seconds": 0.0,
        "product_views_count": 0,
        "cart_additions_count": 0,
        "wishlist_count": 0,
        "checkout_starts_count": 0,
        "cart_to_checkout_ratio": 0.0,
        "total_social_interactions": 0,
        "avg_engagement_score": 0.0,
        "avg_sentiment_score": 0.0,
        "positive_interactions_count": 0,
        "neutral_interactions_count": 0,
        "negative_interactions_count": 0,
        "unique_platforms_count": 0
    }

    unified = unified.na.fill(numeric_defaults)

    # Sort deterministically by customer_id
    unified = unified.orderBy("customer_id")
    return unified
