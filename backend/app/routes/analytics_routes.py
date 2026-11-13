from flask import Blueprint, jsonify
from backend.app.services.data_service import DataService

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@analytics_bp.route("", methods=["GET"])
@analytics_bp.route("/", methods=["GET"])
def get_analytics_root():
    service = DataService.get_instance()
    rfm = service.get_rfm_distributions()
    sentiment = service.get_sentiment_analysis()
    channel = service.get_channel_attribution()

    spending_dist = {item["bin"]: item["count"] for item in rfm.get("spend", [])}
    purchase_freq = {item["bin"]: item["count"] for item in rfm.get("frequency", [])}

    return jsonify({
        "status": "success",
        "data": {
            "spending_distribution": spending_dist,
            "purchase_frequency": purchase_freq,
            "website_engagement": channel.get("device_breakdown", {}),
            "social_engagement": sentiment.get("metrics", {}),
            "sentiment_distribution": sentiment.get("sentiment_distribution", {}),
            "aggregated_statistics": {
                "recency_distribution": rfm.get("recency", []),
                "top_channels": channel.get("top_channels", [])
            }
        }
    })


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
