"""
Ingestion & Student Demonstration REST API Blueprint
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Endpoints:
Stage B:
- POST /api/ingestion/upload
- POST /api/ingestion/validate/<batch_id>
- POST /api/ingestion/commit/<batch_id>
- GET  /api/ingestion/status/<batch_id>
- GET  /api/ingestion/history

Stage C:
- POST /api/ingestion/process/<batch_id>
- GET  /api/ingestion/process/status/<version_id>
- POST /api/ingestion/train/<version_id>
- GET  /api/ingestion/train/status/<version_id>
- GET  /api/ingestion/evaluation/<version_id>

Stage D:
- GET  /api/ingestion/versions
- GET  /api/ingestion/preview/<version_id>/overview
- GET  /api/ingestion/preview/<version_id>/segmentation
- GET  /api/ingestion/preview/<version_id>/recommendations
- GET  /api/ingestion/preview/<version_id>/churn
- POST /api/ingestion/promote/<version_id>
- POST /api/ingestion/rollback
"""

from flask import Blueprint, request, jsonify, send_file, make_response
import os

from backend.app.services.ingestion_service import IngestionService
from backend.app.services.pipeline_execution_service import PipelineExecutionService
from backend.app.services.model_training_service import ModelTrainingService
from backend.app.services.version_preview_service import VersionPreviewService

ingestion_bp = Blueprint("ingestion", __name__, url_prefix="/api/ingestion")


# -------------------------------------------------------------
# Stage B Endpoints
# -------------------------------------------------------------
@ingestion_bp.route("/upload", methods=["POST"])
def upload_batch():
    files = request.files
    service = IngestionService.get_instance()

    success, message, manifest = service.stage_batch(files)
    if not success:
        return jsonify({"status": "error", "message": message, "data": None}), 400

    auto_validate = request.form.get("auto_validate", "true").lower() in ("true", "1", "yes")
    strict_pk = request.form.get("strict_pk", "false").lower() in ("true", "1", "yes")

    if auto_validate:
        batch_id = manifest["batch_id"]
        val_success, val_msg, updated_manifest = service.validate_batch(batch_id, strict_pk=strict_pk)
        return jsonify({
            "status": "success",
            "message": f"{message} {val_msg}",
            "data": updated_manifest
        }), 201

    return jsonify({"status": "success", "message": message, "data": manifest}), 201


@ingestion_bp.route("/upload-multi", methods=["POST"])
def upload_multi_format():
    """
    Accepts 1 to N files across supported formats (.csv, .json, .jsonl, .txt, .log, .xlsx).
    Performs safe staging, SHA-256 calculation, and automated schema discovery.
    """
    files_list = []
    if "files" in request.files:
        files_list = request.files.getlist("files")
    elif "files[]" in request.files:
        files_list = request.files.getlist("files[]")
    else:
        files_list = list(request.files.values())

    if not files_list:
        return jsonify({"status": "error", "message": "No files uploaded. Provide at least one valid raw file.", "data": None}), 400

    service = IngestionService.get_instance()
    success, message, manifest = service.stage_multi_format_batch(files_list)
    if not success:
        return jsonify({"status": "error", "message": message, "data": None}), 400

    return jsonify({"status": "success", "message": message, "data": manifest}), 201


@ingestion_bp.route("/validate/<batch_id>", methods=["POST"])
def validate_batch(batch_id: str):
    service = IngestionService.get_instance()
    body = request.get_json(silent=True) or {}
    strict_pk = body.get("strict_pk", False)

    is_valid, message, manifest = service.validate_batch(batch_id, strict_pk=strict_pk)
    if not manifest:
        return jsonify({"status": "error", "message": f"Batch '{batch_id}' not found.", "data": None}), 404

    status_str = "success" if is_valid else "validation_error"
    http_code = 200 if is_valid else 422
    return jsonify({"status": status_str, "message": message, "data": manifest}), http_code


@ingestion_bp.route("/commit/<batch_id>", methods=["POST"])
def commit_batch(batch_id: str):
    service = IngestionService.get_instance()
    success, message, manifest = service.commit_to_hdfs(batch_id)

    if not manifest:
        return jsonify({"status": "error", "message": f"Batch '{batch_id}' not found.", "data": None}), 404

    if not success:
        return jsonify({"status": "error", "message": message, "data": manifest}), 503 if "OFFLINE" in message else 400

    return jsonify({"status": "success", "message": message, "data": manifest}), 200


