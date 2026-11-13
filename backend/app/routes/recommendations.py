"""
Personalized Recommendations REST Endpoint
GET /api/recommendations/<customer_id>
"""

from flask import Blueprint
from backend.app.services.data_service import data_service
from backend.app.utils.validators import is_valid_customer_id
from backend.app.utils.response import success_response, error_response

recommendations_bp = Blueprint("recommendations", __name__, url_prefix="/api")


@recommendations_bp.route("/recommendations/<customer_id>", methods=["GET"])
def get_customer_recommendations(customer_id: str):
    try:
        clean_cid = customer_id.strip().upper()
        if not is_valid_customer_id(clean_cid):
            return error_response(
                f"Invalid customer ID format: '{customer_id}'. Expected format is 'CUST_xxxx' (e.g. CUST_0001).",
                status_code=400
            )

        customer = data_service.get_customer(clean_cid)
        if customer is None:
            return error_response(
                f"Customer with ID '{clean_cid}' was not found in the system.",
                status_code=404
            )

        recs = data_service.get_recommendations_for_customer(clean_cid)
        eval_metrics = (
            data_service.recommendation_eval_df.to_dict(orient="records")
            if data_service.recommendation_eval_df is not None
            else []
        )

        data = {
            "customer_id": clean_cid,
            "assigned_segment": customer.get("cluster_name"),
            "recommendations_count": len(recs),
            "top_recommendations": recs,
            "model_evaluation_metrics": eval_metrics
        }

        return success_response(
            data=data,
            message=f"Personalized explainable recommendations for {clean_cid} retrieved successfully"
        )
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", status_code=500)
