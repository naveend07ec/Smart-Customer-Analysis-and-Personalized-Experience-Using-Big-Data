"""
Dataset Ingestion Service Layer (Multi-Format & Canonical Ingestion)
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Orchestrates:
1. Multi-format raw dataset upload and staging (.csv, .json, .jsonl, .txt, .log, .xlsx).
2. Checksum (SHA-256) and byte-size verification for raw datasets.
3. Automated schema discovery, data-type inference, and source classification.
4. Intelligent canonical field mapping interface.
5. Accepted raw dataset upload and verification in Hadoop HDFS (/customer-analytics/raw/uploads/<batch_id>/).
6. Non-silent failure handling and batch status tracking.
7. Data export utilities (raw data, canonical templates, processed datasets, analytics reports).
"""

import os
import json
import hashlib
import uuid
import re
import shutil
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from big_data.ingestion.validator import DatasetValidator
from big_data.ingestion.hdfs_client import HDFSManager
from big_data.ingestion.schema_discovery import SchemaDiscoveryEngine

# Standard Batch Status States
STATUS_UPLOADED = "UPLOADED"
STATUS_DISCOVERED = "DISCOVERED"
STATUS_VALIDATING = "VALIDATING"
STATUS_VALIDATION_FAILED = "VALIDATION_FAILED"
STATUS_VALIDATED = "VALIDATED"
STATUS_INGESTING = "INGESTING_TO_HDFS"
STATUS_INGESTION_FAILED = "INGESTION_FAILED"
STATUS_INGESTED = "INGESTED"

