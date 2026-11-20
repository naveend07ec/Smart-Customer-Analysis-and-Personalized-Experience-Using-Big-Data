# SMART Customer Analytics Platform — Final Cumulative Data Ingestion & Production Integration Report

**Date:** November 17, 2026  
**Status:** Completed & Production Verified  
**System Architecture:** Flask REST API, Apache PySpark, Hadoop HDFS, Scikit-Learn, Vite/React  

---

## 1. Executive Summary & Non-Negotiable Business Guarantee

The SMART Customer Analytics Platform simulates an enterprise continuously accumulating customer transactional, clickstream, and social media data over time through periodic batch uploads. 

Every newly ingested batch is **strictly additive**:
$$\text{Production Dataset} = \text{Original Baseline (1,200 Customers)} + \sum \text{Previously Accepted Batches} + \text{Current Validated Batch}$$

A newly uploaded batch is **never** an isolated replacement dataset. The historical 1,200-customer baseline remains preserved across all past, current, and future candidate versions.

---

## 2. Root Cause Analysis of Previous Failure

### 2.1 The Incident Observed
Following a version promotion to `v_batch_20261117_171838_f825`, the dashboard displayed:se
- Web activities: **10** (instead of 120,954)

### 2.2 Mechanism of Failure
1. **Defective Early-Return Bypass:** In `backend/app/services/pipeline_execution_service.py`, uploads categorized as `MULTI_FORMAT` hit an early-return branch (`if is_multi_format:`) that completely bypassed the cumulative PySpark aggregation pipeline (steps 2–18). It processed the 8-customer delta batch in complete isolation and exited without generating a `data_composition.json` manifest.
2. **Missing Pre-Flight Promotion Guardrails:** In `backend/app/services/version_preview_service.py`, `promote_version()` promoted candidates without asserting that `historical.total_customers >= 1200` or validating that primary keys and record counts satisfied cumulative monotonicity.
3. **Empty Source DataFrame Bug in Test Runner:** Standard CSV batches (`CANONICAL_CSV`) were being diverted to the multi-format file loader, which searched for `analytics_eligibility` at the top level of `staged_files` rather than checking nested `discovery` objects, returning empty DataFrames during integration testing.

---

## 3. Comprehensive Remediation Implemented

### 3.1 Pipeline Execution Service (`backend/app/services/pipeline_execution_service.py`)
- **Single Unified Cumulative Pipeline:** Completely removed the isolated `is_multi_format` early exit. All batch formats (CSV, TSV, JSON, JSONL, TXT, LOG) now strictly follow the cumulative path.
- **Robust Multi-Source Ingestion:** Hardened `_load_batch_source_df()` and `_load_multiformat_source_df()` to handle canonical CSV schemas and multi-format discovery metadata seamlessly.
- **Enforced Cumulative Lineage:** Reads parent lineage from `data/accepted_batches.json` or parent candidate `data_composition.json`. Reconstructs cumulative DataFrames:
  $$\text{Cumulative DF} = \text{Baseline DF} \cup \bigcup_{b \in \text{Prior Batches}} \text{Batch}_b \cup \text{Incoming Batch}$$
- **Primary-Key Deduplication & Feature Engineering:** Cumulative deduplication via PySpark `dropDuplicates(["transaction_id"])`, `dropDuplicates(["activity_id"])`, and `dropDuplicates(["interaction_id"])` before computing the 23-column unified customer feature matrix.
- **Idempotency Gate:** Reprocessing is skipped only if `processing_report.json` AND `data_composition.json` both exist and `overall.total_customers >= 1200`.

### 3.2 Hardened Atomic Promotion Guardrails (`backend/app/services/version_preview_service.py`)
`promote_version()` now executes strict transactional pre-flight validation before touching `current_version.json`:
1. Requires `data_composition.json` in candidate directory.
2. Asserts `historical.total_customers >= 1200` and `historical.total_transactions >= 12214`.
3. Verifies mathematical balancing: $\text{Overall Transactions} = \text{Historical Transactions} + \text{Newly Added Valid Transactions}$.
4. Inspects cleaned datasets on disk:
   - `cleaned_transactions.csv` $\ge 12,214$ rows, 100% unique `transaction_id`, $\ge 1,200$ distinct customers.
   - `cleaned_web_activity.csv` $\ge 120,944$ rows, 100% unique `activity_id`.
   - `cleaned_social_media.csv` $\ge 8,828$ rows, 100% unique `interaction_id`.
   - `unified_customer_features.csv` $\ge 1,200$ rows, 100% unique `customer_id`.
