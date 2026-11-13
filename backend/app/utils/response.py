"""
Standardized API Response Envelopes
"""

from flask import jsonify


def success_response(data=None, message="Success", status_code=200):
    payload = {
        "status": "success",
        "message": message,
        "data": data
    }
    return jsonify(payload), status_code


def error_response(message="An error occurred", status_code=400, details=None):
    payload = {
        "status": "error",
        "message": message,
        "error_code": status_code
    }
    if details:
        payload["details"] = details
    return jsonify(payload), status_code
