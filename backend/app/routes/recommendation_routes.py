import re
from flask import Blueprint, jsonify, request
from backend.app.services.data_service import DataService

recommendations_bp = Blueprint("recommendations", __name__, url_prefix="/api/recommendations")

CUSTOMER_ID_REGEX = re.compile(r"^CUST_\d{4}$")


@recommendations_bp.route("/<customer_id>", methods=["GET"])
def get_customer_recommendations(customer_id):
    clean_id = customer_id.strip().upper()
    if not CUSTOMER_ID_REGEX.match(clean_id):
        return jsonify({
            "status": "error",
            "message": f"Invalid customer ID format: '{customer_id}'. Expected format is 'CUST_xxxx' (e.g. CUST_0001)."
        }), 400

    service = DataService.get_instance()
    # Check if customer exists in the customer dataset
    if clean_id not in service.df_segments["customer_id"].values:
        return jsonify({
            "status": "error",
            "message": f"Customer '{clean_id}' not found."
        }), 404

    recs = service.get_customer_recommendations(clean_id)
    return jsonify({
        "status": "success",
        "data": {
            "customer_id": clean_id,
            "recommendations_count": len(recs),
            "top_recommendations": recs
        }
    })


@recommendations_bp.route("/rules", methods=["GET"])
def get_association_rules():
    service = DataService.get_instance()
    limit = request.args.get("limit", default=50, type=int)
    rules = service.get_top_association_rules(limit=limit)
    return jsonify({
        "status": "success",
        "data": rules
    })
