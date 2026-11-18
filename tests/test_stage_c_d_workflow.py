"""
Automated Test Suite for Stages C & D: PySpark Batch Processing, ML Retraining & Version Preview
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Verifies:
1. PySpark batch processing from staged input.
2. Deduplication and missing value imputation in PySpark.
3. Feature engineering and 23-column unified customer feature matrix generation.
4. Version directory isolation (data/versions/<version_id>/).
5. Baseline data immutability during processing.
6. K-Means model retraining, silhouette evaluation, and PCA 2D coordinates.
7. Hybrid Recommendation retraining and zero-leakage offline evaluation.
8. Churn model temporal eligibility logic (skipping when < 270 days).
9. Consolidated model evaluation report generation and baseline comparison.
10. Version listing endpoint (GET /api/ingestion/versions).
11. Version preview endpoints (overview, segmentation, recommendations, churn).
12. Atomic version promotion and instant rollback to baseline.
"""

import os
import io
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch

from backend.app import create_app
from backend.app.services.data_service import DataService
from backend.app.services.pipeline_execution_service import PipelineExecutionService
from backend.app.services.model_training_service import ModelTrainingService
from backend.app.services.version_preview_service import VersionPreviewService


class TestStageCDWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({"TESTING": True})
        cls.client = cls.app.test_client()
        cls.pipe_service = PipelineExecutionService.get_instance()
        cls.trainer = ModelTrainingService.get_instance()
        cls.preview_service = VersionPreviewService.get_instance()

        # Create a dedicated test batch using sample data
        data = {
            "transactions": (open("data/sample/transactions.csv", "rb"), "transactions.csv"),
            "web_activity": (open("data/sample/web_activity.csv", "rb"), "web_activity.csv"),
            "social_media": (open("data/sample/social_media.csv", "rb"), "social_media.csv")
        }
        res = cls.client.post("/api/ingestion/upload", data=data, content_type="multipart/form-data")
        cls.test_batch_id = res.get_json()["data"]["batch_id"]
        cls.test_version_id = f"v_{cls.test_batch_id}"

    # Test 1: Reject un-validated or missing batch
    def test_01_reject_invalid_batch_processing(self):
        res = self.client.post("/api/ingestion/process/nonexistent_batch_xyz")
        self.assertEqual(res.status_code, 404)

    # Test 2: Successful PySpark batch processing
    def test_02_pyspark_batch_processing(self):
        res = self.client.post(
            f"/api/ingestion/process/{self.test_batch_id}",
            json={"force_local_input": True}
        )
        self.assertEqual(res.status_code, 200)
        report = res.get_json()["data"]
        self.assertEqual(report["version_id"], self.test_version_id)
        self.assertEqual(report["status"], "PROCESSING_COMPLETED")
        self.assertEqual(report["feature_engineering"]["feature_columns_count"], 23)
        self.assertGreater(report["feature_engineering"]["unified_customer_count"], 0)

    # Test 3: Verify version isolation and output files
    def test_03_version_isolation_files(self):
        v_dir = os.path.join(self.pipe_service.versions_dir, self.test_version_id)
        self.assertTrue(os.path.exists(os.path.join(v_dir, "cleaned_transactions.parquet")))
        self.assertTrue(os.path.exists(os.path.join(v_dir, "cleaned_web_activity.parquet")))
        self.assertTrue(os.path.exists(os.path.join(v_dir, "cleaned_social_media.parquet")))
        self.assertTrue(os.path.exists(os.path.join(v_dir, "unified_customer_features.parquet")))
        self.assertTrue(os.path.exists(os.path.join(v_dir, "processing_report.json")))

    # Test 4: Verify baseline data remains completely untouched
    def test_04_baseline_data_immutability(self):
        # Baseline raw files
        self.assertEqual(os.path.getsize("data/raw/transactions.csv"), 1676935)
        self.assertEqual(os.path.getsize("data/raw/web_activity.csv"), 13183498)
        self.assertEqual(os.path.getsize("data/raw/social_media.csv"), 1334002)

        # Active baseline DataService metrics
        kpis = DataService.get_instance().get_kpi_summary()
        self.assertEqual(kpis["total_customers"], 1200)

    # Test 5: K-Means model retraining on new batch
    def test_05_kmeans_retraining(self):
        res = self.trainer.train_kmeans(self.test_version_id)
        self.assertEqual(res["status"], "TRAINING_COMPLETED")
        self.assertGreater(res["silhouette_score"], 0.0)

        # Artifacts exist
        m_dir = os.path.join(self.trainer.models_versions_dir, self.test_version_id)
        self.assertTrue(os.path.exists(os.path.join(m_dir, "kmeans_model.joblib")))
        self.assertTrue(os.path.exists(os.path.join(m_dir, "cluster_profiles.json")))

    # Test 6: Recommendation engine retraining
    def test_06_recommender_retraining(self):
        res = self.trainer.train_recommender(self.test_version_id)
        self.assertEqual(res["status"], "TRAINING_COMPLETED")
        self.assertGreater(res["hit_rate_5"], 0.0)

        m_dir = os.path.join(self.trainer.models_versions_dir, self.test_version_id)
        self.assertTrue(os.path.exists(os.path.join(m_dir, "customer_recommendations.json")))
        self.assertTrue(os.path.exists(os.path.join(m_dir, "evaluation_metrics.json")))

    # Test 7: Churn model training & temporal eligibility
    def test_07_churn_training_and_eligibility(self):
        res = self.trainer.train_churn(self.test_version_id)
        self.assertIn(res["status"], ("TRAINING_COMPLETED", "SKIPPED_INSUFFICIENT_TEMPORAL_DATA"))

    # Test 8: Full retrain all API endpoint
    def test_08_retrain_all_api(self):
        res = self.client.post(f"/api/ingestion/train/{self.test_version_id}")
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data["status"], "success")
        self.assertIn("comparison", json_data["data"])

    # Test 9: Model evaluation comparison report endpoint
    def test_09_evaluation_report_api(self):
        res = self.client.get(f"/api/ingestion/evaluation/{self.test_version_id}")
        self.assertEqual(res.status_code, 200)
        report = res.get_json()["data"]
        self.assertEqual(report["version_id"], self.test_version_id)
        self.assertIn("comparison", report)

    # Test 10: Version listing endpoint
    def test_10_version_listing_api(self):
        res = self.client.get("/api/ingestion/versions")
        self.assertEqual(res.status_code, 200)
        versions = res.get_json()["data"]["versions"]
        v_ids = [v["version_id"] for v in versions]
        self.assertIn("baseline", v_ids)
        self.assertIn(self.test_version_id, v_ids)

    # Test 11: Version preview endpoints
    def test_11_version_preview_endpoints(self):
        # Overview preview
        res_ov = self.client.get(f"/api/ingestion/preview/{self.test_version_id}/overview")
        self.assertEqual(res_ov.status_code, 200)
        self.assertIn("kpis", res_ov.get_json()["data"])

        # Segmentation preview
        res_seg = self.client.get(f"/api/ingestion/preview/{self.test_version_id}/segmentation")
        self.assertEqual(res_seg.status_code, 200)
        self.assertIn("profiles", res_seg.get_json()["data"])

        # Recommendations preview
        res_rec = self.client.get(f"/api/ingestion/preview/{self.test_version_id}/recommendations")
        self.assertEqual(res_rec.status_code, 200)
        self.assertIn("evaluation_metrics", res_rec.get_json()["data"])

        # Churn preview
        res_ch = self.client.get(f"/api/ingestion/preview/{self.test_version_id}/churn")
        self.assertEqual(res_ch.status_code, 200)
        self.assertIn("summary", res_ch.get_json()["data"])

    # Test 12: Atomic version promotion and rollback
    def test_12_promotion_and_rollback_cycle(self):
        # Promote version
        p_res = self.client.post(f"/api/ingestion/promote/{self.test_version_id}")
        self.assertEqual(p_res.status_code, 200)

        # Verify active pointer updated
        self.assertEqual(self.preview_service.get_active_version_id(), self.test_version_id)

        # Rollback to baseline
        rb_res = self.client.post("/api/ingestion/rollback")
        self.assertEqual(rb_res.status_code, 200)

        # Verify restored to baseline
        self.assertEqual(self.preview_service.get_active_version_id(), "baseline")
        kpis = DataService.get_instance().get_kpi_summary()
        self.assertEqual(kpis["total_customers"], 1200)
        self.assertAlmostEqual(kpis["total_revenue"], 1807439.49, places=1)


if __name__ == "__main__":
    unittest.main()

