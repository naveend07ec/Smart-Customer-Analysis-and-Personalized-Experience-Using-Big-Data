"""
Data Service Layer
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Loads verified Big Data and ML outputs from data/processed/ and ml/models/
and serves high-performance cached analytical queries for the Flask REST API.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


class DataService:
    _instance = None

    def __init__(self):
        # 3 levels up from backend/app/services to workspace root
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self._load_datasets()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DataService()
        return cls._instance

    def _resolve_path(self, rel_path: str) -> str:
        return os.path.join(self.base_dir, rel_path)

    def _load_datasets(self):
        print("Initializing DataService and loading processed datasets & models...")

        # 1. Customer Segment Assignments
        seg_path = self._resolve_path("data/processed/customer_segment_assignments.csv")
        if os.path.exists(seg_path):
            self.df_segments = pd.read_csv(seg_path)
        else:
            self.df_segments = pd.DataFrame()

        # 2. Cleaned Transactions
        tx_path = self._resolve_path("data/processed/cleaned_transactions.csv")
        if os.path.exists(tx_path):
            self.df_transactions = pd.read_csv(tx_path)
            self.df_transactions["transaction_date"] = pd.to_datetime(self.df_transactions["transaction_date"])
        else:
            self.df_transactions = pd.DataFrame()

        # 3. Cleaned Web Activity
        web_path = self._resolve_path("data/processed/cleaned_web_activity.csv")
        if os.path.exists(web_path):
            self.df_web = pd.read_csv(web_path)
            self.df_web["timestamp"] = pd.to_datetime(self.df_web["timestamp"])
        else:
            self.df_web = pd.DataFrame()

        # 4. Cleaned Social Media
        soc_path = self._resolve_path("data/processed/cleaned_social_media.csv")
        if os.path.exists(soc_path):
            self.df_social = pd.read_csv(soc_path)
            self.df_social["timestamp"] = pd.to_datetime(self.df_social["timestamp"])
        else:
            self.df_social = pd.DataFrame()

        # 5. ML Models & Cluster Profiles
        profiles_path = self._resolve_path("ml/models/cluster_profiles.json")
        if os.path.exists(profiles_path):
            with open(profiles_path, "r", encoding="utf-8") as f:
                self.cluster_profiles = json.load(f)
        else:
            self.cluster_profiles = {"metrics": {}, "clusters": []}

        # 6. Elbow Evaluation Metrics
        elbow_path = self._resolve_path("ml/models/elbow_metrics.json")
        if os.path.exists(elbow_path):
            with open(elbow_path, "r", encoding="utf-8") as f:
                self.elbow_metrics = json.load(f)
        else:
            self.elbow_metrics = []

        # 7. Customer Recommendations
        recs_path = self._resolve_path("ml/models/customer_recommendations.json")
        if os.path.exists(recs_path):
            with open(recs_path, "r", encoding="utf-8") as f:
                self.recommendations = json.load(f)
        else:
            self.recommendations = {}

        # 8. Product Association Rules
        rules_path = self._resolve_path("ml/models/product_association_rules.json")
        if os.path.exists(rules_path):
            with open(rules_path, "r", encoding="utf-8") as f:
                self.association_rules = json.load(f)
        else:
            self.association_rules = []

        print(f"DataService initialized: {len(self.df_segments)} customers, {len(self.df_transactions)} transactions.")

    # -------------------------------------------------------------
    # Overview Dashboard Metrics
    # -------------------------------------------------------------
    def get_kpi_summary(self) -> Dict[str, Any]:
        completed_tx = self.df_transactions[self.df_transactions["order_status"] == "Completed"]
        total_revenue = float(completed_tx["total_amount"].sum())
        total_orders = int(len(self.df_transactions))
        completed_orders = int(len(completed_tx))
        total_customers = int(len(self.df_segments))
        avg_spend_per_cust = float(total_revenue / total_customers) if total_customers > 0 else 0.0
        avg_sentiment = float(self.df_social["sentiment_score"].mean()) if not self.df_social.empty else 0.0

        return {
            "total_revenue": round(total_revenue, 2),
            "total_customers": total_customers,
            "total_transactions": total_orders,
            "completed_orders": completed_orders,
            "fulfillment_rate": round(completed_orders / total_orders * 100, 2) if total_orders > 0 else 0.0,
            "avg_spend_per_customer": round(avg_spend_per_cust, 2),
            "total_web_touchpoints": int(len(self.df_web)),
            "total_social_interactions": int(len(self.df_social)),
            "avg_sentiment_score": round(avg_sentiment, 3)
        }

    def get_segment_distribution(self) -> List[Dict[str, Any]]:
        if not self.cluster_profiles or "clusters" not in self.cluster_profiles:
            return []
        return self.cluster_profiles["clusters"]

    def get_revenue_by_category(self) -> List[Dict[str, Any]]:
        completed_tx = self.df_transactions[self.df_transactions["order_status"] == "Completed"]
        grouped = completed_tx.groupby("product_category").agg(
            revenue=("total_amount", "sum"),
            units_sold=("quantity", "sum"),
            order_count=("transaction_id", "count")
        ).reset_index()

        grouped["revenue"] = grouped["revenue"].round(2)
        grouped = grouped.sort_values("revenue", ascending=False)
        return grouped.to_dict(orient="records")

    def get_monthly_trends(self) -> List[Dict[str, Any]]:
        completed_tx = self.df_transactions[self.df_transactions["order_status"] == "Completed"].copy()
        completed_tx["month"] = completed_tx["transaction_date"].dt.strftime("%Y-%m")
        grouped = completed_tx.groupby("month").agg(
            revenue=("total_amount", "sum"),
            orders=("transaction_id", "count"),
            unique_buyers=("customer_id", "nunique")
        ).reset_index().sort_values("month")

        grouped["revenue"] = grouped["revenue"].round(2)
        return grouped.to_dict(orient="records")

    # -------------------------------------------------------------
    # Customer Analytics Metrics
    # -------------------------------------------------------------
    def get_channel_attribution(self) -> Dict[str, Any]:
        traffic = self.df_web["traffic_source"].value_counts().to_dict()
        devices = self.df_web["device_type"].value_counts().to_dict()
        actions = self.df_web["action_type"].value_counts().to_dict()

        return {
            "traffic_sources": [{"source": k, "count": int(v)} for k, v in traffic.items()],
            "device_types": [{"device": k, "count": int(v)} for k, v in devices.items()],
            "funnel_actions": [{"action": k, "count": int(v)} for k, v in actions.items()]
        }

    def get_sentiment_analysis(self) -> Dict[str, Any]:
        sent_counts = self.df_social["sentiment"].value_counts().to_dict()
        platforms = self.df_social.groupby("platform").agg(
            count=("interaction_id", "count"),
            avg_sentiment=("sentiment_score", "mean"),
            avg_engagement=("engagement_score", "mean")
        ).reset_index()

        platforms["avg_sentiment"] = platforms["avg_sentiment"].round(3)
        platforms["avg_engagement"] = platforms["avg_engagement"].round(1)

        return {
            "sentiment_counts": sent_counts,
            "platform_breakdown": platforms.to_dict(orient="records")
        }

    def get_rfm_distributions(self) -> Dict[str, Any]:
        # Binned Recency, Frequency, Spend for distribution charts
        recency_bins = [0, 30, 60, 90, 180, 365]
        recency_labels = ["0-30d", "31-60d", "61-90d", "91-180d", "180d+"]
        r_cut = pd.cut(self.df_segments["recency_days"], bins=recency_bins, labels=recency_labels).value_counts()

        spend_bins = [-0.01, 250, 500, 1000, 2500, 100000]
        spend_labels = ["$0-250", "$251-500", "$501-1k", "$1k-2.5k", "$2.5k+"]
        s_cut = pd.cut(self.df_segments["total_spend"], bins=spend_bins, labels=spend_labels).value_counts()

        freq_bins = [0, 2, 5, 10, 20, 50]
        freq_labels = ["1-2", "3-5", "6-10", "11-20", "20+"]
        f_cut = pd.cut(self.df_segments["total_transactions"], bins=freq_bins, labels=freq_labels).value_counts()

        return {
            "recency": [{"bin": k, "count": int(r_cut.get(k, 0))} for k in recency_labels],
            "spend": [{"bin": k, "count": int(s_cut.get(k, 0))} for k in spend_labels],
            "frequency": [{"bin": k, "count": int(f_cut.get(k, 0))} for k in freq_labels]
        }

    # -------------------------------------------------------------
    # Customer Segmentation & PCA
    # -------------------------------------------------------------
    def get_segmentation_evaluation(self) -> Dict[str, Any]:
        return {
            "metrics": self.cluster_profiles.get("metrics", {}),
            "elbow_curve": self.elbow_metrics,
            "clusters": self.cluster_profiles.get("clusters", [])
        }

    def get_pca_scatter(self, limit: int = 1200) -> List[Dict[str, Any]]:
        cols = ["customer_id", "cluster_id", "cluster_name", "pca_x", "pca_y", "total_spend", "total_transactions", "avg_sentiment_score"]
        available_cols = [c for c in cols if c in self.df_segments.columns]
        sample_df = self.df_segments[available_cols].head(limit)
        return sample_df.to_dict(orient="records")

    # -------------------------------------------------------------
    # Customer List & Customer 360 View
    # -------------------------------------------------------------
    def get_customers(self, page: int = 1, page_size: int = 20, search: str = "", segment: str = "all", sort_by: str = "total_spend", sort_dir: str = "desc") -> Dict[str, Any]:
        df = self.df_segments.copy()

        if search:
            df = df[df["customer_id"].str.contains(search, case=False, na=False)]

        if segment and segment != "all":
            df = df[df["cluster_name"] == segment]

        if sort_by in df.columns:
            ascending = (sort_dir.lower() == "asc")
            df = df.sort_values(sort_by, ascending=ascending)

        total_records = len(df)
        total_pages = max(1, (total_records + page_size - 1) // page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        display_cols = [
            "customer_id", "cluster_id", "cluster_name", "total_spend",
            "total_transactions", "avg_order_value", "recency_days",
            "total_web_activities", "avg_sentiment_score", "cancellation_rate"
        ]
        available_cols = [c for c in display_cols if c in df.columns]
        page_records = df[available_cols].iloc[start_idx:end_idx].to_dict(orient="records")

        return {
            "total_records": total_records,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "customers": page_records
        }

    def get_customer_detail(self, customer_id: str) -> Optional[Dict[str, Any]]:
        c_rows = self.df_segments[self.df_segments["customer_id"] == customer_id]
        if c_rows.empty:
            return None

        customer_profile = c_rows.iloc[0].to_dict()

        # Customer transactions (recent 25)
        tx_rows = self.df_transactions[self.df_transactions["customer_id"] == customer_id].sort_values("transaction_date", ascending=False).head(25)
        tx_list = tx_rows.to_dict(orient="records")
        for t in tx_list:
            if isinstance(t.get("transaction_date"), pd.Timestamp):
                t["transaction_date"] = t["transaction_date"].strftime("%Y-%m-%d %H:%M:%S")

        # Customer web events (recent 25)
        web_rows = self.df_web[self.df_web["customer_id"] == customer_id].sort_values("timestamp", ascending=False).head(25)
        web_list = web_rows.to_dict(orient="records")
        for w in web_list:
            if isinstance(w.get("timestamp"), pd.Timestamp):
                w["timestamp"] = w["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        # Customer social feedback (recent 25)
        soc_rows = self.df_social[self.df_social["customer_id"] == customer_id].sort_values("timestamp", ascending=False).head(25)
        soc_list = soc_rows.to_dict(orient="records")
        for s in soc_list:
            if isinstance(s.get("timestamp"), pd.Timestamp):
                s["timestamp"] = s["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        # Customer recommendations
        recs = self.recommendations.get(customer_id, [])

        return {
            "profile": customer_profile,
            "transactions": tx_list,
            "web_activity": web_list,
            "social_media": soc_list,
            "recommendations": recs
        }

    # -------------------------------------------------------------
    # Recommendations & Association Rules
    # -------------------------------------------------------------
    def get_customer_recommendations(self, customer_id: str) -> List[Dict[str, Any]]:
        return self.recommendations.get(customer_id, [])

    def get_recommendation_evaluation(self) -> List[Dict[str, Any]]:
        eval_path = self._resolve_path("data/processed/recommendation_evaluation.csv")
        if os.path.exists(eval_path):
            df_eval = pd.read_csv(eval_path)
            return df_eval.to_dict(orient="records")
        return []

    def get_top_association_rules(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.association_rules[:limit]

    # -------------------------------------------------------------
    # Big Data Pipeline & Storage Diagnostics
    # -------------------------------------------------------------
    def get_pipeline_summary(self) -> Dict[str, Any]:
        return {
            "framework": "Apache Spark (PySpark 3.5.1)",
            "execution_mode": "local[2] (2 CPU Cores, 2GB Driver Memory limit)",
            "java_runtime": "Oracle Java 1.8.0_471 (64-Bit)",
            "raw_datasets": {
                "transactions": {"records": 12239, "file": "data/raw/transactions.csv"},
                "web_activity": {"records": 120979, "file": "data/raw/web_activity.csv"},
                "social_media": {"records": 8828, "file": "data/raw/social_media.csv"}
            },
            "cleaning_metrics": {
                "transactions_deduplicated": 25,
                "transactions_imputed_payment": 73,
                "web_deduplicated": 35,
                "meaningful_null_product_ids_preserved": 60540,
                "social_invalid_filtered": 0
            },
            "processed_datasets": {
                "cleaned_transactions": len(self.df_transactions),
                "cleaned_web_activity": len(self.df_web),
                "cleaned_social_media": len(self.df_social),
                "unified_feature_matrix": f"{len(self.df_segments)} rows x 23 columns",
                "customer_coverage": "100.0% (1,200 / 1,200 unique customers across all 3 sources)"
            },
            "storage_formats": [
                {"name": "Parquet (Snappy)", "purpose": "High-throughput binary distributed processing"},
                {"name": "CSV (RFC-4180)", "purpose": "Human-readable inspection, REST API serving, and auditability"}
            ]
        }
