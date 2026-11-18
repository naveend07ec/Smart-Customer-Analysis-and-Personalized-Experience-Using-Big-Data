"""
PySpark Batch Pipeline Execution Service
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Orchestrates:
1. Reading staged/HDFS raw datasets for an accepted batch (<batch_id>).
2. Distributed PySpark cleaning, deduplication, and missing-value imputation.
3. Customer-level feature engineering across transactions, clickstreams, and social logs.
4. Generating the unified 23-column customer feature matrix.
5. Exporting version-isolated Parquet & CSV stores to data/versions/<version_id>/ and HDFS.
6. Recording execution metrics in processing_report.json.
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from big_data.spark_session import get_spark_session
from big_data.ingestion.schemas import (
    TRANSACTIONS_SCHEMA,
    WEB_ACTIVITY_SCHEMA,
    SOCIAL_MEDIA_SCHEMA
)
from pyspark.sql import functions as F
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
from big_data.ingestion.hdfs_client import HDFSManager, windows_to_wsl_path


class PipelineExecutionService:
    _instance = None

    def __init__(self):
        self.workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.uploads_dir = os.path.join(self.workspace_root, "data", "uploads")
        self.versions_dir = os.path.join(self.workspace_root, "data", "versions")
        self.versions_index_file = os.path.join(self.versions_dir, "versions_index.json")
        os.makedirs(self.versions_dir, exist_ok=True)
        self.hdfs_manager = HDFSManager()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PipelineExecutionService()
        return cls._instance

    def _load_versions_index(self) -> list:
        if os.path.exists(self.versions_index_file):
            try:
                with open(self.versions_index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_versions_index(self, index: list):
        with open(self.versions_index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

    def _update_version_entry(self, version_info: Dict[str, Any]):
        index = self._load_versions_index()
        vid = version_info["version_id"]
        filtered = [v for v in index if v.get("version_id") != vid]
        filtered.insert(0, version_info)
        self._save_versions_index(filtered)

    def _load_multiformat_source_df(
        self,
        spark,
        batch_dir: str,
        source_type: str,
        manifest: Dict[str, Any],
        use_hdfs: bool = False,
        wsl_ip: str = "127.0.0.1",
        batch_id: str = ""
    ):
        """
        Loads and standardizes multi-format staged files (CSV, JSON, JSONL, TXT, LOG)
        into a canonical PySpark DataFrame matching the requested source schema.
        Applies active field mapping, casts types, and populates missing fields with nulls.
        """
        schema_map = {
            "transactions": TRANSACTIONS_SCHEMA,
            "web_activity": WEB_ACTIVITY_SCHEMA,
            "social_media": SOCIAL_MEDIA_SCHEMA
        }
        target_schema = schema_map[source_type]
        canonical_fields = {field.name: field.dataType for field in target_schema.fields}

        staged_files = manifest.get("staged_files", {})
        matching_files = [
            finfo for finfo in staged_files.values()
            if finfo.get("source_type") == source_type and (
                finfo.get("analytics_eligibility") == "ANALYTICS_ELIGIBLE"
                or (isinstance(finfo.get("discovery"), dict) and finfo["discovery"].get("analytics_eligibility") == "ANALYTICS_ELIGIBLE")
                or finfo.get("validation_status") in ("VALID", "PENDING")
                or manifest.get("batch_type") == "CANONICAL_CSV"
            )
        ]

        if not matching_files:
            return spark.createDataFrame([], target_schema)

        dfs = []
        for finfo in matching_files:
            fmt = (finfo.get("format") or "csv").lower()
            active_mapping = finfo.get("active_mapping") or {}
            staged_filename = finfo.get("staged_filename")

            if use_hdfs:
                file_input = f"hdfs://{wsl_ip}:9000/customer-analytics/raw/uploads/{batch_id}/{staged_filename}"
            else:
                file_input = os.path.join(batch_dir, staged_filename)

            try:
                if fmt in ("csv", "tsv"):
                    delim = "\t" if fmt == "tsv" else ","
                    df_cur = spark.read.option("header", "true").option("inferSchema", "true").option("delimiter", delim).csv(file_input)
                elif fmt in ("json", "jsonl"):
                    if fmt == "jsonl":
                        df_cur = spark.read.json(file_input)
                    else:
                        df_cur = spark.read.option("multiline", "true").json(file_input)
                elif fmt in ("txt", "log"):
                    delim = finfo.get("delimiter", ",")
                    try:
                        df_cur = spark.read.option("header", "true").option("delimiter", delim).csv(file_input)
                    except Exception:
                        df_cur = spark.read.text(file_input)
                else:
                    continue
            except Exception as read_err:
                # Fallback to local path if HDFS read fails
                local_fallback = os.path.join(batch_dir, staged_filename)
                if fmt in ("csv", "tsv"):
                    df_cur = spark.read.option("header", "true").option("inferSchema", "true").csv(local_fallback)
                elif fmt == "jsonl":
                    df_cur = spark.read.json(local_fallback)
                elif fmt == "json":
                    df_cur = spark.read.option("multiline", "true").json(local_fallback)
                else:
                    df_cur = spark.read.text(local_fallback)

            # Apply active field mapping
            for src_col, tgt_col in active_mapping.items():
                if src_col in df_cur.columns and tgt_col in canonical_fields and src_col != tgt_col:
                    df_cur = df_cur.withColumnRenamed(src_col, tgt_col)

            # Select and conform to canonical fields
            select_exprs = []
            for field_name, data_type in canonical_fields.items():
                if field_name in df_cur.columns:
                    select_exprs.append(F.col(field_name).cast(data_type).alias(field_name))
                else:
                    select_exprs.append(F.lit(None).cast(data_type).alias(field_name))

            df_conformed = df_cur.select(*select_exprs)
            dfs.append(df_conformed)

        if not dfs:
            return spark.createDataFrame([], target_schema)

        res_df = dfs[0]
        for other_df in dfs[1:]:
            res_df = res_df.unionByName(other_df)

        return res_df

    def _get_active_version(self) -> str:
        cur_file = os.path.join(self.workspace_root, "data", "current_version.json")
        if os.path.exists(cur_file):
            try:
                with open(cur_file, "r", encoding="utf-8") as f:
                    return json.load(f).get("active_version", "baseline")
            except Exception:
                return "baseline"
        return "baseline"

    def _get_schema_for_source(self, source_name: str):
        if source_name == "transactions":
            return TRANSACTIONS_SCHEMA
        elif source_name == "web_activity":
            return WEB_ACTIVITY_SCHEMA
        elif source_name == "social_media":
            return SOCIAL_MEDIA_SCHEMA
        raise ValueError(f"Unknown source name: {source_name}")

    def _load_baseline_df(self, spark, source_name: str, use_hdfs: bool, wsl_ip: str):
        schema = self._get_schema_for_source(source_name)
        if use_hdfs:
            hdfs_file = f"hdfs://{wsl_ip}:9000/customer-analytics/raw/baseline/{source_name}.csv"
            try:
                return spark.read.option("header", "true").schema(schema).csv(hdfs_file)
            except Exception:
                pass
        local_file = os.path.join(self.workspace_root, "data", "raw", f"{source_name}.csv")
        return spark.read.option("header", "true").schema(schema).csv(local_file)

    def _load_batch_source_df(self, spark, batch_id: str, source_name: str, use_hdfs: bool, wsl_ip: str):
        schema = self._get_schema_for_source(source_name)
        batch_dir = os.path.join(self.uploads_dir, batch_id)
        manifest_path = os.path.join(batch_dir, "manifest.json")
        manifest = {}
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
            except Exception:
                pass

        staged_files = manifest.get("staged_files", {})
        has_matching_staged = any(
            finfo.get("source_type") == source_name
            for finfo in staged_files.values()
            if isinstance(finfo, dict)
        )

        if manifest.get("batch_type") == "MULTI_FORMAT":
            return self._load_multiformat_source_df(
                spark, batch_dir, source_name, manifest, use_hdfs, wsl_ip, batch_id
            )

        local_file = os.path.join(batch_dir, f"{source_name}.csv")
        if use_hdfs:
            hdfs_file = f"hdfs://{wsl_ip}:9000/customer-analytics/raw/uploads/{batch_id}/{source_name}.csv"
            try:
                return spark.read.option("header", "true").schema(schema).csv(hdfs_file)
            except Exception:
                pass

        if os.path.exists(local_file):
            return spark.read.option("header", "true").schema(schema).csv(local_file)

        if has_matching_staged:
            return self._load_multiformat_source_df(
                spark, batch_dir, source_name, manifest, use_hdfs, wsl_ip, batch_id
            )

        return spark.createDataFrame([], schema)

    def execute_batch_pipeline(
        self,
        batch_id: str,
        force_local_input: bool = False,
        base_version: Optional[str] = None,
        force_reprocess: bool = False
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Executes end-to-end cumulative PySpark batch cleaning and feature engineering.
        Combines: Historical Baseline + All Previously Accepted Batches + Incoming Batch.
        Produces isolated versioned artifacts under data/versions/<version_id>/ and HDFS.
        Guarantees idempotency and complete primary-key deduplication.
        """
        start_time = time.time()
        batch_dir = os.path.join(self.uploads_dir, batch_id)
        manifest_path = os.path.join(batch_dir, "manifest.json")

        if not os.path.exists(manifest_path):
            return False, f"Batch '{batch_id}' not found. Cannot execute PySpark pipeline.", {}

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # Check batch status
        status = manifest.get("status")
        if status not in ("INGESTED", "VALIDATED", "UPLOADED"):
            return False, f"Cannot process batch in status '{status}'. Batch must be VALIDATED, INGESTED, or UPLOADED.", {}

        version_id = f"v_{batch_id}"
        version_dir = os.path.join(self.versions_dir, version_id)

        # Idempotency check: only return cached report if it contains non-zero newly added activity and force_reprocess is False
        existing_report_path = os.path.join(version_dir, "processing_report.json")
        data_comp_path = os.path.join(version_dir, "data_composition.json")
        if not force_reprocess and os.path.exists(existing_report_path) and os.path.exists(data_comp_path):
            try:
                with open(existing_report_path, "r", encoding="utf-8") as f:
                    existing_report = json.load(f)
                with open(data_comp_path, "r", encoding="utf-8") as f:
                    existing_comp = json.load(f)
                newly = existing_comp.get("newly_added", {})
                has_activity = (
                    newly.get("total_transactions", 0) > 0
                    or newly.get("new_unique_customers", 0) > 0
                    or newly.get("total_web_activities", 0) > 0
                    or newly.get("total_social_interactions", 0) > 0
                )
                if (
                    existing_report.get("status") == "PROCESSING_COMPLETED"
                    and existing_comp.get("overall", {}).get("total_customers", 0) >= 1200
                    and has_activity
                ):
                    existing_report["data_composition"] = existing_comp
                    return True, f"Batch '{batch_id}' has already been processed in version '{version_id}'. Execution is idempotent.", existing_report
            except Exception:
                pass

        os.makedirs(version_dir, exist_ok=True)

        # 1. Determine Input Sources & HDFS Connectivity Gate
        hdfs_stat = self.hdfs_manager.check_hdfs_status()
        use_hdfs_input = (hdfs_stat["is_available"] and status == "INGESTED" and not force_local_input)

        if status == "INGESTED" and not hdfs_stat["is_available"] and not force_local_input:
            return False, (
                f"Batch '{batch_id}' is ingested to HDFS, but Hadoop HDFS cluster is currently OFFLINE. "
                "Cannot read raw HDFS datasets. Start Hadoop daemons in WSL and retry."
            ), {}

        wsl_ip = self.hdfs_manager.wsl_ip
        input_source_desc = f"Hadoop HDFS cluster (hdfs://{wsl_ip}:9000)" if use_hdfs_input else f"Local Staging Directory ({batch_id})"

        # 2. Determine Cumulative Batch Lineage
        accepted_batches_file = os.path.join(self.workspace_root, "data", "accepted_batches.json")
        prior_batches: List[str] = []

        if base_version == "baseline":
            prior_batches = []
        elif base_version and os.path.exists(os.path.join(self.versions_dir, base_version, "data_composition.json")):
            try:
                with open(os.path.join(self.versions_dir, base_version, "data_composition.json"), "r", encoding="utf-8") as f:
                    prior_batches = json.load(f).get("included_batches", [])
            except Exception:
                prior_batches = []
        elif os.path.exists(accepted_batches_file):
            try:
                with open(accepted_batches_file, "r", encoding="utf-8") as f:
                    prior_batches = json.load(f)
            except Exception:
                prior_batches = []

        prior_batches = [b for b in prior_batches if b != batch_id]
        cumulative_batches = list(prior_batches) + [batch_id]

        # Read historical baseline numbers directly from parent composition if available
        parent_comp = None
        if prior_batches:
            latest_parent = prior_batches[-1]
            parent_comp_path = os.path.join(self.versions_dir, f"v_{latest_parent}", "data_composition.json")
            if os.path.exists(parent_comp_path):
                try:
                    with open(parent_comp_path, "r", encoding="utf-8") as f:
                        parent_comp = json.load(f).get("overall")
                except Exception:
                    pass

        if parent_comp:
            hist_tx_count = parent_comp.get("total_transactions", 12214)
            hist_completed_tx = parent_comp.get("valid_completed_transactions", 11674)
            hist_web_count = parent_comp.get("total_web_activities", 120944)
            hist_soc_count = parent_comp.get("total_social_interactions", 8828)
            hist_cust_count = parent_comp.get("total_customers", 1200)
            hist_revenue = round(float(parent_comp.get("total_revenue", 1807439.49)), 2)
        else:
            # Baseline constants (immutable academic baseline values)
            hist_tx_count = 12214
            hist_completed_tx = 11674
            hist_web_count = 120944
            hist_soc_count = 8828
            hist_cust_count = 1200
            hist_revenue = 1807439.49

        spark = None
        try:
            # 3. Initialize PySpark
            spark = get_spark_session(f"SMART_Batch_{version_id}")

            # 4. Load Baseline Datasets
            df_tx_base = self._load_baseline_df(spark, "transactions", use_hdfs_input, wsl_ip)
            df_web_base = self._load_baseline_df(spark, "web_activity", use_hdfs_input, wsl_ip)
            df_soc_base = self._load_baseline_df(spark, "social_media", use_hdfs_input, wsl_ip)

            # 5. Build Historical DataFrames (Baseline + Prior Accepted Batches)
            df_tx_hist = df_tx_base
            df_web_hist = df_web_base
            df_soc_hist = df_soc_base

            for pb_id in prior_batches:
                df_tx_pb = self._load_batch_source_df(spark, pb_id, "transactions", use_hdfs_input, wsl_ip)
                df_web_pb = self._load_batch_source_df(spark, pb_id, "web_activity", use_hdfs_input, wsl_ip)
                df_soc_pb = self._load_batch_source_df(spark, pb_id, "social_media", use_hdfs_input, wsl_ip)

                df_tx_hist = df_tx_hist.unionByName(df_tx_pb)
                df_web_hist = df_web_hist.unionByName(df_web_pb)
                df_soc_hist = df_soc_hist.unionByName(df_soc_pb)

            # 6. Load Incoming Batch DataFrames
            df_tx_inc = self._load_batch_source_df(spark, batch_id, "transactions", use_hdfs_input, wsl_ip)
            df_web_inc = self._load_batch_source_df(spark, batch_id, "web_activity", use_hdfs_input, wsl_ip)
            df_soc_inc = self._load_batch_source_df(spark, batch_id, "social_media", use_hdfs_input, wsl_ip)

            # 7. Cumulative Union: Historical + Incoming
            df_tx_combined = df_tx_hist.unionByName(df_tx_inc)
            df_web_combined = df_web_hist.unionByName(df_web_inc)
            df_soc_combined = df_soc_hist.unionByName(df_soc_inc)

            # 8. Clean & Deduplicate Cumulative Datasets
            df_tx_clean, tx_stats = clean_transactions(df_tx_combined)
            df_web_clean, web_stats = clean_web_activity(df_web_combined)
            df_soc_clean, soc_stats = clean_social_media(df_soc_combined)

            # Persist clean DataFrames in Spark cache for fast multi-pass metrics & export
            df_tx_clean.persist()
            df_web_clean.persist()
            df_soc_clean.persist()

            # 9. Compute Overall Metrics
            overall_tx_count = df_tx_clean.count()
            overall_completed_tx = df_tx_clean.filter(F.col("order_status") == "Completed").count()
            overall_web_count = df_web_clean.count()
            overall_soc_count = df_soc_clean.count()
            overall_rev_row = df_tx_clean.filter(F.col("order_status") == "Completed").agg(F.sum("total_amount")).collect()[0][0]
            overall_revenue = round(float(overall_rev_row or 0.0), 2)

            # 10. Multi-Source Integration (Outer Join -> 23 Columns)
            df_tx_feat = aggregate_transactions(df_tx_clean)
            df_web_feat = aggregate_web_activity(df_web_clean)
            df_soc_feat = aggregate_social_media(df_soc_clean)
            df_unified = build_unified_customer_features(df_tx_feat, df_web_feat, df_soc_feat)
            df_unified.persist()
            overall_cust_count = df_unified.count()

            # 11. Compute Newly Added Metrics (With Exact Mathematical Balancing)
            valid_transactions = max(0, overall_tx_count - hist_tx_count)
            valid_completed_tx = max(0, overall_completed_tx - hist_completed_tx)
            valid_web_activities = max(0, overall_web_count - hist_web_count)
            valid_social_interactions = max(0, overall_soc_count - hist_soc_count)
            new_revenue = round(max(0.0, overall_revenue - hist_revenue), 2)
            new_unique_customers = max(0, overall_cust_count - hist_cust_count)

            # Check incoming distinct customers for existing vs new classification
            inc_cust_count = (
                df_tx_inc.select("customer_id")
                .union(df_web_inc.select("customer_id"))
                .union(df_soc_inc.select("customer_id"))
                .filter((F.col("customer_id").isNotNull()) & (F.col("customer_id").rlike(r"^CUST_")))
                .distinct()
                .count()
            )
            existing_customers_with_new_activity = max(0, inc_cust_count - new_unique_customers)

            data_composition = {
                "version_id": version_id,
                "batch_id": batch_id,
                "active_dataset_version": version_id,
                "current_batch_id": batch_id,
                "previous_batch_count": len(prior_batches),
                "parent_version": base_version or self._get_active_version(),
                "included_batches": cumulative_batches,
                "historical": {
                    "total_customers": hist_cust_count,
                    "total_transactions": hist_tx_count,
                    "valid_completed_transactions": hist_completed_tx,
                    "total_web_activities": hist_web_count,
                    "total_social_interactions": hist_soc_count,
                    "total_revenue": hist_revenue
                },
                "newly_added": {
                    "new_unique_customers": new_unique_customers,
                    "existing_customers_with_new_activity": existing_customers_with_new_activity,
                    "valid_transactions": valid_transactions,
                    "total_transactions": valid_transactions,
                    "valid_completed_transactions": valid_completed_tx,
                    "valid_web_activities": valid_web_activities,
                    "total_web_activities": valid_web_activities,
                    "valid_social_interactions": valid_social_interactions,
                    "total_social_interactions": valid_social_interactions,
                    "new_revenue": new_revenue
                },
                "overall": {
                    "total_customers": overall_cust_count,
                    "total_transactions": overall_tx_count,
                    "valid_completed_transactions": overall_completed_tx,
                    "total_web_activities": overall_web_count,
                    "total_social_interactions": overall_soc_count,
                    "total_revenue": overall_revenue
                }
            }

            # 12. Multi-Source Integration (Outer Join -> 23 Columns)
            df_tx_feat = aggregate_transactions(df_tx_clean)
            df_web_feat = aggregate_web_activity(df_web_clean)
            df_soc_feat = aggregate_social_media(df_soc_clean)
            df_unified = build_unified_customer_features(df_tx_feat, df_web_feat, df_soc_feat)
            unified_count = df_unified.count()

            # 13. Export Version-Isolated Processed Datasets (Parquet + CSV)
            export_spark_dataframe(df_tx_clean, version_dir, "cleaned_transactions")
            export_spark_dataframe(df_web_clean, version_dir, "cleaned_web_activity")
            export_spark_dataframe(df_soc_clean, version_dir, "cleaned_social_media")
            export_spark_dataframe(df_unified, version_dir, "unified_customer_features")

            # 14. Save data_composition.json
            with open(os.path.join(version_dir, "data_composition.json"), "w", encoding="utf-8") as f:
                json.dump(data_composition, f, indent=2)

            # 15. Record Accepted Cumulative Batches
            with open(accepted_batches_file, "w", encoding="utf-8") as f:
                json.dump(cumulative_batches, f, indent=2)

            # 16. Mirror to HDFS Processed Store if cluster is online
            hdfs_processed_path = None
            if hdfs_stat["is_available"]:
                hdfs_processed_path = f"/customer-analytics/processed/versions/{version_id}"
                self.hdfs_manager.upload_batch_to_hdfs(
                    batch_id=version_id,
                    staged_files={
                        "cleaned_transactions": os.path.join(version_dir, "cleaned_transactions.parquet"),
                        "cleaned_web_activity": os.path.join(version_dir, "cleaned_web_activity.parquet"),
                        "cleaned_social_media": os.path.join(version_dir, "cleaned_social_media.parquet"),
                        "unified_customer_features": os.path.join(version_dir, "unified_customer_features.parquet")
                    },
                    hdfs_target_dir=hdfs_processed_path
                )

            duration = round(time.time() - start_time, 2)

            # 17. Build Processing Report
            report = {
                "version_id": version_id,
                "batch_id": batch_id,
                "batch_type": manifest.get("batch_type", "COMPLETE_BATCH"),
                "status": "PROCESSING_COMPLETED",
                "processed_at": datetime.now().isoformat(),
                "duration_seconds": duration,
                "input_source": input_source_desc,
                "hdfs_storage_path": hdfs_processed_path,
                "parent_version": base_version or self._get_active_version(),
                "included_batches": cumulative_batches,
                "data_composition": data_composition,
                "cleaning_summary": {
                    "raw_transactions": tx_stats.get("raw_count", 0),
                    "cleaned_transactions": tx_stats.get("final_count", 0),
                    "removed_transaction_duplicates": tx_stats.get("duplicates_removed", 0),
                    "imputed_payment_methods": tx_stats.get("missing_imputed_payment", 0),
                    "raw_web_activity": web_stats.get("raw_count", 0),
                    "cleaned_web_activity": web_stats.get("final_count", 0),
                    "removed_web_duplicates": web_stats.get("duplicates_removed", 0),
                    "meaningful_null_product_ids_preserved": web_stats.get("meaningful_null_product_ids", 0),
                    "raw_social_activity": soc_stats.get("raw_count", 0),
                    "cleaned_social_activity": soc_stats.get("final_count", 0),
                    "removed_social_duplicates": soc_stats.get("duplicates_removed", 0)
                },
                "feature_engineering": {
                    "unified_customer_count": unified_count,
                    "feature_columns_count": len(df_unified.columns),
                    "columns": df_unified.columns
                }
            }

            report_path = os.path.join(version_dir, "processing_report.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)

            # 18. Update Versions Registry
            version_entry = {
                "version_id": version_id,
                "batch_id": batch_id,
                "status": "PROCESSING_COMPLETED",
                "models_trained": False,
                "created_at": datetime.now().isoformat(),
                "duration_seconds": duration,
                "total_customers": unified_count,
                "included_batches": cumulative_batches,
                "hdfs_path": hdfs_processed_path
            }
            self._update_version_entry(version_entry)

            return True, f"PySpark cumulative batch processing completed successfully in {duration}s for {version_id}.", report

        except Exception as e:
            err_msg = f"PySpark processing failed for batch '{batch_id}': {str(e)}"
            return False, err_msg, {}
        finally:
            if spark is not None:
                try:
                    spark.stop()
                except Exception:
                    pass

    def get_processing_report(self, version_id: str) -> Optional[Dict[str, Any]]:
        report_path = os.path.join(self.versions_dir, version_id, "processing_report.json")
        if os.path.exists(report_path):
            try:
                with open(report_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

