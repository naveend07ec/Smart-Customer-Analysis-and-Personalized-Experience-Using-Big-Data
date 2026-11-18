   # Stage 10 — Complete Project & PPT Compliance Audit

   **Project Title:** Smart Customer Analysis and Personalized Experience Using Big Data  
   **Audit Type:** Final Academic Defense & PPT Compliance Verification  
   **Workspace:** `D:\Infynux\big data project`  
   **Date of Audit:** November 14, 2026  
   **Execution Mode:** Strictly Read-Only Audit (No code, models, datasets, or configurations modified)

   ---

   ## 1. Executive Summary

   This audit constitutes an exhaustive, evidence-based evaluation of the entire project against the official college project review presentation documents: **Review 0**, **Review 1**, and **Review 2 (Final Phase I reference)**. 

   Every technical requirement, algorithmic objective, architectural specification, and declared outcome was tested against the live codebase, running services, trained machine learning models, HDFS storage layer, and web interfaces.

   ### Core Audit Findings
   1. **Scope Alignment (100% Core Compliance):** All primary objectives defined in Review 2 Slide 4 (Multi-source collection, cleaning, HDFS storage, PySpark processing, K-Means segmentation, personalized recommendations, and analytical visualization) are genuinely implemented, integrated, and empirically validated.
   2. **Distributed Storage & Processing:** Genuine **Apache Hadoop 3.3.6 HDFS** runs as a single-node cluster inside WSL2 Debian, serving NameNode RPC (port 9000) and DataNode block transfer (port 9866). **PySpark 3.5.1** reads raw inputs directly from HDFS and writes partitioned Parquet feature stores back to HDFS, validated with 0.0 numeric divergence from local baselines.
   3. **Machine Learning & Personalization:** Unsupervised **K-Means ($K=5$)** achieves an optimal Silhouette Score of `0.3451` and Davies-Bouldin Index of `1.1759`. The hybrid recommendation engine combines user-item collaborative filtering with 541 Market Basket association rules, demonstrating a verified **76.0% Hit Rate@5** and **100% catalog coverage**.
   4. **Supervised Customer Retention AI:** A point-in-time supervised Random Forest churn model enforces strict temporal separation (180-day feature window, 90-day future observation window) with zero data leakage, yielding a test-set **ROC-AUC of 0.9365**, **Recall of 90.32%**, and **F1-score of 0.7320** across 1,177 eligible customers.
   5. **Full-Stack Presentation Layer:** All seven dashboard pages in React 18 + Chart.js are actively served by 20 tested Flask REST endpoints (100% pass rate). Telemetry dynamically reflects live HDFS JMX socket state with zero hardcoded metrics.
   6. **Academic Integrity Verification:** Datasets are statistically modeled synthetic benchmarks (142,046 total events across 1,200 unified customers); single-node HDFS and `local[2]` Spark execution operate strictly within standard developer hardware constraints; batch analytics are accurately scoped without claiming uninstalled real-time streaming engines.

   **Overall Verdict:** **READY FOR FINAL SUBMISSION** (with minor documentation polish recommended for viva defense).

   ---

   ## 2. Extraction of Original Project Presentation Documents

   The source presentation decks were retrieved and audited directly from the student archive:
   - `C:\Users\acer\Downloads\Review 0 ppt BigData.pptx` (Review 0 — Problem Formulation & Feasibility)
   - `C:\Users\acer\Downloads\REVIEW 1 BIG DATA (2).pptx` (Review 1 — System Analysis & Design)
   - `C:\Users\acer\Downloads\REVIEW 2 BIG DATA final.pptx` (Review 2 — Phase I Review & Implementation Baseline)

   ### 2.1 Project Identity & Academic Context
   - **Title:** Smart Customer Analysis and Personalized Experience Using Big Data
   - **Authors:** P. Athisha (Reg: 8208E23CSR024), L. Grasy (Reg: 8208E23CSR053)
   - **Batch No:** 27CS14
   - **Faculty Guide:** Mrs. N. Kanagadurga, Assistant Professor of CSE
   - **Institution:** Department of Computer Science and Engineering, E.G.S. Pillay Engineering College (Autonomous), Nagapattinam, Tamil Nadu

   ### 2.2 Problem Statement & Motivation
   - **Problem Statement (Review 2 Slide 2):** Customer data is generated across multiple disparate sources (transactions, web clickstreams, social media). Disparate structures make direct integration difficult, leaving enterprises with fragmented, partial views of customer behavior. Existing single-database systems lack scalability, dynamic clustering, and actionable personalization.
   - **Proposed Solution (Review 2 Slide 3 & 10):** A multi-tier Big Data architecture combining multi-source data integration, centralized HDFS distributed storage, PySpark batch data processing, machine learning (K-Means clustering and personalized recommendations), and interactive visualization dashboards.

   ### 2.3 Explicit Project Scope & Declared Limitations (Review 2 Slide 5)
   - **Included Scope:**
   1. Collection of Transaction, Web Activity, and Social Media Data
   2. Data Cleaning, Preprocessing, and Transformation
   3. Multi-Source Data Integration via Common Customer Identifier
   4. Creation of a Unified Customer Dataset (Feature Matrix)
   5. Hadoop/HDFS for distributed data storage
   6. Apache Spark/PySpark for scalable data processing
   7. K-Means based customer behavioral segmentation
   8. Personalization and Recommendation Engine
   9. Analytical Visualization and Dashboard
   - **Explicit Exclusions & Boundaries (Crucial for Academic Integrity):**
   1. *Real-time or continuous data processing* (Kafka / Spark Streaming explicitly excluded).
   2. *Full-scale production deployment* (Multi-node enterprise clusters / paid cloud infrastructure excluded).
   3. *Advanced recommendation techniques beyond the proposed personalization approach* (Deep neural two-tower / Reinforcement Learning recommenders excluded).

   ### 2.4 Software and Hardware Requirements (Review 1 Slide 7–8, Review 2 Slide 8 & 10)
   - **Hardware:** Intel Core i5 or higher, Minimum 8 GB RAM (16 GB recommended), 256 GB Storage, 64-bit OS.
   - **Software:** Python 3.x, Apache Hadoop / HDFS, Apache Spark / PySpark, Scikit-learn, Pandas, NumPy, Dashboard/Visualization (Power BI / Tableau / Web Dashboard).

   ---

   ## 3. Requirement-by-Requirement Compliance Matrix

   | PPT Requirement | Source Review | Actual Implementation | Verified Evidence | Status | Remaining Gap / Notes |
   | :--- | :---: | :--- | :--- | :---: | :--- |
   | **Multi-Source Data Ingestion** | R0, R1, R2 | 3 distinct customer sources: Sales Transactions, Web Clickstream, Social Media Feedback | 12,239 tx, 120,979 web, 8,828 social rows in `data/raw/` | **FULLY IMPLEMENTED** | None. 100% referential integrity across 1,200 unique customers. |
   | **Data Cleaning & Deduplication** | R0, R1, R2 | PySpark cleaning rules: deduplication, schema casting, null imputation, invalid state removal | 25 duplicate tx, 35 duplicate web events dropped; 73 missing payment methods imputed | **FULLY IMPLEMENTED** | None. Preserves 60,540 legitimate navigation nulls in web activity. |
   | **Multi-Source Data Integration** | R1, R2 | Pre-aggregation by `customer_id` followed by full outer joins into unified matrix | `unified_customer_features` (1,200 rows $\times$ 23 columns) in Parquet/CSV | **FULLY IMPLEMENTED** | None. Cartesian product explosion mathematically avoided. |
   | **Hadoop HDFS Storage** | R1, R2 | Apache Hadoop 3.3.6 single-node deployment in WSL2 Debian | NameNode RPC (:9000), DataNode (:9866); HDFS paths `/customer-analytics/raw` & `/processed` | **FULLY IMPLEMENTED** | Single-node deployment (explicitly scoped; multi-node excluded). |
   | **Apache Spark / PySpark** | R1, R2 | PySpark 3.5.1 batch processing engine configured in `local[2]` mode | `scripts/run_big_data_pipeline.py` executes transformations directly against HDFS | **FULLY IMPLEMENTED** | None. Native Spark DataFrame transformations, zero Pandas fallback. |
   | **K-Means Behavioral Segmentation** | R0, R1, R2 | Unsupervised K-Means ($K=5$) with StandardScaler and PCA 2D projection | $K=5$, Inertia = 9,612.77, Silhouette = 0.3451, Davies-Bouldin = 1.1759 | **FULLY IMPLEMENTED** | None. Generates 5 distinct, explainable business personas. |
   | **Personalized Recommendations** | R0, R1, R2 | Hybrid item collaborative filtering + Market Basket association rule mining | 6,000 recommendations (Top 5 per customer), 76.0% Hit Rate@5, 100% catalog coverage | **FULLY IMPLEMENTED** | None. 541 mined rules; plain-language reasoning for every item. |
   | **Customer Retention / Churn Prediction** | R1 (S12), R2 (S10) | Supervised Random Forest point-in-time churn model with 180d/90d split | ROC-AUC = 0.9365, PR-AUC = 0.8660, Recall = 90.32%, F1 = 0.7320 across 1,177 customers | **FULLY IMPLEMENTED** | Exceeds basic PPT expectations; features zero temporal data leakage. |
   | **Analytical Visualization Dashboard** | R0, R1, R2 | 7-page React 18 + Vite + Chart.js web dashboard served by Flask REST API | Tested across all 7 views on `http://localhost:3000`; 20/20 REST endpoints passed | **FULLY IMPLEMENTED** | Implemented as a full-stack custom web app rather than Power BI file. |
   | **HDFS Health & Diagnostics UI** | R2 (Phase II) | Live NameNode JMX metrics and socket health displayed in Data Pipeline tab | Dynamic binding to `/api/pipeline/summary` (Used/Free bytes, Block status, Active Nodes) | **FULLY IMPLEMENTED** | Fully dynamic; zero hardcoded operational data. |

   ---

   ## 4. Technology Verification & Architecture Audit

   ### 4.1 Technology Stack Layer Audit

   | Layer | Expected in PPT | Implemented in Project | Verification Method | Status |
   | :--- | :--- | :--- | :--- | :---: |
   | **Frontend UI** | Power BI / Tableau / Streamlit | **React 18 + Vite + Chart.js** | Source in `frontend/src/`, `npm run build` passes in 4.42s | **SUPERIOR ALTERNATIVE** |
   | **Backend REST API** | Python / Flask | **Python 3.11.9 + Flask 3.0** | 7 Blueprint modules in `backend/app/routes/` | **GENUINELY USED** |
   | **Big Data Engine** | Apache Spark / PySpark | **PySpark 3.5.1** (`local[2]`, 2 GB) | Py4J bridge, SparkSession in `big_data/spark_session.py` | **GENUINELY USED** |
   | **Distributed Storage** | Hadoop HDFS | **Apache Hadoop 3.3.6 (WSL2 Debian)** | JPS: NameNode (PID 2827), DataNode (PID 2895) | **GENUINELY USED** |
   | **Machine Learning** | Scikit-learn, NumPy | **Scikit-learn 1.5.0 + Joblib** | Models serialized in `ml/models/` | **GENUINELY USED** |
   | **Storage Formats** | CSV / Parquet | **Snappy-Compressed Parquet + CSV** | 7 Parquet datasets in HDFS and `data/processed/` | **GENUINELY USED** |
   | **Development OS** | Windows 64-bit | **Windows 11 + WSL2 Debian Linux** | Cross-OS socket and block transfer verified | **GENUINELY USED** |

   ### 4.2 Architectural Design Justification
   - **Power BI vs React Web Dashboard:** While Review 1 and Review 2 mentioned *Power BI / Tableau / Streamlit*, building an interactive full-stack **React 18 + Flask** web dashboard is significantly more technically rigorous for a Computer Science final-year project. It demonstrates full-stack software engineering, REST API architecture, and asynchronous data fetching.
   - **Dual-Mode Storage Capability:** The pipeline features a dual-mode storage adapter (`--storage hdfs` or `--storage local`). HDFS is active and default, but the local fallback protects academic evaluators if Hadoop daemons are not running.

   ---

   ## 5. In-Depth Audit of Major Technical Components

   ### 5.1 Multi-Source Data Collection & Data Quality Assessment
   1. **Raw Dataset Dimensions:**
      - `transactions.csv`: 12,239 records, 12 features, 1,200 unique customers.
      - `web_activity.csv`: 120,979 records, 10 features, 1,200 unique customers.
      - `social_media.csv`: 8,828 records, 10 features, 1,200 unique customers.
   2. **Referential Integrity:** Exactly 1,200 unique customer IDs (`CUST_0001` through `CUST_1200`) exist across all three datasets with 100% overlap.
   3. **Synthetic Nature:** Datasets were generated by `scripts/generate_datasets.py` using controlled random distributions. They are **realistic synthetic benchmarks**, not crawled proprietary customer records. This aligns with academic ethical standards and eliminates privacy concerns.
   4. **Data Cleaning & Quality:**
      - Deduplication removed 25 redundant sales transactions and 35 duplicate web click events.
      - 73 missing payment methods were cleanly imputed to `'Unknown'`.
      - 60,540 legitimate null values on navigation/category pages were preserved without data corruption.

   ### 5.2 Genuine Apache Hadoop 3.3.6 HDFS Integration
   1. **Daemon Verification:**
      - NameNode running on PID `2827`, listening on RPC port `9000` and HTTP JMX port `9870`.
      - DataNode running on PID `2895`, listening on block transfer port `9866`.
   2. **Directory Structure in HDFS:**
      - `/customer-analytics/raw/` (transactions, web_activity, social_media)
      - `/customer-analytics/processed/` (cleaned_transactions, cleaned_web_activity, cleaned_social_media)
      - `/customer-analytics/features/` (customer_transaction_features, customer_web_features, customer_social_features, unified_customer_features)
   3. **No Silent Fallback:** The pipeline explicitly validates NameNode and DataNode sockets before execution; if unreachable, it raises an immediate `RuntimeError` rather than silently degrading to local storage.
   4. **Restart Persistence:** Daemons were stopped and restarted afresh; independent PySpark readback confirmed 100% block retention across all 7 Parquet datasets.

   ### 5.3 Apache Spark / PySpark Processing Architecture
   - Spark runs in `local[2]` mode with a 2 GB driver heap allocation, preventing memory exhaustion on developer machines with 8 GB RAM.
   - Cleaners and aggregators utilize pure PySpark DataFrame DSL transformations (`groupBy`, `agg`, `F.when`, `F.coalesce`).
   - Cartesian product explosion was prevented by aggregating each source to the customer grain before joining, ensuring a deterministic 1,200-row feature matrix.

   ### 5.4 Customer Segmentation (K-Means Clustering)
   1. **Optimal $K$ Evaluation ($K \in [2, 8]$):**
      - $K=5$ demonstrates an optimal balance: Inertia = `9,612.77`, Silhouette Score = `0.3451` (highest non-degenerate clustering), Davies-Bouldin Index = `1.1759` (lowest / most compact cluster separation).
      - *Note on slide reporting:* Slides 8/10 mention Silhouette `0.3533` from an earlier trial, while the finalized artifact records `0.3451`. Both confirm $K=5$ as the mathematically superior elbow point.
   2. **Discovered Behavioral Personas:**
      - **Cluster 0 (Casual & Occasional Shoppers):** 348 customers (29.0%), avg spend \$483.53, 3.7 orders.
      - **Cluster 1 (High-Value VIP Tech Spenders):** 204 customers (17.0%), avg spend \$4,633.07, 22.0 orders, highest AOV (\$210.35).
      - **Cluster 2 (High-Activity Bargain Hunters):** 305 customers (25.4%), avg spend \$1,397.85, 190 web activities, 20.9 cart additions.
      - **Cluster 3 (At-Risk & Churned Customers):** 168 customers (14.0%), avg recency 291.7 days, 25.6% cancellation rate, negative sentiment (-0.653).
      - **Cluster 4 (Active Brand Advocates):** 175 customers (14.6%), 17.9 social interactions, highest sentiment (+0.818).

   ### 5.5 Personalized Recommendations & Association Mining
   1. **Hybrid Scoring Architecture:**
      - Implicit interaction scoring: $\text{Weight} = 5.0 \times \text{Purchases} + 2.5 \times \text{Cart Adds} + 1.0 \times \text{Views} + 1.5 \times \text{Wishlist}$.
      - Cosine item-item collaborative filtering matrix.
      - 541 Market Basket association rules mined with Support $\ge 0.01$ and Confidence $\ge 0.20$.
   2. **Empirical Performance Verification:**
      - **Hit Rate @ 5:** **76.0%** (0.7600) — independently reproduced from `recommendation_evaluation.csv`.
      - **Catalog Coverage:** **100.0%** (all 20 product catalog items actively recommended).
      - **Precision @ 5:** 0.3007 | **Recall @ 5:** 0.6110.
      - **Explainability:** 100% of generated recommendations include a plain-language justification narrative citing past purchases or market basket lift.

   ### 5.6 Supervised Customer Retention & Churn Prediction
   1. **Methodological Rigor:** Unlike unsupervised clustering, the churn module is a genuine supervised machine learning pipeline with strict temporal split:
      - Prediction Cutoff: `2024-10-01 00:00:00`.
      - Feature Window: 180 days prior to cutoff.
      - Observation Window: 90 days after cutoff.
      - Target: `churn_label = 1` if no completed orders in future window; `0` otherwise.
      - Eligible Cohort: 1,177 customers with pre-cutoff purchase history.
   2. **Model Evaluation Metrics (Random Forest vs Baseline):**
      - **ROC-AUC:** **0.9365** (vs 0.5000 baseline)
      - **PR-AUC:** **0.8660** (vs 0.2627 baseline)
      - **Recall:** **90.32%** (captures 56 of 62 actual churners in test set)
      - **Precision:** **61.54%** | **F1-Score:** **0.7320**
      - **Test Confusion Matrix:** True Negatives: 139, False Positives: 35, False Negatives: 6, True Positives: 56.
   3. **Actionable Retention:** Categorizes customers into Low Risk (57.5%), Medium Risk (23.0%), and High Risk (19.5%), outputting individualized intervention strategies.

   ### 5.7 Full-Stack Web Dashboard Verification
   All seven pages were inspected in the React application:
   1. **Overview Dashboard (`/`):** KPI cards (1,200 customers, 12,214 transactions, \$1.81M spend), monthly revenue trends, category breakdown, segment donut chart.
   2. **Customer Analytics (`/analytics`):** Clickstream acquisition channels, client device split, sentiment polarity distribution, platform engagement table.
   3. **Customer Segmentation (`/segmentation`):** 2D PCA cluster scatter plot, Silhouette & Elbow charts, Persona comparison table.
   4. **Customer 360 View (`/customers`):** Searchable customer directory with paginated table, individual transaction histories, clickstream events, and social sentiment timeline.
   5. **Personalized Recommendations (`/recommendations`):** Top 5 recommendation cards per customer with match scores, plain-language explainability, and association rules table.
   6. **Retention AI (`/churn`):** Churn probability gauge, confusion matrix visualization, feature importance bar chart, risk tier breakdowns.
   7. **Data Pipeline (`/pipeline`):** Live HDFS health badge, storage capacity gauges (Free/Used bytes), NameNode block status, PySpark execution summary.

   ---

   ## 6. End-to-End Reproducibility Audit (GitHub Readiness)

   | Check Item | Findings & Audit Evidence | Status |
   | :--- | :--- | :---: |
   | **1. Repository Structure** | Clean root layout: `big_data/`, `ml/`, `backend/`, `frontend/`, `data/`, `docs/`, `scripts/`, `tests/`. | **PASS** |
   | **2. Python Requirements** | `requirements.txt` specifies exact versions (PySpark 3.5.1, scikit-learn 1.5.0, pandas, flask). | **PASS** |
   | **3. Java Requirements** | Windows environment uses Java 8; WSL2 uses isolated Temurin OpenJDK 8. Zero collision. | **PASS** |
   | **4. Hadoop Requirements** | Automated installation scripts (`scripts/install_hadoop_wsl.sh`) install official Apache Hadoop 3.3.6. | **PASS** |
   | **5. HDFS Startup Scripts** | `scripts/run_hdfs_daemon.sh` and `scripts/start_hdfs_wsl.sh` provide one-command daemon startup. | **PASS** |
   | **6. Dataset Availability** | All raw CSVs exist in `data/raw/`; generation script `generate_datasets.py` provided for reproduction. | **PASS** |
   | **7. Model Artifact Availability** | Serialized models (`kmeans_model.pkl`, `churn_model.joblib`, recs JSON) are tracked and available. | **PASS** |
   | **8. Backend Startup** | Flask backend starts smoothly on port 5000 via `.venv/Scripts/python backend/app.py`. | **PASS** |
   | **9. Frontend Startup** | React frontend starts on port 3000 via `npm run dev` and builds cleanly via `npm run build`. | **PASS** |
   | **10. Complete Pipeline Run** | `python scripts/run_big_data_pipeline.py --storage hdfs` runs end-to-end without errors. | **PASS** |
   | **11. Environment Configuration** | Automated WSL IP resolution eliminates hardcoded network IPs. | **PASS** |
   | **12. Windows Compatibility** | WinUtils binaries included in project; PySpark runs natively on Windows with HDFS in WSL2. | **PASS** |
   | **13. External Dependencies** | Zero paid APIs, zero external database servers, zero proprietary cloud subscriptions required. | **PASS** |
   | **14. Hardcoded Local Paths** | Exactly 1 hardcoded path detected: line 7 in `scripts/upload_raw_to_hdfs.sh`. Zero in core code. | **MINOR POLISH** |
   | **15. Private Credentials** | Comprehensive regex scan confirmed **zero API keys, passwords, or secrets** in the repository. | **PASS** |

   ---

   ## 7. Academic Integrity, Terminology & Presentation Polish

   To ensure academic rigor during oral defense and external evaluation, the following terminology distinctions should be maintained:

   1. **Synthetic vs Real-World Data:**
      - *Current phrasing in some notes:* "Multi-source enterprise customer data".
      - *Academic reality:* The datasets are **statistically generated synthetic datasets** modeled after real e-commerce transactional, web, and social media distributions.
      - *Recommendation:* State clearly in presentations: *"The system is evaluated on a synthetic benchmark of 142,046 multi-source customer records designed to model enterprise e-commerce behavior."*
   2. **Single-Node HDFS vs Distributed Cluster:**
      - *Current phrasing:* "Hadoop Distributed File System".
      - *Academic reality:* Apache Hadoop 3.3.6 is deployed as a genuine **single-node HDFS cluster** inside WSL2.
      - *Recommendation:* Avoid calling it a "multi-machine cluster" or "cloud cluster". Emphasize that single-node HDFS uses the authentic HDFS protocol (RPC port 9000, DataNode block transfers) and proves distributed storage compatibility.
   3. **Batch vs Real-Time Processing:**
      - *Current phrasing in README line 3:* "delivers real-time analytics through a modular React dashboard".
      - *Academic reality:* The analytics pipeline is an offline **batch processing pipeline**; the React dashboard provides *interactive exploration* of the pre-computed batch results.
      - *Recommendation:* Describe the UI as an *"interactive dashboard for batch customer analytics"* to align with Review 2 Slide 5 (which explicitly excluded real-time streaming).
   4. **Dashboard Technology Evolution:**
      - *Original PPT mention:* Power BI / Tableau.
      - *Implemented:* React 18 + Flask web application.
      - *Recommendation:* Highlight this as an engineering enhancement that demonstrates custom software development and REST API integration rather than relying on a commercial BI tool.

   ---

   ## 8. Prioritized List of Remaining Work

   ### Critical (Must be done before submission)
   *None.* All primary project objectives, big data storage requirements, machine learning models, and visualization deliverables are 100% complete and working.

   ### Important (Recommended for final presentation polish)
   1. **Upload Script Relative Path:** Update line 7 of `scripts/upload_raw_to_hdfs.sh` from `DATA_DIR="/mnt/d/Infynux/big data project/data/raw"` to dynamically resolve `DATA_DIR="$(dirname "$0")/../data/raw"` for seamless cloning on different drive letters.
   2. **Presentation Deck Metrics Harmonization:** Ensure slide notes mention $K=5$ Silhouette score as `0.3451` (final optimized run) alongside the earlier trial score `0.3533`.

   ### Minor (Documentation & Cosmetic Polish)
   1. **README Phrasing Refinement:** Replace "delivers real-time analytics" with "delivers interactive analytics" in `README.md` line 3.
   2. **PPT Slide Deck:** Re-run `python scripts/generate_pptx.py` if an updated slide deck reflecting Stage 8 and Stage 9 HDFS achievements is desired.

   ---

   ## 9. Final Decision & Verdict

   ### Final Verdict: **READY FOR FINAL SUBMISSION**

   **Justification:**
   1. The project genuinely satisfies all core objectives from Review 0, Review 1, and Review 2.
   2. Genuine Apache Hadoop HDFS 3.3.6 and Apache Spark 3.5.1 are operational and verified with zero local fallback.
   3. Unsupervised segmentation (K-Means, $K=5$), personalized recommendations (76% Hit Rate@5), and supervised customer churn prediction (ROC-AUC 0.9365) are fully trained, evaluated, and documented.
   4. The full-stack React + Flask web application is active, responsive, and backed by a 100% passing test suite (20 unit tests, 20 API endpoints).
   5. The project runs reproducibly on standard hardware with zero proprietary dependencies.

