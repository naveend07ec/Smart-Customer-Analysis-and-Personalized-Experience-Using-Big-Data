from flask import Flask, jsonify
from flask_cors import CORS

from backend.app.routes.overview_routes import overview_bp
from backend.app.routes.analytics_routes import analytics_bp
from backend.app.routes.segmentation_routes import segmentation_bp
from backend.app.routes.customer_routes import customer_bp
from backend.app.routes.recommendation_routes import recommendations_bp
from backend.app.routes.pipeline_routes import pipeline_bp


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    app.register_blueprint(overview_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(segmentation_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(pipeline_bp)

    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "Big Data Customer Analytics & Recommendation REST API",
            "version": "1.0.0"
        })

    return app
