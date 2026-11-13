"""
Individual Customer REST Endpoint
GET /api/customer/<customer_id>
"""

from flask import Blueprint
from backend.app.services.data_service import data_service
from backend.app.utils.validators import is_valid_customer_id
from backend.app.utils.response import success_response, error_response

customer_bp = Blueprint("customer", __name__, url_prefix="/api")


@customer_bp.route("/customer/<customer_id>", methods=["GET"])
def get_customer_details(customer_id: str):
    try:
        # Validate input format
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

        # Structure customer profile into logical analytical dimensions
        structured_profile = {
            "customer_id": clean_cid,
            "segment": {
                "cluster_id": int(customer["cluster_id"]),
                "cluster_name": customer["cluster_name"],
                "pca_x": float(customer["pca_x"]),
                "pca_y": float(customer["pca_y"])
            },
            "transaction_behaviour": {
                "total_spend": float(customer["total_spend"]),
                "total_transactions": int(customer["total_transactions"]),
                "avg_order_value": float(customer["avg_order_value"]),
                "total_quantity": int(customer["total_quantity"]),
                "recency_days": int(customer["recency_days"]),
                "cancelled_orders_count": int(customer["cancelled_orders_count"]),
                "cancellation_rate": float(customer["cancellation_rate"])
            },
            "web_engagement": {
                "total_web_activities": int(customer["total_web_activities"]),
                "total_sessions": int(customer["total_sessions"]),
                "avg_duration_seconds": float(customer["avg_duration_seconds"]),
                "product_views_count": int(customer["product_views_count"]),
                "cart_additions_count": int(customer["cart_additions_count"]),
                "wishlist_count": int(customer["wishlist_count"]),
                "checkout_starts_count": int(customer["checkout_starts_count"]),
                "cart_to_checkout_ratio": float(customer["cart_to_checkout_ratio"])
            },
            "social_engagement": {
                "total_social_interactions": int(customer["total_social_interactions"]),
                "avg_engagement_score": float(customer["avg_engagement_score"]),
                "avg_sentiment_score": float(customer["avg_sentiment_score"]),
                "positive_interactions_count": int(customer["positive_interactions_count"]),
                "neutral_interactions_count": int(customer["neutral_interactions_count"]),
                "negative_interactions_count": int(customer["negative_interactions_count"]),
                "unique_platforms_count": int(customer["unique_platforms_count"])
            }
        }

        return success_response(data=structured_profile, message=f"Customer details for {clean_cid} retrieved successfully")
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", status_code=500)
