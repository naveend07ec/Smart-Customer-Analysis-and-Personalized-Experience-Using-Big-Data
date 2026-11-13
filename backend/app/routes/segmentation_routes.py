from flask import Blueprint, jsonify, request
from backend.app.services.data_service import DataService

segmentation_bp = Blueprint("segmentation", __name__, url_prefix="/api/segmentation")


@segmentation_bp.route("/evaluation", methods=["GET"])
def get_evaluation():
    service = DataService.get_instance()
    return jsonify(service.get_segmentation_evaluation())


@segmentation_bp.route("/pca-scatter", methods=["GET"])
def get_pca_scatter():
    service = DataService.get_instance()
    limit = request.args.get("limit", default=1200, type=int)
    return jsonify(service.get_pca_scatter(limit=limit))
