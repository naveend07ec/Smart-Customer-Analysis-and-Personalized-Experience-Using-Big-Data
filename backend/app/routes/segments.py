"""
Segmentation REST Endpoint
GET /api/segments
"""

from flask import Blueprint
from backend.app.services.data_service import data_service
from backend.app.utils.response import success_response, error_response

segments_bp = Blueprint("segments", __name__, url_prefix="/api")


@segments_bp.route("/segments", methods=["GET"])
def get_segments():
    try:
        segments_df = data_service.segments_df
        profiles_df = data_service.profiles_df
        k_metrics_df = data_service.k_metrics_df
        cfg = data_service.segmentation_config

        if segments_df is None or profiles_df is None:
            return error_response("Segmentation data is unavailable", status_code=503)

        # 1. Cluster Profiles
        profiles = profiles_df.to_dict(orient="records")

        # 2. PCA Coordinates for Interactive 2D Scatter Visualization
        pca_cols = ["customer_id", "cluster_id", "cluster_name", "pca_x", "pca_y", "total_spend", "total_transactions"]
        pca_data = segments_df[pca_cols].to_dict(orient="records")

        # 3. K-Selection Metrics
        k_metrics = k_metrics_df.to_dict(orient="records") if k_metrics_df is not None else []

        data = {
            "selected_k": cfg.get("selected_k", 5) if cfg else 5,
            "optimal_silhouette_score": cfg.get("silhouette_score") if cfg else 0.3451,
            "optimal_davies_bouldin_index": cfg.get("davies_bouldin_index") if cfg else 1.1759,
            "pca_explained_variance": cfg.get("pca_explained_variance_ratio", [0.394, 0.168]) if cfg else [0.394, 0.168],
            "total_segmented_customers": len(segments_df),
            "cluster_profiles": profiles,
            "k_selection_metrics": k_metrics,
            "pca_coordinates": pca_data
        }
        return success_response(data=data, message="Customer segments and PCA visual coordinates retrieved successfully")
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", status_code=500)
