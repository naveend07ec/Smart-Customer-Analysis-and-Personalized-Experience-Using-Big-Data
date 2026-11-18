"""
Dataset Ingestion Validator
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Enforces strict syntax, schema, data type, numeric range, primary-key uniqueness,
and cross-source relational coverage validation for student CSV uploads before
HDFS raw ingestion. Reuses schema constants from big_data/ingestion/schemas.py.
"""

import os
import csv
import re
from datetime import datetime
from typing import Dict, Any, List, Set, Optional, Tuple

# Reusable schema column definitions
EXPECTED_HEADERS = {
    "transactions": [
        "transaction_id", "customer_id", "transaction_date", "product_id",
        "product_category", "product_name", "quantity", "unit_price",
        "discount_percent", "total_amount", "payment_method", "order_status"
    ],
    "web_activity": [
        "activity_id", "customer_id", "session_id", "timestamp",
        "page_url", "action_type", "product_id", "duration_seconds",
        "device_type", "traffic_source"
    ],
    "social_media": [
        "interaction_id", "customer_id", "timestamp", "platform",
        "interaction_type", "sentiment", "sentiment_score",
        "engagement_score", "feedback_content", "associated_category"
    ]
}

# Permitted domain categories and enums
VALID_ORDER_STATUSES = {"Completed", "Pending", "Cancelled", "Refunded"}
VALID_WEB_ACTIONS = {
    "page_view", "product_view", "search", "add_to_cart",
    "remove_from_cart", "wishlist", "checkout_start"
}
VALID_DEVICE_TYPES = {"Desktop", "Mobile", "Tablet"}
VALID_TRAFFIC_SOURCES = {"Direct", "Organic Search", "Social Media", "Referral", "Email Newsletter"}
VALID_PLATFORMS = {"Twitter/X", "Instagram", "Facebook", "LinkedIn", "YouTube", "Twitter"}
VALID_INTERACTION_TYPES = {"mention", "review", "comment", "direct_message", "share", "like"}
VALID_SENTIMENTS = {"Positive", "Neutral", "Negative"}

CUSTOMER_ID_REGEX = re.compile(r"^CUST_\d+$")


def parse_iso_datetime(date_str: str) -> Optional[datetime]:
    """Parses various ISO timestamp formats without external dependencies."""
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    return None