@ingestion_bp.route("/status/<batch_id>", methods=["GET"])
def get_batch_status(batch_id: str):
    service = IngestionService.get_instance()
    manifest = service.get_batch_status(batch_id)
    if not manifest:
        return jsonify({"status": "error", "message": f"Batch '{batch_id}' not found.", "data": None}), 404

    return jsonify({"status": "success", "data": manifest}), 200


@ingestion_bp.route("/history", methods=["GET"])
def list_batches():
    service = IngestionService.get_instance()
    batches = service.list_batches()
    return jsonify({"status": "success", "data": {"total_batches": len(batches), "batches": batches}}), 200


# -------------------------------------------------------------
# Stage C Endpoints: PySpark Batch Processing & Model Training
# -------------------------------------------------------------
@ingestion_bp.route("/process/<batch_id>", methods=["POST"])
def run_batch_processing(batch_id: str):
    """Triggers PySpark batch cleaning and customer feature matrix generation."""
    body = request.get_json(silent=True) or {}
    force_local = body.get("force_local_input", False)

    pipe_service = PipelineExecutionService.get_instance()
    success, message, report = pipe_service.execute_batch_pipeline(batch_id, force_local_input=force_local)

    if not success:
        if "not found" in message.lower():
            return jsonify({"status": "error", "message": message, "data": None}), 404
        return jsonify({"status": "error", "message": message, "data": None}), 503 if "OFFLINE" in message else 400

    return jsonify({"status": "success", "message": message, "data": report}), 200


@ingestion_bp.route("/process/status/<version_id>", methods=["GET"])
def get_processing_status(version_id: str):
    pipe_service = PipelineExecutionService.get_instance()
    report = pipe_service.get_processing_report(version_id)
    if not report:
        return jsonify({"status": "error", "message": f"Version '{version_id}' processing report not found."}), 404
    return jsonify({"status": "success", "data": report}), 200


@ingestion_bp.route("/train/<version_id>", methods=["POST"])
@ingestion_bp.route("/retrain/<version_id>", methods=["POST"])
def retrain_models(version_id: str):
    """Triggers version-isolated retraining of K-Means, Recommender, and Churn models."""
    trainer = ModelTrainingService.get_instance()
    success, message, report = trainer.retrain_all_models(version_id)

    if not success:
        return jsonify({"status": "error", "message": message, "data": None}), 500

    return jsonify({"status": "success", "message": message, "data": report}), 200


@ingestion_bp.route("/train/status/<version_id>", methods=["GET"])
@ingestion_bp.route("/evaluation/<version_id>", methods=["GET"])
def get_training_evaluation(version_id: str):
    trainer = ModelTrainingService.get_instance()
    report = trainer.get_evaluation_report(version_id)
    if not report:
        return jsonify({"status": "error", "message": f"Version '{version_id}' evaluation report not found."}), 404
    return jsonify({"status": "success", "data": report}), 200


# -------------------------------------------------------------
# Stage D Endpoints: Versioned Analytics Preview & Promotion
# -------------------------------------------------------------
@ingestion_bp.route("/versions", methods=["GET"])
def get_versions():
    preview_service = VersionPreviewService.get_instance()
    versions = preview_service.list_versions()
    return jsonify({"status": "success", "data": {"versions": versions}}), 200


@ingestion_bp.route("/preview/<version_id>/overview", methods=["GET"])
def get_preview_overview(version_id: str):
    preview_service = VersionPreviewService.get_instance()
    try:
        data = preview_service.get_overview_preview(version_id)
        return jsonify({"status": "success", "data": data}), 200
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404


@ingestion_bp.route("/preview/<version_id>/segmentation", methods=["GET"])
def get_preview_segmentation(version_id: str):
    preview_service = VersionPreviewService.get_instance()
    try:
        data = preview_service.get_segmentation_preview(version_id)
        return jsonify({"status": "success", "data": data}), 200
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404


@ingestion_bp.route("/preview/<version_id>/recommendations", methods=["GET"])
def get_preview_recommendations(version_id: str):
    preview_service = VersionPreviewService.get_instance()
    try:
        data = preview_service.get_recommendations_preview(version_id)
        return jsonify({"status": "success", "data": data}), 200
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404


@ingestion_bp.route("/preview/<version_id>/churn", methods=["GET"])
def get_preview_churn(version_id: str):
    preview_service = VersionPreviewService.get_instance()
    try:
        data = preview_service.get_churn_preview(version_id)
        return jsonify({"status": "success", "data": data}), 200
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404


