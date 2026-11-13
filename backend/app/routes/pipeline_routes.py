from flask import Blueprint, jsonify
from backend.app.services.data_service import DataService

pipeline_bp = Blueprint("pipeline", __name__, url_prefix="/api/pipeline")


@pipeline_bp.route("/summary", methods=["GET"])
def get_pipeline_summary():
    service = DataService.get_instance()
    return jsonify(service.get_pipeline_summary())
