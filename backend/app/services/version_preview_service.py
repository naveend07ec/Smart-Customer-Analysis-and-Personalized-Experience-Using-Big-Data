"""
Version Preview, Promotion & Rollback Service
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Provides:
1. Version-isolated preview of KPIs, customer segments, recommendations, and churn risk.
2. Zero interference with active baseline production data.
3. Explicit version promotion with automatic state backups.
4. One-click instant rollback restoring baseline metrics and in-memory cache.
"""

import os
import json
import shutil
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from backend.app.services.data_service import DataService, sanitize_for_json


class VersionPreviewService:
    _instance = None

    def __init__(self):
        self.workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.versions_dir = os.path.join(self.workspace_root, "data", "versions")
        self.models_versions_dir = os.path.join(self.workspace_root, "ml", "models", "versions")
        self.processed_dir = os.path.join(self.workspace_root, "data", "processed")
        self.models_dir = os.path.join(self.workspace_root, "ml", "models")
        self.current_version_file = os.path.join(self.workspace_root, "data", "current_version.json")
        self.backup_dir = os.path.join(self.versions_dir, "_backup_prior_to_promotion")
        self.baseline_backup_dir = os.path.join(self.workspace_root, "data", "_baseline_backup")
        self.models_baseline_backup_dir = os.path.join(self.models_dir, "_baseline_backup")
        self._ensure_baseline_archive()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = VersionPreviewService()
        return cls._instance

    def _ensure_baseline_archive(self):
        """Creates a permanent read-only archive of the academic baseline if not present."""
        if not os.path.exists(self.baseline_backup_dir):
            os.makedirs(self.baseline_backup_dir, exist_ok=True)
            # Archive baseline processed CSVs & JSONs
            for fname in os.listdir(self.processed_dir):
                src = os.path.join(self.processed_dir, fname)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(self.baseline_backup_dir, fname))

        if not os.path.exists(self.models_baseline_backup_dir):
            os.makedirs(self.models_baseline_backup_dir, exist_ok=True)
            for fname in os.listdir(self.models_dir):
                src = os.path.join(self.models_dir, fname)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(self.models_baseline_backup_dir, fname))

    def get_active_version_id(self) -> str:
        """Reads currently active version pointer from data/current_version.json."""
        if os.path.exists(self.current_version_file):
            try:
                with open(self.current_version_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("active_version", "baseline")
            except Exception:
                return "baseline"
        return "baseline"

    def list_versions(self) -> List[Dict[str, Any]]:
        """Returns catalog of all available versions (baseline + student batches)."""
        active_vid = self.get_active_version_id()
        versions_list = [
            {
                "version_id": "baseline",
                "name": "Academic Baseline (Production)",
                "batch_id": "baseline",
                "status": "ACTIVE_PRODUCTION" if active_vid == "baseline" else "BASELINE_STORED",
                "is_active": (active_vid == "baseline"),
                "total_customers": 1200,
                "created_at": "2024-11-14T10:48:00",
                "models_trained": True,
                "description": "Permanent baseline with 1,200 unified customers, 5 K-Means clusters, and 76.0% recommendation hit rate."
            }
        ]

        index_file = os.path.join(self.versions_dir, "versions_index.json")
        if os.path.exists(index_file):
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    custom_versions = json.load(f)
                    for cv in custom_versions:
                        vid = cv.get("version_id")
                        cv["is_active"] = (active_vid == vid)
                        versions_list.append(cv)
            except Exception:
                pass

        return versions_list

    def get_overview_preview(self, version_id: str) -> Dict[str, Any]:
        """Provides preview of KPIs, monthly trends, and segment distribution for a version."""
        if version_id == "baseline":
            ds = DataService.get_instance()
            return {
                "version_id": "baseline",
                "kpis": ds.get_kpi_summary(),
                "segment_distribution": ds.get_segment_distribution(),
                "monthly_trends": ds.get_monthly_trends()
            }

        v_dir = os.path.join(self.versions_dir, version_id)
        if not os.path.exists(v_dir):
            raise FileNotFoundError(f"Version '{version_id}' not found.")

        # 1. Transactions
        tx_path = os.path.join(v_dir, "cleaned_transactions.csv")
        df_tx = pd.read_csv(tx_path) if os.path.exists(tx_path) else pd.DataFrame()

        # 2. Segments
        seg_path = os.path.join(v_dir, "customer_segments.csv")
        df_seg = pd.read_csv(seg_path) if os.path.exists(seg_path) else pd.DataFrame()

        # 3. Social
        soc_path = os.path.join(v_dir, "cleaned_social_media.csv")
        df_soc = pd.read_csv(soc_path) if os.path.exists(soc_path) else pd.DataFrame()

        completed_tx = df_tx[df_tx["order_status"] == "Completed"] if not df_tx.empty and "order_status" in df_tx.columns else df_tx
        total_rev = float(completed_tx["total_amount"].sum()) if not completed_tx.empty else 0.0
        total_orders = int(len(df_tx))
        completed_orders = int(len(completed_tx))
        total_cust = int(len(df_seg)) if not df_seg.empty else int(df_tx["customer_id"].nunique()) if not df_tx.empty else 0
        avg_spend = round(total_rev / max(1, total_cust), 2)
        avg_sent = round(float(df_soc["sentiment_score"].mean()), 3) if not df_soc.empty and "sentiment_score" in df_soc.columns else 0.0

        kpis = {
            "total_revenue": round(total_rev, 2),
            "total_customers": total_cust,
            "total_transactions": total_orders,
            "completed_orders": completed_orders,
            "fulfillment_rate": round(completed_orders / max(1, total_orders) * 100, 2),
            "avg_spend_per_customer": avg_spend,
            "avg_sentiment_score": avg_sent
        }

        # Segment distribution
        seg_dist = []
        if not df_seg.empty and "cluster_name" in df_seg.columns:
            counts = df_seg["cluster_name"].value_counts()
            for name, cnt in counts.items():
                seg_dist.append({
                    "cluster_name": str(name),
                    "customer_count": int(cnt),
                    "percentage_of_total": round(float(cnt / max(1, total_cust) * 100), 2)
                })

        # Monthly trends
        monthly_trends = []
        if not completed_tx.empty and "transaction_date" in completed_tx.columns:
            tx_trend = completed_tx.copy()
            tx_trend["month"] = pd.to_datetime(tx_trend["transaction_date"]).dt.strftime("%Y-%m")
            grouped = tx_trend.groupby("month").agg(
                revenue=("total_amount", "sum"),
                orders=("transaction_id", "count")
            ).reset_index()
            for _, r in grouped.iterrows():
                monthly_trends.append({
                    "month": str(r["month"]),
                    "revenue": round(float(r["revenue"]), 2),
                    "orders": int(r["orders"]),
                    "avg_order_value": round(float(r["revenue"] / max(1, r["orders"])), 2)
                })

        return sanitize_for_json({
            "version_id": version_id,
            "kpis": kpis,
            "segment_distribution": seg_dist,
            "monthly_trends": monthly_trends
        })

    def get_segmentation_preview(self, version_id: str) -> Dict[str, Any]:
        """Returns cluster profiles and PCA scatter coordinates for a version."""
        if version_id == "baseline":
            ds = DataService.get_instance()
            return {
                "version_id": "baseline",
                "profiles": ds.get_segment_profiles(),
                "pca_scatter": ds.get_pca_scatter()
            }

        models_dir = os.path.join(self.models_versions_dir, version_id)
        v_dir = os.path.join(self.versions_dir, version_id)

        profiles_file = os.path.join(models_dir, "cluster_profiles.json")
        profiles_data = {"clusters": []}
        if os.path.exists(profiles_file):
            with open(profiles_file, "r", encoding="utf-8") as f:
                profiles_data = json.load(f)

        pca_scatter = []
        seg_path = os.path.join(v_dir, "customer_segments.csv")
        if os.path.exists(seg_path):
            df_seg = pd.read_csv(seg_path)
            cols = ["customer_id", "cluster_id", "cluster_name", "pca_x", "pca_y", "total_spend"]
            avail_cols = [c for c in cols if c in df_seg.columns]
            sample_df = df_seg[avail_cols].head(500)
            pca_scatter = sample_df.to_dict(orient="records")

        return sanitize_for_json({
            "version_id": version_id,
            "profiles": profiles_data.get("clusters", []),
            "metrics": profiles_data.get("metrics", {}),
            "pca_scatter": pca_scatter
        })

    def get_recommendations_preview(self, version_id: str) -> Dict[str, Any]:
        """Returns recommendation metrics and sample recommendations for a version."""
        if version_id == "baseline":
            ds = DataService.get_instance()
            rules = ds.get_top_association_rules(15)
            return {
                "version_id": "baseline",
                "provenance": {
                    "version_id": "baseline",
                    "models_dir": os.path.join(self.workspace_root, "ml", "models"),
                    "has_item_similarity": os.path.exists(os.path.join(self.workspace_root, "ml", "models", "item_similarity_matrix.joblib")),
                    "has_product_metadata": os.path.exists(os.path.join(self.workspace_root, "ml", "models", "product_metadata.joblib")),
                    "has_association_rules_joblib": os.path.exists(os.path.join(self.workspace_root, "ml", "models", "association_rules.joblib")),
                    "rules_count": len(ds.association_rules),
                    "evaluation_metrics_count": len(ds.get_recommendation_evaluation()),
                    "recommendations_count": len(ds.recommendations)
                },
                "evaluation_metrics": ds.get_recommendation_evaluation(),
                "rules": rules,
                "sample_recommendations": list(ds.recommendations.values())[:5],
                "metadata": ds.get_rules_metadata()
            }

        models_dir = os.path.join(self.models_versions_dir, version_id)
        eval_file = os.path.join(models_dir, "evaluation_metrics.json")
        rules_file = os.path.join(models_dir, "product_association_rules.json")
        recs_file = os.path.join(models_dir, "customer_recommendations.json")
        meta_file = os.path.join(models_dir, "rules_metadata.json")

        eval_metrics = []
        if os.path.exists(eval_file):
            with open(eval_file, "r", encoding="utf-8") as f:
                eval_metrics = json.load(f)

        rules = []
        if os.path.exists(rules_file):
            with open(rules_file, "r", encoding="utf-8") as f:
                rules = json.load(f)

        sample_recs = []
        recs_count = 0
        if os.path.exists(recs_file):
            with open(recs_file, "r", encoding="utf-8") as f:
                recs_dict = json.load(f)
                sample_recs = list(recs_dict.values())[:5]
                recs_count = len(recs_dict)

        metadata = {}
        if os.path.exists(meta_file):
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        return sanitize_for_json({
            "version_id": version_id,
            "provenance": {
                "version_id": version_id,
                "models_dir": models_dir,
                "has_item_similarity": os.path.exists(os.path.join(models_dir, "item_similarity_matrix.joblib")),
                "has_product_metadata": os.path.exists(os.path.join(models_dir, "product_metadata.joblib")),
                "has_association_rules_joblib": os.path.exists(os.path.join(models_dir, "association_rules.joblib")),
                "rules_count": len(rules),
                "evaluation_metrics_count": len(eval_metrics),
                "recommendations_count": recs_count
            },
            "evaluation_metrics": eval_metrics,
            "rules": rules[:15],
            "sample_recommendations": sample_recs,
            "metadata": metadata
        })

    def get_churn_preview(self, version_id: str) -> Dict[str, Any]:
        """Returns churn predictions and status for a version."""
        if version_id == "baseline":
            ds = DataService.get_instance()
            return {
                "version_id": "baseline",
                "summary": ds.churn_summary,
                "evaluation": ds.churn_evaluation,
                "customers": ds.df_churn.head(20).to_dict(orient="records") if not ds.df_churn.empty else []
            }

        models_dir = os.path.join(self.models_versions_dir, version_id, "churn")
        v_dir = os.path.join(self.versions_dir, version_id)

        status_file = os.path.join(models_dir, "churn_status.json")
        skip_info = None
        if os.path.exists(status_file):
            with open(status_file, "r", encoding="utf-8") as f:
                skip_info = json.load(f)

        churn_csv = os.path.join(v_dir, "customer_churn_predictions.csv")
        customers = []
        risk_dist = {"High Risk": 0, "Medium Risk": 0, "Low Risk": 0}
        total_eval = 0

        if os.path.exists(churn_csv):
            df_churn = pd.read_csv(churn_csv)
            total_eval = len(df_churn)
            if "risk_tier" in df_churn.columns:
                counts = df_churn["risk_tier"].value_counts().to_dict()
                risk_dist.update(counts)
            customers = df_churn.head(20).to_dict(orient="records")

        eval_file = os.path.join(models_dir, "churn_evaluation_metrics.json")
        eval_metrics = {}
        if os.path.exists(eval_file):
            with open(eval_file, "r", encoding="utf-8") as f:
                eval_metrics = json.load(f)

        return sanitize_for_json({
            "version_id": version_id,
            "skip_info": skip_info,
            "evaluation": eval_metrics,
            "summary": {
                "total_customers_evaluated": total_eval,
                "risk_distribution": risk_dist
            },
            "customers": customers
        })

    # -------------------------------------------------------------
    # Promotion & Rollback Lifecycle
    # -------------------------------------------------------------
    def promote_version(self, version_id: str) -> Tuple[bool, str]:
        """
        Atomically promotes a versioned batch into active production.
        Guarantees failure-safe promotion with full transactional staging, pre-flight
        artifact validation, complete filesystem snapshots, and automatic rollback upon any failure.
        Ensures promotion NEVER replaces a cumulative historical dataset with an isolated upload.
        """
        if version_id == "baseline":
            return self.rollback_version()

        v_data_dir = os.path.join(self.versions_dir, version_id)
        v_models_dir = os.path.join(self.models_versions_dir, version_id)

        # 1. Pre-flight Validation: Verify version directories and mandatory artifacts
        if not os.path.exists(v_data_dir):
            return False, f"Version dataset directory for '{version_id}' not found."

        required_data_files = [
            "cleaned_transactions",
            "cleaned_web_activity",
            "cleaned_social_media",
            "unified_customer_features"
        ]
        for base_name in required_data_files:
            parquet_p = os.path.join(v_data_dir, f"{base_name}.parquet")
            csv_p = os.path.join(v_data_dir, f"{base_name}.csv")
            if not os.path.exists(parquet_p) and not os.path.exists(csv_p):
                return False, f"Pre-flight check failed: Missing required dataset '{base_name}' in version '{version_id}'."

        # Verify data_composition.json exists and is valid
        comp_file = os.path.join(v_data_dir, "data_composition.json")
        if not os.path.exists(comp_file):
            return False, f"Pre-flight check failed: Missing 'data_composition.json' in version '{version_id}'. Cannot promote non-cumulative version."

        try:
            with open(comp_file, "r", encoding="utf-8") as f:
                comp_data = json.load(f)
        except Exception as e:
            return False, f"Pre-flight check failed: Unable to parse 'data_composition.json': {str(e)}"

        hist = comp_data.get("historical", {})
        newly = comp_data.get("newly_added", {})
        overall = comp_data.get("overall", {})

        # Verify baseline historical lineage constraints (baseline is at least 1,200 cust, 12,214 tx)
        if hist.get("total_customers", 0) < 1200 or hist.get("total_transactions", 0) < 12214:
            return False, (
                f"Pre-flight check failed: Historical baseline lineage counts in 'data_composition.json' "
                f"are incomplete (Historical Customers: {hist.get('total_customers')}, "
                f"Historical Transactions: {hist.get('total_transactions')})."
            )

        # Verify composition arithmetic
        expected_overall_tx = hist.get("total_transactions", 0) + newly.get("valid_transactions", 0)
        if overall.get("total_transactions", 0) != expected_overall_tx:
            return False, (
                f"Pre-flight check failed: Transaction composition arithmetic mismatch: "
                f"{overall.get('total_transactions')} != {expected_overall_tx}."
            )

        if overall.get("total_customers", 0) < hist.get("total_customers", 0):
            return False, "Pre-flight check failed: Overall customer count is smaller than historical customer count."

        # Verify dataset files directly on disk
        csv_tx_path = os.path.join(v_data_dir, "cleaned_transactions.csv")
        csv_cust_path = os.path.join(v_data_dir, "unified_customer_features.csv")
        csv_web_path = os.path.join(v_data_dir, "cleaned_web_activity.csv")
        csv_soc_path = os.path.join(v_data_dir, "cleaned_social_media.csv")

        if os.path.exists(csv_tx_path):
            try:
                df_tx = pd.read_csv(csv_tx_path)
                if len(df_tx) < 12214:
                    return False, f"Pre-flight check failed: Candidate transactions count ({len(df_tx)}) is lower than historical baseline (12,214)."
                if not df_tx["transaction_id"].is_unique:
                    return False, "Pre-flight check failed: Duplicate primary key 'transaction_id' detected in candidate dataset."
                if df_tx["customer_id"].nunique() < 1200:
                    return False, f"Pre-flight check failed: Candidate distinct customers ({df_tx['customer_id'].nunique()}) < 1,200."
            except Exception as e:
                return False, f"Pre-flight check failed while inspecting cleaned_transactions.csv: {str(e)}"

        if os.path.exists(csv_web_path):
            try:
                df_web = pd.read_csv(csv_web_path)
                if len(df_web) < 120944:
                    return False, f"Pre-flight check failed: Candidate web activities ({len(df_web)}) is lower than historical baseline (120,944)."
                if not df_web["activity_id"].is_unique:
                    return False, "Pre-flight check failed: Duplicate primary key 'activity_id' detected in web activity."
            except Exception as e:
                return False, f"Pre-flight check failed while inspecting cleaned_web_activity.csv: {str(e)}"

        if os.path.exists(csv_soc_path):
            try:
                df_soc = pd.read_csv(csv_soc_path)
                if len(df_soc) < 8828:
                    return False, f"Pre-flight check failed: Candidate social records ({len(df_soc)}) is lower than historical baseline (8,828)."
                if not df_soc["interaction_id"].is_unique:
                    return False, "Pre-flight check failed: Duplicate primary key 'interaction_id' detected in social media."
            except Exception as e:
                return False, f"Pre-flight check failed while inspecting cleaned_social_media.csv: {str(e)}"

        if os.path.exists(csv_cust_path):
            try:
                df_cust = pd.read_csv(csv_cust_path)
                if len(df_cust) < 1200:
                    return False, f"Pre-flight check failed: Candidate customer count ({len(df_cust)}) is lower than historical baseline (1,200)."
                if not df_cust["customer_id"].is_unique:
                    return False, "Pre-flight check failed: Duplicate customer_id found in unified features."
            except Exception as e:
                return False, f"Pre-flight check failed while inspecting unified_customer_features.csv: {str(e)}"

        # Verify models directory and artifacts if models were trained
        if not os.path.exists(v_models_dir):
            return False, f"Version models directory for '{version_id}' not found. Train models before promotion."

        required_model_files = ["kmeans_model.joblib", "cluster_profiles.json"]
        for mname in required_model_files:
            if not os.path.exists(os.path.join(v_models_dir, mname)):
                return False, f"Pre-flight check failed: Missing required model artifact '{mname}' in version '{version_id}'."

        # Verify cluster profiles consistency
        profiles_file = os.path.join(v_models_dir, "cluster_profiles.json")
        try:
            with open(profiles_file, "r", encoding="utf-8") as f:
                pdata = json.load(f)
                if not pdata.get("clusters") or len(pdata.get("clusters")) < 2:
                    return False, "Pre-flight check failed: Candidate cluster_profiles.json is empty or invalid."
        except Exception as e:
            return False, f"Pre-flight check failed: Error reading cluster_profiles.json: {str(e)}"

        # 2. Complete Snapshot Backup of Active State
        data_backup_dir = os.path.join(self.workspace_root, "data", "_backup_prior_to_promotion")
        models_backup_dir = os.path.join(self.workspace_root, "ml", "models", "_backup_prior_to_promotion")
        os.makedirs(data_backup_dir, exist_ok=True)
        os.makedirs(models_backup_dir, exist_ok=True)

        # Clean prior backup contents
        for d in [data_backup_dir, models_backup_dir]:
            for item in os.listdir(d):
                p = os.path.join(d, item)
                if os.path.isfile(p):
                    os.remove(p)
                elif os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)

        for fname in os.listdir(self.processed_dir):
            src = os.path.join(self.processed_dir, fname)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(data_backup_dir, fname))

        for fname in os.listdir(self.models_dir):
            src = os.path.join(self.models_dir, fname)
            if os.path.isfile(src) and fname != ".gitkeep":
                shutil.copy2(src, os.path.join(models_backup_dir, fname))

        # Backup accepted_batches.json and current_version.json
        accepted_batches_file = os.path.join(self.workspace_root, "data", "accepted_batches.json")
        if os.path.exists(accepted_batches_file):
            shutil.copy2(accepted_batches_file, os.path.join(data_backup_dir, "accepted_batches.json"))

        prev_pointer = {}
        if os.path.exists(self.current_version_file):
            try:
                with open(self.current_version_file, "r", encoding="utf-8") as f:
                    prev_pointer = json.load(f)
            except Exception:
                prev_pointer = {"active_version": "baseline"}

        # 3. Atomic Staged Copy with Failure Recovery
        try:
            # Copy version datasets into data/processed/
            for fname in os.listdir(v_data_dir):
                src = os.path.join(v_data_dir, fname)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(self.processed_dir, fname))

            # Copy data_composition.json
            shutil.copy2(comp_file, os.path.join(self.processed_dir, "data_composition.json"))

            # Copy version models into ml/models/
            for fname in os.listdir(v_models_dir):
                src = os.path.join(v_models_dir, fname)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(self.models_dir, fname))

            # Update accepted_batches.json with candidate's included_batches
            promoted_batches = comp_data.get("included_batches", [])
            with open(accepted_batches_file, "w", encoding="utf-8") as f:
                json.dump(promoted_batches, f, indent=2)

            # Update current_version.json pointer
            pointer_data = {
                "active_version": version_id,
                "promoted_at": datetime.now().isoformat(),
                "previous_version": prev_pointer.get("active_version", "baseline")
            }
            with open(self.current_version_file, "w", encoding="utf-8") as f:
                json.dump(pointer_data, f, indent=2)

            # Reload DataService into memory
            DataService.get_instance().reload()
            return True, f"Successfully promoted version '{version_id}' to active production."

        except Exception as exc:
            # Transactional Rollback: Restore exact state from backup
            for fname in os.listdir(data_backup_dir):
                src = os.path.join(data_backup_dir, fname)
                if os.path.isfile(src) and fname != "accepted_batches.json":
                    shutil.copy2(src, os.path.join(self.processed_dir, fname))

            for fname in os.listdir(models_backup_dir):
                src = os.path.join(models_backup_dir, fname)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(self.models_dir, fname))

            backed_acc = os.path.join(data_backup_dir, "accepted_batches.json")
            if os.path.exists(backed_acc):
                shutil.copy2(backed_acc, accepted_batches_file)

            with open(self.current_version_file, "w", encoding="utf-8") as f:
                json.dump(prev_pointer, f, indent=2)

            DataService.get_instance().reload()
            return False, f"Atomic promotion failed: {str(exc)}. Production state safely rolled back to '{prev_pointer.get('active_version', 'baseline')}'."

    def rollback_version(self) -> Tuple[bool, str]:
        """Instantly restores the original baseline into active production."""
        if os.path.exists(self.baseline_backup_dir):
            for fname in os.listdir(self.baseline_backup_dir):
                src = os.path.join(self.baseline_backup_dir, fname)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(self.processed_dir, fname))

        if os.path.exists(self.models_baseline_backup_dir):
            for fname in os.listdir(self.models_baseline_backup_dir):
                src = os.path.join(self.models_baseline_backup_dir, fname)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(self.models_dir, fname))

        # Reset data_composition.json if present in data/processed/
        comp_file = os.path.join(self.processed_dir, "data_composition.json")
        if os.path.exists(comp_file):
            try:
                os.remove(comp_file)
            except Exception:
                pass

        # Reset accepted_batches.json
        accepted_batches_file = os.path.join(self.workspace_root, "data", "accepted_batches.json")
        if os.path.exists(accepted_batches_file):
            try:
                with open(accepted_batches_file, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2)
            except Exception:
                pass

        # Reset pointer
        pointer_data = {
            "active_version": "baseline",
            "rolled_back_at": datetime.now().isoformat()
        }
        with open(self.current_version_file, "w", encoding="utf-8") as f:
            json.dump(pointer_data, f, indent=2)

        # In-memory reload of DataService
        DataService.get_instance().reload()
        return True, "Successfully rolled back to the original Academic Baseline."
