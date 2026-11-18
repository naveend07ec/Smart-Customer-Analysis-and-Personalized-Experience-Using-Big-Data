"""
Churn Routes Blueprint
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Provides REST endpoints for supervised customer churn predictions,
risk category distribution, and historical feature diagnostics.
"""

import re
from flask import Blueprint, jsonify, request
from backend.app.services.data_service import DataService

churn_bp = Blueprint("churn", __name__, url_prefix="/api/churn")
CUSTOMER_ID_REGEX = re.compile(r"^CUST_\d{4}$")


@churn_bp.route("", methods=["GET"])
@churn_bp.route("/", methods=["GET"])
@churn_bp.route("/summary", methods=["GET"])
def get_churn_summary():
    service = DataService.get_instance()
    summary = service.get_churn_summary()
    return jsonify({
        "status": "success",
        "data": summary
    })


@churn_bp.route("/customers", methods=["GET"])
def get_churn_customers():
    service = DataService.get_instance()
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("pageSize", default=20, type=int)
    search = request.args.get("search", default="", type=str)
    risk_category = request.args.get("riskCategory", default="all", type=str)
    sort_by = request.args.get("sortBy", default="churn_risk_score", type=str)
    sort_dir = request.args.get("sortDir", default="desc", type=str)

    res = service.get_churn_customers(
        page=page,
        page_size=page_size,
        search=search,
        risk_category=risk_category,
        sort_by=sort_by,
        sort_dir=sort_dir
    )
    return jsonify({
        "status": "success",
        "data": res
    })


@churn_bp.route("/customer/<customer_id>", methods=["GET"])
def get_customer_churn_detail(customer_id):
    clean_id = customer_id.strip().upper()
    if not CUSTOMER_ID_REGEX.match(clean_id):
        return jsonify({
            "status": "error",
            "message": f"Invalid customer ID format: '{customer_id}'. Expected format is 'CUST_xxxx' (e.g. CUST_0001)."
        }), 400

    service = DataService.get_instance()
    detail = service.get_customer_churn_detail(clean_id)
    if detail is None:
        return jsonify({
            "status": "error",
            "message": f"Customer '{clean_id}' was not eligible for churn evaluation at the prediction cutoff date."
        }), 404

    return jsonify({
        "status": "success",
        "data": detail
    })

