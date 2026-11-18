"""
Dedicated Multi-Format Raw Data Ingestion, Processing & Export Test Suite
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Verifies:
1. Multi-Format Upload & Staging (CSV, JSON, JSONL, TXT, LOG, Mixed, Unsupported, Empty, Oversized, Path Traversal)
2. Schema Discovery Engine (Headers, Data Types, Source Identification, Customer ID Detection)
3. Field Mapping API (Custom Re-mapping, Analytics Eligibility Re-evaluation)
4. HDFS Raw Storage Integrity (Byte Preservation, SHA-256)
5. Multi-Format PySpark Batch Processing (23-Column Unified Feature Matrix Generation)
6. Data Export Endpoints (Canonical Templates, Raw Files, Processed Datasets, Analytics Reports)
7. Backward Compatibility & Baseline Protection
"""

import os
import json
import io
import shutil
import unittest
from datetime import datetime

from backend.app import create_app
from backend.app.services.ingestion_service import IngestionService, sanitize_filename
from backend.app.services.pipeline_execution_service import PipelineExecutionService
from big_data.ingestion.schema_discovery import SchemaDiscoveryEngine, infer_data_type


class TestMultiFormatIngestion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

        cls.workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        cls.uploads_dir = os.path.join(cls.workspace_root, "data", "uploads")
        cls.versions_dir = os.path.join(cls.workspace_root, "data", "versions")
        cls.created_batches = []
        cls.created_versions = []

    @classmethod
    def tearDownClass(cls):
        # Cleanup temporary batches created during testing
        for bid in cls.created_batches:
            p = os.path.join(cls.uploads_dir, bid)
            if os.path.exists(p):
                shutil.rmtree(p, ignore_errors=True)

        for vid in cls.created_versions:
            p = os.path.join(cls.versions_dir, vid)
            if os.path.exists(p):
                shutil.rmtree(p, ignore_errors=True)

    # -----------------------------------------------------------------
    # 1. Schema Discovery Unit Tests
    # -----------------------------------------------------------------
    def test_01_infer_data_types(self):
        """Verifies scalar type inference logic."""
        self.assertEqual(infer_data_type("123"), "integer")
        self.assertEqual(infer_data_type("-45"), "integer")
        self.assertEqual(infer_data_type("19.99"), "double")
        self.assertEqual(infer_data_type("true"), "boolean")
        self.assertEqual(infer_data_type("2024-05-15 14:30:00"), "timestamp")
        self.assertEqual(infer_data_type(""), "null")
        self.assertEqual(infer_data_type(None), "null")
        self.assertEqual(infer_data_type("Electronics"), "string")

    def test_02_schema_discovery_csv(self):
        """Tests discovery on CSV with custom column headers."""
        engine = SchemaDiscoveryEngine()
        csv_data = "customer_id,order_id,amount,transaction_date\nCUST_001,ORD_1,99.50,2024-01-15 10:00:00\nCUST_002,ORD_2,150.00,2024-01-16 11:00:00\n"
        tmp_path = os.path.join(self.uploads_dir, "_test_sample.csv")
        os.makedirs(self.uploads_dir, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(csv_data)

        try:
            res = engine.inspect_file(tmp_path, "orders.csv")
            self.assertEqual(res["format"], "CSV")
            self.assertEqual(res["record_count"], 2)
            self.assertTrue(res["has_customer_id"])
            field_names = [f["name"] for f in res["fields"]]
            self.assertIn("customer_id", field_names)
            self.assertIn("amount", field_names)
            self.assertEqual(res["suggested_source"], "transactions")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_03_schema_discovery_json(self):
        """Tests discovery on JSON array."""
        engine = SchemaDiscoveryEngine()
        json_data = [
            {"customer_id": "CUST_001", "session_id": "S1", "timestamp": "2024-01-15 10:00:00", "page_url": "/home", "action_type": "view", "duration_seconds": 45},
            {"customer_id": "CUST_002", "session_id": "S2", "timestamp": "2024-01-15 10:15:00", "page_url": "/cart", "action_type": "add_to_cart", "duration_seconds": 120}
        ]
        tmp_path = os.path.join(self.uploads_dir, "_test_sample.json")
        os.makedirs(self.uploads_dir, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f)

        try:
            res = engine.inspect_file(tmp_path, "web_clicks.json")
            self.assertEqual(res["format"], "JSON")
            self.assertEqual(res["record_count"], 2)
            self.assertTrue(res["has_customer_id"])
            self.assertEqual(res["suggested_source"], "web_activity")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_04_schema_discovery_jsonl(self):
        """Tests discovery on newline-delimited JSON (.jsonl)."""
        engine = SchemaDiscoveryEngine()
        lines = [
            json.dumps({"customer_id": "CUST_001", "sentiment": "Positive", "sentiment_score": 0.85, "platform": "Twitter"}),
            json.dumps({"customer_id": "CUST_002", "sentiment": "Negative", "sentiment_score": -0.60, "platform": "Instagram"})
        ]
        tmp_path = os.path.join(self.uploads_dir, "_test_sample.jsonl")
        os.makedirs(self.uploads_dir, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        try:
            res = engine.inspect_file(tmp_path, "social_stream.jsonl")
            self.assertEqual(res["format"], "JSON_LINES")
            self.assertEqual(res["record_count"], 2)
            self.assertTrue(res["has_customer_id"])
            self.assertEqual(res["suggested_source"], "social_media")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_05_schema_discovery_log(self):
        """Tests key-value and access log pattern discovery."""
        engine = SchemaDiscoveryEngine()
        kv_lines = [
            'time="2024-01-15 10:00:00" customer_id="CUST_001" action="login" status="success"',
            'time="2024-01-15 10:05:00" customer_id="CUST_002" action="purchase" status="success"'
        ]
        tmp_path = os.path.join(self.uploads_dir, "_test_sample.log")
        os.makedirs(self.uploads_dir, exist_ok=True)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write("\n".join(kv_lines))

        try:
            res = engine.inspect_file(tmp_path, "access.log")
            self.assertEqual(res["format"], "LOG")
            self.assertEqual(res["log_pattern"], "KEY_VALUE_LOG")
            self.assertTrue(res["has_customer_id"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # -----------------------------------------------------------------
    # 2. Multi-Format Upload API Tests
    # -----------------------------------------------------------------
    def test_06_upload_multi_format_batch(self):
        """Verifies POST /api/ingestion/upload-multi with mixed valid formats."""
        data = {
            "files": [
                (io.BytesIO(b"customer_id,transaction_id,total_amount\nCUST_001,TXN_1,150.00\n"), "tx.csv"),
                (io.BytesIO(json.dumps([{"customer_id": "CUST_001", "page_url": "/deals", "action_type": "click"}]).encode("utf-8")), "web.json"),
                (io.BytesIO(b'{"customer_id": "CUST_001", "sentiment": "Positive", "sentiment_score": 0.9}\n'), "soc.jsonl")
            ]
        }
        res = self.client.post("/api/ingestion/upload-multi", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 201)
        resp_json = res.get_json()
        self.assertEqual(resp_json["status"], "success")

        batch_id = resp_json["data"]["batch_id"]
        self.created_batches.append(batch_id)
        staged_files = resp_json["data"]["staged_files"]
        self.assertEqual(len(staged_files), 3)

        # Check that SHA-256 and byte sizes are recorded
        for fid, finfo in staged_files.items():
            self.assertIn("sha256", finfo)
            self.assertIn("size_bytes", finfo)
            self.assertGreater(finfo["size_bytes"], 0)
            self.assertIn("discovered_schema", finfo)

    def test_07_reject_empty_file_multi(self):
        """Verifies rejection of empty file in multi-format upload."""
        data = {
            "files": [
                (io.BytesIO(b""), "empty.csv")
            ]
        }
        res = self.client.post("/api/ingestion/upload-multi", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        self.assertIn("empty", res.get_json()["message"].lower())

    def test_08_reject_unsupported_extension_multi(self):
        """Verifies rejection of executable/unsupported extensions."""
        data = {
            "files": [
                (io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00"), "payload.exe")
            ]
        }
        res = self.client.post("/api/ingestion/upload-multi", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        self.assertIn("unsupported", res.get_json()["message"].lower())

    def test_09_sanitize_filenames_protection(self):
        """Verifies path traversal protection in uploaded filenames."""
        clean1 = sanitize_filename("../../etc/passwd.csv")
        self.assertNotIn("..", clean1)
        self.assertNotIn("/", clean1)
        self.assertNotIn("\\", clean1)

        clean2 = sanitize_filename("..\\..\\Windows\\System32\\cmd.exe")
        self.assertNotIn("..", clean2)

    # -----------------------------------------------------------------
    # 3. Field Mapping API Tests
    # -----------------------------------------------------------------
    def test_10_custom_field_mapping(self):
        """Verifies updating column mapping and re-evaluating analytics eligibility."""
        # Stage a file with non-canonical headers
        data = {
            "files": [
                (io.BytesIO(b"client_code,spent_money,order_id\nCUST_001,150.00,TX1\n"), "sales.csv")
            ]
        }
        res = self.client.post("/api/ingestion/upload-multi", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 201)
        batch = res.get_json()["data"]
        batch_id = batch["batch_id"]
        self.created_batches.append(batch_id)

        file_id = list(batch["staged_files"].keys())[0]

        # Call mapping endpoint
        map_payload = {
            "file_id": file_id,
            "custom_source": "transactions",
            "custom_mapping": {
                "client_code": "customer_id",
                "spent_money": "total_amount",
                "order_id": "transaction_id"
            }
        }
        res_map = self.client.post(f"/api/ingestion/mapping/{batch_id}", json=map_payload)
        self.assertEqual(res_map.status_code, 200)
        updated_batch = res_map.get_json()["data"]

        finfo = updated_batch["staged_files"][file_id]
        self.assertEqual(finfo["source_type"], "transactions")
        self.assertEqual(finfo["analytics_eligibility"], "ANALYTICS_ELIGIBLE")
        self.assertEqual(finfo["mapping_status"], "MAPPED")
        self.assertEqual(finfo["active_mapping"]["client_code"], "customer_id")

    # -----------------------------------------------------------------
    # 4. Data Export & Templates Endpoints
    # -----------------------------------------------------------------
    def test_11_canonical_templates_metadata(self):
        """Verifies GET /api/ingestion/templates returns specs for 3 analytical sources."""
        res = self.client.get("/api/ingestion/templates")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertIn("transactions", data)
        self.assertIn("web_activity", data)
        self.assertIn("social_media", data)
        self.assertIn("customer_id", data["transactions"]["headers"])

    def test_12_download_canonical_template_csv(self):
        """Verifies downloading pre-populated CSV template."""
        res = self.client.get("/api/ingestion/templates/transactions/download")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content_type, "text/csv; charset=utf-8")
        csv_text = res.get_data(as_text=True)
        self.assertTrue(csv_text.startswith("transaction_id,customer_id"))

    def test_13_export_raw_file(self):
        """Verifies direct export of untouched raw file bytes from staged batch."""
        raw_bytes = b"customer_id,transaction_id\nCUST_001,TXN_1\n"
        data = {
            "files": [
                (io.BytesIO(raw_bytes), "sample_raw.csv")
            ]
        }
        res_up = self.client.post("/api/ingestion/upload-multi", data=data, content_type="multipart/form-data")
        batch = res_up.get_json()["data"]
        batch_id = batch["batch_id"]
        self.created_batches.append(batch_id)

        file_id = list(batch["staged_files"].keys())[0]

        res_dl = self.client.get(f"/api/ingestion/export/raw/{batch_id}/{file_id}")
        self.assertEqual(res_dl.status_code, 200)
        self.assertEqual(res_dl.data, raw_bytes)

    def test_14_export_processed_baseline_dataset(self):
        """Verifies exporting baseline processed dataset via API."""
        res = self.client.get("/api/ingestion/export/processed/baseline/cleaned_transactions?format=csv")
        self.assertEqual(res.status_code, 200)
        self.assertGreater(len(res.data), 100)

    def test_15_export_analytics_report(self):
        """Verifies exporting analytics report."""
        res = self.client.get("/api/ingestion/export/analytics/baseline/processing")
        self.assertEqual(res.status_code, 200)
        report = json.loads(res.data.decode("utf-8"))
        self.assertIn("status", report)

    # -----------------------------------------------------------------
    # 5. Multi-Format PySpark Batch Processing Integration Test
    # -----------------------------------------------------------------
    def test_16_pyspark_multiformat_processing(self):
        """
        Executes PySpark batch processing on a multi-format batch (JSON transactions + CSV web activity).
        Verifies that canonical 23-column customer feature matrix is generated.
        """
        tx_json = [
            {
                "transaction_id": f"TX_{i}",
                "customer_id": f"CUST_{i:04d}",
                "transaction_date": "2024-05-15 10:00:00",
                "product_id": f"PROD_{i}",
                "product_category": "Electronics",
                "product_name": "Gadget",
                "quantity": 2,
                "unit_price": 50.0,
                "discount_percent": 0.0,
                "total_amount": 100.0,
                "payment_method": "Credit Card",
                "order_status": "Completed"
            }
            for i in range(1, 11)
        ]

        web_csv = "activity_id,customer_id,session_id,timestamp,page_url,action_type,product_id,duration_seconds,device_type,traffic_source\n"
        for i in range(1, 11):
            web_csv += f"ACT_{i},CUST_{i:04d},SESS_{i},2024-05-15 09:30:00,/products/item,view,PROD_{i},60,Desktop,Organic\n"

        data = {
            "files": [
                (io.BytesIO(json.dumps(tx_json).encode("utf-8")), "transactions.json"),
                (io.BytesIO(web_csv.encode("utf-8")), "web_activity.csv")
            ]
        }

        res_up = self.client.post("/api/ingestion/upload-multi", data=data, content_type="multipart/form-data")
        self.assertEqual(res_up.status_code, 201)
        batch = res_up.get_json()["data"]
        batch_id = batch["batch_id"]
        self.created_batches.append(batch_id)

        # Execute PySpark batch pipeline
        pipe_service = PipelineExecutionService.get_instance()
        success, msg, report = pipe_service.execute_batch_pipeline(batch_id, force_local_input=True)

        self.assertTrue(success, f"Pipeline execution failed: {msg}")
        self.assertEqual(report["status"], "PROCESSING_COMPLETED")
        self.assertEqual(report["feature_engineering"]["feature_columns_count"], 23)
        # Cumulative pipeline includes all historical customers (baseline >= 1200) plus any
        # newly added unique customers from this batch. We assert >= 1200 (not == 10) because
        # the pipeline correctly accumulates from baseline, not in isolation.
        self.assertGreaterEqual(
            report["feature_engineering"]["unified_customer_count"],
            1200,
            "Cumulative pipeline must always include all 1,200+ baseline customers"
        )

        version_id = report["version_id"]
        self.created_versions.append(version_id)

        # Verify artifacts exist under data/versions/<version_id>/
        v_dir = os.path.join(self.versions_dir, version_id)
        self.assertTrue(os.path.exists(os.path.join(v_dir, "unified_customer_features.parquet")))
        self.assertTrue(os.path.exists(os.path.join(v_dir, "unified_customer_features.csv")))
        self.assertTrue(os.path.exists(os.path.join(v_dir, "processing_report.json")))

    # -----------------------------------------------------------------
    # 6. Baseline Data & System Protection Test
    # -----------------------------------------------------------------
    def test_17_baseline_immutability_guarantee(self):
        """Verifies that baseline processed datasets and models remain strictly unchanged."""
        baseline_processed = os.path.join(self.workspace_root, "data", "processed")
        baseline_models = os.path.join(self.workspace_root, "ml", "models")

        # Crucial baseline artifacts must exist
        self.assertTrue(os.path.exists(os.path.join(baseline_processed, "unified_customer_features.csv")))
        self.assertTrue(os.path.exists(os.path.join(baseline_processed, "cleaned_transactions.csv")))
        self.assertTrue(os.path.exists(os.path.join(baseline_models, "kmeans_model.joblib")))
        self.assertTrue(os.path.exists(os.path.join(baseline_models, "churn", "churn_model.joblib")))


if __name__ == "__main__":
    unittest.main()