5. Requires $\ge 2$ clusters in `cluster_profiles.json`.
6. Creates atomic backup of `accepted_batches.json`; automatically rolls back on any write or promotion failure.

### 3.3 Data Service & API Hardening (`backend/app/services/data_service.py`)
- `get_data_composition()` reads `current_version.json` dynamically.
- Returns immutable academic baseline metrics when active version is `baseline`.
- Raises an explicit `ValueError` if an active non-baseline version lacks a valid `data_composition.json`.
- Wrapped `/api/overview/data-composition` route with standard error handling returning HTTP 400 on composition discrepancies.

---

## 4. Verification Results & Test Execution Summary

### 4.1 Incremental Integration Test Suite (`tests/test_incremental_integration.py`)
All 12 enterprise integration scenarios executed and passed with 100% success:

| Test Scenario | Description | Target Metrics | Observed Result | Status |
|:---|:---|:---|:---|:---:|
| **LIVE_HDFS** | Genuine HDFS NameNode Ingestion | Cluster operational, raw bytes uploaded | Uploaded to `/customer-analytics/raw/uploads/` | **PASSED** |
| **Scenario A** | Baseline Only State | 1,200 customers, 12,214 tx, 0 newly added | 1,200 cust, 12,214 tx, 0 new | **PASSED** |
| **Scenario B** | First Incoming Batch (100 New Cust) | 1,200 + 100 = 1,300 unique customers | 1,300 cust, 100 new, 100 tx, $10,000 rev | **PASSED** |
| **Scenario C** | Existing Customer Activity | 500 new transactions, 0 new customers | 1,200 cust, 12,714 tx, $25,000 new rev | **PASSED** |
| **Scenario D** | Chained Batch Accumulation | 1,300 + 50 new customers = 1,350 unique | 1,350 cust, 50 new customers | **PASSED** |
| **Scenario E** | Cross-Batch Duplicate Upload | Re-submitting baseline TXN IDs | 0 net new records, $0 revenue added | **PASSED** |
| **Scenario F** | Idempotent Batch Reprocessing | Re-submitting existing batch ID | Idempotent return without duplicate rows | **PASSED** |
| **Scenario G** | HDFS Failure Resilience | Simulation of offline HDFS NameNode | Active version unharmed, error logged | **PASSED** |
| **Scenario H** | Failed Processing Isolation | Broken batch upload handling | Prior active dataset unaffected | **PASSED** |
| **Scenario I** | Failed Promotion Rollback | Injected file I/O failure during promotion | Transactional recovery to prior version | **PASSED** |
| **Scenario J** | Mathematical Balancing | Historical + Newly Added = Overall | Exact arithmetic verified across all keys | **PASSED** |
| **Scenario K** | 7-Module Dashboard Consistency | All endpoints query single active version | Unified active version resolved across all | **PASSED** |

### 4.2 Regression Test Suites
- **Association Rule Remediation Suite (`tests/test_association_rules_remediation.py`):** **10/10 PASSED**
  - Customer-level basket grouping: Verified
  - Discovered association rules: Exactly 394 rules mined
  - Recommender Hit Rate@5: 76.17%
- **Multi-Format Ingestion Suite (`tests/test_multi_format_ingestion.py`):** **17/17 PASSED**
  - Schema discovery across CSV, TSV, JSON, JSONL, LOG: Verified
  - Immutability guarantee of baseline datasets: Verified

---

## 5. Live Production Candidate Verification (`v_batch_20261117_171838_f825`)

The batch involved in the initial failure was reprocessed through the corrected cumulative pipeline:

