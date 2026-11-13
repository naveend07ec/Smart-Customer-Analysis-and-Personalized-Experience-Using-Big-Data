import re
from flask import Blueprint, jsonify, request
from backend.app.services.data_service import DataService

customer_bp = Blueprint("customers", __name__, url_prefix="/api/customers")

CUSTOMER_ID_REGEX = re.compile(r"^CUST_\d{4}$")


@customer_bp.route("", methods=["GET"])
@customer_bp.route("/", methods=["GET"])
def get_customers():
    service = DataService.get_instance()
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("pageSize", default=20, type=int)
    search = request.args.get("search", default="", type=str)
    segment = request.args.get("segment", default="all", type=str)
    sort_by = request.args.get("sortBy", default="total_spend", type=str)
    sort_dir = request.args.get("sortDir", default="desc", type=str)

    res = service.get_customers(
        page=page,
        page_size=page_size,
        search=search,
        segment=segment,
        sort_by=sort_by,
        sort_dir=sort_dir
    )
    return jsonify({
        "status": "success",
        "data": res
    })


@customer_bp.route("/<customer_id>", methods=["GET"])
def get_customer_detail(customer_id):
    clean_id = customer_id.strip().upper()
    if not CUSTOMER_ID_REGEX.match(clean_id):
        return jsonify({
            "status": "error",
            "message": f"Invalid customer ID format: '{customer_id}'. Expected format is 'CUST_xxxx' (e.g. CUST_0001)."
        }), 400

    service = DataService.get_instance()
    detail = service.get_customer_detail(clean_id)
    if detail is None:
        return jsonify({
            "status": "error",
            "message": f"Customer '{clean_id}' not found."
        }), 404

    return jsonify({
        "status": "success",
        "data": detail
    })
