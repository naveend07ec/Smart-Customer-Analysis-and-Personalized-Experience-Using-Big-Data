# SMART — Multi-Format Big Data Ingestion & Intelligent Processing Architecture

**Project:** Smart Customer Analysis and Personalized Experience Using Big Data  
**Component:** Multi-Format Ingestion, Schema Discovery, Distributed Storage & Processing  
**Status:** Implemented & Verified  

---

## 1. Executive Architectural Overview

In commercial enterprise environments, customer behavioral data originates across disparate channels and non-uniform storage formats:
- Point-of-sale and transaction registers export **CSV / TSV** records.
- Modern web event collectors stream **JSON** payloads and **JSON Lines (.jsonl)** logs.
- Customer support and feedback desks store semi-structured **text (.txt)** files.
- Nginx and Apache web proxies generate access and key-value **server logs (.log)**.

The SMART Multi-Format Big Data Ingestion architecture transforms the previously rigid fixed three-CSV interface into a flexible, resilient batch ingestion engine that:
1. **Preserves Original Raw Data:** Staged files are persisted untouched with SHA-256 integrity verification locally and in Apache Hadoop HDFS (`/customer-analytics/raw/uploads/<batch_id>/`).
2. **Discovers Schemas Automatically:** Inspects headers, infers data types, detects customer identifiers (`CUST_\d+`), and classifies candidate analytical sources.
3. **Supports User-Governed Field Mapping:** Allows operators to review discovered attributes and map custom source columns to canonical project schemas.
4. **Executes Distributed PySpark Batch Processing:** Transforms heterogeneous sources into the canonical 23-column unified customer feature matrix using Spark in `local[2]` mode within an 8 GB RAM boundary.
5. **Enables Model Retraining & Preview:** Retrains K-Means, CF + Apriori Recommender, and Supervised Churn with temporal verification in isolated version directories (`data/versions/<version_id>/` and `ml/models/versions/<version_id>/`).
6. **Provides Full Data Export Capabilities:** Supports downloads of canonical CSV templates, raw batch files, processed CSV/Parquet datasets, and JSON analytics reports.

