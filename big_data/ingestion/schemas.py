"""
Explicit PySpark Schemas for Ingestion
Project: Smart Customer Analysis and Personalized Experience Using Big Data
"""

from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType
)

TRANSACTION_SCHEMA = StructType([
    StructField("transaction_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("transaction_date", StringType(), False),
    StructField("product_id", StringType(), False),
    StructField("product_category", StringType(), False),
    StructField("product_name", StringType(), False),
    StructField("quantity", IntegerType(), True),
    StructField("unit_price", DoubleType(), True),
    StructField("discount_percent", DoubleType(), True),
    StructField("total_amount", DoubleType(), True),
    StructField("payment_method", StringType(), True),  # Nullable for testing cleaning
    StructField("order_status", StringType(), False)
])

WEB_ACTIVITY_SCHEMA = StructType([
    StructField("activity_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("session_id", StringType(), False),
    StructField("timestamp", StringType(), False),
    StructField("page_url", StringType(), False),
    StructField("action_type", StringType(), False),
    StructField("product_id", StringType(), True),      # Nullable on non-product views
    StructField("duration_seconds", IntegerType(), True),
    StructField("device_type", StringType(), False),
    StructField("traffic_source", StringType(), False)
])

SOCIAL_MEDIA_SCHEMA = StructType([
    StructField("interaction_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("timestamp", StringType(), False),
    StructField("platform", StringType(), False),
    StructField("interaction_type", StringType(), False),
    StructField("sentiment", StringType(), False),
    StructField("sentiment_score", DoubleType(), True),
    StructField("engagement_score", IntegerType(), True),
    StructField("feedback_content", StringType(), True),
    StructField("associated_category", StringType(), False)
])
