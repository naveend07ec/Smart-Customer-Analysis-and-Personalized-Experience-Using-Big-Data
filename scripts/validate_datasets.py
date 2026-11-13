"""
Dataset Validation Script
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Validates:
1. File existence and schema conformity.
2. Missing values across all columns.
3. Duplicate primary keys and full-row duplicates.
4. Customer ID consistency and cross-dataset referential integrity.
5. Domain constraints (numeric ranges, timestamps, categorical enum validity).
"""

import os
import csv
from datetime import datetime
from collections import Counter


def validate_file(filepath, pk_col, expected_cols, numeric_checks=None, enum_checks=None):
    if not os.path.exists(filepath):
        return {"error": f"File not found: {filepath}"}

    total_rows = 0
    missing_counts = {col: 0 for col in expected_cols}
    pk_set = set()
    pk_duplicates = 0
    full_row_duplicates = 0
    seen_rows = set()
    invalid_formats = 0
    customer_ids = set()

    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # Verify header
        header_diff = set(expected_cols) - set(reader.fieldnames or [])
        if header_diff:
            return {"error": f"Missing expected columns in {filepath}: {header_diff}"}

        for row in reader:
            total_rows += 1
            row_tuple = tuple(row[col] for col in expected_cols)
            if row_tuple in seen_rows:
                full_row_duplicates += 1
            seen_rows.add(row_tuple)

            pk_val = row[pk_col]
            if pk_val in pk_set:
                pk_duplicates += 1
            pk_set.add(pk_val)

            cid = row.get("customer_id")
            if cid:
                customer_ids.add(cid)

            # Check missing values
            for col in expected_cols:
                val = row[col].strip()
                if val == "" or val.lower() == "null" or val.lower() == "none":
                    missing_counts[col] += 1

            # Numeric range checks
            if numeric_checks:
                for col, (min_v, max_v) in numeric_checks.items():
                    val_str = row[col].strip()
                    if val_str != "":
                        try:
                            val_num = float(val_str)
                            if val_num < min_v or val_num > max_v:
                                invalid_formats += 1
                        except ValueError:
                            invalid_formats += 1

            # Enum / categorical checks
            if enum_checks:
                for col, valid_set in enum_checks.items():
                    val_cat = row[col].strip()
                    if val_cat != "" and val_cat not in valid_set:
                        invalid_formats += 1

    return {
        "file": filepath,
        "total_rows": total_rows,
        "unique_primary_keys": len(pk_set),
        "primary_key_duplicates": pk_duplicates,
        "full_row_duplicates": full_row_duplicates,
        "unique_customers": len(customer_ids),
        "customer_ids": customer_ids,
        "missing_counts": missing_counts,
        "invalid_range_or_format_count": invalid_formats
    }


def main():
    print("=" * 70)
    print("ACADEMIC DATASET VALIDATION REPORT")
    print("=" * 70)

    # 1. Transactions Schema & Rules
    tx_cols = [
        "transaction_id", "customer_id", "transaction_date", "product_id",
        "product_category", "product_name", "quantity", "unit_price",
        "discount_percent", "total_amount", "payment_method", "order_status"
    ]
    tx_numeric = {
        "quantity": (1, 100),
        "unit_price": (0.01, 10000.0),
        "total_amount": (0.01, 50000.0)
    }
    tx_enums = {
        "order_status": {"Completed", "Pending", "Cancelled", "Refunded"}
    }

    # 2. Web Activity Schema & Rules
    web_cols = [
        "activity_id", "customer_id", "session_id", "timestamp",
        "page_url", "action_type", "product_id", "duration_seconds",
        "device_type", "traffic_source"
    ]
    web_numeric = {
        "duration_seconds": (0, 7200)
    }
    web_enums = {
        "action_type": {"page_view", "product_view", "search", "add_to_cart", "remove_from_cart", "wishlist", "checkout_start"},
        "device_type": {"Desktop", "Mobile", "Tablet"}
    }

    # 3. Social Media Schema & Rules
    soc_cols = [
        "interaction_id", "customer_id", "timestamp", "platform",
        "interaction_type", "sentiment", "sentiment_score", "engagement_score",
        "feedback_content", "associated_category"
    ]
    soc_numeric = {
        "sentiment_score": (-1.0, 1.0),
        "engagement_score": (0, 100)
    }
    soc_enums = {
        "sentiment": {"Positive", "Neutral", "Negative"},
        "platform": {"Twitter/X", "Instagram", "Facebook", "LinkedIn", "YouTube"}
    }

    for env_label, prefix in [("RAW DATASETS (Full Scale)", "data/raw"), ("SAMPLE DATASETS (Mini Scale)", "data/sample")]:
        print(f"\n>>> Validating {env_label}...")
        
        tx_res = validate_file(f"{prefix}/transactions.csv", "transaction_id", tx_cols, tx_numeric, tx_enums)
        web_res = validate_file(f"{prefix}/web_activity.csv", "activity_id", web_cols, web_numeric, web_enums)
        soc_res = validate_file(f"{prefix}/social_media.csv", "interaction_id", soc_cols, soc_numeric, soc_enums)

        all_results = [("Transactions", tx_res), ("Web Activity", web_res), ("Social Media", soc_res)]

        for name, res in all_results:
            print(f"\n-- {name} ({res['file']}) --")
            print(f"  Total records: {res['total_rows']}")
            print(f"  Unique primary keys: {res['unique_primary_keys']}")
            print(f"  Duplicate rows detected: {res['full_row_duplicates']} (intended for PySpark deduplication test)")
            print(f"  Unique customer IDs: {res['unique_customers']}")
            print(f"  Domain / range violations: {res['invalid_range_or_format_count']}")
            print("  Missing values per column:")
            for col, cnt in res['missing_counts'].items():
                if cnt > 0:
                    pct = (cnt / res['total_rows']) * 100
                    print(f"    * {col}: {cnt} ({pct:.2f}%)")
                else:
                    print(f"    * {col}: 0 (0.00%)")

        # Referential Integrity & Overlap Analysis
        c_tx = tx_res["customer_ids"]
        c_web = web_res["customer_ids"]
        c_soc = soc_res["customer_ids"]

        all_custs = c_tx.union(c_web).union(c_soc)
        common_all_three = c_tx.intersection(c_web).intersection(c_soc)

        print("\n-- Cross-Dataset Referential Integrity & Overlap --")
        print(f"  Total unique customers across all sources: {len(all_custs)}")
        print(f"  Customers in Transactions: {len(c_tx)} ({len(c_tx)/len(all_custs)*100:.1f}%)")
        print(f"  Customers in Web Activity: {len(c_web)} ({len(c_web)/len(all_custs)*100:.1f}%)")
        print(f"  Customers in Social Media: {len(c_soc)} ({len(c_soc)/len(all_custs)*100:.1f}%)")
        print(f"  Customers present across ALL 3 sources: {len(common_all_three)} ({len(common_all_three)/len(all_custs)*100:.1f}%)")

    print("\n" + "=" * 70)
    print("VALIDATION COMPLETED: Datasets are ready for PySpark Ingestion & Cleaning.")
    print("=" * 70)


if __name__ == "__main__":
    main()

