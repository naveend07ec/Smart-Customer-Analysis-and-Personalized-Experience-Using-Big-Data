"""
Data Cleaning and Preprocessing Module
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Implements:
1. Duplicate detection and elimination.
2. Missing value imputation (e.g. unknown payment methods).
3. Domain constraint validation and invalid record filtering.
4. Meaningful null preservation (product_id on generic navigation pages).
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, when, trim, lit, rlike


def clean_transactions(df_tx: DataFrame) -> (DataFrame, dict):
    """
    Cleans raw transaction records:
    - Removes exact duplicate records.
    - Imputes missing/empty payment methods with 'Unknown'.
    - Validates numeric bounds: quantity > 0, unit_price > 0, total_amount > 0.
    - Enforces valid customer_id format.
    """
    raw_count = df_tx.count()

    # 1. Deduplication
    df_dedup = df_tx.dropDuplicates(["transaction_id"])
    dedup_count = df_dedup.count()
    duplicates_removed = raw_count - dedup_count

    # 2. Impute missing/empty payment methods with 'Unknown'
    df_imputed = df_dedup.withColumn(
        "payment_method",
        when(
            col("payment_method").isNull() | (trim(col("payment_method")) == "") | (col("payment_method") == "null"),
            lit("Unknown")
        ).otherwise(trim(col("payment_method")))
    )

    # Count how many missing payment methods were imputed
    imputed_payment_count = df_dedup.filter(
        col("payment_method").isNull() | (trim(col("payment_method")) == "") | (col("payment_method") == "null")
    ).count()

    # 3. Numeric constraints & customer ID format validation
    valid_condition = (
        (col("customer_id").isNotNull()) &
        (col("customer_id").rlike(r"^CUST_")) &
        (col("quantity") > 0) &
        (col("unit_price") > 0.0) &
        (col("total_amount") > 0.0) &
        (col("order_status").isin("Completed", "Pending", "Cancelled", "Refunded"))
    )

    df_cleaned = df_imputed.filter(valid_condition)
    final_count = df_cleaned.count()
    invalid_records = dedup_count - final_count

    stats = {
        "dataset": "transactions",
        "raw_count": raw_count,
        "duplicates_removed": duplicates_removed,
        "missing_imputed_payment": imputed_payment_count,
        "invalid_records": invalid_records,
        "final_count": final_count
    }

    return df_cleaned, stats


def clean_web_activity(df_web: DataFrame) -> (DataFrame, dict):
    """
    Cleans raw web activity clickstream logs:
    - Removes exact duplicate activity events.
    - Validates duration_seconds >= 0.
    - Preserves null/empty product_id on generic navigation pages (/home, /category/*).
    - Enforces valid customer_id format.
    """
    raw_count = df_web.count()

    # 1. Deduplication
    df_dedup = df_web.dropDuplicates(["activity_id"])
    dedup_count = df_dedup.count()
    duplicates_removed = raw_count - dedup_count

    # 2. Normalize product_id: preserve None/null for non-product pages
    df_norm = df_dedup.withColumn(
        "product_id",
        when(
            col("product_id").isNull() | (trim(col("product_id")) == "") | (col("product_id") == "null"),
            lit(None).cast("string")
        ).otherwise(trim(col("product_id")))
    )

    # 3. Numeric and ID validation
    valid_condition = (
        (col("customer_id").isNotNull()) &
        (col("customer_id").rlike(r"^CUST_")) &
        (col("duration_seconds") >= 0) &
        (col("action_type").isin(
            "page_view", "product_view", "search", "add_to_cart",
            "remove_from_cart", "wishlist", "checkout_start"
        ))
    )

    df_cleaned = df_norm.filter(valid_condition)
    final_count = df_cleaned.count()
    invalid_records = dedup_count - final_count

    stats = {
        "dataset": "web_activity",
        "raw_count": raw_count,
        "duplicates_removed": duplicates_removed,
        "meaningful_null_product_ids": df_cleaned.filter(col("product_id").isNull()).count(),
        "invalid_records": invalid_records,
        "final_count": final_count
    }

    return df_cleaned, stats


def clean_social_media(df_soc: DataFrame) -> (DataFrame, dict):
    """
    Cleans raw social media sentiment logs:
    - Removes duplicates.
    - Validates sentiment_score in [-1.0, 1.0] and engagement_score in [0, 100].
    - Enforces valid customer_id format.
    """
    raw_count = df_soc.count()

    # 1. Deduplication
    df_dedup = df_soc.dropDuplicates(["interaction_id"])
    dedup_count = df_dedup.count()
    duplicates_removed = raw_count - dedup_count

    # 2. Validation bounds
    valid_condition = (
        (col("customer_id").isNotNull()) &
        (col("customer_id").rlike(r"^CUST_")) &
        (col("sentiment_score") >= -1.0) &
        (col("sentiment_score") <= 1.0) &
        (col("engagement_score") >= 0) &
        (col("engagement_score") <= 100) &
        (col("sentiment").isin("Positive", "Neutral", "Negative"))
    )

    df_cleaned = df_dedup.filter(valid_condition)
    final_count = df_cleaned.count()
    invalid_records = dedup_count - final_count

    stats = {
        "dataset": "social_media",
        "raw_count": raw_count,
        "duplicates_removed": duplicates_removed,
        "invalid_records": invalid_records,
        "final_count": final_count
    }

    return df_cleaned, stats
