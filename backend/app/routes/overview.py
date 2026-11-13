"""
Overview REST Endpoint
GET /api/overview
"""

from flask import Blueprint
from backend.app.services.data_service import data_service
from backend.app.utils.response import success_response, error_response

overview_bp = Blueprint("overview", __name__, url_prefix="/api")


@overview_bp.route("/overview", methods=["GET"])
def get_overview():
    try:
        segments_df = data_service.segments_df
        recs_df = data_service.recommendations_df

        if segments_df is None:
            return error_response("Customer segmentation data is unavailable", status_code=503)

        total_customers = len(segments_df)
        total_transactions = int(data_service.cleaned_counts.get("transactions", 0))
        total_web_activities = int(data_service.cleaned_counts.get("web_activity", 0))
        total_social_interactions = int(data_service.cleaned_counts.get("social_media", 0))
        total_segments = int(segments_df["cluster_id"].nunique())
        total_recommendations = len(recs_df) if recs_df is not None else 0
        total_revenue = round(float(segments_df["total_spend"].sum()), 2)
        avg_spend = round(float(segments_df["total_spend"].mean()), 2)

        data = {
            "total_customers": total_customers,
            "total_transactions": total_transactions,
            "total_web_activities": total_web_activities,
            "total_social_interactions": total_social_interactions,
            "total_customer_segments": total_segments,
            "total_recommendations_generated": total_recommendations,
            "total_revenue": total_revenue,
            "avg_spend_per_customer": avg_spend,
            "system_status": "Healthy",
            "pipeline_mode": "Batch Processing (PySpark & PyArrow)"
        }
        return success_response(data=data, message="System overview metrics retrieved successfully")
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", status_code=500)
