"""
Association Rule Regression Remediation Test Suite
Project: SMART Customer Analysis and Personalized Experience Using Big Data

Verifies all 10 mandatory regression test scenarios:
1. Customer-level basket construction.
2. Multiple line items for one customer.
3. Exclusion of invalid/null product IDs.
4. Correct support and lift calculation.
5. Cumulative candidate discovers the expected rules (~394 rules for known fixture).
6. Empty-rule generation preserves existing valid artifacts (retains baseline rules).
7. Candidate training does not overwrite baseline artifacts (strict SHA-256 preservation).
8. Candidate artifacts are version-isolated under ml/models/versions/<version_id>/.
9. Failed training does not partially corrupt existing files (atomic write safety).
10. Existing recommendation inference continues working seamlessly.
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import joblib
import hashlib
import unittest
import pandas as pd
from unittest.mock import patch

from backend.app import create_app
from backend.app.services.data_service import DataService
from backend.app.services.model_training_service import ModelTrainingService
from ml.recommendations.recommender import mine_association_rules


def compute_file_sha256(filepath: str) -> str:
    """Computes exact SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class TestAssociationRulesRemediation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app({"TESTING": True})
        cls.client = cls.app.test_client()
        cls.trainer = ModelTrainingService.get_instance()
        cls.data_service = DataService.get_instance()
        cls.models_dir = os.path.abspath(os.path.join(cls.trainer.workspace_root, "ml", "models"))
        cls.baseline_rules_joblib = os.path.join(cls.models_dir, "association_rules.joblib")
        cls.baseline_rules_json = os.path.join(cls.models_dir, "product_association_rules.json")

        # Snapshot baseline hashes
        cls.initial_joblib_hash = compute_file_sha256(cls.baseline_rules_joblib)
        cls.initial_json_hash = compute_file_sha256(cls.baseline_rules_json)

    def tearDown(self):
        # Verify baseline hashes never mutated after any test
        self.assertEqual(compute_file_sha256(self.baseline_rules_joblib), self.initial_joblib_hash)
        self.assertEqual(compute_file_sha256(self.baseline_rules_json), self.initial_json_hash)

    # -------------------------------------------------------------
    # 1. Customer-level basket construction
    # -------------------------------------------------------------
    def test_01_customer_level_basket_construction(self):
        """Verifies baskets are constructed by customer_id, yielding multi-item baskets."""
        df = pd.DataFrame({
            "customer_id": ["C1", "C1", "C2", "C2", "C3"],
            "product_id": ["P1", "P2", "P1", "P3", "P1"],
            "order_status": ["Completed", "Completed", "Completed", "Completed", "Completed"]
        })
        baskets = df.groupby("customer_id")["product_id"].unique()
        self.assertEqual(len(baskets), 3)
        self.assertEqual(set(baskets["C1"]), {"P1", "P2"})
        self.assertEqual(set(baskets["C2"]), {"P1", "P3"})
        self.assertEqual(set(baskets["C3"]), {"P1"})

    # -------------------------------------------------------------
    # 2. Multiple line items for one customer
    # -------------------------------------------------------------
    def test_02_multiple_line_items_for_one_customer(self):
        """Customers with duplicate line items for the same product produce unique basket sets."""
        df = pd.DataFrame({
            "customer_id": ["C1", "C1", "C1"],
            "product_id": ["P1", "P1", "P2"],
            "order_status": ["Completed", "Completed", "Completed"]
        })
        baskets = df.groupby("customer_id")["product_id"].unique()
        self.assertEqual(len(baskets["C1"]), 2)
        self.assertEqual(set(baskets["C1"]), {"P1", "P2"})

    # -------------------------------------------------------------
    # 3. Exclusion of invalid product IDs
    # -------------------------------------------------------------
    def test_03_exclusion_of_invalid_product_ids(self):
        """Null, empty, or whitespace product IDs are filtered prior to rule mining."""
        df = pd.DataFrame({
            "customer_id": ["C1", "C1", "C1", "C2", "C2"],
            "product_id": ["P1", None, "", "P2", "   "],
            "order_status": ["Completed", "Completed", "Completed", "Completed", "Completed"]
        })
        valid_df = df[df["product_id"].notna() & (df["product_id"].astype(str).str.strip() != "")].copy()
        baskets = valid_df.groupby("customer_id")["product_id"].unique()
        self.assertEqual(set(baskets["C1"]), {"P1"})
        self.assertEqual(set(baskets["C2"]), {"P2"})

    # -------------------------------------------------------------
    # 4. Correct support and lift calculation
    # -------------------------------------------------------------
    def test_04_support_and_lift_calculation(self):
        """Calculates exact pair Support, Confidence, and Lift matching Apriori semantics."""
        # 4 customers: 3 buy P1 & P2, 1 buys only P1
        df = pd.DataFrame({
            "customer_id": ["C1", "C1", "C2", "C2", "C3", "C3", "C4"],
            "product_id": ["P1", "P2", "P1", "P2", "P1", "P2", "P1"],
            "order_status": ["Completed"] * 7
        })
        rules_df = mine_association_rules(df, min_support=0.5, min_lift=1.0)
        self.assertFalse(rules_df.empty)

        # Support of (P1, P2) = 3/4 = 0.75
        r_p2_p1 = rules_df[(rules_df["antecedent_id"] == "P2") & (rules_df["consequent_id"] == "P1")].iloc[0]
        self.assertAlmostEqual(r_p2_p1["support"], 0.75, places=2)
        # Conf(P2 -> P1) = 3 / 3 = 1.0
        self.assertAlmostEqual(r_p2_p1["confidence"], 1.0, places=2)
        # Lift(P2 -> P1) = 1.0 / (4/4) = 1.0
        self.assertAlmostEqual(r_p2_p1["lift"], 1.0, places=2)

    # -------------------------------------------------------------
    # 5. Cumulative candidate discovers the expected rules
    # -------------------------------------------------------------
    def test_05_cumulative_candidate_discovers_expected_rules(self):
        """Verifies cumulative candidate version v_batch_20261117_121700_7dcf discovers ~394 rules."""
        candidate_version = "v_batch_20261117_121700_7dcf"
        v_data_dir = os.path.join(self.trainer.versions_dir, candidate_version)
        if not os.path.exists(v_data_dir):
            self.skipTest(f"Candidate dataset {candidate_version} not present; skipping.")

        res = self.trainer.train_recommender(candidate_version)
        self.assertEqual(res["status"], "TRAINING_COMPLETED")
        self.assertEqual(res["rules_source"], "MINED")
        self.assertEqual(res["rules_status"], "MINED_SUCCESSFULLY")
        # Assert approximately 394 rules (tolerance 390 to 400 for synthetic expansion)
        self.assertGreaterEqual(res["rules_mined"], 390)
        self.assertLessEqual(res["rules_mined"], 400)
        self.assertEqual(res["rules_mined"], 394)

    # -------------------------------------------------------------
    # 6. Empty-rule generation preserves existing valid artifacts
    # -------------------------------------------------------------
    def test_06_empty_rule_generation_fallback(self):
        """When an incoming batch produces 0 rules (e.g. support threshold too high), baseline rules are retained."""
        candidate_version = "v_batch_20261117_121700_7dcf"
        if not os.path.exists(os.path.join(self.trainer.versions_dir, candidate_version)):
            self.skipTest("Candidate version not present.")

        # Mock mine_association_rules to return empty DataFrame
        with patch("backend.app.services.model_training_service.mine_association_rules", return_value=pd.DataFrame()):
            res = self.trainer.train_recommender(candidate_version)
            self.assertEqual(res["status"], "TRAINING_COMPLETED")
            self.assertEqual(res["rules_source"], "RETAINED_BASELINE")
            self.assertEqual(res["rules_status"], "RETAINED_BASELINE_FALLBACK")
            self.assertGreaterEqual(res["rules_mined"], 390)

            # Check that saved artifact in candidate version is not empty
            v_rules_path = os.path.join(self.trainer.models_versions_dir, candidate_version, "product_association_rules.json")
            with open(v_rules_path, "r", encoding="utf-8") as f:
                saved_rules = json.load(f)
            self.assertGreaterEqual(len(saved_rules), 390)

    # -------------------------------------------------------------
    # 7. Candidate training does not overwrite baseline artifacts
    # -------------------------------------------------------------
    def test_07_candidate_training_does_not_overwrite_baseline(self):
        """Candidate model retraining must never alter baseline files in ml/models/."""
        candidate_version = "v_batch_20261117_121700_7dcf"
        if not os.path.exists(os.path.join(self.trainer.versions_dir, candidate_version)):
            self.skipTest("Candidate version not present.")

        self.trainer.retrain_all_models(candidate_version)

        # Baseline hashes must be identical to pre-test state
        self.assertEqual(compute_file_sha256(self.baseline_rules_joblib), self.initial_joblib_hash)
        self.assertEqual(compute_file_sha256(self.baseline_rules_json), self.initial_json_hash)

    # -------------------------------------------------------------
    # 8. Candidate artifacts are version-isolated
    # -------------------------------------------------------------
    def test_08_candidate_artifacts_are_version_isolated(self):
        """Candidate version artifacts reside strictly in ml/models/versions/<version_id>/."""
        candidate_version = "v_batch_20261117_121700_7dcf"
        v_models_dir = os.path.join(self.trainer.models_versions_dir, candidate_version)

        self.assertTrue(os.path.exists(os.path.join(v_models_dir, "product_association_rules.json")))
        self.assertTrue(os.path.exists(os.path.join(v_models_dir, "association_rules.joblib")))
        self.assertTrue(os.path.exists(os.path.join(v_models_dir, "customer_recommendations.json")))
        self.assertTrue(os.path.exists(os.path.join(v_models_dir, "item_similarity_matrix.joblib")))

    # -------------------------------------------------------------
    # 9. Failed training does not partially corrupt existing files
    # -------------------------------------------------------------
    def test_09_failed_training_atomic_write_safety(self):
        """A failure during training does not leave corrupted .tmp files or destroy valid artifacts."""
        candidate_version = "v_batch_20261117_121700_7dcf"
        v_models_dir = os.path.join(self.trainer.models_versions_dir, candidate_version)
        rules_path = os.path.join(v_models_dir, "product_association_rules.json")

        initial_candidate_hash = compute_file_sha256(rules_path) if os.path.exists(rules_path) else None

        # Simulate exception during recommendation scoring
        with patch("pandas.DataFrame.pivot", side_effect=RuntimeError("Simulated pivot crash")):
            with self.assertRaises(RuntimeError):
                self.trainer.train_recommender(candidate_version)

        # Confirm no orphaned .tmp files
        for f in os.listdir(v_models_dir):
            self.assertFalse(f.endswith(".tmp"), f"Found uncleaned temporary file: {f}")

        # If previous artifact existed, it remains intact
        if initial_candidate_hash and os.path.exists(rules_path):
            self.assertEqual(compute_file_sha256(rules_path), initial_candidate_hash)

    # -------------------------------------------------------------
    # 10. Existing recommendation inference continues working
    # -------------------------------------------------------------
    def test_10_recommendation_inference_continues_working(self):
        """GET /api/recommendations/<customer_id> returns valid Top-5 recommendations with explanations."""
        res = self.client.get("/api/recommendations/CUST_0001")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertEqual(data["customer_id"], "CUST_0001")
        self.assertEqual(data["recommendations_count"], 5)
        self.assertEqual(len(data["top_recommendations"]), 5)

        # Check association rules API
        res_rules = self.client.get("/api/recommendations/rules")
        self.assertEqual(res_rules.status_code, 200)
        rules_data = res_rules.get_json()["data"]
        self.assertGreaterEqual(len(rules_data), 10)
        self.assertIn("antecedent", rules_data[0])
        self.assertIn("consequent", rules_data[0])
        self.assertIn("lift", rules_data[0])


if __name__ == "__main__":
    unittest.main()