| Dimension | Baseline Historical | Newly Added Delta | Cumulative Candidate Total |
|:---|---:|---:|---:|
| **Unique Customers** | 1,200 | 3 | **1,203** |
| **Existing Customer Activity** | — | 5 | — |
| **Transactions** | 12,214 | 9 | **12,223** |
| **Completed Transactions** | 11,674 | 7 | **11,681** |
| **Web Activities** | 120,944 | 10 | **120,954** |
| **Social Media Events** | 8,828 | 8 | **8,836** |
| **Total Revenue** | \$1,807,439.49 | \$756.60 | **\$1,808,196.09** |

### Model Retraining Evaluation on Cumulative Candidate:
- **K-Means Clustering:** 5 clusters, Silhouette Score = `0.3453` ($\Delta = +0.0002$)
- **Association Rules Mined:** Exactly `394` rules (min support: 0.01, min lift: 1.05)
- **Recommendation Quality:** Hit Rate@5 = `76.17%`, Precision@5 = `30.05%`, Recall@5 = `61.02%`
- **Customer Churn Model:** ROC-AUC = `0.9076`

---

## 6. Baseline Data Integrity & SHA-256 Hashes

All original baseline datasets and processed references remain completely intact and uncorrupted:

| Dataset Path | File Size | SHA-256 Checksum | Verification |
|:---|---:|:---|:---:|
| `data/raw/transactions.csv` | 1,676,935 bytes | `9dec44e670f2b048f18bd872c7f70916ae79e695f7359f0843759779877b8f0a` | **MATCH** |
| `data/raw/web_activity.csv` | 13,183,498 bytes | `df2aa8fb00f4b3a7abb103e4cbe9cccb6be513eebe39aabab5ea5a9bf3d58827` | **MATCH** |
| `data/raw/social_media.csv` | 1,334,002 bytes | `d6e8c0e63d4e225eec11f4ccca0a755f437f96e3fad6b7c05aed5b8f31de4285` | **MATCH** |
| `data/processed/cleaned_transactions.csv` | 1,886,605 bytes | `41516758b314b3f1017c20e1aeae85ca0a46ebe9cbbaeb0114997019ce4b48f8` | **MATCH** |
| `data/processed/cleaned_web_activity.csv` | 15,719,408 bytes | `e7a5406d81e01f47e1114e576d6ecb9eb23c66e70bd891b6a7e5c8493c0b945a` | **MATCH** |
| `data/processed/cleaned_social_media.csv` | 1,505,098 bytes | `68a9ff6b9be5816c4a5129af79395aecf8b80db66a5abe49bd7c0f0b522273a4` | **MATCH** |
| `data/processed/unified_customer_features.csv` | 104,643 bytes | `38afe622f6a21982179046ba8ea436afc3739291c1197f076efee75597790e42` | **MATCH** |

---

## 7. Frontend Production Build & Live REST API Status

- **Vite Production Build:** Successfully compiled in 4.96s with 0 errors (`frontend/dist/index.html`, `dist/assets/`).
- **Flask REST API Service:** Actively serving requests on `http://127.0.0.1:5000`.
- **Active System Version:** Restored safely to `baseline` (`data/current_version.json`).
- **Dashboard Endpoints Tested & Responding 200 OK:**
  - `GET /api/overview/data-composition`
  - `GET /api/overview/kpis`
  - `GET /api/segments/`
  - `GET /api/recommendations/CUST_0001`
  - `GET /api/churn/summary`
  - `GET /api/ingestion/versions`
  - `GET /api/pipeline/summary`

---

## 8. Remaining Limitations & Operating Guidance

1. **Temporal Observation Window for Churn:** Churn point-in-time label generation requires a minimum 270-day observation window (180d feature window + 90d observation). New batches spanning under 270 days will safely fall back to the production baseline churn model during retraining.
2. **PySpark JVM Lifecycle:** In local development on Windows without winutils, PySpark logs warnings regarding `HADOOP_HOME`. These are benign and do not affect dataset computation accuracy or HDFS networking.
3. **Candidate Promotion:** Automated version promotion is permanently disabled; promotions require deliberate operator action via `/api/ingestion/promote/<version_id>`, protected by the newly established pre-flight validation gates.