REQUIRED_DATASETS = ["transactions", "web_activity", "social_media"]
ALLOWED_EXTENSIONS = {".csv", ".tsv", ".json", ".jsonl", ".txt", ".log", ".xlsx"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit per file


def compute_sha256(file_path: str) -> str:
    """Calculates SHA-256 checksum of a local file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def sanitize_filename(name: str) -> str:
    """Strips path traversal elements and retains safe ASCII characters."""
    base = os.path.basename(name).replace("\\", "/").split("/")[-1]
    # Replace unsafe characters
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
    return clean or "uploaded_file.dat"


class IngestionService:
    _instance = None

    def __init__(self):
        self.workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.uploads_base_dir = os.path.join(self.workspace_root, "data", "uploads")
        self.index_file = os.path.join(self.uploads_base_dir, "batches_index.json")
        self.processed_dir = os.path.join(self.workspace_root, "data", "processed")
        self.versions_dir = os.path.join(self.workspace_root, "data", "versions")
        self.models_dir = os.path.join(self.workspace_root, "ml", "models")
        os.makedirs(self.uploads_base_dir, exist_ok=True)
        self.hdfs_manager = HDFSManager()
        self.validator = DatasetValidator()
        self.schema_discovery = SchemaDiscoveryEngine()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = IngestionService()
        return cls._instance

    def _generate_batch_id(self) -> str:
        """Generates a clean, timestamped, collision-free batch identifier."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_hex = uuid.uuid4().hex[:4]
        return f"batch_{ts}_{short_hex}"

    def _load_index(self) -> List[Dict[str, Any]]:
        """Reads batch history registry."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_index(self, index: List[Dict[str, Any]]):
        """Persists batch history registry."""
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2)

    def _update_index_entry(self, manifest: Dict[str, Any]):
        """Inserts or updates a batch summary entry in the index."""
        index = self._load_index()
        batch_id = manifest["batch_id"]
        entry = {
            "batch_id": batch_id,
            "batch_type": manifest.get("batch_type", "CANONICAL_CSV"),
            "status": manifest["status"],
            "created_at": manifest.get("created_at"),
            "validated_at": manifest.get("validated_at"),
            "ingested_at": manifest.get("ingested_at"),
            "file_count": len(manifest.get("staged_files", {})),
            "total_records": manifest.get("summary", {}).get("total_records", 0),
            "unique_customers": manifest.get("summary", {}).get("unique_customers", {}).get("total_unique", 0),
            "hdfs_path": manifest.get("hdfs_path")
        }
        filtered = [b for b in index if b["batch_id"] != batch_id]
        filtered.insert(0, entry)
        self._save_index(filtered)

    def _get_batch_dir(self, batch_id: str) -> str:
        return os.path.join(self.uploads_base_dir, batch_id)

    def _get_manifest_path(self, batch_id: str) -> str:
        return os.path.join(self._get_batch_dir(batch_id), "manifest.json")

    def sanitize_manifest_for_client(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Removes local filesystem host paths before returning response to client."""
        clean = json.loads(json.dumps(manifest))
        if "staged_files" in clean:
            for k, info in clean["staged_files"].items():
                if isinstance(info, dict) and "local_path" in info:
                    del info["local_path"]
        return clean

    # -------------------------------------------------------------
    # 1. Canonical 3-CSV Upload (Preserved for Backward Compatibility)
    # -------------------------------------------------------------
    def stage_batch(self, files_dict: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Receives three uploaded file objects, verifies all 3 are present,
        and saves them into an isolated local staging directory.
        """
        missing = [key for key in REQUIRED_DATASETS if key not in files_dict or not files_dict[key]]
        if missing:
            return False, f"Incomplete batch upload. Missing required CSV files: {missing}. All 3 datasets must be uploaded together.", {}

        batch_id = self._generate_batch_id()
        batch_dir = self._get_batch_dir(batch_id)
        os.makedirs(batch_dir, exist_ok=True)

        staged_files: Dict[str, Any] = {}
        total_bytes = 0

        # Save original uploaded files untouched
        for key in REQUIRED_DATASETS:
            file_storage = files_dict[key]
            filename = getattr(file_storage, "filename", f"{key}.csv") or f"{key}.csv"

            if not filename.lower().endswith(".csv"):
                return False, f"Invalid file format for '{key}'. Expected .csv file (got '{filename}').", {}

            dest_filename = f"{key}.csv"
            dest_path = os.path.join(batch_dir, dest_filename)

            # Save untouched raw bytes
            file_storage.save(dest_path)
            size = os.path.getsize(dest_path)
            total_bytes += size
            checksum = compute_sha256(dest_path)

            # Run schema discovery
            discovery = self.schema_discovery.inspect_file(dest_path, filename)

            staged_files[key] = {
                "file_id": key,
                "original_filename": filename,
                "staged_filename": dest_filename,
                "local_path": dest_path,
                "bytes": size,
                "size_bytes": size,
                "sha256": checksum,
                "format": "CSV",
                "source_type": key,
                "schema_discovery_status": discovery.get("status", "DISCOVERED"),
                "validation_status": "PENDING",
                "processing_status": "PENDING",
                "discovery": discovery,
                "discovered_schema": discovery
            }

        manifest = {
            "batch_id": batch_id,
            "batch_type": "CANONICAL_CSV",
            "status": STATUS_UPLOADED,
            "created_at": datetime.now().isoformat(),
            "total_bytes": total_bytes,
            "staged_files": staged_files,
            "is_canonical_three_source": True,
            "validation": None,
            "hdfs_path": None,
            "ingested_at": None,
            "message": "Files staged locally. Ready for validation."
        }

        manifest_path = self._get_manifest_path(batch_id)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        self._update_index_entry(manifest)
        return True, f"Batch '{batch_id}' successfully staged with all 3 files.", self.sanitize_manifest_for_client(manifest)

    # -------------------------------------------------------------
    # 2. Multi-Format Batch Ingestion (New Additive Capability)
    # -------------------------------------------------------------
    def stage_multi_format_batch(self, files_list: List[Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Accepts 1 to N files of mixed supported formats (.csv, .json, .jsonl, .txt, .log, .xlsx),
        preserves their exact bytes in an isolated directory, computes checksums,
        and runs automated schema discovery and source classification.
        """
        if not files_list or len(files_list) == 0:
            return False, "No files uploaded. Please upload at least one valid data file.", {}

        batch_id = self._generate_batch_id()
        batch_dir = self._get_batch_dir(batch_id)
        os.makedirs(batch_dir, exist_ok=True)

        staged_files: Dict[str, Any] = {}
        total_bytes = 0
        file_count = 0

        for file_storage in files_list:
            orig_name = getattr(file_storage, "filename", None) or "unnamed_file"
            if not orig_name or orig_name.strip() == "":
                continue

            safe_name = sanitize_filename(orig_name)
            ext = os.path.splitext(safe_name.lower())[1]

            if ext not in ALLOWED_EXTENSIONS:
                shutil.rmtree(batch_dir, ignore_errors=True)
                return False, f"Unsupported file format '{ext}' for file '{orig_name}'. Supported formats: {sorted(list(ALLOWED_EXTENSIONS))}.", {}

            dest_filename = f"{uuid.uuid4().hex[:6]}_{safe_name}"
            dest_path = os.path.join(batch_dir, dest_filename)

            # Save exact bytes
            file_storage.save(dest_path)
            size = os.path.getsize(dest_path)

            if size == 0:
                shutil.rmtree(batch_dir, ignore_errors=True)
                return False, f"File '{orig_name}' is empty (0 bytes). Rejected.", {}

            if size > MAX_FILE_SIZE_BYTES:
                shutil.rmtree(batch_dir, ignore_errors=True)
                return False, f"File '{orig_name}' exceeds size limit ({round(size/(1024*1024), 2)} MB > {round(MAX_FILE_SIZE_BYTES/(1024*1024), 2)} MB).", {}

            total_bytes += size
            file_count += 1
            checksum = compute_sha256(dest_path)

            # Automated Schema Discovery
            discovery = self.schema_discovery.inspect_file(dest_path, orig_name)
            file_id = f"file_{file_count}_{uuid.uuid4().hex[:4]}"

            staged_files[file_id] = {
                "file_id": file_id,
                "original_filename": orig_name,
                "staged_filename": dest_filename,
                "local_path": dest_path,
                "bytes": size,
                "size_bytes": size,
                "sha256": checksum,
                "format": discovery.get("format", ext.replace(".", "").upper()),
                "source_type": discovery.get("suggested_source", "other"),
                "confidence_score": discovery.get("confidence_score", 0.0),
                "has_customer_id": discovery.get("has_customer_id", False),
                "analytics_eligibility": discovery.get("analytics_eligibility", "NOT_ANALYTICS_ELIGIBLE"),
                "mapping_status": discovery.get("mapping_status", "MAPPING_REQUIRED"),
                "suggested_mapping": discovery.get("suggested_mapping", {}),
                "active_mapping": discovery.get("suggested_mapping", {}),
                "schema_discovery_status": discovery.get("status", "DISCOVERED"),
                "validation_status": "PENDING",
                "processing_status": "PENDING",
                "discovery": discovery,
                "discovered_schema": discovery
            }

        if file_count == 0:
            shutil.rmtree(batch_dir, ignore_errors=True)
            return False, "No valid files could be processed from the upload.", {}

        # Determine if this upload satisfies the classic 3-source analytical contract
        detected_sources = set(f["source_type"] for f in staged_files.values())
        is_canonical = ("transactions" in detected_sources and "web_activity" in detected_sources and "social_media" in detected_sources)

        manifest = {
            "batch_id": batch_id,
            "batch_type": "MULTI_FORMAT",
            "status": STATUS_UPLOADED,
            "created_at": datetime.now().isoformat(),
            "total_bytes": total_bytes,
            "file_count": file_count,
            "staged_files": staged_files,
            "is_canonical_three_source": is_canonical,
            "validation": {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "summary": {
                    "total_files": file_count,
                    "total_bytes": total_bytes,
                    "detected_sources": list(detected_sources)
                }
            },
            "hdfs_path": None,
            "ingested_at": None,
            "message": f"Successfully staged {file_count} raw file(s) with automated schema discovery."
        }

        manifest_path = self._get_manifest_path(batch_id)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        self._update_index_entry(manifest)
        return True, manifest["message"], self.sanitize_manifest_for_client(manifest)

    # -------------------------------------------------------------
    # 3. Validation & Schema Verification
    # -------------------------------------------------------------
    def validate_batch(self, batch_id: str, strict_pk: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates batch datasets. For canonical CSV batches, executes rigid schema checks.
        For multi-format batches, validates data integrity and mapping requirements.
        """
        manifest_path = self._get_manifest_path(batch_id)
        if not os.path.exists(manifest_path):
            return False, f"Batch '{batch_id}' not found.", {}

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        batch_dir = self._get_batch_dir(batch_id)

        # Canonical CSV Batch Validation
        if manifest.get("batch_type") == "CANONICAL_CSV" or "transactions" in manifest.get("staged_files", {}):
            tx_path = os.path.join(batch_dir, "transactions.csv")
            web_path = os.path.join(batch_dir, "web_activity.csv")
            soc_path = os.path.join(batch_dir, "social_media.csv")

            val_result = self.validator.validate_batch(
                batch_id=batch_id,
                transactions_path=tx_path,
                web_activity_path=web_path,
                social_media_path=soc_path,
                strict_pk=strict_pk
            )

            is_valid = val_result["is_valid"]
            manifest["status"] = STATUS_VALIDATED if is_valid else STATUS_VALIDATION_FAILED
            manifest["validated_at"] = datetime.now().isoformat()
            manifest["validation"] = val_result
            manifest["summary"] = val_result.get("summary", {})
            manifest["message"] = (
                "Batch passed validation with zero blocking errors."
                if is_valid else
                f"Validation failed with {len(val_result['errors'])} blocking error(s)."
            )

            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            self._update_index_entry(manifest)
            return is_valid, manifest["message"], self.sanitize_manifest_for_client(manifest)

        # Multi-Format Batch Validation
        errors = []
        warnings = []
        staged_files = manifest.get("staged_files", {})

        for fid, finfo in staged_files.items():
            loc_path = finfo.get("local_path")
            if not loc_path or not os.path.exists(loc_path):
                errors.append(f"File '{finfo.get('original_filename')}' is missing from staging.")
                continue

            # Verify integrity
            curr_size = os.path.getsize(loc_path)
            if curr_size == 0:
                errors.append(f"File '{finfo.get('original_filename')}' has 0 bytes.")

            disc = finfo.get("discovery", {})
            if disc.get("status") == "PARSER_NOT_INSTALLED":
                warnings.append(f"File '{finfo.get('original_filename')}': {disc.get('message')}")

            if finfo.get("analytics_eligibility") == "NOT_ANALYTICS_ELIGIBLE":
                warnings.append(f"File '{finfo.get('original_filename')}' lacks a verified customer_id and will remain in raw storage without analytical processing.")

        is_valid = len(errors) == 0
        manifest["status"] = STATUS_VALIDATED if is_valid else STATUS_VALIDATION_FAILED
        manifest["validated_at"] = datetime.now().isoformat()
        manifest["validation"] = {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "summary": {
                "total_files": len(staged_files),
                "valid_files": len(staged_files) - len(errors),
                "total_bytes": manifest.get("total_bytes", 0)
            }
        }
        manifest["message"] = (
            "Multi-format raw files validated and ready for HDFS commit."
            if is_valid else
            f"Validation encountered {len(errors)} blocking error(s)."
        )

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        self._update_index_entry(manifest)
        return is_valid, manifest["message"], self.sanitize_manifest_for_client(manifest)

    # -------------------------------------------------------------
    # 4. HDFS Raw Storage Commit & Remote Verification
    # -------------------------------------------------------------
    def commit_to_hdfs(self, batch_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Commits all staged raw files to HDFS under:
        /customer-analytics/raw/uploads/<batch_id>/
        Verifies exact remote byte sizes. Fails fast with HTTP 503 if HDFS is offline.
        If batch is in INGESTION_FAILED, delegates to safe recover_failed_batch.
        """
        manifest_path = self._get_manifest_path(batch_id)
        if not os.path.exists(manifest_path):
            return False, f"Batch '{batch_id}' not found.", {}

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        current_status = manifest.get("status")
        if current_status == STATUS_INGESTION_FAILED:
            return self.recover_failed_batch(batch_id)

        if current_status == STATUS_UPLOADED and manifest.get("batch_type") == "MULTI_FORMAT":
            # Auto-validate multi-format batch before commit
            self.validate_batch(batch_id)
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            current_status = manifest.get("status")

        if current_status not in (STATUS_VALIDATED, STATUS_UPLOADED, STATUS_INGESTION_FAILED):
            return False, f"Cannot commit batch in '{current_status}' status. Batch must be in '{STATUS_VALIDATED}' status.", self.sanitize_manifest_for_client(manifest)

        # 1. Genuine HDFS connectivity check
        hdfs_stat = self.hdfs_manager.check_hdfs_status()
        retry_history = manifest.setdefault("retry_history", [])
        now_iso = datetime.now().isoformat()

        if not hdfs_stat["is_available"]:
            fail_reason = (
                f"Hadoop HDFS cluster is OFFLINE. Cannot ingest to HDFS. "
                f"Details: {hdfs_stat['message']}. Start Hadoop daemons in WSL2 and retry."
            )
            manifest["status"] = STATUS_INGESTION_FAILED
            manifest["message"] = fail_reason
            manifest["last_retry_at"] = now_iso
            retry_history.append({
                "attempt": len(retry_history) + 1,
                "timestamp": now_iso,
                "status": "FAILED",
                "action": "COMMIT_TO_HDFS_CONNECTIVITY_CHECK",
                "reason": fail_reason
            })
            manifest["retry_count"] = len(retry_history)
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            self._update_index_entry(manifest)
            return False, manifest["message"], self.sanitize_manifest_for_client(manifest)

        # 2. Collect all staged files to transfer
        staged_files = manifest.get("staged_files", {})
        files_to_transfer: Dict[str, str] = {}

        for fid, finfo in staged_files.items():
            loc_path = finfo.get("local_path")
            if loc_path and os.path.exists(loc_path):
                files_to_transfer[fid] = loc_path

        files_to_transfer["manifest"] = manifest_path

        manifest["status"] = STATUS_INGESTING
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # 3. Transfer & Verify
        target_hdfs_dir = f"/customer-analytics/raw/uploads/{batch_id}"
        success, msg, upload_details = self.hdfs_manager.upload_batch_to_hdfs(
            batch_id=batch_id,
            staged_files=files_to_transfer,
            hdfs_target_dir=target_hdfs_dir
        )

        if not success:
            manifest["status"] = STATUS_INGESTION_FAILED
            manifest["message"] = f"HDFS Ingestion failed: {msg}"
            manifest["last_retry_at"] = now_iso
            retry_history.append({
                "attempt": len(retry_history) + 1,
                "timestamp": now_iso,
                "status": "FAILED",
                "action": "COMMIT_TO_HDFS_UPLOAD",
                "reason": msg
            })
            manifest["retry_count"] = len(retry_history)
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            self._update_index_entry(manifest)
            return False, manifest["message"], self.sanitize_manifest_for_client(manifest)

        manifest["status"] = STATUS_INGESTED
        manifest["ingested_at"] = now_iso
        manifest["hdfs_path"] = target_hdfs_dir
        manifest["hdfs_details"] = upload_details
        manifest["message"] = f"Batch successfully ingested and verified in Hadoop HDFS ({target_hdfs_dir})."
        retry_history.append({
            "attempt": len(retry_history) + 1,
            "timestamp": now_iso,
            "status": "SUCCESS",
            "action": "COMMIT_TO_HDFS_UPLOAD",
            "message": f"Successfully uploaded and verified {len(files_to_transfer)} files in HDFS."
        })
        manifest["retry_count"] = len(retry_history)

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # Upload final verified manifest copy to HDFS
        self.hdfs_manager.upload_batch_to_hdfs(
            batch_id=batch_id,
            staged_files={"manifest": manifest_path},
            hdfs_target_dir=target_hdfs_dir
        )

        self._update_index_entry(manifest)
        return True, manifest["message"], self.sanitize_manifest_for_client(manifest)

    def recover_failed_batch(self, batch_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Safely recovers a batch in INGESTION_FAILED (or VALIDATED/UPLOADED) status.
        1. Preserves original batch ID and local staged files.
        2. Inspects HDFS directory /customer-analytics/raw/uploads/<batch_id>/.
        3. Verifies file presence and byte size against manifest.
        4. If all files exist & verify in HDFS -> idempotently recovers status to INGESTED.
        5. If files are missing/incomplete -> retries HDFS upload with same batch ID.
        6. Logs retry attempt, timestamp, and failure reason in retry_history.
        7. Returns sanitized manifest.
        """
        manifest_path = self._get_manifest_path(batch_id)
        if not os.path.exists(manifest_path):
            return False, f"Batch '{batch_id}' not found.", {}

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        current_status = manifest.get("status")
        if current_status == STATUS_INGESTED:
            return True, f"Batch '{batch_id}' is already in INGESTED status.", self.sanitize_manifest_for_client(manifest)

        if current_status not in (STATUS_INGESTION_FAILED, STATUS_VALIDATED, STATUS_UPLOADED):
            return False, (
                f"Cannot recover batch in status '{current_status}'. "
                f"Batch must be in '{STATUS_INGESTION_FAILED}', '{STATUS_VALIDATED}', or '{STATUS_UPLOADED}'."
            ), self.sanitize_manifest_for_client(manifest)

        # 1. Collect local staged files to verify/transfer
        staged_files = manifest.get("staged_files", {})
        if not staged_files:
            return False, f"Batch '{batch_id}' has no staged files to recover.", self.sanitize_manifest_for_client(manifest)

        batch_dir = self._get_batch_dir(batch_id)
        files_to_transfer: Dict[str, str] = {}
        for fid, finfo in staged_files.items():
            loc_path = finfo.get("local_path")
            if not loc_path or not os.path.exists(loc_path):
                candidate_name = finfo.get("staged_filename") or finfo.get("original_filename") or f"{fid}.csv"
                fallback_path = os.path.join(batch_dir, candidate_name)
                if os.path.exists(fallback_path):
                    loc_path = fallback_path
                    finfo["local_path"] = loc_path
                else:
                    return False, f"Local raw file '{candidate_name}' for file '{fid}' is missing on disk. Cannot recover batch without original files.", self.sanitize_manifest_for_client(manifest)
            files_to_transfer[fid] = loc_path

        files_to_transfer["manifest"] = manifest_path

        target_hdfs_dir = f"/customer-analytics/raw/uploads/{batch_id}"
        now_iso = datetime.now().isoformat()
        retry_history = manifest.setdefault("retry_history", [])
        attempt_number = len(retry_history) + 1

        # 2. Check HDFS connectivity
        hdfs_stat = self.hdfs_manager.check_hdfs_status()
        if not hdfs_stat["is_available"]:
            fail_reason = (
                f"Hadoop HDFS cluster is OFFLINE. Cannot recover or ingest batch '{batch_id}' to HDFS. "
                f"Details: {hdfs_stat['message']}. Start Hadoop daemons in WSL2 and retry."
            )
            retry_history.append({
                "attempt": attempt_number,
                "timestamp": now_iso,
                "status": "FAILED",
                "action": "CHECK_HDFS_CONNECTIVITY",
                "reason": fail_reason
            })
            manifest["status"] = STATUS_INGESTION_FAILED
            manifest["message"] = fail_reason
            manifest["last_retry_at"] = now_iso
            manifest["retry_count"] = len(retry_history)
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            self._update_index_entry(manifest)
            return False, fail_reason, self.sanitize_manifest_for_client(manifest)

        # 3. Check if all raw data files already exist in HDFS and verify byte sizes
        dir_exists, hdfs_listing = self.hdfs_manager.verify_hdfs_directory(target_hdfs_dir)
        raw_files_to_check = {fid: p for fid, p in files_to_transfer.items() if fid != "manifest"}
        all_files_verified = dir_exists and len(raw_files_to_check) > 0

        if dir_exists:
            for fid, loc_path in raw_files_to_check.items():
                fname = os.path.basename(loc_path)
                target_file = f"{target_hdfs_dir}/{fname}"
                local_size = os.path.getsize(loc_path)
                stat_ret, stat_out, _ = self.hdfs_manager._exec_hdfs_cmd(["dfs", "-stat", "%b", target_file])
                if stat_ret != 0:
                    all_files_verified = False
                    break
                try:
                    remote_size = int(stat_out.strip())
                    if remote_size != local_size:
                        all_files_verified = False
                        break
                except (ValueError, TypeError):
                    all_files_verified = False
                    break
        else:
            all_files_verified = False

        # 4. If all files already present & verified in HDFS: Recover idempotently without re-upload
        if all_files_verified:
            manifest["status"] = STATUS_INGESTED
            manifest["hdfs_path"] = target_hdfs_dir
            manifest["ingested_at"] = manifest.get("ingested_at") or now_iso
            manifest["recovered_at"] = now_iso
            manifest["message"] = f"Batch raw files verified in Hadoop HDFS ({target_hdfs_dir}) and recovered to INGESTED."
            retry_history.append({
                "attempt": attempt_number,
                "timestamp": now_iso,
                "status": "SUCCESS",
                "action": "VERIFY_EXISTING_HDFS_FILES",
                "message": f"All {len(raw_files_to_check)} raw data files already present and verified in HDFS. Batch recovered to INGESTED."
            })
            manifest["retry_count"] = len(retry_history)
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            # Upload updated manifest copy to HDFS
            self.hdfs_manager.upload_batch_to_hdfs(
                batch_id=batch_id,
                staged_files={"manifest": manifest_path},
                hdfs_target_dir=target_hdfs_dir
            )

            self._update_index_entry(manifest)
            return True, manifest["message"], self.sanitize_manifest_for_client(manifest)

        # 5. Missing or incomplete files -> retry ingestion using the SAME batch ID
        manifest["status"] = STATUS_INGESTING
        manifest["last_retry_at"] = now_iso
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        upload_success, upload_msg, upload_details = self.hdfs_manager.upload_batch_to_hdfs(
            batch_id=batch_id,
            staged_files=files_to_transfer,
            hdfs_target_dir=target_hdfs_dir
        )

        if not upload_success:
            manifest["status"] = STATUS_INGESTION_FAILED
            manifest["message"] = f"HDFS Ingestion retry failed: {upload_msg}"
            retry_history.append({
                "attempt": attempt_number,
                "timestamp": now_iso,
                "status": "FAILED",
                "action": "RETRY_HDFS_UPLOAD",
                "reason": upload_msg
            })
            manifest["retry_count"] = len(retry_history)
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            self._update_index_entry(manifest)
            return False, manifest["message"], self.sanitize_manifest_for_client(manifest)

        # 6. Upload succeeded -> update to INGESTED
        manifest["status"] = STATUS_INGESTED
        manifest["ingested_at"] = now_iso
        manifest["hdfs_path"] = target_hdfs_dir
        manifest["hdfs_details"] = upload_details
        manifest["message"] = f"Batch successfully ingested and verified in Hadoop HDFS ({target_hdfs_dir}) on retry."
        retry_history.append({
            "attempt": attempt_number,
            "timestamp": now_iso,
            "status": "SUCCESS",
            "action": "RETRY_HDFS_UPLOAD",
            "message": f"Successfully uploaded and verified {len(files_to_transfer)} files in HDFS."
        })
        manifest["retry_count"] = len(retry_history)

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # Upload final verified manifest copy to HDFS
        self.hdfs_manager.upload_batch_to_hdfs(
            batch_id=batch_id,
            staged_files={"manifest": manifest_path},
            hdfs_target_dir=target_hdfs_dir
        )

        self._update_index_entry(manifest)
        return True, manifest["message"], self.sanitize_manifest_for_client(manifest)


    # -------------------------------------------------------------
    # 5. Schema Discovery & Intelligent Field Mapping API
    # -------------------------------------------------------------
    def save_field_mapping(
        self,
        batch_id: str,
        file_id: str,
        custom_source: str,
        custom_mapping: Dict[str, str]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Updates source classification and canonical field mappings for a specific file.
        Re-evaluates analytics eligibility based on the updated mapping.
        """
        manifest_path = self._get_manifest_path(batch_id)
        if not os.path.exists(manifest_path):
            return False, f"Batch '{batch_id}' not found.", {}

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        staged_files = manifest.get("staged_files", {})
        if file_id not in staged_files:
            return False, f"File '{file_id}' not found in batch '{batch_id}'.", {}

        finfo = staged_files[file_id]
        finfo["source_type"] = custom_source
        finfo["active_mapping"] = custom_mapping

        # Check eligibility: requires customer_id mapped
        has_cust_id = "customer_id" in custom_mapping.values()
        is_eligible = (has_cust_id and custom_source in ("transactions", "web_activity", "social_media"))

        finfo["has_customer_id"] = has_cust_id
        finfo["analytics_eligibility"] = "ANALYTICS_ELIGIBLE" if is_eligible else "NOT_ANALYTICS_ELIGIBLE"
        finfo["mapping_status"] = "MAPPED" if is_eligible else "MAPPING_REQUIRED"

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return True, f"Field mapping updated for '{finfo.get('original_filename')}'.", self.sanitize_manifest_for_client(manifest)

    # -------------------------------------------------------------
    # 6. Data Export Utilities & Canonical Templates
    # -------------------------------------------------------------
    def get_next_sequence_ids(self) -> Dict[str, Any]:
        """Calculates the next non-colliding primary keys based on historical baseline."""
        try:
            tx_path = os.path.join(self.workspace_root, "data", "raw", "transactions.csv")
            web_path = os.path.join(self.workspace_root, "data", "raw", "web_activity.csv")
            soc_path = os.path.join(self.workspace_root, "data", "raw", "social_media.csv")

            max_cust = 1200
            if os.path.exists(tx_path):
                df_tx = pd.read_csv(tx_path, usecols=["customer_id", "transaction_id"])
                c_nums = [int(str(c).split("_")[1]) for c in df_tx["customer_id"].dropna() if "_" in str(c) and str(c).split("_")[1].isdigit()]
                if c_nums:
                    max_cust = max(c_nums)
                tx_nums = [int(str(t).split("_")[1]) for t in df_tx["transaction_id"].dropna() if "_" in str(t) and str(t).split("_")[1].isdigit()]
                max_tx = max(tx_nums) if tx_nums else 12214
            else:
                max_tx = 12214

            max_web = 120944
            if os.path.exists(web_path):
                df_web = pd.read_csv(web_path, usecols=["activity_id", "session_id"])
                w_nums = [int(str(w).split("_")[1]) for w in df_web["activity_id"].dropna() if "_" in str(w) and str(w).split("_")[1].isdigit()]
                if w_nums:
                    max_web = max(w_nums)
                s_nums = [int(str(s).split("_")[1]) for s in df_web["session_id"].dropna() if "_" in str(s) and str(s).split("_")[1].isdigit()]
                max_sess = max(s_nums) if s_nums else 30236
            else:
                max_sess = 30236

            max_soc = 8828
            if os.path.exists(soc_path):
                df_soc = pd.read_csv(soc_path, usecols=["interaction_id"])
                soc_nums = [int(str(s).split("_")[1]) for s in df_soc["interaction_id"].dropna() if "_" in str(s) and str(s).split("_")[1].isdigit()]
                if soc_nums:
                    max_soc = max(soc_nums)

            return {
                "max_historical_customer_id": f"CUST_{max_cust:04d}",
                "next_customer_id": f"CUST_{max_cust + 1:04d}",
                "next_transaction_id": f"TXN_{max_tx + 1:06d}",
                "next_activity_id": f"WEB_{max_web + 1:06d}",
                "next_session_id": f"SESS_{max_sess + 1:06d}",
                "next_interaction_id": f"SOC_{max_soc + 1:06d}",
                "guidance": f"Historical baseline contains CUST_0001 through CUST_{max_cust:04d}. To register NEW customers, start IDs at CUST_{max_cust + 1:04d}. Any IDs from CUST_0001 to CUST_{max_cust:04d} will be correctly recorded as repeat activities by existing customers."
            }
        except Exception:
            return {
                "max_historical_customer_id": "CUST_1200",
                "next_customer_id": "CUST_1201",
                "next_transaction_id": "TXN_012215",
                "next_activity_id": "WEB_120945",
                "next_session_id": "SESS_030237",
                "next_interaction_id": "SOC_008829",
                "guidance": "Historical baseline contains CUST_0001 through CUST_1200. To register NEW customers, start IDs at CUST_1201. Any IDs <= 1200 are recorded as repeat activities by existing customers."
            }

    def get_canonical_templates(self) -> Dict[str, Any]:
        """Returns standard CSV templates for canonical analytical sources with dynamic non-overlapping sample IDs."""
        next_ids = self.get_next_sequence_ids()
        next_cid = next_ids["next_customer_id"]
        next_tx = next_ids["next_transaction_id"]
        next_web = next_ids["next_activity_id"]
        next_sess = next_ids["next_session_id"]
        next_soc = next_ids["next_interaction_id"]

        return {
            "metadata": next_ids,
            "transactions": {
                "filename": "transactions_template.csv",
                "headers": [
                    "transaction_id", "customer_id", "transaction_date", "product_id",
                    "product_category", "product_name", "quantity", "unit_price",
                    "discount_percent", "total_amount", "payment_method", "order_status"
                ],
                "sample_row": [
                    next_tx, next_cid, "2024-06-15 10:30:00", "PROD_101",
                    "Electronics", "Wireless Noise-Canceling Headphones", "1", "149.99",
                    "0.0", "149.99", "Credit Card", "Completed"
                ]
            },
            "web_activity": {
                "filename": "web_activity_template.csv",
                "headers": [
                    "activity_id", "customer_id", "session_id", "timestamp",
                    "page_url", "action_type", "product_id", "duration_seconds",
                    "device_type", "traffic_source"
                ],
                "sample_row": [
                    next_web, next_cid, next_sess, "2024-06-15 10:25:00",
                    "/products/headphones", "product_view", "PROD_101", "120",
                    "Desktop", "Organic Search"
                ]
            },
            "social_media": {
                "filename": "social_media_template.csv",
                "headers": [
                    "interaction_id", "customer_id", "timestamp", "platform",
                    "interaction_type", "sentiment", "sentiment_score",
                    "engagement_score", "feedback_content", "associated_category"
                ],
                "sample_row": [
                    next_soc, next_cid, "2024-06-15 14:00:00", "Twitter/X",
                    "review", "Positive", "0.85", "65",
                    "Amazing sound quality on these headphones!", "Electronics"
                ]
            }
        }

    def generate_synthetic_batch(self, customer_count: int = 100) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Generates realistic, non-colliding synthetic batch for `customer_count` new customers
        starting at CUST_1201+ with strict zero-collision integrity against baseline.
        Automatically stages and validates the batch, ready for 1-Click Evaluation.
        """
        try:
            from scripts.data_expansion_utility import DataExpansionUtility
            util = DataExpansionUtility(workspace_root=self.workspace_root, random_seed=int(time.time()))
            synth = util.generate_synthetic_expansion(num_new_customers=customer_count)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_uuid = uuid.uuid4().hex[:4]
            batch_id = f"batch_{timestamp}_{batch_uuid}"
            batch_dir = os.path.join(self.uploads_base_dir, batch_id)
            os.makedirs(batch_dir, exist_ok=True)

            tx_path = os.path.join(batch_dir, "transactions.csv")
            web_path = os.path.join(batch_dir, "web_activity.csv")
            soc_path = os.path.join(batch_dir, "social_media.csv")

            synth["transactions"].to_csv(tx_path, index=False)
            synth["web_activity"].to_csv(web_path, index=False)
            synth["social_media"].to_csv(soc_path, index=False)

            manifest = {
                "batch_id": batch_id,
                "batch_type": "CANONICAL_CSV",
                "status": STATUS_UPLOADED,
                "created_at": datetime.now().isoformat(),
                "total_bytes": os.path.getsize(tx_path) + os.path.getsize(web_path) + os.path.getsize(soc_path),
                "staged_files": {
                    "transactions": {
                        "file_id": "transactions",
                        "original_filename": "transactions.csv",
                        "staged_filename": "transactions.csv",
                        "local_path": tx_path,
                        "bytes": os.path.getsize(tx_path),
                        "sha256": compute_sha256(tx_path),
                        "format": "CSV",
                        "source_type": "transactions"
                    },
                    "web_activity": {
                        "file_id": "web_activity",
                        "original_filename": "web_activity.csv",
                        "staged_filename": "web_activity.csv",
                        "local_path": web_path,
                        "bytes": os.path.getsize(web_path),
                        "sha256": compute_sha256(web_path),
                        "format": "CSV",
                        "source_type": "web_activity"
                    },
                    "social_media": {
                        "file_id": "social_media",
                        "original_filename": "social_media.csv",
                        "staged_filename": "social_media.csv",
                        "local_path": soc_path,
                        "bytes": os.path.getsize(soc_path),
                        "sha256": compute_sha256(soc_path),
                        "format": "CSV",
                        "source_type": "social_media"
                    }
                },
                "is_canonical_three_source": True
            }

            manifest_path = os.path.join(batch_dir, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            # Auto validate the synthetic batch
            val_ok, val_msg, updated_manifest = self.validate_batch(batch_id)
            self._update_index_entry(updated_manifest)

            first_cid = synth["new_customer_ids"][0]
            last_cid = synth["new_customer_ids"][-1]

            return True, f"Generated and staged batch '{batch_id}' with {customer_count} new unique customers ({first_cid} to {last_cid}). Zero ID collisions with historical data.", updated_manifest
        except Exception as e:
            return False, f"Synthetic generation failed: {str(e)}", {}

    def get_raw_file_path(self, batch_id: str, file_key: str) -> Optional[str]:
        """Locates staged raw file for direct download export."""
        manifest_path = self._get_manifest_path(batch_id)
        if not os.path.exists(manifest_path):
            return None
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        staged_files = manifest.get("staged_files", {})
        if file_key in staged_files:
            return staged_files[file_key].get("local_path")
        for fid, finfo in staged_files.items():
            if finfo.get("original_filename") == file_key or finfo.get("staged_filename") == file_key:
                return finfo.get("local_path")
        return None

    def get_processed_export_path(self, version_id: str, dataset_name: str, format_type: str = "csv") -> Optional[str]:
        """Returns path to processed output file in data/versions/<version_id>/."""
        v_dir = os.path.join(self.versions_dir, version_id) if version_id != "baseline" else self.processed_dir
        ext = ".csv" if format_type.lower() == "csv" else ".parquet"
        candidate = os.path.join(v_dir, f"{dataset_name}{ext}")
        return candidate if os.path.exists(candidate) else None

    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Returns sanitized manifest details for a given batch ID."""
        manifest_path = self._get_manifest_path(batch_id)
        if not os.path.exists(manifest_path):
            return None
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            return self.sanitize_manifest_for_client(manifest)
        except Exception:
            return None

    def list_batches(self) -> List[Dict[str, Any]]:
        """Returns registered upload batch history."""
        return self._load_index()
