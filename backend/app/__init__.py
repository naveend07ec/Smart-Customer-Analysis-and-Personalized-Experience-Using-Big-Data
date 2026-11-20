from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.app.routes.overview_routes import overview_bp
from backend.app.routes.analytics_routes import analytics_bp
from backend.app.routes.segmentation_routes import segmentation_bp
from backend.app.routes.customer_routes import customer_bp
from backend.app.routes.recommendation_routes import recommendations_bp
from backend.app.routes.pipeline_routes import pipeline_bp
from backend.app.routes.churn_routes import churn_bp
from backend.app.routes.ingestion_routes import ingestion_bp


def create_app(config_override=None) -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    if config_override:
        app.config.update(config_override)

    # Configure CORS for local React development server
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register primary route blueprints
    app.register_blueprint(overview_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(segmentation_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(pipeline_bp)
    app.register_blueprint(churn_bp)
    app.register_blueprint(ingestion_bp)

    # Register aliases to satisfy strict prompt endpoint paths
    # /api/segments alias for /api/segmentation
    app.register_blueprint(segmentation_bp, url_prefix="/api/segments", name="segments_alias")
    # /api/customer alias for /api/customers
    app.register_blueprint(customer_bp, url_prefix="/api/customer", name="customer_alias")
    # /api/processing alias for /api/pipeline
    app.register_blueprint(pipeline_bp, url_prefix="/api/processing", name="processing_alias")
    # /api/pipeline/ingest alias for /api/ingestion
    app.register_blueprint(ingestion_bp, url_prefix="/api/pipeline/ingest", name="ingestion_alias")

    @app.route("/api/health", methods=["GET"])
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "Big Data Customer Analytics & Recommendation REST API",
            "version": "1.0.0"
        })

    @app.route("/api/dataset-mode", methods=["GET", "POST"])
    def app_dataset_mode():
        from backend.app.services.data_service import DataService
        data_service = DataService.get_instance()
        if request.method == "POST":
            body = request.get_json(silent=True) or {}
            mode = body.get("mode", "cumulative")
            batch_id = body.get("batch_id")
            ok, msg, ctx = data_service.switch_mode(mode, batch_id)
            if not ok:
                return jsonify({"status": "error", "message": msg, "data": ctx}), 400
            return jsonify({"status": "success", "message": msg, "data": ctx}), 200
        return jsonify({"status": "success", "data": data_service.get_mode_context()}), 200

    return app