class DatasetValidator:
    """Validates complete multi-source CSV dataset batches."""

    def __init__(self, max_file_size_mb: float = 50.0, strict_primary_key: bool = False):
        self.max_file_size_bytes = int(max_file_size_mb * 1024 * 1024)
        self.strict_primary_key = strict_primary_key

    def validate_file_metadata(self, file_path: str, dataset_key: str) -> Tuple[bool, List[str], List[str]]:
        """Validates existence, file size, readability, and column headers."""
        errors: List[str] = []
        warnings: List[str] = []

        if not os.path.exists(file_path):
            errors.append(f"{dataset_key}.csv is missing.")
            return False, errors, warnings

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            errors.append(f"{dataset_key}.csv is empty (0 bytes).")
            return False, errors, warnings

        if file_size > self.max_file_size_bytes:
            errors.append(
                f"{dataset_key}.csv exceeds size limit: {round(file_size / (1024*1024), 2)} MB "
                f"> {round(self.max_file_size_bytes / (1024*1024), 2)} MB limit."
            )
            return False, errors, warnings

        try:
            with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    errors.append(f"{dataset_key}.csv contains no headers.")
                    return False, errors, warnings

                header = [c.strip() for c in header]
                expected = EXPECTED_HEADERS[dataset_key]
                if header != expected:
                    missing_cols = [c for c in expected if c not in header]
                    extra_cols = [c for c in header if c not in expected]
                    msg = f"{dataset_key}.csv header mismatch."
                    if missing_cols:
                        msg += f" Missing required columns: {missing_cols}."
                    if extra_cols:
                        msg += f" Unexpected columns: {extra_cols}."
                    errors.append(msg)
                    return False, errors, warnings
        except Exception as e:
            errors.append(f"Failed to read {dataset_key}.csv: {str(e)}")
            return False, errors, warnings

        return True, errors, warnings

    def validate_transactions(self, file_path: str, strict_pk: bool = False) -> Dict[str, Any]:
        """Validates transactions.csv data rows."""
        errors: List[str] = []
        warnings: List[str] = []
        seen_ids: Set[str] = set()
        duplicate_ids: Dict[str, List[int]] = {}
        customer_ids: Set[str] = set()
        min_date: Optional[datetime] = None
        max_date: Optional[datetime] = None
        missing_payment_count = 0
        row_count = 0

        with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2):  # Row 2 = first data row
                row_count += 1
                tx_id = (row.get("transaction_id") or "").strip()
                cust_id = (row.get("customer_id") or "").strip()

                # 1. Primary Key Uniqueness
                if not tx_id:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: Missing transaction_id.")
                elif tx_id in seen_ids:
                    if tx_id not in duplicate_ids:
                        duplicate_ids[tx_id] = []
                    duplicate_ids[tx_id].append(row_idx)
                else:
                    seen_ids.add(tx_id)

                # 2. Customer ID
                if not cust_id:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: Missing customer_id.")
                else:
                    customer_ids.add(cust_id)
                    if not CUSTOMER_ID_REGEX.match(cust_id):
                        if len(warnings) < 30:
                            warnings.append(f"Row {row_idx}: Customer ID '{cust_id}' does not match standard pattern CUST_XXXX.")

                # 3. Transaction Date
                date_str = row.get("transaction_date")
                parsed_date = parse_iso_datetime(date_str)
                if not parsed_date:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: Invalid transaction_date format '{date_str}'. Expected YYYY-MM-DD HH:MM:SS.")
                else:
                    min_date = parsed_date if min_date is None or parsed_date < min_date else min_date
                    max_date = parsed_date if max_date is None or parsed_date > max_date else max_date

                # 4. Numerics
                try:
                    qty = int(row.get("quantity") or 0)
                    if qty <= 0:
                        if len(errors) < 50:
                            errors.append(f"Row {row_idx}: quantity must be > 0 (found {qty}).")
                except ValueError:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: quantity '{row.get('quantity')}' is not an integer.")

                try:
                    price = float(row.get("unit_price") or 0.0)
                    if price <= 0.0:
                        if len(errors) < 50:
                            errors.append(f"Row {row_idx}: unit_price must be > 0.0 (found {price}).")
                except ValueError:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: unit_price '{row.get('unit_price')}' is not a valid float.")

                try:
                    disc = float(row.get("discount_percent") or 0.0)
                    if disc < 0.0 or disc > 100.0:
                        if len(errors) < 50:
                            errors.append(f"Row {row_idx}: discount_percent must be in [0.0, 100.0] (found {disc}).")
                except ValueError:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: discount_percent '{row.get('discount_percent')}' is not a valid float.")

                try:
                    total = float(row.get("total_amount") or 0.0)
                    if total <= 0.0:
                        if len(errors) < 50:
                            errors.append(f"Row {row_idx}: total_amount must be > 0.0 (found {total}).")
                except ValueError:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: total_amount '{row.get('total_amount')}' is not a valid float.")

                # 5. Nullable Payment Method (Preserved for PySpark imputation)
                pay_method = (row.get("payment_method") or "").strip()
                if not pay_method or pay_method.lower() in ("null", "none"):
                    missing_payment_count += 1

                # 6. Order Status
                status = (row.get("order_status") or "").strip()
                if status not in VALID_ORDER_STATUSES:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: Invalid order_status '{status}'. Permitted: {sorted(VALID_ORDER_STATUSES)}.")

        # Aggregate duplicates into warnings or errors
        total_dup_rows = sum(len(r) for r in duplicate_ids.values())
        if duplicate_ids:
            dup_summary = [f"{tid} (row {rows[0]})" for tid, rows in list(duplicate_ids.items())[:10]]
            dup_msg = f"Found {len(duplicate_ids)} duplicate transaction_id values ({total_dup_rows} duplicate rows): {', '.join(dup_summary)}"
            if strict_pk:
                errors.append(dup_msg)
            else:
                warnings.append(f"{dup_msg}. PySpark batch cleaning will automatically deduplicate these records.")

        if missing_payment_count > 0:
            warnings.append(f"{missing_payment_count} transactions have missing payment_method; will be auto-imputed to 'Unknown' by PySpark.")

        return {
            "record_count": row_count,
            "unique_primary_keys": len(seen_ids),
            "duplicate_count": len(duplicate_ids),
            "duplicate_rows": total_dup_rows,
            "duplicate_details": duplicate_ids,
            "customer_ids": customer_ids,
            "min_date": min_date.strftime("%Y-%m-%d %H:%M:%S") if min_date else None,
            "max_date": max_date.strftime("%Y-%m-%d %H:%M:%S") if max_date else None,
            "missing_payment_count": missing_payment_count,
            "errors": errors,
            "warnings": warnings
        }

    def validate_web_activity(self, file_path: str, strict_pk: bool = False) -> Dict[str, Any]:
        """Validates web_activity.csv data rows."""
        errors: List[str] = []
        warnings: List[str] = []
        seen_ids: Set[str] = set()
        duplicate_ids: Dict[str, List[int]] = {}
        customer_ids: Set[str] = set()
        min_date: Optional[datetime] = None
        max_date: Optional[datetime] = None
        meaningful_null_product_id_count = 0
        row_count = 0

        with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2):
                row_count += 1
                act_id = (row.get("activity_id") or "").strip()
                cust_id = (row.get("customer_id") or "").strip()

                # 1. Primary Key Uniqueness
                if not act_id:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: Missing activity_id.")
                elif act_id in seen_ids:
                    if act_id not in duplicate_ids:
                        duplicate_ids[act_id] = []
                    duplicate_ids[act_id].append(row_idx)
                else:
                    seen_ids.add(act_id)

                # 2. Customer ID
                if not cust_id:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: Missing customer_id.")
                else:
                    customer_ids.add(cust_id)

                # 3. Timestamp
                date_str = row.get("timestamp")
                parsed_date = parse_iso_datetime(date_str)
                if not parsed_date:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: Invalid web timestamp '{date_str}'.")
                else:
                    min_date = parsed_date if min_date is None or parsed_date < min_date else min_date
                    max_date = parsed_date if max_date is None or parsed_date > max_date else max_date

                # 4. Action Type
                act_type = (row.get("action_type") or "").strip()
                if act_type not in VALID_WEB_ACTIONS:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: Invalid action_type '{act_type}'. Permitted: {sorted(VALID_WEB_ACTIONS)}.")

                # 5. Meaningful Null Product ID (Preserved for generic navigation)
                prod_id = (row.get("product_id") or "").strip()
                if not prod_id or prod_id.lower() in ("null", "none"):
                    meaningful_null_product_id_count += 1

                # 6. Duration Seconds
                try:
                    dur = int(row.get("duration_seconds") or 0)
                    if dur < 0:
                        if len(errors) < 50:
                            errors.append(f"Row {row_idx}: duration_seconds must be >= 0 (found {dur}).")
                except ValueError:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: duration_seconds '{row.get('duration_seconds')}' is not an integer.")

                # 7. Device Type & Traffic Source
                dev = (row.get("device_type") or "").strip()
                if dev and dev not in VALID_DEVICE_TYPES:
                    if len(warnings) < 30:
                        warnings.append(f"Row {row_idx}: Unrecognized device_type '{dev}'. Permitted: {sorted(VALID_DEVICE_TYPES)}.")

                src = (row.get("traffic_source") or "").strip()
                if src and src not in VALID_TRAFFIC_SOURCES:
                    if len(warnings) < 30:
                        warnings.append(f"Row {row_idx}: Unrecognized traffic_source '{src}'. Permitted: {sorted(VALID_TRAFFIC_SOURCES)}.")

        total_dup_rows = sum(len(r) for r in duplicate_ids.values())
        if duplicate_ids:
            dup_summary = [f"{aid} (row {rows[0]})" for aid, rows in list(duplicate_ids.items())[:10]]
            dup_msg = f"Found {len(duplicate_ids)} duplicate activity_id values ({total_dup_rows} duplicate rows): {', '.join(dup_summary)}"
            if strict_pk:
                errors.append(dup_msg)
            else:
                warnings.append(f"{dup_msg}. PySpark batch cleaning will automatically deduplicate these records.")

        return {
            "record_count": row_count,
            "unique_primary_keys": len(seen_ids),
            "duplicate_count": len(duplicate_ids),
            "duplicate_rows": total_dup_rows,
            "duplicate_details": duplicate_ids,
            "customer_ids": customer_ids,
            "min_date": min_date.strftime("%Y-%m-%d %H:%M:%S") if min_date else None,
            "max_date": max_date.strftime("%Y-%m-%d %H:%M:%S") if max_date else None,
            "meaningful_null_product_ids": meaningful_null_product_id_count,
            "errors": errors,
            "warnings": warnings
        }

    def validate_social_media(self, file_path: str, strict_pk: bool = False) -> Dict[str, Any]:
        """Validates social_media.csv data rows."""
        errors: List[str] = []
        warnings: List[str] = []
        seen_ids: Set[str] = set()
        duplicate_ids: Dict[str, List[int]] = {}
        customer_ids: Set[str] = set()
        min_date: Optional[datetime] = None
        max_date: Optional[datetime] = None
        row_count = 0

        with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, start=2):
                row_count += 1
                soc_id = (row.get("interaction_id") or "").strip()
                cust_id = (row.get("customer_id") or "").strip()

                # 1. Primary Key Uniqueness
                if not soc_id:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: Missing interaction_id.")
                elif soc_id in seen_ids:
                    if soc_id not in duplicate_ids:
                        duplicate_ids[soc_id] = []
                    duplicate_ids[soc_id].append(row_idx)
                else:
                    seen_ids.add(soc_id)

                # 2. Customer ID
                if not cust_id:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: Missing customer_id.")
                else:
                    customer_ids.add(cust_id)

                # 3. Timestamp
                date_str = row.get("timestamp")
                parsed_date = parse_iso_datetime(date_str)
                if not parsed_date:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: Invalid social timestamp '{date_str}'.")
                else:
                    min_date = parsed_date if min_date is None or parsed_date < min_date else min_date
                    max_date = parsed_date if max_date is None or parsed_date > max_date else max_date

                # 4. Sentiment & Categoricals
                sent = (row.get("sentiment") or "").strip()
                if sent not in VALID_SENTIMENTS:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: Invalid sentiment '{sent}'. Permitted: {sorted(VALID_SENTIMENTS)}.")

                plat = (row.get("platform") or "").strip()
                if plat and plat not in VALID_PLATFORMS:
                    if len(warnings) < 30:
                        warnings.append(f"Row {row_idx}: Unrecognized social platform '{plat}'. Permitted: {sorted(VALID_PLATFORMS)}.")

                itype = (row.get("interaction_type") or "").strip()
                if itype and itype not in VALID_INTERACTION_TYPES:
                    if len(warnings) < 30:
                        warnings.append(f"Row {row_idx}: Unrecognized interaction_type '{itype}'. Permitted: {sorted(VALID_INTERACTION_TYPES)}.")

                # 5. Sentiment Score [-1.0, 1.0]
                try:
                    s_score = float(row.get("sentiment_score") or 0.0)
                    if s_score < -1.0 or s_score > 1.0:
                        if len(errors) < 50:
                            errors.append(f"Row {row_idx}: sentiment_score must be between -1.0 and 1.0 (found {s_score}).")
                except ValueError:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: sentiment_score '{row.get('sentiment_score')}' is not a float.")

                # 6. Engagement Score [0, 100]
                try:
                    e_score = int(row.get("engagement_score") or 0)
                    if e_score < 0 or e_score > 100:
                        if len(errors) < 50:
                            errors.append(f"Row {row_idx}: engagement_score must be between 0 and 100 (found {e_score}).")
                except ValueError:
                    if len(errors) < 50:
                        errors.append(f"Row {row_idx}: engagement_score '{row.get('engagement_score')}' is not an integer.")

        total_dup_rows = sum(len(r) for r in duplicate_ids.values())
        if duplicate_ids:
            dup_summary = [f"{sid} (row {rows[0]})" for sid, rows in list(duplicate_ids.items())[:10]]
            dup_msg = f"Found {len(duplicate_ids)} duplicate interaction_id values ({total_dup_rows} duplicate rows): {', '.join(dup_summary)}"
            if strict_pk:
                errors.append(dup_msg)
            else:
                warnings.append(f"{dup_msg}. PySpark batch cleaning will automatically deduplicate these records.")

        return {
            "record_count": row_count,
            "unique_primary_keys": len(seen_ids),
            "duplicate_count": len(duplicate_ids),
            "duplicate_rows": total_dup_rows,
            "duplicate_details": duplicate_ids,
            "customer_ids": customer_ids,
            "min_date": min_date.strftime("%Y-%m-%d %H:%M:%S") if min_date else None,
            "max_date": max_date.strftime("%Y-%m-%d %H:%M:%S") if max_date else None,
            "errors": errors,
            "warnings": warnings
        }

    def validate_batch(
        self,
        batch_id: str,
        transactions_path: str,
        web_activity_path: str,
        social_media_path: str,
        strict_pk: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Performs full syntactic, schema, range, and cross-source coverage validation."""
        use_strict_pk = self.strict_primary_key if strict_pk is None else strict_pk
        all_errors: List[str] = []
        all_warnings: List[str] = []

        # 1. File Metadata & Header Validation
        files_to_check = [
            (transactions_path, "transactions"),
            (web_activity_path, "web_activity"),
            (social_media_path, "social_media")
        ]

        file_checks_passed = True
        for path, key in files_to_check:
            ok, errs, warns = self.validate_file_metadata(path, key)
            all_errors.extend(errs)
            all_warnings.extend(warns)
            if not ok:
                file_checks_passed = False

        if not file_checks_passed:
            return {
                "batch_id": batch_id,
                "is_valid": False,
                "summary": {},
                "checks": {
                    "files_present": False,
                    "headers_valid": False,
                    "data_types_valid": False,
                    "primary_keys_unique": False
                },
                "warnings": all_warnings,
                "errors": all_errors
            }

        # 2. Detailed Row Validation
        tx_res = self.validate_transactions(transactions_path, strict_pk=use_strict_pk)
        web_res = self.validate_web_activity(web_activity_path, strict_pk=use_strict_pk)
        soc_res = self.validate_social_media(social_media_path, strict_pk=use_strict_pk)

        all_errors.extend(tx_res["errors"])
        all_errors.extend(web_res["errors"])
        all_errors.extend(soc_res["errors"])

        all_warnings.extend(tx_res["warnings"])
        all_warnings.extend(web_res["warnings"])
        all_warnings.extend(soc_res["warnings"])

        # 3. Cross-Source Customer Coverage Analysis
        cust_tx: Set[str] = tx_res["customer_ids"]
        cust_web: Set[str] = web_res["customer_ids"]
        cust_soc: Set[str] = soc_res["customer_ids"]

        all_custs = cust_tx | cust_web | cust_soc
        in_all_three = cust_tx & cust_web & cust_soc
        in_two_sources = (
            (cust_tx & cust_web) | (cust_tx & cust_soc) | (cust_web & cust_soc)
        ) - in_all_three
        single_source = all_custs - (in_all_three | in_two_sources)

        total_unique_custs = len(all_custs)
        coverage_pct = round((len(in_all_three) / max(1, total_unique_custs)) * 100, 1)

        # 4. Combined Date Span Calculation
        all_dates = [
            parse_iso_datetime(d) for d in [
                tx_res["min_date"], tx_res["max_date"],
                web_res["min_date"], web_res["max_date"],
                soc_res["min_date"], soc_res["max_date"]
            ] if d is not None
        ]
        min_batch_date = min(all_dates) if all_dates else None
        max_batch_date = max(all_dates) if all_dates else None
        span_days = (max_batch_date - min_batch_date).days if min_batch_date and max_batch_date else 0

        if span_days < 270:
            all_warnings.append(
                f"Batch timeline span ({span_days} days) is less than the 270-day requirement "
                f"(180d historical feature window + 90d future observation) for supervised churn point-in-time retraining. "
                f"If retrained in Stage C, the churn model will safely fallback to the baseline production model."
            )

        pk_unique = (
            tx_res["duplicate_count"] == 0 and
            web_res["duplicate_count"] == 0 and
            soc_res["duplicate_count"] == 0
        )

        is_valid = (len(all_errors) == 0)

        return {
            "batch_id": batch_id,
            "is_valid": is_valid,
            "summary": {
                "transactions_count": tx_res["record_count"],
                "web_activity_count": web_res["record_count"],
                "social_media_count": soc_res["record_count"],
                "total_records": tx_res["record_count"] + web_res["record_count"] + soc_res["record_count"],
                "unique_customers": {
                    "transactions": len(cust_tx),
                    "web_activity": len(cust_web),
                    "social_media": len(cust_soc),
                    "total_unique": total_unique_custs,
                    "in_all_three": len(in_all_three),
                    "coverage_percentage": f"{coverage_pct}%"
                },
                "customer_coverage": {
                    "all_three_sources": len(in_all_three),
                    "two_sources": len(in_two_sources),
                    "single_source_only": len(single_source)
                },
                "date_ranges": {
                    "transactions": {"min": tx_res["min_date"], "max": tx_res["max_date"]},
                    "web_activity": {"min": web_res["min_date"], "max": web_res["max_date"]},
                    "social_media": {"min": soc_res["min_date"], "max": soc_res["max_date"]},
                    "batch_span_days": span_days
                },
                "null_handling": {
                    "transactions_missing_payment": tx_res["missing_payment_count"],
                    "web_meaningful_null_product_ids": web_res["meaningful_null_product_ids"]
                },
                "duplicate_counts": {
                    "transactions": tx_res["duplicate_count"],
                    "web_activity": web_res["duplicate_count"],
                    "social_media": soc_res["duplicate_count"]
                }
            },
            "checks": {
                "files_present": True,
                "headers_valid": True,
                "data_types_valid": (len(all_errors) == 0),
                "primary_keys_unique": pk_unique,
                "cross_source_coverage_evaluated": True,
                "temporal_span_evaluated": True
            },
            "warnings": all_warnings,
            "errors": all_errors
        }
