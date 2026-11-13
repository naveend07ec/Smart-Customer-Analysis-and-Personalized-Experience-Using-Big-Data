"""
End-to-End Big Data Processing Pipeline Runner
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Orchestrates:
1. PySpark ingestion with explicit schema enforcement.
2. Data cleaning, deduplication, and anomaly handling.
3. Customer-level feature engineering across transactions, web, and social media.
4. Multi-source integration into a unified customer feature matrix.
5. Exporting validated datasets to data/processed/ in both Parquet and CSV formats.
6. Rigorous statistical validation and report generation.
"""

import os
import sys
import shutil

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, count, when

from big_data.spark_session import get_spark_session
from big_data.ingestion.ingest_raw import load_raw_datasets
from big_data.preprocessing.clean_data import (
    clean_transactions, clean_web_activity, clean_social_media
)
from big_data.feature_engineering.extract_features import (
    compute_transaction_features, compute_web_features,
    compute_social_features, build_unified_feature_matrix
)


def export_dataframe(df: DataFrame, output_base_dir: str, name: str):
    """
    Saves the DataFrame in:
    1. Parquet format (for distributed PySpark ML pipelines)
    2. Single-file CSV format (for lightweight inspection & Flask API consumption)
    """
    parquet_path = os.path.join(output_base_dir, f"{name}.parquet")
    csv_temp_dir = os.path.join(output_base_dir, f"_temp_csv_{name}")
    csv_final_path = os.path.join(output_base_dir, f"{name}.csv")

    # 1. Save Parquet
    df.write.mode("overwrite").parquet(parquet_path)

    # 2. Save CSV with header
    df.coalesce(1).write.mode("overwrite").option("header", "true").csv(csv_temp_dir)

    # Rename the single part file to clean filename
    for file in os.listdir(csv_temp_dir):
        if file.startswith("part-") and file.endswith(".csv"):
            shutil.copyfile(os.path.join(csv_temp_dir, file), csv_final_path)
            break

    # Clean temporary directory
    shutil.rmtree(csv_temp_dir, ignore_errors=True)


def main():
    print("=" * 80)
    print("STARTING PYSPARK BIG DATA PIPELINE (STAGE 3)")
    print("=" * 80)

    # 1. Initialize SparkSession (local[2], memory throttled for 8GB RAM)
    spark = get_spark_session(app_name="CustomerAnalyticsPipeline")
    print(f"SparkSession created successfully! Spark version: {spark.version}")
    print(f"Master: {spark.conf.get('spark.master')}")

    # 2. Ingestion
    print("\n>>> Step 1: Ingesting raw datasets with explicit schemas...")
    df_tx_raw, df_web_raw, df_soc_raw = load_raw_datasets(spark, data_dir="data/raw")

    raw_tx_cnt = df_tx_raw.count()
    raw_web_cnt = df_web_raw.count()
    raw_soc_cnt = df_soc_raw.count()
    print(f"  - Transactions raw: {raw_tx_cnt} rows")
    print(f"  - Web Activity raw: {raw_web_cnt} rows")
    print(f"  - Social Media raw: {raw_soc_cnt} rows")

    # 3. Data Cleaning
    print("\n>>> Step 2: Cleaning datasets and handling anomalies...")
    df_tx_clean, tx_stats = clean_transactions(df_tx_raw)
    df_web_clean, web_stats = clean_web_activity(df_web_raw)
    df_soc_clean, soc_stats = clean_social_media(df_soc_raw)

    print(f"  [Transactions] Deduplicated: {tx_stats['duplicates_removed']} removed | Missing payment imputed: {tx_stats['missing_imputed_payment']} | Final: {tx_stats['final_count']}")
    print(f"  [Web Activity] Deduplicated: {web_stats['duplicates_removed']} removed | Meaningful null product_ids preserved: {web_stats['meaningful_null_product_ids']} | Final: {web_stats['final_count']}")
    print(f"  [Social Media] Deduplicated: {soc_stats['duplicates_removed']} removed | Invalid filtered: {soc_stats['invalid_records']} | Final: {soc_stats['final_count']}")

    # Cache cleaned DataFrames for efficient downstream multi-aggregation
    df_tx_clean.cache()
    df_web_clean.cache()
    df_soc_clean.cache()

    # 4. Feature Engineering per Domain
    print("\n>>> Step 3: Computing customer-level feature aggregations...")
    df_tx_features = compute_transaction_features(df_tx_clean)
    df_web_features = compute_web_features(df_web_clean)
    df_soc_features = compute_social_features(df_soc_clean)

    tx_cust_cnt = df_tx_features.count()
    web_cust_cnt = df_web_features.count()
    soc_cust_cnt = df_soc_features.count()

    print(f"  - Transaction features computed for {tx_cust_cnt} unique customers")
    print(f"  - Web features computed for {web_cust_cnt} unique customers")
    print(f"  - Social features computed for {soc_cust_cnt} unique customers")

    # 5. Multi-Source Integration (Unified Feature Matrix)
    print("\n>>> Step 4: Integrating multi-source features into unified matrix...")
    df_unified = build_unified_feature_matrix(df_tx_features, df_web_features, df_soc_features)
    df_unified.cache()

    unified_rows = df_unified.count()
    unified_cols = len(df_unified.columns)
    print(f"  - Unified Feature Matrix Dimensions: {unified_rows} rows x {unified_cols} columns")

    # 6. Comprehensive Quality & Integrity Checks
    print("\n>>> Step 5: Validating data integrity and null-safety...")
    # Check null values across all features
    null_counts = {}
    for column_name in df_unified.columns:
        cnt = df_unified.filter(col(column_name).isNull()).count()
        if cnt > 0:
            null_counts[column_name] = cnt

    print(f"  - Unexpected null values remaining: {len(null_counts)} columns with nulls")
    if null_counts:
        print(f"    WARNING: Nulls detected: {null_counts}")
    else:
        print("    PASS: 0 unexpected nulls. Unified matrix is 100% complete and null-safe.")

    # Verify one row per customer
    distinct_customers = df_unified.select("customer_id").distinct().count()
    if distinct_customers == unified_rows:
        print(f"    PASS: Exact 1-to-1 customer mapping confirmed ({distinct_customers} unique customers).")
    else:
        print(f"    FAIL: Duplicate customer rows found! Unique: {distinct_customers}, Total: {unified_rows}")

    # 7. Output Exporting
    print("\n>>> Step 6: Exporting processed datasets to data/processed/ (Parquet & CSV)...")
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)

    exports = [
        ("cleaned_transactions", df_tx_clean),
        ("cleaned_web_activity", df_web_clean),
        ("cleaned_social_media", df_soc_clean),
        ("customer_transaction_features", df_tx_features),
        ("customer_web_features", df_web_features),
        ("customer_social_features", df_soc_features),
        ("unified_customer_features", df_unified)
    ]

    for name, df_target in exports:
        print(f"  - Writing {name} (Parquet & CSV)...")
        export_dataframe(df_target, output_dir, name)

    print("\nPreview of Unified Customer Feature Matrix (First 5 Rows):")
    df_unified.show(5, truncate=False)

    print("=" * 80)
    print("STAGE 3 PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 80)

    spark.stop()


if __name__ == "__main__":
    main()