@ingestion_bp.route("/promote/<version_id>", methods=["POST"])
def promote_version(version_id: str):
    preview_service = VersionPreviewService.get_instance()
    success, message = preview_service.promote_version(version_id)
    if not success:
        return jsonify({"status": "error", "message": message}), 400
    return jsonify({"status": "success", "message": message}), 200


@ingestion_bp.route("/evaluate-and-apply/<batch_id>", methods=["POST"])
def evaluate_and_apply(batch_id: str):
    """
    1-Click Master Integration:
    Evaluates new incoming data with historical baseline data and immediately applies
    the combined analytics to the main dashboard and all modules.
    
    1. Commits raw batch to HDFS (if available, else local staging)
    2. Runs cumulative PySpark batch pipeline: Historical + Incoming = Combined 23-feature matrix
    3. Retrains ML models (K-Means, Recommender, Churn) on the combined dataset
    4. Automatically promotes version to production and reloads DataService
    """
    ingestion_service = IngestionService.get_instance()
    pipe_service = PipelineExecutionService.get_instance()
    trainer = ModelTrainingService.get_instance()
    preview_service = VersionPreviewService.get_instance()

    batch_manifest = ingestion_service.get_batch_status(batch_id)
    if not batch_manifest:
        return jsonify({"status": "error", "message": f"Batch '{batch_id}' not found."}), 404

    force_local = False
    if batch_manifest.get("status") != "INGESTED":
        hdfs_ok, hdfs_msg, _ = ingestion_service.commit_to_hdfs(batch_id)
        if not hdfs_ok:
            force_local = True

    # 1. Cumulative PySpark Processing (Historical + Incoming)
    pipe_ok, pipe_msg, pipe_report = pipe_service.execute_batch_pipeline(batch_id, force_local_input=force_local, force_reprocess=True)
    if not pipe_ok:
        return jsonify({"status": "error", "message": f"PySpark processing failed: {pipe_msg}"}), 400

    version_id = pipe_report.get("version_id", f"v_{batch_id}")

    # 2. Retrain ML Models on Combined Data
    train_ok, train_msg, train_report = trainer.retrain_all_models(version_id)
    if not train_ok:
        return jsonify({"status": "error", "message": f"Model retraining failed: {train_msg}"}), 500

    # 3. Promote to Live Production & Reload Dashboard State
    promote_ok, promote_msg = preview_service.promote_version(version_id)
    if not promote_ok:
        return jsonify({"status": "error", "message": f"Promotion failed: {promote_msg}"}), 500

    comp = pipe_report.get("data_composition", {})
    total_cust = comp.get("overall", {}).get("total_customers", 0)
    total_rev = comp.get("overall", {}).get("total_revenue", 0.0)

    return jsonify({
        "status": "success",
        "message": f"New data evaluated with historical baseline! Main dashboard and all charts updated with combined data ({total_cust} total customers, ${total_rev:,.2f} total revenue).",
        "data": {
            "version_id": version_id,
            "batch_id": batch_id,
            "data_composition": comp,
            "processing": pipe_report,
            "evaluation": train_report
        }
    }), 200


@ingestion_bp.route("/rollback", methods=["POST"])
def rollback_version():
    preview_service = VersionPreviewService.get_instance()
    success, message = preview_service.rollback_version()
    if not success:
        return jsonify({"status": "error", "message": message}), 400
    return jsonify({"status": "success", "message": message}), 200


# -------------------------------------------------------------
# Multi-Format Field Mapping & Export Utilities
# -------------------------------------------------------------
@ingestion_bp.route("/mapping/<batch_id>", methods=["POST"])
def update_field_mapping(batch_id: str):
    """
    Updates custom source classification and column-to-canonical mapping for a staged file in the batch.
    Body JSON:
    {
        "file_id": "file_xxx",
        "custom_source": "transactions" | "web_activity" | "social_media" | "other",
        "custom_mapping": { "source_col": "target_col", ... }
    }
    """
    body = request.get_json(silent=True) or {}
    file_id = body.get("file_id")
    custom_source = body.get("custom_source")
    custom_mapping = body.get("custom_mapping")

    if not file_id or not custom_source or custom_mapping is None:
        return jsonify({"status": "error", "message": "file_id, custom_source, and custom_mapping are required."}), 400

    service = IngestionService.get_instance()
    success, message, manifest = service.save_field_mapping(
        batch_id=batch_id,
        file_id=file_id,
        custom_source=custom_source,
        custom_mapping=custom_mapping
    )
    if not success:
        return jsonify({"status": "error", "message": message, "data": None}), 400

    return jsonify({"status": "success", "message": message, "data": manifest}), 200


