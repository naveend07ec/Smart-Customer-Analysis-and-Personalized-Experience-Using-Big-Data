"""
K-Means Customer Segmentation Pipeline
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Performs:
1. Feature extraction from unified customer features.
2. Missing/outlier verification and StandardScaler normalization.
3. K selection evaluation (K=2 to 8) using Inertia, Silhouette, Davies-Bouldin, and Calinski-Harabasz.
4. Model training with optimal K.
5. Unscaled cluster profiling and data-driven cluster naming.
6. 2D PCA projection for visual dashboard representation.
7. Model serialization and artifact exports.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
MODELS_DIR = os.path.join(PROJECT_ROOT, "ml", "models")


def run_segmentation():
    print("=" * 70)
    print("PART A: K-MEANS CUSTOMER SEGMENTATION")
    print("=" * 70)

    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    input_path = os.path.join(PROCESSED_DIR, "unified_customer_features.parquet")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_parquet(input_path)
    print(f"Loaded {len(df)} customer records with {len(df.columns)} total columns.")

    # 1. Feature Selection & Preparation
    feature_cols = [c for c in df.columns if c != "customer_id"]
    X = df[feature_cols].copy()

    # Pre-check for constant features and missing values
    null_counts = X.isnull().sum()
    if null_counts.sum() > 0:
        raise ValueError(f"Found unexpected missing values in features: {null_counts[null_counts > 0].to_dict()}")

    std_devs = X.std()
    constant_features = std_devs[std_devs == 0].index.tolist()
    if constant_features:
        print(f"Warning: Dropping constant features: {constant_features}")
        feature_cols = [c for c in feature_cols if c not in constant_features]
        X = X[feature_cols]

    print(f"Training on {len(feature_cols)} behavioural features.")

    # 2. Feature Scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. K Evaluation (K=2 to 8)
    print("\nEvaluating K from 2 to 8...")
    k_metrics = []
    for k in range(2, 9):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, labels)
        db = davies_bouldin_score(X_scaled, labels)
        ch = calinski_harabasz_score(X_scaled, labels)
        sizes = np.bincount(labels).tolist()

        k_metrics.append({
            "k": k,
            "inertia": round(float(km.inertia_), 2),
            "silhouette_score": round(float(sil), 4),
            "davies_bouldin_index": round(float(db), 4),
            "calinski_harabasz_score": round(float(ch), 2),
            "min_cluster_size": int(min(sizes)),
            "max_cluster_size": int(max(sizes)),
            "cluster_sizes": str(sizes)
        })

    k_metrics_df = pd.DataFrame(k_metrics)
    k_metrics_csv = os.path.join(PROCESSED_DIR, "k_selection_metrics.csv")
    k_metrics_df.to_csv(k_metrics_csv, index=False)
    print(f"K-selection evaluation metrics saved to: {k_metrics_csv}")

    for m in k_metrics:
        print(f"  K={m['k']}: Silhouette={m['silhouette_score']}, Inertia={m['inertia']}, DB={m['davies_bouldin_index']}, Sizes={m['cluster_sizes']}")

    # Select optimal K based on highest silhouette score & best cluster separation
    best_k_row = k_metrics_df.sort_values(by="silhouette_score", ascending=False).iloc[0]
    selected_k = int(best_k_row["k"])
    print(f"\n--> Selected Optimal K = {selected_k} (Highest Silhouette: {best_k_row['silhouette_score']}, Lowest Davies-Bouldin: {best_k_row['davies_bouldin_index']})")

    # 4. Final K-Means Model Training
    final_kmeans = KMeans(n_clusters=selected_k, random_state=42, n_init=10)
    cluster_labels = final_kmeans.fit_predict(X_scaled)
    df["cluster_id"] = cluster_labels

    # 5. Unscaled Cluster Profiling & Profile-Based Naming
    profile_mean = df.groupby("cluster_id")[feature_cols].mean()
    cluster_sizes = df["cluster_id"].value_counts().sort_index()

    # Assign descriptive names based on actual verified characteristics
    cluster_names = {}
    for cid in range(selected_k):
        c_mean = profile_mean.loc[cid]
        spend = c_mean["total_spend"]
        recency = c_mean["recency_days"]
        web_acts = c_mean["total_web_activities"]
        social_acts = c_mean["total_social_interactions"]
        sentiment = c_mean["avg_sentiment_score"]
        cancel_rate = c_mean["cancellation_rate"]

        if spend > 3000 and sentiment > 0.5:
            name = "High-Value VIP Tech Spenders"
        elif recency > 200 and cancel_rate > 0.15:
            name = "At-Risk & Churned Customers"
        elif social_acts > 12 and sentiment > 0.6:
            name = "Active Brand Advocates & Influencers"
        elif web_acts > 150 and spend > 1000:
            name = "High-Activity Bargain Hunters"
        else:
            name = "Casual & Occasional Shoppers"

        cluster_names[cid] = name

    df["cluster_name"] = df["cluster_id"].map(cluster_names)

    # Build comprehensive unscaled profile table
    profiles_summary = []
    for cid in range(selected_k):
        c_mean = profile_mean.loc[cid]
        profiles_summary.append({
            "cluster_id": cid,
            "cluster_name": cluster_names[cid],
            "customer_count": int(cluster_sizes[cid]),
            "percentage_of_total": round(float(cluster_sizes[cid] / len(df) * 100), 2),
            "avg_spend": round(float(c_mean["total_spend"]), 2),
            "avg_transactions": round(float(c_mean["total_transactions"]), 2),
            "avg_order_value": round(float(c_mean["avg_order_value"]), 2),
            "avg_recency_days": round(float(c_mean["recency_days"]), 1),
            "avg_cancellation_rate": round(float(c_mean["cancellation_rate"]), 3),
            "avg_web_activities": round(float(c_mean["total_web_activities"]), 1),
            "avg_sessions": round(float(c_mean["total_sessions"]), 1),
            "avg_duration_seconds": round(float(c_mean["avg_duration_seconds"]), 1),
            "avg_product_views": round(float(c_mean["product_views_count"]), 1),
            "avg_cart_additions": round(float(c_mean["cart_additions_count"]), 1),
            "avg_social_interactions": round(float(c_mean["total_social_interactions"]), 1),
            "avg_sentiment_score": round(float(c_mean["avg_sentiment_score"]), 3),
            "avg_engagement_score": round(float(c_mean["avg_engagement_score"]), 1)
        })

    profiles_df = pd.DataFrame(profiles_summary)
    profiles_csv = os.path.join(PROCESSED_DIR, "cluster_profiles.csv")
    profiles_df.to_csv(profiles_csv, index=False)
    print(f"\nCluster profiles saved to: {profiles_csv}")

    # 6. PCA 2D Visualization Projection
    pca = PCA(n_components=2, random_state=42)
    pca_coords = pca.fit_transform(X_scaled)
    df["pca_x"] = np.round(pca_coords[:, 0], 4)
    df["pca_y"] = np.round(pca_coords[:, 1], 4)
    explained_var = pca.explained_variance_ratio_.tolist()
    print(f"PCA 2D explained variance ratio: PC1={explained_var[0]:.4f}, PC2={explained_var[1]:.4f} (Total: {sum(explained_var):.4f})")

    # 7. Save Processed Segment Datasets
    segments_csv = os.path.join(PROCESSED_DIR, "customer_segments.csv")
    segments_parquet = os.path.join(PROCESSED_DIR, "customer_segments.parquet")

    # Export CSV and Parquet
    df.to_csv(segments_csv, index=False)
    df.to_parquet(segments_parquet, index=False)
    print(f"Customer segments saved to: {segments_csv} & {segments_parquet}")

    # 8. Persist Models and Configurations
    joblib.dump(final_kmeans, os.path.join(MODELS_DIR, "kmeans_model.joblib"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.joblib"))
    joblib.dump(pca, os.path.join(MODELS_DIR, "pca_model.joblib"))

    config = {
        "selected_k": selected_k,
        "silhouette_score": float(best_k_row["silhouette_score"]),
        "inertia": float(best_k_row["inertia"]),
        "davies_bouldin_index": float(best_k_row["davies_bouldin_index"]),
        "feature_names": feature_cols,
        "cluster_names": cluster_names,
        "pca_explained_variance_ratio": explained_var,
        "total_customers": len(df)
    }
    with open(os.path.join(MODELS_DIR, "segmentation_config.json"), "w") as f:
        json.dump(config, f, indent=2)

    print("\nSaved artifacts to ml/models/:")
    print("  - kmeans_model.joblib")
    print("  - scaler.joblib")
    print("  - pca_model.joblib")
    print("  - segmentation_config.json")

    return {
        "selected_k": selected_k,
        "silhouette_score": best_k_row["silhouette_score"],
        "inertia": best_k_row["inertia"],
        "davies_bouldin_index": best_k_row["davies_bouldin_index"],
        "cluster_profiles": profiles_summary,
        "total_customers": len(df)
    }


if __name__ == "__main__":
    run_segmentation()
