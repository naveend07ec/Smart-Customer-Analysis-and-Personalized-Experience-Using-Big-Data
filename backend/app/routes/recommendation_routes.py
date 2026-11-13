from flask import Blueprint, jsonify, request
from backend.app.services.data_service import DataService

recommendations_bp = Blueprint("recommendations", __name__, url_prefix="/api/recommendations")


@recommendations_bp.route("/<customer_id>", methods=["GET"])
def get_customer_recommendations(customer_id):
    service = DataService.get_instance()
    recs = service.get_customer_recommendations(customer_id)
    return jsonify({
        "customer_id": customer_id,
        "recommendations": recs
    })


@recommendations_bp.route("/rules", methods=["GET"])
def get_association_rules():
    service = DataService.get_instance()
    limit = request.args.get("limit", default=50, type=int)
    return jsonify(service.get_top_association_rules(limit=limit))
