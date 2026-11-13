from flask import Blueprint, jsonify
from backend.app.services.data_service import DataService

overview_bp = Blueprint("overview", __name__, url_prefix="/api/overview")


@overview_bp.route("/kpis", methods=["GET"])
def get_kpis():
    service = DataService.get_instance()
    return jsonify(service.get_kpi_summary())


@overview_bp.route("/segment-distribution", methods=["GET"])
def get_segment_distribution():
    service = DataService.get_instance()
    return jsonify(service.get_segment_distribution())


@overview_bp.route("/revenue-by-category", methods=["GET"])
def get_revenue_by_category():
    service = DataService.get_instance()
    return jsonify(service.get_revenue_by_category())


@overview_bp.route("/monthly-trends", methods=["GET"])
def get_monthly_trends():
    service = DataService.get_instance()
    return jsonify(service.get_monthly_trends())
