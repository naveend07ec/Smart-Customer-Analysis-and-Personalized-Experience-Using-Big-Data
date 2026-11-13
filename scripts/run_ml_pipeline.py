"""
Master Stage 4 Machine Learning Pipeline
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Runs:
1. Part A: K-Means Customer Segmentation & PCA Visualization
2. Part B: Personalized Recommendation Engine & Association Mining
3. Comprehensive Verification & Artifact Audit
"""

import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.segmentation.train_kmeans import run_segmentation
from ml.recommendations.recommender import generate_recommendations


def main():
    start_time = time.time()
    print("=" * 75)
    print("STARTING STAGE 4: MACHINE LEARNING PIPELINE")
    print("=" * 75)

    # 1. Run Part A: Segmentation
    seg_results = run_segmentation()

    # 2. Run Part B: Recommendations
    rec_results = generate_recommendations()

    # 3. Artifact Verification
    print("\n" + "=" * 75)
    print("STAGE 4 ARTIFACT VERIFICATION & AUDIT")
    print("=" * 75)

    expected_datasets = [
        "customer_segments.csv",
        "customer_segments.parquet",
        "cluster_profiles.csv",
        "k_selection_metrics.csv",
        "customer_recommendations.csv",
        "customer_recommendations.parquet",
        "recommendation_evaluation.csv",
        "association_rules.csv",
        "customer_product_interactions.csv"
    ]

    expected_models = [
        "kmeans_model.joblib",
        "scaler.joblib",
        "pca_model.joblib",
        "segmentation_config.json",
        "item_similarity_matrix.joblib",
        "product_metadata.joblib",
        "association_rules.joblib"
    ]

    processed_dir = os.path.join(PROJECT_ROOT, "data", "processed")
    models_dir = os.path.join(PROJECT_ROOT, "ml", "models")

    print("\nVerifying Processed Datasets (data/processed/):")
    for fname in expected_datasets:
        fpath = os.path.join(processed_dir, fname)
        assert os.path.exists(fpath), f"Missing dataset: {fname}"
        sz = os.path.getsize(fpath)
        print(f"  * {fname:<36}: OK ({sz:,} bytes)")

    print("\nVerifying Model Artifacts (ml/models/):")
    for fname in expected_models:
        fpath = os.path.join(models_dir, fname)
        assert os.path.exists(fpath), f"Missing model: {fname}"
        sz = os.path.getsize(fpath)
        print(f"  * {fname:<36}: OK ({sz:,} bytes)")

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 75)
    print(f"STAGE 4 PIPELINE EXECUTED SUCCESSFULLY IN {elapsed}s")
    print("=" * 75)


if __name__ == "__main__":
    main()

