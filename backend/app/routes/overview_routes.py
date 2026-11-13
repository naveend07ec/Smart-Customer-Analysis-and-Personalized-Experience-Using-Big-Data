from flask import Blueprint, jsonify
from backend.app.services.data_service import DataService

overview_bp = Blueprint("overview", __name__, url_prefix="/api/overview")


@overview_bp.route("", methods=["GET"])
@overview_bp.route("/", methods=["GET"])
def get_overview_root():
    service = DataService.get_instance()
    kpis = service.get_kpi_summary()
    clusters = service.cluster_profiles.get("clusters", [])
    total_recs = len(service.recommendations) * 5 if service.recommendations else 6000

    return jsonify({
        "status": "success",
        "data": {
            "total_customers": kpis["total_customers"],
            "total_transactions": kpis["total_transactions"],
            "total_web_activities": kpis["total_web_touchpoints"],
            "total_social_interactions": kpis["total_social_interactions"],
            "total_customer_segments": len(clusters) if clusters else 5,
            "total_recommendations_generated": total_recs,
            "total_revenue": kpis["total_revenue"],
            "avg_spend_per_customer": kpis["avg_spend_per_customer"],
            "fulfillment_rate": kpis["fulfillment_rate"],
            "avg_sentiment_score": kpis["avg_sentiment_score"]
        }
    })


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
