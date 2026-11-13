"""
Raw Data Ingestion and Schema Validation
Project: Smart Customer Analysis and Personalized Experience Using Big Data
"""

import os
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, to_timestamp
from big_data.ingestion.schemas import (
    TRANSACTION_SCHEMA, WEB_ACTIVITY_SCHEMA, SOCIAL_MEDIA_SCHEMA
)


def load_raw_datasets(spark: SparkSession, data_dir: str = "data/raw"):
    """
    Ingests raw multi-source CSV files using explicit PySpark schemas and validates formats.
    """
    tx_path = os.path.join(data_dir, "transactions.csv")
    web_path = os.path.join(data_dir, "web_activity.csv")
    soc_path = os.path.join(data_dir, "social_media.csv")

    for p in [tx_path, web_path, soc_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Source dataset missing at expected path: {p}")

    # Read with explicit schema & header
    df_tx = spark.read.csv(tx_path, schema=TRANSACTION_SCHEMA, header=True)
    df_web = spark.read.csv(web_path, schema=WEB_ACTIVITY_SCHEMA, header=True)
    df_soc = spark.read.csv(soc_path, schema=SOCIAL_MEDIA_SCHEMA, header=True)

    # Convert string timestamps to native Spark TimestampType
    df_tx = df_tx.withColumn("transaction_date", to_timestamp(col("transaction_date"), "yyyy-MM-dd HH:mm:ss"))
    df_web = df_web.withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))
    df_soc = df_soc.withColumn("timestamp", to_timestamp(col("timestamp"), "yyyy-MM-dd HH:mm:ss"))

    return df_tx, df_web, df_soc
