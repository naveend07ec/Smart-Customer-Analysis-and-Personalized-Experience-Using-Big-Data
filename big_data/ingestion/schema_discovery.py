"""
Multi-Format Schema Discovery and Source Identification Engine
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Provides automated format detection, structural inspection, data type inference,
source classification, and canonical field mapping suggestions across:
1. CSV / TSV tabular files (.csv, .tsv)
2. JSON records and nested documents (.json)
3. JSON Lines newline-delimited streams (.jsonl)
4. Semi-structured text files (.txt)
5. Web and server log files (.log)
6. Excel spreadsheets (.xlsx, if parser available)
"""

import os
import csv
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Canonical analytical field signatures for source detection
CANONICAL_SIGNATURES = {
    "transactions": {
        "required_keys": {"customer_id"},
        "signature_keys": {
            "transaction_id", "order_id", "product_id", "product_category",
            "product_name", "quantity", "unit_price", "discount_percent",
            "total_amount", "amount", "payment_method", "order_status", "purchase_date", "transaction_date"
        },
        "target_fields": [
            "transaction_id", "customer_id", "transaction_date", "product_id",
            "product_category", "product_name", "quantity", "unit_price",
            "discount_percent", "total_amount", "payment_method", "order_status"
        ]
    },
    "web_activity": {
        "required_keys": {"customer_id"},
        "signature_keys": {
            "activity_id", "event_id", "session_id", "timestamp", "event_time",
            "page_url", "url", "action_type", "action", "product_id",
            "duration_seconds", "duration", "device_type", "device", "traffic_source", "source"
        },
        "target_fields": [
            "activity_id", "customer_id", "session_id", "timestamp",
            "page_url", "action_type", "product_id", "duration_seconds",
            "device_type", "traffic_source"
        ]
    },
    "social_media": {
        "required_keys": {"customer_id"},
        "signature_keys": {
            "interaction_id", "post_id", "timestamp", "platform",
            "interaction_type", "sentiment", "sentiment_score",
            "engagement_score", "feedback_content", "comment", "associated_category"
        },
        "target_fields": [
            "interaction_id", "customer_id", "timestamp", "platform",
            "interaction_type", "sentiment", "sentiment_score",
            "engagement_score", "feedback_content", "associated_category"
        ]
    }
}

# Regex patterns for field detection
CUSTOMER_ID_REGEX = re.compile(r"CUST_\d+", re.IGNORECASE)
ISO_TIMESTAMP_REGEX = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?\b")
APACHE_LOG_REGEX = re.compile(
    r'^(\S+)\s+\S+\s+(\S+)\s+\[([^\]]+)\]\s+"([A-Z]+)\s+([^"]+?)\s+HTTP/[0-9.]+"\s+(\d{3})\s+(\d+|-)'
)
KV_LOG_REGEX = re.compile(r'([a-zA-Z0-9_]+)=([^\s"\'=]+|"[^"]*"|\'[^\']*\')')


def infer_data_type(val: Any) -> str:
    """Infers primitive scalar type from string or native value."""
    if val is None:
        return "null"
    s = str(val).strip()
    if s == "" or s.lower() in ("null", "none", "nan"):
        return "null"
    if s.lower() in ("true", "false"):
        return "boolean"
    if re.fullmatch(r"-?\d+", s):
        return "integer"
    if re.fullmatch(r"-?\d+\.\d+", s):
        return "double"
    if ISO_TIMESTAMP_REGEX.search(s):
        return "timestamp"
    return "string"


