"""
PySpark Explicit Schemas for Multi-Source Ingestion
Ensures strict type enforcement and contract validation during ingestion.
"""

from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType
)

# 1. Transactions Schema
TRANSACTIONS_SCHEMA = StructType([
    StructField("transaction_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("transaction_date", StringType(), False),
    StructField("product_id", StringType(), False),
    StructField("product_category", StringType(), False),
    StructField("product_name", StringType(), False),
    StructField("quantity", IntegerType(), False),
    StructField("unit_price", DoubleType(), False),
    StructField("discount_percent", DoubleType(), False),
    StructField("total_amount", DoubleType(), False),
    StructField("payment_method", StringType(), True),   # Nullable to capture missing values
    StructField("order_status", StringType(), False)
])

# 2. Web Activity Schema
WEB_ACTIVITY_SCHEMA = StructType([
    StructField("activity_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("session_id", StringType(), False),
    StructField("timestamp", StringType(), False),
    StructField("page_url", StringType(), False),
    StructField("action_type", StringType(), False),
    StructField("product_id", StringType(), True),        # Nullable for non-product pages
    StructField("duration_seconds", IntegerType(), False),
    StructField("device_type", StringType(), False),
    StructField("traffic_source", StringType(), False)
])

# 3. Social Media Schema
SOCIAL_MEDIA_SCHEMA = StructType([
    StructField("interaction_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("timestamp", StringType(), False),
    StructField("platform", StringType(), False),
    StructField("interaction_type", StringType(), False),
    StructField("sentiment", StringType(), False),
    StructField("sentiment_score", DoubleType(), False),
    StructField("engagement_score", IntegerType(), False),
    StructField("feedback_content", StringType(), True),
    StructField("associated_category", StringType(), False)
])