```
+---------------------------------------------------------------------------------------------------------+
|                                    RAW DATA INGESTION WORKFLOW                                          |
+---------------------------------------------------------------------------------------------------------+
|                                                                                                         |
|   Supported Formats:                                                                                    |
|   [.csv, .tsv, .json, .jsonl, .txt, .log]                                                               |
|                         |                                                                               |
|                         v                                                                               |
|   +-------------------------------------------------------------+                                       |
|   | 1. Ingestion Service (Local Staging & SHA-256 Checksums)    |                                       |
|   |    data/uploads/<batch_id>/                                 |                                       |
|   +-------------------------------------------------------------+                                       |
|                         |                                                                               |
|                         v                                                                               |
|   +-------------------------------------------------------------+                                       |
|   | 2. Hadoop HDFS Distributed Raw Storage                      |                                       |
|   |    /customer-analytics/raw/uploads/<batch_id>/              |                                       |
|   +-------------------------------------------------------------+                                       |
|                         |                                                                               |
|                         v                                                                               |
|   +-------------------------------------------------------------+                                       |
|   | 3. Schema Discovery & Intelligent Field Mapping Engine       |                                       |
|   |    big_data/ingestion/schema_discovery.py                   |                                       |
|   |    - Structural inspection & type inference                 |                                       |
|   |    - Source classification & target field mapping           |                                       |
|   |    - Customer identifier validation (CUST_\d+)              |                                       |
|   +-------------------------------------------------------------+                                       |
|                         |                                                                               |
|                         v                                                                               |
|   +-------------------------------------------------------------+                                       |
|   | 4. PySpark Distributed Batch Processing Engine              |                                       |
|   |    - Multi-format readers (CSV, JSON, JSONL, TXT, LOG)      |                                       |
|   |    - Cleaning, deduplication, missing-value imputation      |                                       |
|   |    - Behavioral feature aggregation per source              |                                       |
|   |    - Canonical 23-column outer join integration             |                                       |
|   |    data/versions/<version_id>/ & HDFS Mirror                |                                       |
|   +-------------------------------------------------------------+                                       |
|                         |                                                                               |
|                         v                                                                               |
|   +-------------------------------------------------------------+                                       |
|   | 5. Version-Isolated Machine Learning Retraining             |                                       |
|   |    - K-Means Customer Segmentation                          |                                       |
|   |    - Collaborative Filtering & Apriori Recommender          |                                       |
|   |    - Supervised Random Forest Churn (Temporal Validation)   |                                       |
|   |    ml/models/versions/<version_id>/                         |                                       |
|   +-------------------------------------------------------------+                                       |
|                         |                                                                               |
|                         v                                                                               |
|   +-------------------------------------------------------------+                                       |
|   | 6. Isolated Dashboard Preview & Verified Promotion/Rollback |                                       |
|   |    - Isolated preview via VersionPreviewService             |                                       |
|   |    - Explicit promotion with atomic backup                  |                                       |
|   |    - 1-click rollback restoring Academic Baseline           |                                       |
|   +-------------------------------------------------------------+                                       |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. Supported File Formats & Reader Implementations

| Format | Extension | Discovery Method | PySpark Reader Method | Special Handling |
|---|---|---|---|---|
| **CSV / TSV** | `.csv`, `.tsv` | Python `csv.Sniffer` for delimiter detection, row counting, scalar type inference. | `spark.read.option("header", "true").option("inferSchema", "true").option("delimiter", delim).csv()` | Automatic header normalization and whitespace stripping. |
| **JSON** | `.json` | Inspects top-level structure (array of objects vs. single object with records array). | `spark.read.option("multiline", "true").json()` | Handles multiline JSON object records and nested structures. |
| **JSON Lines** | `.jsonl` | Line-by-line streaming parse, inspecting distinct keys across records. | `spark.read.json()` | Efficient newline-delimited record parsing. |
| **Text** | `.txt` | Checks for customer ID regex (`CUST_\d+`), pipe delimiters (`\|`), and line records. | `spark.read.option("delimiter", "\|").csv()` or `spark.read.text()` | Preserves original text; maps delimited fields to canonical schemas. |
| **Server Logs** | `.log` | Tests Apache/Nginx combined access log regex and key-value regex patterns (`k=v`). | Structured key-value regex extraction into PySpark DataFrame. | Extracts IP, timestamp, action, and customer ID attributes. |
| **Excel** | `.xlsx` | Magic-byte signature check (`PK\x03\x04`). Rejects if `openpyxl` missing. | Dependency-gated safe fallback. | Prevents unvetted package installations and environment instability. |

---

## 3. Storage Hierarchy & Immutability Guarantees

### Raw Storage Architecture
Raw batches are stored in isolated directories keyed by unique timestamps:
- **Local Staging:** `data/uploads/<batch_id>/`
  - `manifest.json`: Full batch metadata, checksums, schema discovery records, and active mappings.
  - `<hash>_<filename>`: Byte-preserved uploaded files.
- **Hadoop HDFS:** `/customer-analytics/raw/uploads/<batch_id>/`
  - Distributed mirror of untouched source files.
  - Verified using `hdfs dfs -stat %b` and SHA-256 checksum tracking.

### Processed Storage Architecture
PySpark outputs are written exclusively to version-isolated directories:
- **Version Store:** `data/versions/<version_id>/`
  - `cleaned_transactions.parquet` & `.csv`
  - `cleaned_web_activity.parquet` & `.csv`
  - `cleaned_social_media.parquet` & `.csv`
  - `unified_customer_features.parquet` & `.csv` (23 canonical columns)
  - `processing_report.json`
- **HDFS Processed Store:** `/customer-analytics/processed/versions/<version_id>/`

### Baseline Protection Guarantee
- `data/processed/` and `ml/models/` represent the verified **Academic Baseline**.
- An automated baseline backup is maintained under `data/_baseline_backup/` and `ml/models/_baseline_backup/`.
- No upload or batch execution touches baseline files without explicit user promotion.
- Rollback instantly restores baseline files from `_baseline_backup/` and clears memory caches.

---

## 4. The Canonical 23-Column Customer Feature Matrix

Regardless of whether the raw input arrives as JSON, CSV, TXT, or LOG, PySpark maps and standardizes attributes into the project's canonical 23-column schema:

1. `customer_id` (String)
2. `total_spend` (Double)
3. `avg_order_value` (Double)
4. `total_orders` (Integer)
5. `total_quantity` (Integer)
6. `avg_discount_rate` (Double)
7. `days_since_last_order` (Integer)
8. `canceled_orders` (Integer)
9. `refunded_orders` (Integer)
10. `category_diversity` (Integer)
11. `total_sessions` (Integer)
12. `total_web_actions` (Integer)
13. `total_web_duration_seconds` (Integer)
14. `avg_session_duration_seconds` (Double)
15. `cart_add_count` (Integer)
16. `checkout_count` (Integer)
17. `view_count` (Integer)
18. `desktop_ratio` (Double)
19. `mobile_ratio` (Double)
20. `days_since_last_web_activity` (Integer)
21. `total_social_interactions` (Integer)
22. `avg_sentiment_score` (Double)
23. `avg_engagement_score` (Double)

If an uploaded batch provides only a subset of sources (e.g. transactions + web activity without social media), `build_unified_customer_features` performs outer joins on `customer_id` and coalesces unprovided metrics to default neutral values (0 for counts/spend, 0.0 for sentiment), preserving analytical contract integrity.

---

## 5. Security & Ingestion Safeguards

1. **Path Traversal Protection:** All filenames are sanitized with regex stripping path separators (`..`, `/`, `\`), preventing arbitrary file write vulnerabilities.
2. **File Execution Prohibition:** Uploaded files are strictly parsed as passive text, JSON, or tabular data; never evaluated via `eval`, `exec`, or shell invocations.
3. **Mandatory HDFS Availability:** Fast-fail with HTTP 503 if HDFS is offline during commit actions. Staged files are preserved locally for retry without silent fallback substitution.
4. **Size Boundaries:** Strict 50 MB per-file and 200 MB per-batch limits prevent denial-of-service memory exhaustion.