class SchemaDiscoveryEngine:
    """Inspects multi-format raw files to extract schema, types, and mapping hints."""

    def __init__(self, max_sample_records: int = 5, max_inspect_bytes: int = 2 * 1024 * 1024):
        self.max_sample_records = max_sample_records
        self.max_inspect_bytes = max_inspect_bytes

    def inspect_file(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """Main entrypoint: identifies extension, inspects structure, and suggests mappings."""
        if not os.path.exists(file_path):
            return {
                "format": "UNKNOWN",
                "status": "DISCOVERY_FAILED",
                "error": f"File does not exist: {file_path}",
                "fields": [],
                "record_count": 0,
                "sample_records": []
            }

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return {
                "format": "EMPTY",
                "status": "EMPTY_FILE",
                "error": "File is empty (0 bytes).",
                "fields": [],
                "record_count": 0,
                "sample_records": []
            }

        ext = os.path.splitext(original_filename.lower())[1]

        if ext == ".csv":
            result = self._inspect_csv(file_path)
        elif ext == ".json":
            result = self._inspect_json(file_path)
        elif ext == ".jsonl":
            result = self._inspect_jsonl(file_path)
        elif ext == ".txt":
            result = self._inspect_txt(file_path)
        elif ext == ".log":
            result = self._inspect_log(file_path)
        elif ext == ".xlsx":
            result = self._inspect_xlsx(file_path)
        else:
            # Fallback sniffer
            result = self._sniff_format(file_path, original_filename)

        # Source Classification & Field Mapping Suggestions
        source_eval = self._classify_source_and_map(result.get("fields", []), result.get("sample_records", []))
        result.update(source_eval)
        result["file_size_bytes"] = file_size
        result["original_filename"] = original_filename

        return result

    # -------------------------------------------------------------
    # Format-Specific Inspectors
    # -------------------------------------------------------------
    def _inspect_csv(self, file_path: str) -> Dict[str, Any]:
        """Inspects CSV / TSV files with delimiter sniffing and column profiling."""
        try:
            with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
                head_chunk = f.read(8192)
                f.seek(0)

                # Sniff delimiter
                delimiter = ","
                if head_chunk:
                    try:
                        dialect = csv.Sniffer().sniff(head_chunk, delimiters=[",", "\t", ";", "|"])
                        delimiter = dialect.delimiter
                    except Exception:
                        delimiter = "\t" if "\t" in head_chunk else ","

                reader = csv.reader(f, delimiter=delimiter)
                headers = next(reader, None)
                if not headers:
                    return {
                        "format": "CSV",
                        "status": "NO_HEADERS",
                        "error": "No headers found in CSV file.",
                        "fields": [],
                        "record_count": 0,
                        "sample_records": []
                    }

                clean_headers = [h.strip() for h in headers if h is not None]
                type_counts: Dict[str, Dict[str, int]] = {h: {} for h in clean_headers}
                null_counts: Dict[str, int] = {h: 0 for h in clean_headers}
                samples = []
                row_count = 0

                for row in reader:
                    row_count += 1
                    row_dict = {}
                    for i, h in enumerate(clean_headers):
                        val = row[i].strip() if i < len(row) else ""
                        row_dict[h] = val
                        t = infer_data_type(val)
                        if t == "null":
                            null_counts[h] += 1
                        else:
                            type_counts[h][t] = type_counts[h].get(t, 0) + 1

                    if len(samples) < self.max_sample_records:
                        samples.append(row_dict)

                # Determine dominant inferred type
                fields_info = []
                for h in clean_headers:
                    types = type_counts[h]
                    dominant_type = max(types.items(), key=lambda x: x[1])[0] if types else "string"
                    fields_info.append({
                        "name": h,
                        "inferred_type": dominant_type,
                        "null_count": null_counts[h],
                        "nullable": null_counts[h] > 0 or row_count == 0
                    })

                return {
                    "format": "CSV",
                    "delimiter": delimiter,
                    "status": "DISCOVERED",
                    "fields": fields_info,
                    "record_count": row_count,
                    "sample_records": samples
                }
        except Exception as e:
            return {
                "format": "CSV",
                "status": "DISCOVERY_ERROR",
                "error": str(e),
                "fields": [],
                "record_count": 0,
                "sample_records": []
            }

    def _inspect_json(self, file_path: str) -> Dict[str, Any]:
        """Inspects JSON arrays of objects, records dictionaries, or single objects."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(self.max_inspect_bytes).strip()

            if not content:
                return {"format": "JSON", "status": "EMPTY_JSON", "fields": [], "record_count": 0, "sample_records": []}

            # Attempt JSON load
            data = json.loads(content)
            records = []
            json_flavor = "OBJECT"

            if isinstance(data, list):
                json_flavor = "ARRAY_OF_OBJECTS"
                records = [r for r in data if isinstance(r, dict)]
            elif isinstance(data, dict):
                # Check for common record wrappers: data, records, items, rows
                for key in ("data", "records", "items", "rows", "transactions", "events"):
                    if key in data and isinstance(data[key], list) and len(data[key]) > 0 and isinstance(data[key][0], dict):
                        json_flavor = f"OBJECT_WITH_{key.upper()}_ARRAY"
                        records = data[key]
                        break
                if not records:
                    records = [data]

            if not records:
                return {
                    "format": "JSON",
                    "flavor": json_flavor,
                    "status": "NON_TABULAR_JSON",
                    "message": "JSON structure is valid but contains no object records.",
                    "fields": [],
                    "record_count": 0,
                    "sample_records": []
                }

            # Discover all distinct keys across records
            all_keys = []
            for r in records[:100]:
                for k in r.keys():
                    if k not in all_keys:
                        all_keys.append(k)

            type_counts = {k: {} for k in all_keys}
            null_counts = {k: 0 for k in all_keys}
            samples = []

            for r in records:
                for k in all_keys:
                    val = r.get(k)
                    if isinstance(val, (dict, list)):
                        t = "nested"
                    else:
                        t = infer_data_type(val)

                    if t == "null":
                        null_counts[k] += 1
                    else:
                        type_counts[k][t] = type_counts[k].get(t, 0) + 1

                if len(samples) < self.max_sample_records:
                    samples.append({k: (r.get(k) if not isinstance(r.get(k), (dict, list)) else json.dumps(r.get(k))) for k in all_keys})

            fields_info = []
            for k in all_keys:
                types = type_counts[k]
                dom_type = max(types.items(), key=lambda x: x[1])[0] if types else "string"
                fields_info.append({
                    "name": k,
                    "inferred_type": dom_type,
                    "null_count": null_counts[k],
                    "nullable": null_counts[k] > 0
                })

            return {
                "format": "JSON",
                "flavor": json_flavor,
                "status": "DISCOVERED",
                "fields": fields_info,
                "record_count": len(records),
                "sample_records": samples
            }
        except Exception as e:
            # Maybe it is newline-delimited JSON (.jsonl with .json extension)
            return self._inspect_jsonl(file_path)

    def _inspect_jsonl(self, file_path: str) -> Dict[str, Any]:
        """Inspects newline-delimited JSON stream."""
        try:
            records = []
            line_count = 0
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    line_count += 1
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, dict):
                            records.append(obj)
                    except json.JSONDecodeError:
                        pass
                    if len(records) >= 200:
                        break

            if not records:
                return {
                    "format": "JSON_LINES",
                    "status": "INVALID_JSONL",
                    "error": "No valid JSON objects found per line.",
                    "fields": [],
                    "record_count": line_count,
                    "sample_records": []
                }

            all_keys = []
            for r in records:
                for k in r.keys():
                    if k not in all_keys:
                        all_keys.append(k)

            samples = []
            for r in records[:self.max_sample_records]:
                samples.append({k: (r.get(k) if not isinstance(r.get(k), (dict, list)) else json.dumps(r.get(k))) for k in all_keys})

            fields_info = []
            for k in all_keys:
                types = {}
                nulls = 0
                for r in records:
                    val = r.get(k)
                    t = "nested" if isinstance(val, (dict, list)) else infer_data_type(val)
                    if t == "null":
                        nulls += 1
                    else:
                        types[t] = types.get(t, 0) + 1
                dom = max(types.items(), key=lambda x: x[1])[0] if types else "string"
                fields_info.append({
                    "name": k,
                    "inferred_type": dom,
                    "null_count": nulls,
                    "nullable": nulls > 0
                })

            return {
                "format": "JSON_LINES",
                "status": "DISCOVERED",
                "fields": fields_info,
                "record_count": line_count,
                "sample_records": samples
            }
        except Exception as e:
            return {
                "format": "JSON_LINES",
                "status": "DISCOVERY_ERROR",
                "error": str(e),
                "fields": [],
                "record_count": 0,
                "sample_records": []
            }

    def _inspect_txt(self, file_path: str) -> Dict[str, Any]:
        """Inspects raw text files (customer reviews, feedback, or custom delimited rows)."""
        try:
            lines = []
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if line:
                        lines.append(line)
                    if i > 500:
                        break

            if not lines:
                return {"format": "TEXT", "status": "EMPTY_TEXT", "fields": [], "record_count": 0, "sample_records": []}

            # Check if lines have customer IDs or timestamps
            cust_matches = [CUSTOMER_ID_REGEX.findall(l) for l in lines]
            cust_found = any(len(m) > 0 for m in cust_matches)

            # Check for pipe or tab delimiters
            if all("|" in l for l in lines[:10]):
                pipe_parts = [l.split("|") for l in lines[:self.max_sample_records]]
                col_count = len(pipe_parts[0])
                fields = [{"name": f"col_{i+1}", "inferred_type": "string", "null_count": 0, "nullable": False} for i in range(col_count)]
                samples = [{f"col_{i+1}": p[i].strip() if i < len(p) else "" for i in range(col_count)} for p in pipe_parts]
                return {
                    "format": "DELIMITED_TEXT",
                    "delimiter": "|",
                    "status": "DISCOVERED",
                    "fields": fields,
                    "record_count": len(lines),
                    "sample_records": samples
                }

            # Unstructured text records
            samples = [{"line_no": i + 1, "text": l, "detected_customer_id": (cust_matches[i][0] if cust_matches[i] else None)} for i, l in enumerate(lines[:self.max_sample_records])]

            return {
                "format": "TEXT",
                "status": "DISCOVERED",
                "has_customer_ids": cust_found,
                "fields": [
                    {"name": "line_no", "inferred_type": "integer", "null_count": 0, "nullable": False},
                    {"name": "text", "inferred_type": "string", "null_count": 0, "nullable": False},
                    {"name": "detected_customer_id", "inferred_type": "string", "null_count": 0, "nullable": True}
                ],
                "record_count": len(lines),
                "sample_records": samples
            }
        except Exception as e:
            return {"format": "TEXT", "status": "DISCOVERY_ERROR", "error": str(e), "fields": [], "record_count": 0, "sample_records": []}

    def _inspect_log(self, file_path: str) -> Dict[str, Any]:
        """Inspects log files (Apache/Nginx access log or key-value activity logs)."""
        try:
            lines = []
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        lines.append(line)
                    if len(lines) >= 100:
                        break

            if not lines:
                return {"format": "LOG", "status": "EMPTY_LOG", "fields": [], "record_count": 0, "sample_records": []}

            # Test Apache/Nginx combined pattern
            apache_matches = [APACHE_LOG_REGEX.match(l) for l in lines]
            if sum(1 for m in apache_matches if m is not None) >= len(lines) * 0.7:
                fields = [
                    {"name": "ip_address", "inferred_type": "string"},
                    {"name": "ident", "inferred_type": "string"},
                    {"name": "timestamp", "inferred_type": "timestamp"},
                    {"name": "http_method", "inferred_type": "string"},
                    {"name": "request_url", "inferred_type": "string"},
                    {"name": "status_code", "inferred_type": "integer"},
                    {"name": "bytes_sent", "inferred_type": "integer"}
                ]
                samples = []
                for m in [m for m in apache_matches if m is not None][:self.max_sample_records]:
                    samples.append({
                        "ip_address": m.group(1),
                        "ident": m.group(2),
                        "timestamp": m.group(3),
                        "http_method": m.group(4),
                        "request_url": m.group(5),
                        "status_code": int(m.group(6)),
                        "bytes_sent": int(m.group(7)) if m.group(7) != "-" else 0
                    })
                return {
                    "format": "LOG",
                    "log_pattern": "COMBINED_ACCESS_LOG",
                    "status": "DISCOVERED",
                    "fields": fields,
                    "record_count": len(lines),
                    "sample_records": samples
                }

            # Test Key-Value Log Pattern
            kv_parsed = []
            for l in lines:
                kvs = dict(KV_LOG_REGEX.findall(l))
                if kvs:
                    kv_parsed.append(kvs)

            if len(kv_parsed) >= len(lines) * 0.5:
                all_keys = []
                for kvs in kv_parsed:
                    for k in kvs.keys():
                        if k not in all_keys:
                            all_keys.append(k)
                fields = [{"name": k, "inferred_type": "string"} for k in all_keys]
                samples = [{k: kvs.get(k, "") for k in all_keys} for kvs in kv_parsed[:self.max_sample_records]]
                return {
                    "format": "LOG",
                    "log_pattern": "KEY_VALUE_LOG",
                    "status": "DISCOVERED",
                    "fields": fields,
                    "record_count": len(lines),
                    "sample_records": samples
                }

            # Raw unparsed log lines
            samples = [{"line_no": i + 1, "raw_entry": l} for i, l in enumerate(lines[:self.max_sample_records])]
            return {
                "format": "LOG",
                "log_pattern": "GENERIC_RAW_LOG",
                "status": "DISCOVERED",
                "fields": [
                    {"name": "line_no", "inferred_type": "integer"},
                    {"name": "raw_entry", "inferred_type": "string"}
                ],
                "record_count": len(lines),
                "sample_records": samples
            }
        except Exception as e:
            return {"format": "LOG", "status": "DISCOVERY_ERROR", "error": str(e), "fields": [], "record_count": 0, "sample_records": []}

    def _inspect_xlsx(self, file_path: str) -> Dict[str, Any]:
        """Inspects Excel (.xlsx) file if openpyxl dependency is installed."""
        try:
            import openpyxl  # type: ignore
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            sheet_names = wb.sheetnames
            first_sheet = wb[sheet_names[0]]
            rows_iter = first_sheet.iter_rows(values_only=True)
            header = next(rows_iter, None)
            if not header:
                return {"format": "EXCEL", "status": "EMPTY_SHEET", "fields": [], "record_count": 0, "sample_records": []}

            clean_headers = [str(h).strip() if h is not None else f"col_{i+1}" for i, h in enumerate(header)]
            samples = []
            for r in rows_iter:
                row_dict = {clean_headers[i]: str(r[i]) if i < len(r) and r[i] is not None else "" for i in range(len(clean_headers))}
                samples.append(row_dict)
                if len(samples) >= self.max_sample_records:
                    break

            fields = [{"name": h, "inferred_type": "string"} for h in clean_headers]
            return {
                "format": "EXCEL",
                "status": "DISCOVERED",
                "sheet_names": sheet_names,
                "selected_sheet": sheet_names[0],
                "fields": fields,
                "record_count": len(samples),
                "sample_records": samples
            }
        except ImportError:
            # Check magic bytes for ZIP/XLSX
            with open(file_path, "rb") as f:
                sig = f.read(4)
            is_zip = sig.startswith(b"PK\x03\x04")
            return {
                "format": "EXCEL",
                "status": "PARSER_NOT_INSTALLED",
                "is_valid_xlsx_container": is_zip,
                "message": "Excel (.xlsx) files require the optional 'openpyxl' Python dependency. Install openpyxl in the environment to parse worksheet contents.",
                "fields": [],
                "record_count": 0,
                "sample_records": []
            }
        except Exception as e:
            return {"format": "EXCEL", "status": "DISCOVERY_ERROR", "error": str(e), "fields": [], "record_count": 0, "sample_records": []}

    def _sniff_format(self, file_path: str, original_filename: str) -> Dict[str, Any]:
        """Sniffs format when extension is ambiguous."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            chunk = f.read(1024).strip()

        if chunk.startswith("{") or chunk.startswith("["):
            return self._inspect_json(file_path)
        if "," in chunk and "\n" in chunk:
            return self._inspect_csv(file_path)
        return self._inspect_txt(file_path)

    # -------------------------------------------------------------
    # Source Classification & Field Mapping Engine
    # -------------------------------------------------------------
    def _classify_source_and_map(self, fields: List[Dict[str, Any]], sample_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Determines whether the dataset resembles Transactions, Web Activity, or Social Media.
        Computes match score and generates intelligent canonical mapping suggestions.
        """
        if not fields:
            return {
                "suggested_source": "other",
                "confidence_score": 0.0,
                "has_customer_id": False,
                "analytics_eligibility": "NOT_ANALYTICS_ELIGIBLE",
                "mapping_status": "MAPPING_REQUIRED",
                "suggested_mapping": {},
                "unmapped_fields": []
            }

        field_names = [f["name"].lower().strip() for f in fields]
        scores: Dict[str, float] = {}
        mapping_suggestions: Dict[str, Dict[str, str]] = {}

        # Look for customer id field
        has_direct_cust = any(f in ("customer_id", "cust_id", "client_id", "user_id", "buyer_id") for f in field_names)
        
        # Check samples if any value matches CUST_\d+
        if not has_direct_cust and sample_records:
            for f in field_names:
                for row in sample_records:
                    v = str(row.get(f, ""))
                    if CUSTOMER_ID_REGEX.search(v):
                        has_direct_cust = True
                        break

        for source_key, sig in CANONICAL_SIGNATURES.items():
            matches = 0
            cur_mapping = {}
            for target_field in sig["target_fields"]:
                for input_field in field_names:
                    # Exact match
                    if input_field == target_field:
                        matches += 1.0
                        cur_mapping[input_field] = target_field
                        break
                    # Clean semantic alias matches
                    elif (
                        (target_field == "customer_id" and input_field in ("client_id", "user_id", "buyer_id", "account_id")) or
                        (target_field == "transaction_id" and input_field in ("order_id", "invoice_id", "txn_id")) or
                        (target_field == "transaction_date" and input_field in ("purchase_date", "order_date", "date")) or
                        (target_field == "total_amount" and input_field in ("amount", "total", "revenue", "price_total")) or
                        (target_field == "timestamp" and input_field in ("event_time", "created_at", "date_time", "time")) or
                        (target_field == "activity_id" and input_field in ("event_id", "hit_id")) or
                        (target_field == "page_url" and input_field in ("url", "path", "page")) or
                        (target_field == "interaction_id" and input_field in ("post_id", "social_id", "msg_id")) or
                        (target_field == "feedback_content" and input_field in ("comment", "review", "text", "message"))
                    ):
                        matches += 0.85
                        cur_mapping[input_field] = target_field
                        break

            score = matches / len(sig["target_fields"])
            scores[source_key] = round(score, 3)
            mapping_suggestions[source_key] = cur_mapping

        best_source = max(scores.items(), key=lambda x: x[1])
        source_name = best_source[0]
        confidence = best_source[1]

        # If confidence is lower than threshold, designate as other
        if confidence < 0.25:
            source_name = "other"
            final_mapping = {}
        else:
            final_mapping = mapping_suggestions[source_name]

        # Determine Analytics Eligibility
        # Requires customer_id mapped and confidence >= 0.5
        mapped_targets = set(final_mapping.values())
        is_eligible = ("customer_id" in mapped_targets and confidence >= 0.45)
        
        eligibility_status = "ANALYTICS_ELIGIBLE" if is_eligible else "NOT_ANALYTICS_ELIGIBLE"
        mapping_status = "MAPPED" if (is_eligible and len(final_mapping) >= 5) else "MAPPING_REQUIRED"

        unmapped = [f["name"] for f in fields if f["name"] not in final_mapping]

        return {
            "suggested_source": source_name,
            "confidence_score": confidence,
            "has_customer_id": has_direct_cust or ("customer_id" in mapped_targets),
            "analytics_eligibility": eligibility_status,
            "mapping_status": mapping_status,
            "suggested_mapping": final_mapping,
            "unmapped_fields": unmapped
        }

