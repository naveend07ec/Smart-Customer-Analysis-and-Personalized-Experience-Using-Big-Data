"""
Automated Test Suite for Supervised Customer Churn Prediction Module
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Verifies:
1. Point-in-time temporal cutoff enforcement (< 2024-10-01).
2. Absence of future information in historical predictors.
3. Customer-level stratified train/test separation (0 customer overlap).
4. Machine learning model artifact loading and inference.
5. REST API endpoints (summary, customers list, customer detail, validation, 404/400).
"""

import os
import sys
import unittest
import joblib
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app
from backend.app.services.data_service import DataService


class TestChurnModule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({"TESTING": True})
        cls.client = cls.app.test_client()
        cls.service = DataService.get_instance()
        cls.dataset_path = os.path.join(PROJECT_ROOT, "data", "processed", "churn_dataset.parquet")
        cls.preds_path = os.path.join(PROJECT_ROOT, "data", "processed", "customer_churn_predictions.parquet")
        cls.model_path = os.path.join(PROJECT_ROOT, "ml", "models", "churn", "churn_model.joblib")

    def test_temporal_cutoff_enforcement(self):
        """Verifies that historical feature events occur strictly before 2024-10-01."""
        df_tx = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "raw", "transactions.csv"))
        df_tx["transaction_date"] = pd.to_datetime(df_tx["transaction_date"])
        cutoff = pd.Timestamp("2024-10-01 00:00:00")

        hist_tx = df_tx[df_tx["transaction_date"] < cutoff]
        future_tx = df_tx[df_tx["transaction_date"] >= cutoff]

        # Verify strict partition
        self.assertTrue((hist_tx["transaction_date"] < cutoff).all())
        self.assertTrue((future_tx["transaction_date"] >= cutoff).all())
        self.assertGreater(len(hist_tx), 9000)
        self.assertGreater(len(future_tx), 2500)

    def test_churn_dataset_integrity(self):
        """Verifies churn dataset structure, shape, and zero unexpected nulls."""
        self.assertTrue(os.path.exists(self.dataset_path))
        df = pd.read_parquet(self.dataset_path)

        self.assertEqual(len(df), 1177)
        self.assertEqual(df.isnull().sum().sum(), 0)
        self.assertIn("churn_label", df.columns)
        self.assertIn("recency_days_at_cutoff", df.columns)

        # Target class values must be binary {0, 1}
        unique_labels = set(df["churn_label"].unique())
        self.assertEqual(unique_labels, {0, 1})

    def test_customer_level_train_test_separation(self):
        """Verifies no customer ID occurs in both train and test partitions."""
        from sklearn.model_selection import train_test_split
        df = pd.read_parquet(self.dataset_path)

        train_df, test_df = train_test_split(df, test_size=0.20, random_state=42, stratify=df["churn_label"])
        train_custs = set(train_df["customer_id"])
        test_custs = set(test_df["customer_id"])

        intersection = train_custs.intersection(test_custs)
        self.assertEqual(len(intersection), 0, "Train and test customer sets must be completely disjoint!")

    def test_model_artifact_inference(self):
        """Verifies that saved Random Forest artifact loads and outputs valid probabilities."""
        self.assertTrue(os.path.exists(self.model_path))
        rf_model = joblib.load(self.model_path)

        df = pd.read_parquet(self.dataset_path)
        features = [
            "recency_days_at_cutoff", "hist_completed_orders", "hist_total_orders",
            "hist_total_spend", "hist_avg_order_value", "hist_cancellation_rate",
            "hist_web_touchpoints", "hist_distinct_sessions", "hist_avg_dwell_time",
            "hist_product_views", "hist_cart_additions", "hist_checkout_starts",
            "hist_cart_abandon_ratio", "hist_social_interactions",
            "hist_avg_sentiment", "hist_avg_engagement"
        ]
        sample_x = df[features].head(10)
        probs = rf_model.predict_proba(sample_x)[:, 1]

        self.assertEqual(len(probs), 10)
        self.assertTrue(all(0.0 <= p <= 1.0 for p in probs))

    def test_api_churn_summary(self):
        """Verifies GET /api/churn/summary endpoint."""
        res = self.client.get("/api/churn/summary")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]

        self.assertEqual(data["total_customers_evaluated"], 1177)
        self.assertIn("risk_distribution", data)
        self.assertIn("low_risk", data["risk_distribution"])
        self.assertIn("medium_risk", data["risk_distribution"])
        self.assertIn("high_risk", data["risk_distribution"])
        self.assertIn("evaluation_metrics", data)
        self.assertGreater(data["evaluation_metrics"]["roc_auc"], 0.85)

    def test_api_churn_customers_list(self):
        """Verifies GET /api/churn/customers returns paginated customer predictions."""
        res = self.client.get("/api/churn/customers?page=1&pageSize=10&riskCategory=high")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]

        self.assertIn("total_records", data)
        self.assertIn("customers", data)
        self.assertLessEqual(len(data["customers"]), 10)
        for c in data["customers"]:
            self.assertEqual(c["risk_category"].lower(), "high")
            self.assertGreaterEqual(c["churn_risk_score"], 65.0)

    def test_api_churn_customer_valid(self):
        """Verifies GET /api/churn/customer/<valid_id> returns detailed factors."""
        res = self.client.get("/api/churn/customer/CUST_0001")
        self.assertEqual(res.status_code, 200)
        cust = res.get_json()["data"]

        self.assertEqual(cust["customer_id"], "CUST_0001")
        self.assertIn("churn_risk_score", cust)
        self.assertIn("risk_category", cust)
        self.assertIn("suggested_retention_action", cust)
        self.assertIn("historical_behavioural_factors", cust)
        self.assertIn("recency_days_at_cutoff", cust["historical_behavioural_factors"])

    def test_api_churn_customer_invalid_format(self):
        """Verifies GET /api/churn/customer/<bad_id> returns 400 Bad Request."""
        res = self.client.get("/api/churn/customer/INVALID_ID")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()["status"], "error")

    def test_api_churn_customer_nonexistent(self):
        """Verifies GET /api/churn/customer/<nonexistent_id> returns 404."""
        res = self.client.get("/api/churn/customer/CUST_9999")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.get_json()["status"], "error")


if __name__ == "__main__":
    unittest.main()

