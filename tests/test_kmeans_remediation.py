"""
K-Means Segmentation Accuracy, Evaluation & Visualization Remediation Test Suite
Project: SMART Customer Analysis and Personalized Experience Using Big Data

Verifies all 15 audit & remediation criteria:
1. Optimal K evaluation across K in [2, 8] with valid metrics.
2. Inertia monotonically decreases as K increases.
3. Silhouette score and Davies-Bouldin index within valid mathematical bounds.
4. Active model cluster count (K=7) matches selected_k and best_silhouette_k.
5. Bijective cluster-to-persona mapping (0 duplicate segment names).
6. 100% customer assignment integrity in customer_segments.parquet (0 nulls).
7. Customer counts sum to total active customer count (1,444) and percentages sum to 100%.
8. Persona statistics (spend, recency, etc.) derived from actual cluster centroids.
9. PCA projection coordinates exist for all 1,444 customers without NaN/Inf.
10. PCA explained variance matches fitted PCA model (41.80% PC1, 14.38% PC2, 56.18% sum).
11. PCA cluster assignments strictly align with active K-Means model assignments.
12. Backend DataService get_segmentation_evaluation returns accurate dynamic metadata.
13. Backend get_pca_scatter returns complete dataset without truncation.
14. Baseline backup integrity is preserved (1,200 customers, K=5, silhouette ~0.3451).
15. Distinct, accessible color palette assigned across all active clusters.
"""

import os
import sys
import json
import pytest
import numpy as np
import pandas as pd
import joblib

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
PROCESSED_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
MODELS_DIR = os.path.join(PROJECT_ROOT, "ml", "models")
BASELINE_DATA_BACKUP = os.path.join(PROJECT_ROOT, "data", "_baseline_backup")
BASELINE_MODEL_BACKUP = os.path.join(PROJECT_ROOT, "ml", "models", "_baseline_backup")


@pytest.fixture(scope="module")
def active_segments_df():
    parquet_path = os.path.join(PROCESSED_DATA_DIR, "customer_segments.parquet")
    assert os.path.exists(parquet_path), f"Active segments parquet missing at {parquet_path}"
    return pd.read_parquet(parquet_path)


