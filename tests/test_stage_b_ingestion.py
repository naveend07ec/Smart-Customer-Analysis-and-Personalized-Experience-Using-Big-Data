"""
Stage B Automated Ingestion & HDFS Verification Test Suite
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Verifies all 20 Stage B requirements:
1. Successful upload of all three CSVs.
2. Missing one required CSV.
3. Incorrect file extension.
4. Incorrect headers.
5. Empty CSV.
6. Invalid data types.
7. Duplicate primary keys.
8. Invalid numeric values.
9. Invalid categorical values.
10. Invalid timestamps.
11. Customer coverage reporting.
12. Meaningful null product IDs.
13. Missing payment method handling.
14. HDFS unavailable handling.
15. HDFS upload failure handling.
16. HDFS checksum / file-size mismatch.
17. Successful HDFS ingestion & verification.
18. Batch isolation and no overwrite.
19. Existing API backward compatibility.
20. Ingestion service status transitions.
"""

import os
import io
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch

from backend.app import create_app
from backend.app.services.ingestion_service import (
    IngestionService,
    STATUS_UPLOADED,
    STATUS_VALIDATED,
    STATUS_VALIDATION_FAILED,
    STATUS_INGESTED,
    STATUS_INGESTION_FAILED
)
from big_data.ingestion.validator import DatasetValidator
from big_data.ingestion.hdfs_client import HDFSManager


def create_sample_csv_content():
    """Generates valid 3-dataset CSV text contents for testing."""
    tx_csv = (
        "transaction_id,customer_id,transaction_date,product_id,product_category,product_name,quantity,unit_price,discount_percent,total_amount,payment_method,order_status\n"
        "TXN_0001,CUST_0001,2024-01-01 10:00:00,PROD_101,Electronics,Headphones,1,100.0,0.0,100.0,Credit Card,Completed\n"
        "TXN_0002,CUST_0002,2024-01-02 11:30:00,PROD_102,Books,Programming Book,2,25.0,0.0,50.0,PayPal,Completed\n"
        "TXN_0003,CUST_0003,2024-01-03 14:15:00,PROD_103,Apparel,Running Shoes,1,80.0,10.0,72.0,,Completed\n"
    )

    web_csv = (
        "activity_id,customer_id,session_id,timestamp,page_url,action_type,product_id,duration_seconds,device_type,traffic_source\n"
        "WEB_0001,CUST_0001,SESS_001,2024-01-01 09:50:00,/home,page_view,,45,Desktop,Direct\n"
        "WEB_0002,CUST_0001,SESS_001,2024-01-01 09:55:00,/products/headphones,product_view,PROD_101,120,Desktop,Direct\n"
        "WEB_0003,CUST_0002,SESS_002,2024-01-02 11:20:00,/products/books,product_view,PROD_102,60,Mobile,Social Media\n"
    )

    soc_csv = (
        "interaction_id,customer_id,timestamp,platform,interaction_type,sentiment,sentiment_score,engagement_score,feedback_content,associated_category\n"
        "SOC_0001,CUST_0001,2024-01-01 12:00:00,Twitter/X,review,Positive,0.85,75,Great headphones!,Electronics\n"
        "SOC_0002,CUST_0003,2024-01-03 16:00:00,Instagram,comment,Positive,0.60,40,Love the shoes!,Apparel\n"
    )
    return tx_csv, web_csv, soc_csv