@ingestion_bp.route("/templates", methods=["GET"])
def get_canonical_templates():
    """Returns canonical analytical CSV template specifications with dynamic next available IDs."""
    service = IngestionService.get_instance()
    templates = service.get_canonical_templates()
    return jsonify({"status": "success", "data": templates}), 200


@ingestion_bp.route("/generate-synthetic-batch", methods=["POST"])
def generate_synthetic_batch():
    """
    Generates a realistic synthetic test batch with non-colliding customer IDs (CUST_1201+).
    Automatically stages and validates the batch, ready for 1-Click Evaluation and Live Promotion.
    """
    body = request.get_json(silent=True) or {}
    customer_count = int(body.get("customer_count", 100))
    if customer_count < 1 or customer_count > 1000:
        return jsonify({"status": "error", "message": "customer_count must be between 1 and 1000."}), 400

    service = IngestionService.get_instance()
    success, message, manifest = service.generate_synthetic_batch(customer_count=customer_count)
    if not success:
        return jsonify({"status": "error", "message": message}), 500

    return jsonify({"status": "success", "message": message, "data": manifest}), 201


@ingestion_bp.route("/templates/<source_type>/download", methods=["GET"])
def download_canonical_template(source_type: str):
    """Downloads a canonical CSV template populated with standard headers and sample row."""
    service = IngestionService.get_instance()
    templates = service.get_canonical_templates()
    if source_type not in templates:
        return jsonify({"status": "error", "message": f"Template '{source_type}' not found."}), 404

    tmpl = templates[source_type]
    csv_content = ",".join(tmpl["headers"]) + "\n" + ",".join(tmpl["sample_row"]) + "\n"
    response = make_response(csv_content)
    response.headers["Content-Disposition"] = f"attachment; filename={tmpl['filename']}"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response


@ingestion_bp.route("/export/raw/<batch_id>/<file_key>", methods=["GET"])
def export_raw_file(batch_id: str, file_key: str):
    """Downloads an untouched raw file from an ingested/staged batch."""
    service = IngestionService.get_instance()
    raw_path = service.get_raw_file_path(batch_id, file_key)
    if not raw_path or not os.path.exists(raw_path):
        return jsonify({"status": "error", "message": f"Raw file '{file_key}' in batch '{batch_id}' not found."}), 404

    filename = os.path.basename(raw_path)
    return send_file(raw_path, as_attachment=True, download_name=filename)


@ingestion_bp.route("/export/processed/<version_id>/<dataset_name>", methods=["GET"])
def export_processed_dataset(version_id: str, dataset_name: str):
    """
    Exports a processed dataset (CSV or Parquet) from data/versions/<version_id>/.
    Valid dataset_name: 'cleaned_transactions', 'cleaned_web_activity', 'cleaned_social_media', 'unified_customer_features'.
    Query param format: 'csv' (default) or 'parquet'.
    """
    format_type = request.args.get("format", "csv").lower()
    service = IngestionService.get_instance()
    file_path = service.get_processed_export_path(version_id, dataset_name, format_type=format_type)
    if not file_path or not os.path.exists(file_path):
        return jsonify({"status": "error", "message": f"Processed dataset '{dataset_name}' ({format_type}) for version '{version_id}' not found."}), 404

    filename = os.path.basename(file_path)
    return send_file(file_path, as_attachment=True, download_name=filename)


@ingestion_bp.route("/export/analytics/<version_id>/<report_name>", methods=["GET"])
def export_analytics_report(version_id: str, report_name: str):
    """
    Exports an analytics or ML evaluation report in JSON format.
    Valid report_name: 'evaluation', 'processing'.
    """
    service = IngestionService.get_instance()
    is_baseline = (version_id.lower() == "baseline")
    v_dir = service.processed_dir if is_baseline else os.path.join(service.versions_dir, version_id)

    if report_name in ("evaluation", "evaluation_report"):
        if is_baseline:
            path = os.path.join(service.models_dir, "model_evaluation_report.json")
        else:
            path = os.path.join(service.models_dir, "versions", version_id, "evaluation_report.json")
    elif report_name in ("processing", "processing_report"):
        path = os.path.join(v_dir, "processing_report.json")
    else:
        path = os.path.join(v_dir, f"{report_name}.json")

    if not os.path.exists(path):
        return jsonify({"status": "error", "message": f"Analytics report '{report_name}' for version '{version_id}' not found."}), 404

    return send_file(path, as_attachment=True, download_name=f"{version_id}_{report_name}.json")
