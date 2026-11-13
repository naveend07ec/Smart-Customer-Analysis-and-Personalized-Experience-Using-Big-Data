from flask import Blueprint, jsonify
from backend.app.services.data_service import DataService

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@analytics_bp.route("/channel-attribution", methods=["GET"])
def get_channel_attribution():
    service = DataService.get_instance()
    return jsonify(service.get_channel_attribution())


@analytics_bp.route("/sentiment-analysis", methods=["GET"])
def get_sentiment_analysis():
    service = DataService.get_instance()
    return jsonify(service.get_sentiment_analysis())


@analytics_bp.route("/rfm-distributions", methods=["GET"])
def get_rfm_distributions():
    service = DataService.get_instance()
    return jsonify(service.get_rfm_distributions())
