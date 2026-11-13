from flask import Blueprint, jsonify, request
from backend.app.services.data_service import DataService

segmentation_bp = Blueprint("segmentation", __name__, url_prefix="/api/segmentation")


@segmentation_bp.route("", methods=["GET"])
@segmentation_bp.route("/", methods=["GET"])
def get_segments_root():
    service = DataService.get_instance()
    eval_data = service.get_segmentation_evaluation()
    pca_data = service.get_pca_scatter(limit=1200)
    clusters = service.cluster_profiles.get("clusters", [])

    segment_names = [c.get("cluster_name", c.get("name")) for c in clusters]
    customer_counts = {c.get("cluster_name", c.get("name")): c.get("customer_count", c.get("count")) for c in clusters}
    segment_percentages = {c.get("cluster_name", c.get("name")): c.get("percentage") for c in clusters}
    pca_points = pca_data if isinstance(pca_data, list) else pca_data.get("points", [])

    return jsonify({
        "status": "success",
        "data": {
            "segment_names": segment_names,
            "customer_counts": customer_counts,
            "segment_percentages": segment_percentages,
            "cluster_profiles": clusters,
            "pca_coordinates": pca_points,
            "k_means_evaluation_metrics": eval_data.get("elbow_curve", []) if isinstance(eval_data, dict) else eval_data,
            "evaluation_metrics": eval_data.get("metrics", {}) if isinstance(eval_data, dict) else {}
        }
    })


@segmentation_bp.route("/evaluation", methods=["GET"])
def get_evaluation():
    service = DataService.get_instance()
    return jsonify(service.get_segmentation_evaluation())


@segmentation_bp.route("/pca-scatter", methods=["GET"])
def get_pca_scatter():
    service = DataService.get_instance()
    limit = request.args.get("limit", default=1200, type=int)
    return jsonify(service.get_pca_scatter(limit=limit))
