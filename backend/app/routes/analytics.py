"""
Customer Analytics REST Endpoint
GET /api/analytics
"""

from flask import Blueprint
from backend.app.services.analytics_service import compute_customer_analytics
from backend.app.utils.response import success_response, error_response

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api")


@analytics_bp.route("/analytics", methods=["GET"])
def get_analytics():
    try:
        analytics = compute_customer_analytics()
        if not analytics:
            return error_response("Customer analytics dataset is unavailable", status_code=503)

        return success_response(data=analytics, message="Customer analytics distributions retrieved successfully")
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", status_code=500)