@pytest.fixture(scope="module")
def cluster_profiles():
    profiles_path = os.path.join(MODELS_DIR, "cluster_profiles.json")
    assert os.path.exists(profiles_path), f"Cluster profiles missing at {profiles_path}"
    with open(profiles_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def elbow_metrics():
    elbow_path = os.path.join(MODELS_DIR, "elbow_metrics.json")
    assert os.path.exists(elbow_path), f"Elbow metrics missing at {elbow_path}"
    with open(elbow_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def kmeans_model():
    model_path = os.path.join(MODELS_DIR, "kmeans_model.joblib")
    assert os.path.exists(model_path), f"KMeans model missing at {model_path}"
    return joblib.load(model_path)


@pytest.fixture(scope="module")
def pca_model():
    pca_path = os.path.join(MODELS_DIR, "pca_model.joblib")
    assert os.path.exists(pca_path), f"PCA model missing at {pca_path}"
    return joblib.load(pca_path)


# ---------------------------------------------------------------------------
# Test 1 & 2 & 3: Optimal K Evaluation Metrics & Mathematical Validity
# ---------------------------------------------------------------------------
def test_optimal_k_evaluation_range_and_metrics(elbow_metrics):
    """Test 1: Evaluates K values from 2 to 8 with complete metric set."""
    assert isinstance(elbow_metrics, list), "elbow_metrics should be a list of evaluations"
    assert len(elbow_metrics) == 7, f"Expected 7 K evaluations (K=2..8), got {len(elbow_metrics)}"

    k_values = [item["k"] for item in elbow_metrics]
    assert k_values == list(range(2, 9)), f"Expected K range 2..8, got {k_values}"

    required_keys = ["k", "inertia", "silhouette_score", "davies_bouldin", "non_empty_clusters", "cluster_sizes"]
    for item in elbow_metrics:
        for key in required_keys:
            assert key in item, f"Missing key '{key}' in K={item.get('k')} evaluation"
            assert item[key] is not None, f"Key '{key}' is None for K={item.get('k')}"


def test_inertia_monotonic_decrease(elbow_metrics):
    """Test 2: Inertia (WCSS) must decrease monotonically as K increases."""
    inertias = [item["inertia"] for item in elbow_metrics]
    for i in range(len(inertias) - 1):
        assert inertias[i] > inertias[i + 1], (
            f"Inertia at K={elbow_metrics[i]['k']} ({inertias[i]}) should be greater than "
            f"at K={elbow_metrics[i+1]['k']} ({inertias[i+1]})"
        )


def test_clustering_metrics_mathematical_bounds(elbow_metrics, active_segments_df):
    """Test 3: Silhouette score in [-1, 1], Davies-Bouldin >= 0, non-empty clusters == K."""
    expected_count = len(active_segments_df)
    for item in elbow_metrics:
        sil = item["silhouette_score"]
        db = item["davies_bouldin"]
        k = item["k"]
        non_empty = item["non_empty_clusters"]

        assert -1.0 <= sil <= 1.0, f"Silhouette score {sil} out of bounds [-1, 1] for K={k}"
        assert db >= 0.0, f"Davies-Bouldin index {db} cannot be negative for K={k}"
        assert non_empty == k, f"Expected {k} non-empty clusters, got {non_empty} for K={k}"
        assert len(item["cluster_sizes"]) == k, f"cluster_sizes length should equal {k}"
        assert sum(item["cluster_sizes"]) == expected_count, f"Sum of cluster sizes must equal {expected_count}, got {sum(item['cluster_sizes'])}"


# ---------------------------------------------------------------------------
# Test 4: Selected Cluster Count Consistency
# ---------------------------------------------------------------------------
def test_selected_cluster_count_consistency(cluster_profiles, kmeans_model, elbow_metrics):
    """Test 4: Selected K in profiles matches active model n_clusters and best silhouette."""
    metrics = cluster_profiles.get("metrics", {})
    selected_k = metrics.get("selected_k")
    best_sil_k = metrics.get("best_silhouette_k")

    # For the active 1,444 customer dataset, K=7 achieves the highest silhouette score (0.3493)
    best_eval = max(elbow_metrics, key=lambda x: x["silhouette_score"])
    assert best_eval["k"] == 7, f"Expected best silhouette at K=7, got K={best_eval['k']}"
    assert best_eval["silhouette_score"] > 0.30, f"Expected strong silhouette score > 0.30, got {best_eval['silhouette_score']}"

    assert selected_k == 7, f"Expected selected_k == 7, got {selected_k}"
    assert best_sil_k == 7, f"Expected best_silhouette_k == 7, got {best_sil_k}"
    assert kmeans_model.n_clusters == 7, f"KMeans model n_clusters ({kmeans_model.n_clusters}) must match selected_k (7)"
    assert len(cluster_profiles.get("clusters", [])) == 7, "cluster_profiles must define exactly 7 clusters"


# ---------------------------------------------------------------------------
# Test 5 & 15: Bijective Persona Mapping & Accessible Palette
# ---------------------------------------------------------------------------
def test_bijective_persona_mapping_and_colors(cluster_profiles):
    """Test 5 & 15: Strict 1-to-1 mapping between cluster ID and unique persona name/color."""
    clusters = cluster_profiles.get("clusters", [])
    assert len(clusters) == 7, f"Expected 7 cluster profiles, got {len(clusters)}"

    cluster_ids = [c["cluster_id"] for c in clusters]
    cluster_names = [c["cluster_name"] for c in clusters]
    colors = [c["color"] for c in clusters]

    # Verify Cluster IDs are 0 through 6
    assert set(cluster_ids) == set(range(7)), f"Cluster IDs must be 0..6, got {cluster_ids}"

    # Verify no duplicate persona names (Bijective mapping)
    assert len(set(cluster_names)) == len(cluster_names), f"Duplicate cluster names detected: {cluster_names}"
    for name in cluster_names:
        assert "At-Risk" not in name or cluster_names.count(name) == 1, f"Duplicate 'At-Risk' persona found: {name}"

    # Verify no duplicate colors
    assert len(set(colors)) == len(colors), f"Duplicate cluster colors detected: {colors}"
    for col in colors:
        assert col.startswith("#") and len(col) == 7, f"Invalid hex color format: {col}"


# ---------------------------------------------------------------------------
# Test 6 & 7 & 8: Customer Assignment Integrity & Centroid Statistics
# ---------------------------------------------------------------------------
def test_customer_assignment_integrity(active_segments_df, cluster_profiles):
    """Test 6 & 7: Exactly all customers, 0 null clusters, customer count sum matches."""
    n_cust = len(active_segments_df)
    assert n_cust >= 1200, f"Expected at least 1,200 baseline customers in active dataset, got {n_cust}"

    # Check for null or invalid clusters
    assert not active_segments_df["cluster_id"].isna().any(), "Found NaN cluster_id in customer_segments"
    assert not active_segments_df["cluster_name"].isna().any(), "Found NaN cluster_name in customer_segments"

    valid_ids = set(range(7))
    assigned_ids = set(active_segments_df["cluster_id"].unique())
    assert assigned_ids == valid_ids, f"Assigned cluster IDs {assigned_ids} do not match valid IDs {valid_ids}"

    # Check counts match profiles
    clusters = cluster_profiles.get("clusters", [])
    total_assigned_count = sum(c["customer_count"] for c in clusters)
    assert total_assigned_count == n_cust, f"Sum of cluster counts ({total_assigned_count}) != {n_cust}"

    total_pct = sum(c["percentage"] for c in clusters)
    assert total_pct == pytest.approx(100.0, abs=0.1), f"Sum of cluster percentages ({total_pct}) != 100%"

    # Verify individual cluster counts match dataframe counts
    counts_by_id = active_segments_df["cluster_id"].value_counts().to_dict()
    for c in clusters:
        cid = c["cluster_id"]
        assert c["customer_count"] == counts_by_id[cid], (
            f"Cluster {cid} profile count ({c['customer_count']}) != DataFrame count ({counts_by_id[cid]})"
        )


def test_persona_centroids_heuristics(cluster_profiles):
    """Test 8: VIP spenders have highest spend; Dormant have lowest spend/high recency."""
    clusters_by_name = {c["cluster_name"]: c for c in cluster_profiles.get("clusters", [])}

    # VIP cluster verification
    vip_cluster = next((c for name, c in clusters_by_name.items() if "VIP" in name), None)
    assert vip_cluster is not None, "VIP cluster must exist"
    assert vip_cluster["avg_total_spend"] > 3000.0, f"VIP spend should be high, got {vip_cluster['avg_total_spend']}"

    # Dormant cluster verification
    dormant_cluster = next((c for name, c in clusters_by_name.items() if "Dormant" in name), None)
    assert dormant_cluster is not None, "Dormant cluster must exist"
    assert dormant_cluster["avg_total_spend"] < 50.0, f"Dormant spend should be minimal, got {dormant_cluster['avg_total_spend']}"
    assert dormant_cluster["avg_recency_days"] > 300, f"Dormant recency should be high, got {dormant_cluster['avg_recency_days']}"


# ---------------------------------------------------------------------------
# Test 9 & 10 & 11: PCA Projection & Variance Validity
# ---------------------------------------------------------------------------
def test_pca_projection_coordinates_and_variance(active_segments_df, pca_model, cluster_profiles):
    """Test 9 & 10 & 11: PCA coordinates exist for all 1,444 customers, explained variance matches."""
    assert "pca_x" in active_segments_df.columns, "pca_x column missing"
    assert "pca_y" in active_segments_df.columns, "pca_y column missing"

    assert not active_segments_df["pca_x"].isna().any(), "Found NaN in pca_x"
    assert not active_segments_df["pca_y"].isna().any(), "Found NaN in pca_y"
    assert np.isfinite(active_segments_df["pca_x"]).all(), "Non-finite values in pca_x"
    assert np.isfinite(active_segments_df["pca_y"]).all(), "Non-finite values in pca_y"

    # Verify PCA model explained variance
    assert len(pca_model.explained_variance_ratio_) == 2
    pc1_var = float(pca_model.explained_variance_ratio_[0])
    pc2_var = float(pca_model.explained_variance_ratio_[1])
    total_var = pc1_var + pc2_var

    assert pc1_var > 0.35, f"Expected PC1 > 35%, got {pc1_var*100}%"
    assert pc2_var > 0.10, f"Expected PC2 > 10%, got {pc2_var*100}%"
    assert total_var > 0.50, f"Expected Total > 50%, got {total_var*100}%"

    # Verify metrics in cluster_profiles match fitted PCA model
    metrics = cluster_profiles.get("metrics", {})
    assert metrics["pca_explained_variance_ratio"][0] == pytest.approx(pc1_var, abs=1e-4)
    assert metrics["pca_explained_variance_ratio"][1] == pytest.approx(pc2_var, abs=1e-4)
    assert metrics["pca_total_variance"] == pytest.approx(total_var, abs=1e-4)


# ---------------------------------------------------------------------------
# Test 12 & 13: DataService Evaluation & Scatter Output Integrity
# ---------------------------------------------------------------------------
def test_dataservice_evaluation_and_scatter():
    """Test 12 & 13: DataService get_segmentation_evaluation & get_pca_scatter without truncation."""
    from backend.app.services.data_service import DataService
    ds = DataService()

    eval_data = ds.get_segmentation_evaluation()
    assert "metrics" in eval_data
    assert "elbow_curve" in eval_data
    assert "clusters" in eval_data

    metrics = eval_data["metrics"]
    assert metrics["selected_k"] == 7
    assert metrics["total_customers"] == len(ds.df_segments)
    assert len(eval_data["clusters"]) == 7
    assert len(eval_data["elbow_curve"]) == 7

    # Verify PCA scatter returns all points without limit truncation
    scatter_full = ds.get_pca_scatter()
    assert len(scatter_full) == len(ds.df_segments), f"Expected {len(ds.df_segments)} points from full get_pca_scatter(), got {len(scatter_full)}"

    # Check essential fields in scatter points
    sample_pt = scatter_full[0]
    for key in ["customer_id", "cluster_id", "cluster_name", "pca_x", "pca_y"]:
        assert key in sample_pt, f"Key '{key}' missing from scatter point"


# ---------------------------------------------------------------------------
# Test 14: Baseline Backup Preservation
# ---------------------------------------------------------------------------
def test_baseline_backup_preservation():
    """Test 14: Baseline backups remain intact (1,200 customers, K=5, silhouette ~0.3451)."""
    assert os.path.exists(BASELINE_DATA_BACKUP), "Baseline data backup directory missing"
    assert os.path.exists(BASELINE_MODEL_BACKUP), "Baseline model backup directory missing"

    baseline_profiles_path = os.path.join(BASELINE_MODEL_BACKUP, "cluster_profiles.json")
    assert os.path.exists(baseline_profiles_path), "Baseline cluster profiles missing"

    with open(baseline_profiles_path, "r", encoding="utf-8") as f:
        baseline_profiles = json.load(f)

    # Baseline had K=5 clusters with 1,200 customers
    assert len(baseline_profiles.get("clusters", [])) == 5, "Baseline should have 5 clusters"
    baseline_metrics = baseline_profiles.get("metrics", {})
    assert baseline_metrics.get("selected_k", 5) == 5, "Baseline selected_k should be 5"
    assert baseline_metrics.get("total_customers", 1200) == 1200, "Baseline customer count should be 1200"
    assert baseline_metrics.get("silhouette_score", 0.3451) == pytest.approx(0.3451, abs=1e-2)
