"""
Master PySpark Big Data Processing Pipeline (HDFS & Local Staged Storage)
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Executes:
1. Data Ingestion from Genuine Apache Hadoop HDFS (or local staged fallback)
2. Data Cleaning & Deduplication
3. Customer-Level Behavioral Aggregation
4. Multi-Source Integration (customer_id)
5. Unified Feature Matrix Generation
6. Distributed HDFS Parquet Storage & PyArrow Local Export
7. End-to-End Verification and Validation Reporting
"""

import os
import sys
import time
import json
import socket
import argparse
import subprocess
from datetime import datetime

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


def get_wsl_ip() -> str:
    """Dynamically queries the current WSL2 Debian IP address."""
    try:
        out = subprocess.check_output(['wsl', '-d', 'Debian', 'hostname', '-I'], text=True)
        return out.strip().split()[0]
    except Exception as e:
        raise RuntimeError(f"Failed to query WSL2 IP address: {e}")


def verify_hdfs_socket(ip: str, port: int = 9000, timeout: float = 3.0):
    """Verifies TCP socket connectivity to the HDFS NameNode."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        s.close()
    except Exception as e:
        raise RuntimeError(
            f"HDFS NameNode at {ip}:{port} is unreachable: {e}. "
            "Cannot proceed with HDFS storage. Verify WSL HDFS daemons."
        )


def run_pipeline(storage_mode: str = "hdfs", export_local: bool = True):
    start_time = time.time()
    print("=" * 80)
    print(f"STARTING PYSPARK BIG DATA PIPELINE (STORAGE MODE: {storage_mode.upper()})")
    print("=" * 80)

    wsl_ip = None
    hdfs_base_uri = None

    if storage_mode == "hdfs":
        print("\n[Step 1/7] Resolving HDFS cluster endpoints and auditing connectivity...")
        wsl_ip = get_wsl_ip()
        print(f"  * WSL2 Host Address: {wsl_ip}")
        print(f"  * Testing NameNode RPC (port 9000)...")
        verify_hdfs_socket(wsl_ip, 9000)
        print(f"    [PASS] NameNode RPC reachable at {wsl_ip}:9000")
        print(f"  * Testing DataNode Block Transfer (port 9866)...")
        verify_hdfs_socket(wsl_ip, 9866)
        print(f"    [PASS] DataNode reachable at {wsl_ip}:9866")
        hdfs_base_uri = f"hdfs://{wsl_ip}:9000/customer-analytics"
    elif storage_mode == "local":
        print("\n[Step 1/7] Using explicit local filesystem staged storage fallback...")
    else:
        raise ValueError(f"Unknown storage_mode: '{storage_mode}'. Must be 'hdfs' or 'local'.")

    # 1. Initialize SparkSession
    print("\n[Step 2/7] Initializing SparkSession (local[2], memory: 2g)...")
    spark = get_spark_session("Stage9_PySpark_HDFS_Pipeline")
    print(f"  * Spark version: {spark.version}")
    print(f"  * Master: {spark.sparkContext.master}")

    raw_dir = os.path.join(PROJECT_ROOT, "data", "raw")
    processed_dir = os.path.join(PROJECT_ROOT, "data", "processed")

    if storage_mode == "hdfs":
        tx_raw_path = f"{hdfs_base_uri}/raw/transactions/transactions.csv"
        web_raw_path = f"{hdfs_base_uri}/raw/web_activity/web_activity.csv"
        soc_raw_path = f"{hdfs_base_uri}/raw/social_media/social_media.csv"
    else:
        tx_raw_path = os.path.join(raw_dir, "transactions.csv")
        web_raw_path = os.path.join(raw_dir, "web_activity.csv")
        soc_raw_path = os.path.join(raw_dir, "social_media.csv")

    # 2. Data Ingestion with Explicit Schemas
    print(f"\n[Step 3/7] Ingesting raw datasets from {storage_mode.upper()} storage...")
    print(f"  * Transactions source: {tx_raw_path}")
    print(f"  * Web activity source: {web_raw_path}")
    print(f"  * Social media source: {soc_raw_path}")

    raw_tx_df = spark.read.csv(tx_raw_path, header=True, schema=TRANSACTIONS_SCHEMA)
    raw_web_df = spark.read.csv(web_raw_path, header=True, schema=WEB_ACTIVITY_SCHEMA)
    raw_soc_df = spark.read.csv(soc_raw_path, header=True, schema=SOCIAL_MEDIA_SCHEMA)

    raw_tx_count = raw_tx_df.count()
    raw_web_count = raw_web_df.count()
    raw_soc_count = raw_soc_df.count()

    print(f"  * Raw Transactions loaded: {raw_tx_count} records")
    print(f"  * Raw Web Activity loaded: {raw_web_count} records")
    print(f"  * Raw Social Media loaded: {raw_soc_count} records")

    # 3. Data Cleaning & Validation
    print("\n[Step 4/7] Applying cleaning, deduplication, and schema standardization...")
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

    # Assert baseline cleaned record counts match verified numbers
    assert tx_metrics['final_count'] == 12214, f"Cleaned transactions count mismatch: {tx_metrics['final_count']} != 12214"
    assert web_metrics['final_count'] == 120944, f"Cleaned web activity count mismatch: {web_metrics['final_count']} != 120944"
    assert soc_metrics['final_count'] == 8828, f"Cleaned social media count mismatch: {soc_metrics['final_count']} != 8828"

    # 4. Feature Engineering: Customer-Level Aggregations
    print("\n[Step 5/7] Computing customer-level behavioural aggregations...")
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
    print("\n[Step 6/7] Building unified customer feature matrix...")
    unified_features_df = build_unified_customer_features(
        tx_features_df,
        web_features_df,
        social_features_df
    )
    unified_features_df.cache()

    total_customers = unified_features_df.count()
    total_cols = len(unified_features_df.columns)
    print(f"  * Unified customer feature matrix shape: ({total_customers} rows, {total_cols} columns)")

    # Assert exactly 1,200 unique customers with 23 features
    assert total_customers == 1200, f"Customer row count mismatch: {total_customers} != 1200"
    assert total_cols == 23, f"Customer feature column count mismatch: {total_cols} != 23"
    distinct_customers = unified_features_df.select("customer_id").distinct().count()
    assert total_customers == distinct_customers, f"Duplicate customer rows found! {total_customers} != {distinct_customers}"

    # Check for unexpected nulls
    null_counts = {}
    for col_name in unified_features_df.columns:
        nc = unified_features_df.filter(F.col(col_name).isNull()).count()
        if nc > 0:
            null_counts[col_name] = nc
    assert len(null_counts) == 0, f"Unexpected null values found in unified features: {null_counts}"

    # 6. Exporting Outputs: HDFS Distributed Storage & Local Mirroring
    print("\n[Step 7/7] Storing outputs to HDFS Parquet and mirroring locally for downstream ML/API...")
    
    hdfs_write_results = []
    if storage_mode == "hdfs":
        hdfs_targets = [
            ("processed/cleaned_transactions", clean_tx_df),
            ("processed/cleaned_web_activity", clean_web_df),
            ("processed/cleaned_social_media", clean_soc_df),
            ("features/customer_transaction_features", tx_features_df),
            ("features/customer_web_features", web_features_df),
            ("features/customer_social_features", social_features_df),
            ("features/unified_customer_features", unified_features_df)
        ]
        print(f"  * Writing {len(hdfs_targets)} datasets directly to HDFS in Parquet format...")
        for rel_path, df_obj in hdfs_targets:
            target_uri = f"{hdfs_base_uri}/{rel_path}"
            df_obj.write.mode("overwrite").parquet(target_uri)
            # Immediate readback verification
            read_df = spark.read.parquet(target_uri)
            rb_count = read_df.count()
            expected = df_obj.count()
            assert rb_count == expected, f"HDFS verification failed for {rel_path}: {rb_count} != {expected}"
            hdfs_write_results.append({
                "target_uri": target_uri,
                "dataset": rel_path,
                "rows_verified": rb_count,
                "status": "VERIFIED"
            })
            print(f"    - [HDFS OK] {rel_path}: {rb_count} rows written & verified.")

    local_export_results = []
    if export_local:
        print("  * Mirroring local artifacts to data/processed/ for existing ML & REST API...")
        local_exports = [
            ("cleaned_transactions", clean_tx_df),
            ("cleaned_web_activity", clean_web_df),
            ("cleaned_social_media", clean_soc_df),
            ("customer_transaction_features", tx_features_df),
            ("customer_web_features", web_features_df),
            ("customer_social_features", social_features_df),
            ("unified_customer_features", unified_features_df)
        ]
        for base_name, df_obj in local_exports:
            res = export_spark_dataframe(
                df=df_obj,
                output_dir=processed_dir,
                base_name=base_name,
                batch_size=25000,
                export_parquet=True,
                export_csv=True
            )
            local_export_results.append(res)
            print(f"    - [LOCAL OK] {base_name}: {res['spark_row_count']} rows exported.")

    elapsed_time = round(time.time() - start_time, 2)

    # Save pipeline execution metadata for Backend & Dashboard consumption
    metadata = {
        "pipeline_name": "Smart Customer Analysis Big Data Pipeline",
        "storage_mode": storage_mode,
        "execution_mode": "PySpark local[2] Batch Processing",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": elapsed_time,
        "hdfs": {
            "namenode_uri": f"hdfs://{wsl_ip}:9000" if wsl_ip else "N/A",
            "base_uri": hdfs_base_uri if hdfs_base_uri else "N/A",
            "wsl_ip": wsl_ip,
            "status": "CONNECTED" if storage_mode == "hdfs" else "STANDBY",
            "datasets_stored": len(hdfs_write_results)
        },
        "datasets": {
            "transactions": {
                "raw": raw_tx_count,
                "cleaned": tx_metrics['final_count'],
                "duplicates_removed": tx_metrics['duplicates_removed']
            },
            "web_activity": {
                "raw": raw_web_count,
                "cleaned": web_metrics['final_count'],
                "duplicates_removed": web_metrics['duplicates_removed']
            },
            "social_media": {
                "raw": raw_soc_count,
                "cleaned": soc_metrics['final_count'],
                "duplicates_removed": soc_metrics['duplicates_removed']
            },
            "unified_customer_features": {
                "total_customers": total_customers,
                "features_count": total_cols,
                "unexpected_nulls": 0
            }
        }
    }

    meta_file = os.path.join(processed_dir, "hdfs_pipeline_metadata.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Print Final Verification & Audit Summary
    print("\n" + "=" * 80)
    print("STAGE 9 PIPELINE EXECUTION SUMMARY & VERIFICATION REPORT")
    print("=" * 80)
    print(f"Total Execution Time: {elapsed_time} seconds")
    print(f"Storage Layer:        {storage_mode.upper()} (HDFS URI: {hdfs_base_uri})")
    print(f"Unified Customer Dim: {total_customers} rows x {total_cols} columns (0 nulls)")
    print(f"HDFS Verified Sets:   {len(hdfs_write_results)} Parquet datasets verified")
    print(f"Metadata Recorded:    {meta_file}")
    print("=" * 80)

    spark.stop()
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PySpark Big Data Processing Pipeline")
    parser.add_argument(
        "--storage",
        choices=["hdfs", "local"],
        default="hdfs",
        help="Storage layer to use: 'hdfs' (default genuine Hadoop storage) or 'local' (explicit fallback)"
    )
    args = parser.parse_args()
    run_pipeline(storage_mode=args.storage)
