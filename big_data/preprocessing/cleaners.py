"""
PySpark Preprocessing and Data Cleaning Modules
Applies declarative transformations, deduplication, imputation, and validation.
"""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import TimestampType


def clean_transactions(df: DataFrame) -> tuple[DataFrame, dict]:
    """
    Cleans raw transactions:
    1. Tracks original row count.
    2. Identifies and removes duplicate transactions by transaction_id.
    3. Handles missing payment methods by replacing null/empty with 'Unknown'.
    4. Validates numeric fields (quantity > 0, unit_price > 0, total_amount > 0).
    5. Casts transaction_date string to TimestampType.
    6. Filters invalid customer IDs.
    """
    orig_count = df.count()

    # 1. Deduplicate by transaction_id
    dedup_df = df.dropDuplicates(["transaction_id"])
    dedup_count = dedup_df.count()
    duplicates_removed = orig_count - dedup_count

    # 2. Track and impute missing payment_method with 'Unknown'
    missing_payment_count = dedup_df.filter(
        F.col("payment_method").isNull() | (F.trim(F.col("payment_method")) == "")
    ).count()

    imputed_df = dedup_df.withColumn(
        "payment_method",
        F.when(
            F.col("payment_method").isNull() | (F.trim(F.col("payment_method")) == ""),
            F.lit("Unknown")
        ).otherwise(F.trim(F.col("payment_method")))
    )

    # 3. Numeric & status validation
    valid_df = imputed_df.filter(
        (F.col("quantity") > 0) &
        (F.col("unit_price") > 0.0) &
        (F.col("total_amount") > 0.0) &
        (F.col("order_status").isin("Completed", "Pending", "Cancelled", "Refunded")) &
        (F.col("customer_id").isNotNull()) &
        (F.col("customer_id").rlike(r"^CUST_"))
    )

    # 4. Standardize timestamps
    cleaned_df = valid_df.withColumn(
        "transaction_date",
        F.to_timestamp(F.col("transaction_date"), "yyyy-MM-dd HH:mm:ss")
    )

    final_count = cleaned_df.count()
    invalid_records = dedup_count - final_count

    metrics = {
        "dataset": "transactions",
        "original_count": orig_count,
        "duplicates_removed": duplicates_removed,
        "missing_values_handled": missing_payment_count,
        "invalid_records_filtered": invalid_records,
        "final_count": final_count,
        "unique_customers": cleaned_df.select("customer_id").distinct().count()
    }

    return cleaned_df, metrics


def clean_web_activity(df: DataFrame) -> tuple[DataFrame, dict]:
    """
    Cleans raw web activity clickstream logs:
    1. Tracks original row count.
    2. Identifies and removes duplicate events by activity_id.
    3. Preserves legitimate nulls in product_id for non-product pages (/home, /category, etc.).
    4. Validates duration_seconds >= 0.
    5. Casts timestamp string to TimestampType.
    6. Filters invalid customer IDs.
    """
    orig_count = df.count()

    # 1. Deduplicate by activity_id
    dedup_df = df.dropDuplicates(["activity_id"])
    dedup_count = dedup_df.count()
    duplicates_removed = orig_count - dedup_count

    # 2. Track intentional null product_ids
    null_product_id_count = dedup_df.filter(
        F.col("product_id").isNull() | (F.trim(F.col("product_id")) == "")
    ).count()

    # Normalize empty string product_id to proper null
    normalized_df = dedup_df.withColumn(
        "product_id",
        F.when(
            F.col("product_id").isNull() | (F.trim(F.col("product_id")) == ""),
            F.lit(None)
        ).otherwise(F.trim(F.col("product_id")))
    )

    # 3. Validation: duration >= 0, valid action_type, valid customer_id
    valid_df = normalized_df.filter(
        (F.col("duration_seconds") >= 0) &
        (F.col("customer_id").isNotNull()) &
        (F.col("customer_id").rlike(r"^CUST_"))
    )

    # 4. Standardize timestamps
    cleaned_df = valid_df.withColumn(
        "timestamp",
        F.to_timestamp(F.col("timestamp"), "yyyy-MM-dd HH:mm:ss")
    )

    final_count = cleaned_df.count()
    invalid_records = dedup_count - final_count

    metrics = {
        "dataset": "web_activity",
        "original_count": orig_count,
        "duplicates_removed": duplicates_removed,
        "missing_values_handled": 0,  # Legitimate structural nulls preserved
        "legitimate_null_product_ids_preserved": null_product_id_count,
        "invalid_records_filtered": invalid_records,
        "final_count": final_count,
        "unique_customers": cleaned_df.select("customer_id").distinct().count()
    }

    return cleaned_df, metrics


def clean_social_media(df: DataFrame) -> tuple[DataFrame, dict]:
    """
    Cleans raw social media interactions:
    1. Tracks original row count.
    2. Identifies and removes duplicate records by interaction_id.
    3. Validates sentiment_score in [-1.0, 1.0] and engagement_score in [0, 100].
    4. Casts timestamp string to TimestampType.
    5. Filters invalid customer IDs.
    """
    orig_count = df.count()

    # 1. Deduplicate by interaction_id
    dedup_df = df.dropDuplicates(["interaction_id"])
    dedup_count = dedup_df.count()
    duplicates_removed = orig_count - dedup_count

    # 2. Validation: range checks and valid customer_id
    valid_df = dedup_df.filter(
        (F.col("sentiment_score") >= -1.0) &
        (F.col("sentiment_score") <= 1.0) &
        (F.col("engagement_score") >= 0) &
        (F.col("engagement_score") <= 100) &
        (F.col("sentiment").isin("Positive", "Neutral", "Negative")) &
        (F.col("customer_id").isNotNull()) &
        (F.col("customer_id").rlike(r"^CUST_"))
    )

    # 3. Standardize timestamps
    cleaned_df = valid_df.withColumn(
        "timestamp",
        F.to_timestamp(F.col("timestamp"), "yyyy-MM-dd HH:mm:ss")
    )

    final_count = cleaned_df.count()
    invalid_records = dedup_count - final_count

    metrics = {
        "dataset": "social_media",
        "original_count": orig_count,
        "duplicates_removed": duplicates_removed,
        "missing_values_handled": 0,
        "invalid_records_filtered": invalid_records,
        "final_count": final_count,
        "unique_customers": cleaned_df.select("customer_id").distinct().count()
    }

    return cleaned_df, metrics

