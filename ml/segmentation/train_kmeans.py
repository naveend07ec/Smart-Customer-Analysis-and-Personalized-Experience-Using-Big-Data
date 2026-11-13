"""
K-Means Customer Segmentation Pipeline
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Performs:
1. Feature scaling with StandardScaler.
2. Elbow method & Silhouette evaluation for optimal K selection.
3. K-Means clustering (K=5).
4. Rigorous cluster evaluation (Silhouette Score, Davies-Bouldin, Calinski-Harabasz).
5. Cluster profiling and rule-based persona naming.
6. PCA 2D dimensionality reduction for interactive dashboard visualization.
7. Model artifact serialization.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

FEATURE_COLUMNS = [
    "total_spend",
    "total_transactions",
    "completed_transactions",
    "cancelled_transactions",
    "cancellation_rate",
    "avg_order_value",
    "total_quantity",
    "recency_days",
    "total_web_activities",
    "total_sessions",
    "avg_duration_seconds",
    "product_views_count",
    "cart_additions_count",
    "wishlist_count",
    "checkout_starts_count",
    "cart_to_checkout_ratio",
    "total_social_interactions",
    "avg_engagement_score",
    "avg_sentiment_score",
    "positive_interactions_count",
    "neutral_interactions_count",
    "negative_interactions_count",
    "unique_platforms_count"
]


def load_feature_matrix(csv_path: str = "data/processed/unified_customer_features.csv") -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Feature matrix not found at: {csv_path}. Run Stage 3 pipeline first.")
    df = pd.read_csv(csv_path)
    return df


def evaluate_elbow_and_silhouette(X_scaled: np.ndarray, k_range=range(2, 9)):
    """Computes inertia and silhouette scores across multiple K values."""
    results = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertia = float(km.inertia_)
        sil = float(silhouette_score(X_scaled, labels))
        results.append({
            "k": k,
            "inertia": round(inertia, 2),
            "silhouette_score": round(sil, 4)
        })
    return results


def assign_cluster_personas(profiles: dict) -> dict:
    """
    Assigns human-interpretable persona names and descriptions based on cluster centers.
    """
    personas = {}
    for cid, stats in profiles.items():
        spend = stats["avg_total_spend"]
        sent = stats["avg_sentiment"]
        cancel = stats["avg_cancellation_rate"]
        web = stats["avg_web_activities"]
        soc = stats["avg_social_interactions"]
        recency = stats["avg_recency_days"]

        # Classification logic matching the 5 distinct customer behaviors
        if cancel > 0.15 or recency > 200 or sent < -0.2:
            name = "At-Risk / Dissatisfied Customers"
            desc = "Lapsed customers with high cancellation/return rates, high recency (>200 days), and negative feedback."
            color = "#EF4444"
        elif spend > 3000:
            name = "High-Value VIP Tech Spenders"
            desc = "Top-tier premium spenders with highest average order value, frequent transactions, and high satisfaction."
            color = "#10B981"
        elif soc > 12 and sent > 0.6:
            name = "Social Brand Advocates"
            desc = "Highly vocal social champions with highest interaction volume, strong engagement, and enthusiastic sentiment."
            color = "#8B5CF6"
        elif web > 150 or stats["avg_cart_additions"] > 18:
            name = "Active Bargain Hunters"
            desc = "Extensive digital window-shoppers with highest web dwell time and cart additions, driven by promotions."
            color = "#F59E0B"
        else:
            name = "Casual Occasional Shoppers"
            desc = "Moderate engagement customers making steady, low-frequency purchases with balanced sentiment."
            color = "#3B82F6"

        personas[cid] = {
            "cluster_name": name,
            "description": desc,
            "color": color
        }
    return personas


def train_kmeans_pipeline(k: int = 5):
    print("=" * 70)
    print("STAGE 4: K-MEANS CUSTOMER SEGMENTATION PIPELINE")
    print("=" * 70)

    # 1. Load data
    df = load_feature_matrix()
    print(f"Loaded feature matrix: {df.shape[0]} customers, {df.shape[1]} columns.")

    X = df[FEATURE_COLUMNS].values

    # 2. Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. Elbow & Silhouette Evaluation
    print("Evaluating K range [2..8] for Elbow & Silhouette...")
    elbow_metrics = evaluate_elbow_and_silhouette(X_scaled, range(2, 9))
    for m in elbow_metrics:
        print(f"  K={m['k']}: Inertia={m['inertia']} | Silhouette={m['silhouette_score']}")

    # 4. Train Final Model
    print(f"\nFitting final KMeans model with K={k}...")
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=15)
    labels = kmeans.fit_predict(X_scaled)
    df["cluster_id"] = labels

    # 5. Model Quality Metrics
    sil = float(silhouette_score(X_scaled, labels))
    db_index = float(davies_bouldin_score(X_scaled, labels))
    ch_score = float(calinski_harabasz_score(X_scaled, labels))

    print("\nModel Quality Metrics:")
    print(f"  - Silhouette Score: {sil:.4f} (Higher is better, >0.25 indicates distinct clusters)")
    print(f"  - Davies-Bouldin Index: {db_index:.4f} (Lower is better)")
    print(f"  - Calinski-Harabasz Score: {ch_score:.2f} (Higher is better)")

    # 6. PCA 2D Projection for UI Visualization
    pca = PCA(n_components=2, random_state=42)
    pca_coords = pca.fit_transform(X_scaled)
    df["pca_x"] = np.round(pca_coords[:, 0], 4)
    df["pca_y"] = np.round(pca_coords[:, 1], 4)
    var_ratio = pca.explained_variance_ratio_
    print(f"PCA Variance Explained: PC1={var_ratio[0]*100:.2f}%, PC2={var_ratio[1]*100:.2f}% (Total={sum(var_ratio)*100:.2f}%)")

    # 7. Cluster Profiling
    profiles_raw = {}
    cluster_counts = df["cluster_id"].value_counts().to_dict()

    for cid in range(k):
        c_df = df[df["cluster_id"] == cid]
        profiles_raw[str(cid)] = {
            "cluster_id": cid,
            "customer_count": int(cluster_counts.get(cid, 0)),
            "percentage": round(float(cluster_counts.get(cid, 0)) / len(df) * 100, 2),
            "avg_total_spend": round(float(c_df["total_spend"].mean()), 2),
            "avg_order_value": round(float(c_df["avg_order_value"].mean()), 2),
            "avg_transactions": round(float(c_df["total_transactions"].mean()), 2),
            "avg_recency_days": round(float(c_df["recency_days"].mean()), 1),
            "avg_cancellation_rate": round(float(c_df["cancellation_rate"].mean()), 4),
            "avg_web_activities": round(float(c_df["total_web_activities"].mean()), 1),
            "avg_sessions": round(float(c_df["total_sessions"].mean()), 1),
            "avg_cart_additions": round(float(c_df["cart_additions_count"].mean()), 1),
            "avg_social_interactions": round(float(c_df["total_social_interactions"].mean()), 1),
            "avg_engagement_score": round(float(c_df["avg_engagement_score"].mean()), 2),
            "avg_sentiment": round(float(c_df["avg_sentiment_score"].mean()), 4)
        }

    # Assign explainable persona labels
    personas = assign_cluster_personas(profiles_raw)
    final_profiles = []
    for cid_str, stats in profiles_raw.items():
        stats.update(personas[cid_str])
        final_profiles.append(stats)

    # Map cluster names back to DataFrame
    cid_to_name = {int(p["cluster_id"]): p["cluster_name"] for p in final_profiles}
    df["cluster_name"] = df["cluster_id"].map(cid_to_name)

    # 8. Save Artifacts
    models_dir = "ml/models"
    os.makedirs(models_dir, exist_ok=True)

    joblib.dump(kmeans, os.path.join(models_dir, "kmeans_model.pkl"))
    joblib.dump(scaler, os.path.join(models_dir, "scaler.pkl"))
    joblib.dump(pca, os.path.join(models_dir, "pca_model.pkl"))

    with open(os.path.join(models_dir, "elbow_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(elbow_metrics, f, indent=2)

    with open(os.path.join(models_dir, "cluster_profiles.json"), "w", encoding="utf-8") as f:
        json.dump({
            "metrics": {
                "silhouette_score": round(sil, 4),
                "davies_bouldin_index": round(db_index, 4),
                "calinski_harabasz_score": round(ch_score, 2),
                "pca_explained_variance_ratio": [round(float(v), 4) for v in var_ratio]
            },
            "clusters": final_profiles
        }, f, indent=2)

    # Save assignments CSV
    output_assignments_path = "data/processed/customer_segment_assignments.csv"
    df.to_csv(output_assignments_path, index=False)
    print(f"\nSaved customer segment assignments: {output_assignments_path}")

    print("\nCluster Persona Summary:")
    for prof in sorted(final_profiles, key=lambda x: x["customer_count"], reverse=True):
        print(f"  [{prof['cluster_id']}] {prof['cluster_name']}: {prof['customer_count']} customers ({prof['percentage']}%) | Avg Spend: ${prof['avg_total_spend']} | Avg Sentiment: {prof['avg_sentiment']}")

    print("=" * 70)
    print("K-MEANS CLUSTERING PIPELINE COMPLETED!")
    print("=" * 70)


if __name__ == "__main__":
    train_kmeans_pipeline()