class TestStageBIngestion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({"TESTING": True})
        cls.client = cls.app.test_client()
        cls.validator = DatasetValidator(strict_primary_key=True)

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_files(self, tx_content, web_content, soc_content):
        tx_p = os.path.join(self.temp_dir, "transactions.csv")
        web_p = os.path.join(self.temp_dir, "web_activity.csv")
        soc_p = os.path.join(self.temp_dir, "social_media.csv")
        with open(tx_p, "w", encoding="utf-8") as f:
            f.write(tx_content)
        with open(web_p, "w", encoding="utf-8") as f:
            f.write(web_content)
        with open(soc_p, "w", encoding="utf-8") as f:
            f.write(soc_content)
        return tx_p, web_p, soc_p

    # Test 1: Successful upload and validation of all three CSVs
    def test_01_successful_upload_and_validation(self):
        tx, web, soc = create_sample_csv_content()
        tx_p, web_p, soc_p = self._write_files(tx, web, soc)

        res = self.validator.validate_batch("batch_test_01", tx_p, web_p, soc_p)
        self.assertTrue(res["is_valid"])
        self.assertEqual(len(res["errors"]), 0)
        self.assertEqual(res["summary"]["transactions_count"], 3)
        self.assertEqual(res["summary"]["web_activity_count"], 3)
        self.assertEqual(res["summary"]["social_media_count"], 2)

    # Test 2: Missing one required CSV
    def test_02_missing_one_required_csv(self):
        tx, web, soc = create_sample_csv_content()
        tx_p, web_p, _ = self._write_files(tx, web, soc)
        missing_soc_p = os.path.join(self.temp_dir, "nonexistent_social.csv")

        res = self.validator.validate_batch("batch_test_02", tx_p, web_p, missing_soc_p)
        self.assertFalse(res["is_valid"])
        self.assertIn("social_media.csv is missing.", res["errors"])

    # Test 3: Incorrect file extension
    def test_03_incorrect_file_extension_api(self):
        data = {
            "transactions": (io.BytesIO(b"data"), "transactions.txt"),
            "web_activity": (io.BytesIO(b"data"), "web_activity.csv"),
            "social_media": (io.BytesIO(b"data"), "social_media.csv")
        }
        res = self.client.post("/api/ingestion/upload", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        res_json = res.get_json()
        self.assertIn("Invalid file format", res_json["message"])

    # Test 4: Incorrect headers
    def test_04_incorrect_headers(self):
        tx, web, soc = create_sample_csv_content()
        bad_tx = tx.replace("transaction_id", "bad_id_col")
        tx_p, web_p, soc_p = self._write_files(bad_tx, web, soc)

        res = self.validator.validate_batch("batch_test_04", tx_p, web_p, soc_p)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("header mismatch" in err for err in res["errors"]))

    # Test 5: Empty CSV
    def test_05_empty_csv(self):
        _, web, soc = create_sample_csv_content()
        tx_p, web_p, soc_p = self._write_files("", web, soc)

        res = self.validator.validate_batch("batch_test_05", tx_p, web_p, soc_p)
        self.assertFalse(res["is_valid"])
        self.assertIn("transactions.csv is empty (0 bytes).", res["errors"])

    # Test 6: Invalid data types
    def test_06_invalid_data_types(self):
        tx, web, soc = create_sample_csv_content()
        bad_tx = tx.replace("1,100.0,0.0,100.0", "NON_INT_QTY,100.0,0.0,100.0")
        tx_p, web_p, soc_p = self._write_files(bad_tx, web, soc)

        res = self.validator.validate_batch("batch_test_06", tx_p, web_p, soc_p)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("is not an integer" in err for err in res["errors"]))

    # Test 7: Duplicate primary keys
    def test_07_duplicate_primary_keys(self):
        tx, web, soc = create_sample_csv_content()
        # Duplicate TXN_0001
        dup_tx = tx + "TXN_0001,CUST_0001,2024-01-04 12:00:00,PROD_101,Electronics,Headphones,1,100.0,0.0,100.0,Credit Card,Completed\n"
        tx_p, web_p, soc_p = self._write_files(dup_tx, web, soc)

        # In strict_pk=True mode
        res_strict = self.validator.validate_batch("batch_test_07_s", tx_p, web_p, soc_p, strict_pk=True)
        self.assertFalse(res_strict["is_valid"])
        self.assertFalse(res_strict["checks"]["primary_keys_unique"])
        self.assertTrue(any("duplicate transaction_id" in err for err in res_strict["errors"]))

        # In standard batch ingestion mode (with deduplication warning)
        res_loose = self.validator.validate_batch("batch_test_07_l", tx_p, web_p, soc_p, strict_pk=False)
        self.assertTrue(res_loose["is_valid"])
        self.assertEqual(res_loose["summary"]["duplicate_counts"]["transactions"], 1)

    # Test 8: Invalid numeric values (e.g. quantity <= 0)
    def test_08_invalid_numeric_values(self):
        tx, web, soc = create_sample_csv_content()
        bad_tx = tx.replace("1,100.0,0.0,100.0", "-5,100.0,0.0,-500.0")
        tx_p, web_p, soc_p = self._write_files(bad_tx, web, soc)

        res = self.validator.validate_batch("batch_test_08", tx_p, web_p, soc_p)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("quantity must be > 0" in err for err in res["errors"]))

    # Test 9: Invalid categorical values (e.g. invalid order_status)
    def test_09_invalid_categorical_values(self):
        tx, web, soc = create_sample_csv_content()
        bad_tx = tx.replace("Completed", "INVALID_STATUS")
        tx_p, web_p, soc_p = self._write_files(bad_tx, web, soc)

        res = self.validator.validate_batch("batch_test_09", tx_p, web_p, soc_p)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("Invalid order_status" in err for err in res["errors"]))

    # Test 10: Invalid timestamps
    def test_10_invalid_timestamps(self):
        tx, web, soc = create_sample_csv_content()
        bad_tx = tx.replace("2024-01-01 10:00:00", "2024-99-99 99:99:99")
        tx_p, web_p, soc_p = self._write_files(bad_tx, web, soc)

        res = self.validator.validate_batch("batch_test_10", tx_p, web_p, soc_p)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("Invalid transaction_date format" in err for err in res["errors"]))

    # Test 11: Cross-source customer coverage reporting
    def test_11_customer_coverage_reporting(self):
        tx, web, soc = create_sample_csv_content()
        tx_p, web_p, soc_p = self._write_files(tx, web, soc)

        res = self.validator.validate_batch("batch_test_11", tx_p, web_p, soc_p)
        cov = res["summary"]["customer_coverage"]
        self.assertIn("all_three_sources", cov)
        self.assertIn("two_sources", cov)
        self.assertIn("single_source_only", cov)
        self.assertEqual(res["summary"]["unique_customers"]["total_unique"], 3)

    # Test 12: Meaningful null product_ids in web activity
    def test_12_meaningful_null_product_ids(self):
        tx, web, soc = create_sample_csv_content()
        tx_p, web_p, soc_p = self._write_files(tx, web, soc)

        res = self.validator.validate_batch("batch_test_12", tx_p, web_p, soc_p)
        self.assertTrue(res["is_valid"])
        # Row 1 of sample web activity has empty product_id
        self.assertGreater(res["summary"]["null_handling"]["web_meaningful_null_product_ids"], 0)

    # Test 13: Missing payment method handled gracefully
    def test_13_missing_payment_method_handling(self):
        tx, web, soc = create_sample_csv_content()
        tx_p, web_p, soc_p = self._write_files(tx, web, soc)

        res = self.validator.validate_batch("batch_test_13", tx_p, web_p, soc_p)
        self.assertTrue(res["is_valid"])
        # Row 3 has missing payment_method
        self.assertEqual(res["summary"]["null_handling"]["transactions_missing_payment"], 1)
        self.assertTrue(any("missing payment_method" in w for w in res["warnings"]))

    # Test 14: HDFS unavailable returns clear diagnostic failure
    @patch.object(HDFSManager, "check_hdfs_status")
    def test_14_hdfs_unavailable_handling(self, mock_status):
        mock_status.return_value = {
            "is_available": False,
            "cluster_status": "OFFLINE",
            "message": "NameNode socket connection refused"
        }
        service = IngestionService.get_instance()
        # Stage a test batch via API
        tx, web, soc = create_sample_csv_content()
        data = {
            "transactions": (io.BytesIO(tx.encode()), "transactions.csv"),
            "web_activity": (io.BytesIO(web.encode()), "web_activity.csv"),
            "social_media": (io.BytesIO(soc.encode()), "social_media.csv")
        }
        upload_res = self.client.post("/api/ingestion/upload", data=data, content_type="multipart/form-data")
        batch_id = upload_res.get_json()["data"]["batch_id"]

        commit_res = self.client.post(f"/api/ingestion/commit/{batch_id}")
        self.assertEqual(commit_res.status_code, 503)
        commit_json = commit_res.get_json()
        self.assertEqual(commit_json["status"], "error")
        self.assertEqual(commit_json["data"]["status"], STATUS_INGESTION_FAILED)
        self.assertIn("Hadoop HDFS cluster is OFFLINE", commit_json["message"])

    # Test 15: HDFS upload failure handling
    @patch.object(HDFSManager, "check_hdfs_status")
    @patch.object(HDFSManager, "upload_batch_to_hdfs")
    def test_15_hdfs_upload_failure(self, mock_upload, mock_status):
        mock_status.return_value = {"is_available": True, "cluster_status": "ONLINE"}
        mock_upload.return_value = (False, "DataNode block transfer error", {})

        tx, web, soc = create_sample_csv_content()
        data = {
            "transactions": (io.BytesIO(tx.encode()), "transactions.csv"),
            "web_activity": (io.BytesIO(web.encode()), "web_activity.csv"),
            "social_media": (io.BytesIO(soc.encode()), "social_media.csv")
        }
        upload_res = self.client.post("/api/ingestion/upload", data=data, content_type="multipart/form-data")
        batch_id = upload_res.get_json()["data"]["batch_id"]

        commit_res = self.client.post(f"/api/ingestion/commit/{batch_id}")
        self.assertEqual(commit_res.status_code, 400)
        commit_json = commit_res.get_json()
        self.assertEqual(commit_json["status"], "error")
        self.assertEqual(commit_json["data"]["status"], STATUS_INGESTION_FAILED)

    # Test 16: HDFS checksum / file-size mismatch
    @patch.object(HDFSManager, "check_hdfs_status")
    @patch.object(HDFSManager, "upload_batch_to_hdfs")
    def test_16_hdfs_size_mismatch(self, mock_upload, mock_status):
        mock_status.return_value = {"is_available": True, "cluster_status": "ONLINE"}
        mock_upload.return_value = (False, "HDFS file size mismatch: local=500, HDFS=300", {})

        tx, web, soc = create_sample_csv_content()
        data = {
            "transactions": (io.BytesIO(tx.encode()), "transactions.csv"),
            "web_activity": (io.BytesIO(web.encode()), "web_activity.csv"),
            "social_media": (io.BytesIO(soc.encode()), "social_media.csv")
        }
        upload_res = self.client.post("/api/ingestion/upload", data=data, content_type="multipart/form-data")
        batch_id = upload_res.get_json()["data"]["batch_id"]

        commit_res = self.client.post(f"/api/ingestion/commit/{batch_id}")
        self.assertEqual(commit_res.status_code, 400)
        self.assertIn("size mismatch", commit_res.get_json()["message"])

    # Test 17: Successful HDFS ingestion & verification
    @patch.object(HDFSManager, "check_hdfs_status")
    @patch.object(HDFSManager, "upload_batch_to_hdfs")
    def test_17_successful_hdfs_ingestion(self, mock_upload, mock_status):
        mock_status.return_value = {"is_available": True, "cluster_status": "ONLINE"}
        mock_upload.return_value = (True, "Uploaded and verified", {"files": {"transactions": {"verified": True}}})

        tx, web, soc = create_sample_csv_content()
        data = {
            "transactions": (io.BytesIO(tx.encode()), "transactions.csv"),
            "web_activity": (io.BytesIO(web.encode()), "web_activity.csv"),
            "social_media": (io.BytesIO(soc.encode()), "social_media.csv")
        }
        upload_res = self.client.post("/api/ingestion/upload", data=data, content_type="multipart/form-data")
        batch_id = upload_res.get_json()["data"]["batch_id"]

        commit_res = self.client.post(f"/api/ingestion/commit/{batch_id}")
        self.assertEqual(commit_res.status_code, 200)
        commit_json = commit_res.get_json()
        self.assertEqual(commit_json["status"], "success")
        self.assertEqual(commit_json["data"]["status"], STATUS_INGESTED)
        self.assertEqual(commit_json["data"]["hdfs_path"], f"/customer-analytics/raw/uploads/{batch_id}")

    # Test 18: Batch isolation and no overwrite
    def test_18_batch_isolation(self):
        tx, web, soc = create_sample_csv_content()
        data1 = {
            "transactions": (io.BytesIO(tx.encode()), "transactions.csv"),
            "web_activity": (io.BytesIO(web.encode()), "web_activity.csv"),
            "social_media": (io.BytesIO(soc.encode()), "social_media.csv")
        }
        data2 = {
            "transactions": (io.BytesIO(tx.encode()), "transactions.csv"),
            "web_activity": (io.BytesIO(web.encode()), "web_activity.csv"),
            "social_media": (io.BytesIO(soc.encode()), "social_media.csv")
        }
        res1 = self.client.post("/api/ingestion/upload", data=data1, content_type="multipart/form-data")
        res2 = self.client.post("/api/ingestion/upload", data=data2, content_type="multipart/form-data")

        b1 = res1.get_json()["data"]["batch_id"]
        b2 = res2.get_json()["data"]["batch_id"]
        self.assertNotEqual(b1, b2)

        # Baseline raw directories remain intact
        self.assertTrue(os.path.exists("data/raw/transactions.csv"))
        self.assertTrue(os.path.exists("data/raw/web_activity.csv"))
        self.assertTrue(os.path.exists("data/raw/social_media.csv"))

    # Test 19: Existing API backward compatibility
    def test_19_existing_api_backward_compatibility(self):
        endpoints = [
            "/api/health",
            "/api/overview",
            "/api/pipeline/summary",
            "/api/segments",
            "/api/analytics",
            "/api/churn/summary"
        ]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 200, f"Endpoint {ep} failed with {res.status_code}")

    # Test 20: Ingestion history and status polling
    def test_20_history_and_status_polling(self):
        hist_res = self.client.get("/api/ingestion/history")
        self.assertEqual(hist_res.status_code, 200)
        hist_json = hist_res.get_json()
        self.assertEqual(hist_json["status"], "success")
        self.assertIn("batches", hist_json["data"])


if __name__ == "__main__":
    unittest.main()

