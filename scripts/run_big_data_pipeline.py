"""
Master PySpark Big Data Processing Pipeline
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Executes:
1. Data Ingestion with Explicit Schemas
2. Data Cleaning & Deduplication
3. Customer-Level Behavioral Aggregation
4. Multi-Source Integration (customer_id)
5. Unified Feature Matrix Generation
6. PyArrow-based Local Parquet & CSV Export
7. End-to-End Verification and Validation Reporting
"""

import os
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pyspark.sql import functions as F
from big_data.spark_session import get_spark_session
from big_data.ingestion.schemas import (
    TRANSACTIONS_SCHEMA,
    WEB_ACTIVITY_SCHEMA,
    SOCIAL_MEDIA_SCHEMA
)
from big_data.preprocessing.cleaners import (
    clean_transactions,
    clean_web_activity,
    clean_social_media
)
from big_data.feature_engineering.aggregators import (
    aggregate_transactions,
    aggregate_web_activity,
    aggregate_social_media,
    build_unified_customer_features
)
from big_data.export_utils import export_spark_dataframe


def run_pipeline():
    start_time = time.time()
    print("=" * 75)
    print("STARTING PYSPARK BIG DATA PIPELINE (STAGE 3)")
    print("=" * 75)

    # 1. Initialize SparkSession
    print("\n[Step 1/6] Initializing SparkSession (local[2], memory: 2g)...")
    spark = get_spark_session("Stage3_PySpark_Pipeline")
    print(f"  * Spark version: {spark.version}")
    print(f"  * Master: {spark.sparkContext.master}")

    raw_dir = os.path.join(PROJECT_ROOT, "data", "raw")
    processed_dir = os.path.join(PROJECT_ROOT, "data", "processed")

    tx_raw_path = os.path.join(raw_dir, "transactions.csv")
    web_raw_path = os.path.join(raw_dir, "web_activity.csv")
    soc_raw_path = os.path.join(raw_dir, "social_media.csv")

    # 2. Data Ingestion with Explicit Schemas
    print("\n[Step 2/6] Ingesting raw datasets with explicit PySpark schemas...")
    raw_tx_df = spark.read.csv(tx_raw_path, header=True, schema=TRANSACTIONS_SCHEMA)
    raw_web_df = spark.read.csv(web_raw_path, header=True, schema=WEB_ACTIVITY_SCHEMA)
    raw_soc_df = spark.read.csv(soc_raw_path, header=True, schema=SOCIAL_MEDIA_SCHEMA)

    print(f"  * Raw Transactions loaded: {raw_tx_df.count()} records")
    print(f"  * Raw Web Activity loaded: {raw_web_df.count()} records")
    print(f"  * Raw Social Media loaded: {raw_soc_df.count()} records")

    # 3. Data Cleaning & Validation
    print("\n[Step 3/6] Applying cleaning, deduplication, and schema standardization...")
    clean_tx_df, tx_metrics = clean_transactions(raw_tx_df)
    clean_web_df, web_metrics = clean_web_activity(raw_web_df)
    clean_soc_df, soc_metrics = clean_social_media(raw_soc_df)

    # Cache cleaned DataFrames for subsequent feature aggregations
    clean_tx_df.cache()
    clean_web_df.cache()
    clean_soc_df.cache()

    print(f"  * Cleaned Transactions: {tx_metrics['final_count']} records (Removed {tx_metrics['duplicates_removed']} duplicates, handled {tx_metrics['missing_values_handled']} missing payment methods)")
    print(f"  * Cleaned Web Activity: {web_metrics['final_count']} records (Removed {web_metrics['duplicates_removed']} duplicates, preserved {web_metrics['legitimate_null_product_ids_preserved']} non-product nulls)")
    print(f"  * Cleaned Social Media: {soc_metrics['final_count']} records (Removed {soc_metrics['duplicates_removed']} duplicates)")

    # 4. Feature Engineering: Customer-Level Aggregations
    print("\n[Step 4/6] Computing customer-level behavioural aggregations...")
    tx_features_df = aggregate_transactions(clean_tx_df)
    web_features_df = aggregate_web_activity(clean_web_df)
    social_features_df = aggregate_social_media(clean_soc_df)

    tx_features_df.cache()
    web_features_df.cache()
    social_features_df.cache()

    print(f"  * Transaction feature records: {tx_features_df.count()} (Columns: {len(tx_features_df.columns)})")
    print(f"  * Web activity feature records: {web_features_df.count()} (Columns: {len(web_features_df.columns)})")
    print(f"  * Social media feature records: {social_features_df.count()} (Columns: {len(social_features_df.columns)})")

    # 5. Multi-Source Integration: Unified Feature Matrix
    print("\n[Step 5/6] Building unified customer feature matrix...")
    unified_features_df = build_unified_customer_features(
        tx_features_df,
        web_features_df,
        social_features_df
    )
    unified_features_df.cache()

    total_customers = unified_features_df.count()
    total_cols = len(unified_features_df.columns)
    print(f"  * Unified customer feature matrix shape: ({total_customers} rows, {total_cols} columns)")

    # Assert exactly 1 row per customer
    distinct_customers = unified_features_df.select("customer_id").distinct().count()
    assert total_customers == distinct_customers, f"Duplicate customer rows found! {total_customers} != {distinct_customers}"

    # 6. Exporting Outputs via PyArrow
    print("\n[Step 6/6] Exporting verified processed datasets to data/processed/ (Parquet & CSV)...")
    exports = [
        ("cleaned_transactions", clean_tx_df),
        ("cleaned_web_activity", clean_web_df),
        ("cleaned_social_media", clean_soc_df),
        ("customer_transaction_features", tx_features_df),
        ("customer_web_features", web_features_df),
        ("customer_social_features", social_features_df),
        ("unified_customer_features", unified_features_df)
    ]

    export_results = []
    for base_name, df_obj in exports:
        res = export_spark_dataframe(
            df=df_obj,
            output_dir=processed_dir,
            base_name=base_name,
            batch_size=25000,
            export_parquet=True,
            export_csv=True
        )
        export_results.append(res)
        print(f"  - Verified {base_name}: {res['spark_row_count']} rows -> Parquet & CSV validated successfully.")

    # Check for any unexpected null values across the unified feature matrix
    null_counts = {}
    for col_name in unified_features_df.columns:
        nc = unified_features_df.filter(F.col(col_name).isNull()).count()
        if nc > 0:
            null_counts[col_name] = nc

    elapsed_time = round(time.time() - start_time, 2)

    # Print Final Verification & Audit Summary
    print("\n" + "=" * 75)
    print("STAGE 3 PIPELINE EXECUTION SUMMARY & VERIFICATION REPORT")
    print("=" * 75)
    print(f"Total Execution Time: {elapsed_time} seconds\n")

    print("1. DATASET CLEANING & DEDUPLICATION AUDIT:")
    print(f"  * Transactions:")
    print(f"      Original Records:       {tx_metrics['original_count']}")
    print(f"      Duplicates Removed:     {tx_metrics['duplicates_removed']}")
    print(f"      Missing Values Handled: {tx_metrics['missing_values_handled']} ('Unknown' imputed)")
    print(f"      Invalid Records:        {tx_metrics['invalid_records_filtered']}")
    print(f"      Final Cleaned Records:  {tx_metrics['final_count']}")
    print(f"      Unique Customers:       {tx_metrics['unique_customers']}")

    print(f"  * Web Activity:")
    print(f"      Original Records:       {web_metrics['original_count']}")
    print(f"      Duplicates Removed:     {web_metrics['duplicates_removed']}")
    print(f"      Legitimate Null Preserved: {web_metrics['legitimate_null_product_ids_preserved']}")
    print(f"      Invalid Records:        {web_metrics['invalid_records_filtered']}")
    print(f"      Final Cleaned Records:  {web_metrics['final_count']}")
    print(f"      Unique Customers:       {web_metrics['unique_customers']}")

    print(f"  * Social Media:")
    print(f"      Original Records:       {soc_metrics['original_count']}")
    print(f"      Duplicates Removed:     {soc_metrics['duplicates_removed']}")
    print(f"      Invalid Records:        {soc_metrics['invalid_records_filtered']}")
    print(f"      Final Cleaned Records:  {soc_metrics['final_count']}")
    print(f"      Unique Customers:       {soc_metrics['unique_customers']}")

    print("\n2. UNIFIED FEATURE MATRIX METRICS:")
    print(f"  * Total Customer Dimension: {total_customers} rows (1 row per customer verified)")
    print(f"  * Feature Count:            {total_cols} columns")
    print(f"  * Columns: {', '.join(unified_features_df.columns)}")
    print(f"  * Unexpected Null Values:   {len(null_counts)} columns with nulls")
    if null_counts:
        print(f"      WARNING: Null details: {null_counts}")
    else:
        print(f"      SUCCESS: 0 unexpected null values across all {total_cols} columns.")

    print("\n3. VERIFIED PROCESSED OUTPUT FILES (data/processed/):")
    for r in export_results:
        print(f"  * {r['base_name']}: {r['spark_row_count']} rows [Parquet: OK, CSV: OK]")

    spark.stop()
    print("\n" + "=" * 75)
    print("STAGE 3 COMPLETED SUCCESSFULLY.")
    print("=" * 75)


if __name__ == "__main__":
    run_pipeline()

