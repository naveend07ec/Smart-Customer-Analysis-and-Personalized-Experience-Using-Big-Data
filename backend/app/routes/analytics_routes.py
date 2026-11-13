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

    monetary_bins = rfm.get("monetary_distribution", {}).get("bins", [])
    freq_bins = rfm.get("frequency_distribution", {}).get("bins", [])

    spending_dist = {f"${b['min']}-${b['max']}": b["count"] for b in monetary_bins}
    purchase_freq = {f"{b['min']}-{b['max']} orders": b["count"] for b in freq_bins}

    return jsonify({
        "status": "success",
        "data": {
            "spending_distribution": spending_dist,
            "purchase_frequency": purchase_freq,
            "website_engagement": channel.get("device_breakdown", {}),
            "social_engagement": sentiment.get("metrics", {}),
            "sentiment_distribution": sentiment.get("sentiment_distribution", {}),
            "aggregated_statistics": {
                "rfm_summary": rfm.get("summary", {}),
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
