"""
Automated REST API Test Suite
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Verifies:
1. Endpoint availability and HTTP status codes.
2. Standard response envelopes (status, message, data).
3. Data integrity between endpoints and Stage 3/4 pipeline outputs.
4. Existing vs Nonexistent customer handling (200 vs 404).
5. Input validation on customer_id formats (400).
6. Recommendation structure (5 ranked products with explainable reasons).
7. Segmentation and PCA coordinate alignment.
8. Data processing audit accuracy.
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app
from backend.app.services.data_service import DataService


class TestBackendAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({"TESTING": True})
        cls.client = cls.app.test_client()
        cls.service = DataService.get_instance()

    def test_health_check(self):
        """Verifies server health endpoint."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data.get("status"), "healthy")

    def test_get_overview(self):
        """Verifies GET /api/overview returns correct real statistics."""
        res = self.client.get("/api/overview")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()

        self.assertEqual(json_data["status"], "success")
        data = json_data["data"]

        # Assert data matches actual pipeline outputs
        self.assertEqual(data["total_customers"], 1200)
        self.assertEqual(data["total_transactions"], 12214)
        self.assertEqual(data["total_web_activities"], 120944)
        self.assertEqual(data["total_social_interactions"], 8828)
        self.assertEqual(data["total_customer_segments"], 5)
        self.assertEqual(data["total_recommendations_generated"], 6000)
        self.assertGreater(data["total_revenue"], 1000000)

    def test_get_analytics(self):
        """Verifies GET /api/analytics returns multi-channel distributions."""
        res = self.client.get("/api/analytics")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()

        self.assertEqual(json_data["status"], "success")
        data = json_data["data"]

        self.assertIn("spending_distribution", data)
        self.assertIn("purchase_frequency", data)
        self.assertIn("website_engagement", data)
        self.assertIn("social_engagement", data)
        self.assertIn("sentiment_distribution", data)
        self.assertIn("aggregated_statistics", data)

        # Spending distribution has valid customer distribution bins
        total_in_spend = sum(data["spending_distribution"].values())
        self.assertGreater(total_in_spend, 1100)
        self.assertLessEqual(total_in_spend, 1200)

    def test_get_segments(self):
        """Verifies GET /api/segments returns profiles and PCA coordinates."""
        res = self.client.get("/api/segments")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()

        self.assertEqual(json_data["status"], "success")
        data = json_data["data"]

        self.assertEqual(len(data["segment_names"]), 5)
        self.assertEqual(len(data["cluster_profiles"]), 5)
        self.assertEqual(len(data["pca_coordinates"]), 1200)

        # Check PCA point schema
        first_pt = data["pca_coordinates"][0]
        self.assertIn("customer_id", first_pt)
        self.assertIn("pca_x", first_pt)
        self.assertIn("pca_y", first_pt)
        self.assertIn("cluster_id", first_pt)
        self.assertIn("cluster_name", first_pt)

    def test_get_customer_valid(self):
        """Verifies GET /api/customer/<valid_id> returns detailed profile."""
        res = self.client.get("/api/customer/CUST_0001")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()

        self.assertEqual(json_data["status"], "success")
        cust = json_data["data"]

        self.assertIn("profile", cust)
        self.assertEqual(cust["profile"]["customer_id"], "CUST_0001")
        self.assertIn("transactions", cust)
        self.assertIn("web_activity", cust)
        self.assertIn("social_media", cust)
        self.assertIn("recommendations", cust)

    def test_get_customer_nonexistent(self):
        """Verifies GET /api/customer/<nonexistent_id> returns 404."""
        res = self.client.get("/api/customer/CUST_9999")
        self.assertEqual(res.status_code, 404)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "error")
        self.assertIn("not found", json_data["message"].lower())

    def test_get_customer_invalid_format(self):
        """Verifies GET /api/customer/<invalid_format> returns 400 Bad Request."""
        res = self.client.get("/api/customer/INVALID_ID")
        self.assertEqual(res.status_code, 400)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "error")
        self.assertIn("invalid customer id format", json_data["message"].lower())

    def test_get_recommendations_valid(self):
        """Verifies GET /api/recommendations/<valid_id> returns 5 explainable recommendations."""
        res = self.client.get("/api/recommendations/CUST_0002")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()

        self.assertEqual(json_data["status"], "success")
        data = json_data["data"]

        self.assertEqual(data["customer_id"], "CUST_0002")
        self.assertEqual(data["recommendations_count"], 5)
        recs = data["top_recommendations"]
        self.assertEqual(len(recs), 5)

        for rec in recs:
            self.assertTrue(rec["product_id"].startswith("PROD_"))
            self.assertIsNotNone(rec["product_name"])
            self.assertIsNotNone(rec["category"])
            self.assertGreater(rec["unit_price"], 0)
            self.assertGreater(rec["score"], 0)
            self.assertTrue(len(rec["explanation"]) > 10)

    def test_get_recommendations_nonexistent(self):
        """Verifies GET /api/recommendations/<nonexistent_id> returns 404."""
        res = self.client.get("/api/recommendations/CUST_9999")
        self.assertEqual(res.status_code, 404)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "error")

    def test_get_recommendations_invalid_format(self):
        """Verifies GET /api/recommendations/<invalid_format> returns 400."""
        res = self.client.get("/api/recommendations/BAD_ID")
        self.assertEqual(res.status_code, 400)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "error")

    def test_get_processing(self):
        """Verifies GET /api/processing returns complete data processing audit."""
        res = self.client.get("/api/processing")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()

        self.assertEqual(json_data["status"], "success")
        data = json_data["data"]

        self.assertIn("source_dataset_counts", data)
        self.assertIn("cleaned_record_counts", data)
        self.assertIn("duplicates_removed", data)
        self.assertIn("missing_values_handled", data)
        self.assertIn("feature_matrix_dimensions", data)

        self.assertEqual(data["source_dataset_counts"]["transactions"], 12239)
        self.assertEqual(data["cleaned_record_counts"]["cleaned_transactions"], 12214)
        self.assertEqual(data["duplicates_removed"]["transactions"], 25)
        self.assertEqual(data["missing_values_handled"], 73)


if __name__ == "__main__":
    unittest.main()
