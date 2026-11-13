"""
PySpark Feature Engineering and Multi-Source Customer Aggregation
Aggregates transactional, clickstream, and social media data by customer_id
and builds the unified, explainable customer feature matrix.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def aggregate_transactions(df: DataFrame) -> DataFrame:
    """
    Computes customer-level transactional and RFM behavioural features:
    - total_spend: Total monetary spending on completed orders.
    - total_transactions: Frequency of completed transactions.
    - avg_order_value: Average spend per completed order.
    - total_quantity: Cumulative units purchased.
    - recency_days: Days elapsed since customer's last purchase relative to dataset cutoff.
    - cancelled_orders_count: Total orders cancelled or refunded.
    - cancellation_rate: Ratio of cancelled/refunded orders to total orders placed.
    """
    # Determine the global dataset reference date for recency computation
    max_date_row = df.select(F.max("transaction_date")).collect()
    ref_date = max_date_row[0][0]

    # Completed orders slice for monetary & quantity features
    completed_df = df.filter(F.col("order_status") == "Completed")

    completed_agg = completed_df.groupBy("customer_id").agg(
        F.round(F.sum("total_amount"), 2).alias("total_spend"),
        F.count("transaction_id").alias("total_transactions"),
        F.sum("quantity").alias("total_quantity"),
        F.round(F.avg("total_amount"), 2).alias("avg_order_value"),
        F.max("transaction_date").alias("last_transaction_date")
    ).withColumn(
        "recency_days",
        F.datediff(F.lit(ref_date), F.col("last_transaction_date"))
    ).drop("last_transaction_date")

    # All orders slice for cancellation metrics
    all_agg = df.groupBy("customer_id").agg(
        F.count("transaction_id").alias("total_orders_placed"),
        F.sum(
            F.when(F.col("order_status").isin("Cancelled", "Refunded"), 1).otherwise(0)
        ).alias("cancelled_orders_count")
    ).withColumn(
        "cancellation_rate",
        F.round(
            F.col("cancelled_orders_count") / F.greatest(F.col("total_orders_placed"), F.lit(1)),
            3
        )
    )

    # Join completed aggregates with cancellation metrics
    tx_features = all_agg.join(completed_agg, on="customer_id", how="left").select(
        "customer_id",
        F.coalesce(F.col("total_spend"), F.lit(0.0)).alias("total_spend"),
        F.coalesce(F.col("total_transactions"), F.lit(0)).alias("total_transactions"),
        F.coalesce(F.col("avg_order_value"), F.lit(0.0)).alias("avg_order_value"),
        F.coalesce(F.col("total_quantity"), F.lit(0)).alias("total_quantity"),
        F.coalesce(F.col("recency_days"), F.lit(365)).alias("recency_days"),
        "cancelled_orders_count",
        "cancellation_rate"
    )

    return tx_features


def aggregate_web_activity(df: DataFrame) -> DataFrame:
    """
    Computes customer-level clickstream behavioural features:
    - total_web_activities: Total browsing events logged.
    - total_sessions: Unique browsing sessions.
    - avg_duration_seconds: Mean dwell time per interaction.
    - product_views_count: Volume of product catalog views.
    - cart_additions_count: Volume of items added to cart.
    - wishlist_count: Volume of items bookmarked in wishlist.
    - checkout_starts_count: Initiation of purchase checkout flow.
    - cart_to_checkout_ratio: Conversion ratio from cart additions to checkout starts.
    """
    web_features = df.groupBy("customer_id").agg(
        F.count("activity_id").alias("total_web_activities"),
        F.countDistinct("session_id").alias("total_sessions"),
        F.round(F.avg("duration_seconds"), 1).alias("avg_duration_seconds"),
        F.sum(F.when(F.col("action_type") == "product_view", 1).otherwise(0)).alias("product_views_count"),
        F.sum(F.when(F.col("action_type") == "add_to_cart", 1).otherwise(0)).alias("cart_additions_count"),
        F.sum(F.when(F.col("action_type") == "wishlist", 1).otherwise(0)).alias("wishlist_count"),
        F.sum(F.when(F.col("action_type") == "checkout_start", 1).otherwise(0)).alias("checkout_starts_count")
    ).withColumn(
        "cart_to_checkout_ratio",
        F.round(
            F.col("checkout_starts_count") / F.greatest(F.col("cart_additions_count"), F.lit(1)),
            3
        )
    )

    return web_features


def aggregate_social_media(df: DataFrame) -> DataFrame:
    """
    Computes customer-level social media engagement & sentiment features:
    - total_social_interactions: Volume of social touchpoints.
    - avg_engagement_score: Average engagement reach score [0-100].
    - avg_sentiment_score: Average continuous sentiment polarity [-1.0 to +1.0].
    - positive_interactions_count: Count of positive posts.
    - neutral_interactions_count: Count of neutral posts.
    - negative_interactions_count: Count of negative posts.
    - unique_platforms_count: Breadth of social network touchpoints.
    """
    social_features = df.groupBy("customer_id").agg(
        F.count("interaction_id").alias("total_social_interactions"),
        F.round(F.avg("engagement_score"), 2).alias("avg_engagement_score"),
        F.round(F.avg("sentiment_score"), 3).alias("avg_sentiment_score"),
        F.sum(F.when(F.col("sentiment") == "Positive", 1).otherwise(0)).alias("positive_interactions_count"),
        F.sum(F.when(F.col("sentiment") == "Neutral", 1).otherwise(0)).alias("neutral_interactions_count"),
        F.sum(F.when(F.col("sentiment") == "Negative", 1).otherwise(0)).alias("negative_interactions_count"),
        F.countDistinct("platform").alias("unique_platforms_count")
    )

    return social_features


def build_unified_customer_features(
    tx_features: DataFrame,
    web_features: DataFrame,
    social_features: DataFrame
) -> DataFrame:
    """
    Integrates the three customer-level feature sets on customer_id.
    Ensures exactly 1 row per customer and zero unintended nulls.
    """
    # Outer join to guarantee complete customer coverage
    unified = tx_features.join(web_features, on="customer_id", how="outer")
    unified = unified.join(social_features, on="customer_id", how="outer")

    # Clean fill any missing metric columns
    clean_unified = unified.select(
        "customer_id",
        # Transactions
        F.coalesce(F.col("total_spend"), F.lit(0.0)).alias("total_spend"),
        F.coalesce(F.col("total_transactions"), F.lit(0)).alias("total_transactions"),
        F.coalesce(F.col("avg_order_value"), F.lit(0.0)).alias("avg_order_value"),
        F.coalesce(F.col("total_quantity"), F.lit(0)).alias("total_quantity"),
        F.coalesce(F.col("recency_days"), F.lit(365)).alias("recency_days"),
        F.coalesce(F.col("cancelled_orders_count"), F.lit(0)).alias("cancelled_orders_count"),
        F.coalesce(F.col("cancellation_rate"), F.lit(0.0)).alias("cancellation_rate"),
        # Web Activity
        F.coalesce(F.col("total_web_activities"), F.lit(0)).alias("total_web_activities"),
        F.coalesce(F.col("total_sessions"), F.lit(0)).alias("total_sessions"),
        F.coalesce(F.col("avg_duration_seconds"), F.lit(0.0)).alias("avg_duration_seconds"),
        F.coalesce(F.col("product_views_count"), F.lit(0)).alias("product_views_count"),
        F.coalesce(F.col("cart_additions_count"), F.lit(0)).alias("cart_additions_count"),
        F.coalesce(F.col("wishlist_count"), F.lit(0)).alias("wishlist_count"),
        F.coalesce(F.col("checkout_starts_count"), F.lit(0)).alias("checkout_starts_count"),
        F.coalesce(F.col("cart_to_checkout_ratio"), F.lit(0.0)).alias("cart_to_checkout_ratio"),
        # Social Media
        F.coalesce(F.col("total_social_interactions"), F.lit(0)).alias("total_social_interactions"),
        F.coalesce(F.col("avg_engagement_score"), F.lit(0.0)).alias("avg_engagement_score"),
        F.coalesce(F.col("avg_sentiment_score"), F.lit(0.0)).alias("avg_sentiment_score"),
        F.coalesce(F.col("positive_interactions_count"), F.lit(0)).alias("positive_interactions_count"),
        F.coalesce(F.col("neutral_interactions_count"), F.lit(0)).alias("neutral_interactions_count"),
        F.coalesce(F.col("negative_interactions_count"), F.lit(0)).alias("negative_interactions_count"),
        F.coalesce(F.col("unique_platforms_count"), F.lit(0)).alias("unique_platforms_count")
    )

    return clean_unified

