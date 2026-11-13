# Smart Customer Analysis and Personalized Experience Using Big Data

An end-to-end Big Data & Machine Learning system designed for academic demonstration, research evaluation, and reproducible customer behavioral analytics. The platform ingests multi-source customer datasets (sales transactions, website clickstream interactions, and social media sentiment feedback), runs distributed batch transformations via Apache Spark / PySpark, generates customer behavioral segments using K-Means clustering, computes explainable personalized recommendations via collaborative filtering and market basket association mining, and delivers real-time analytics through a modular React dashboard.

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/naveend07ec/Smart-Customer-Analysis-and-Personalized-Experience-Using-Big-Data)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.5.1-E25A1C?logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

---

## System Architecture

```
                    Multi-Source Raw Datasets
     ┌──────────────────────────┼──────────────────────────┐
     ▼                          ▼                          ▼
Sales Transactions      Website Clickstream       Social Media Sentiment
 (12,239 records)        (120,979 records)           (8,828 records)
     │                          │                          │
     └──────────────────────────┼──────────────────────────┘
                                ▼
           Storage & Ingestion Layer (HDFS / Staged Parquet)
                                ▼
          Distributed Big Data Processing (PySpark 3.5.1)
           - Primary key deduplication (dropDuplicates)
           - Imputation of missing payment methods ('Unknown')
           - Preservation of non-product navigation nulls
           - Customer-level aggregation across all 3 channels
           - Multi-source outer join on customer_id
                                ▼
           Unified Behavioral Feature Matrix (1,200 x 24)
                                ▼
     ┌──────────────────────────┴──────────────────────────┐
     ▼                                                     ▼
K-Means Segmentation (K=5)               Explainable Recommendation Engine
 - Elbow & Silhouette evaluation (0.3533)  - User-Item Collaborative Filtering
 - PCA 2D Dimensionality Reduction        - Market Basket Association Mining (541 rules)
 - 5 Distinct Behavioral Personas          - Transparent Reasoning & Confidence Scores
     │                                                     │
     └──────────────────────────┬──────────────────────────┘
                                ▼
                   Flask REST API Server (:5000)
                    - 15 verified analytics & ML endpoints
                    - Cached DataService with CORS enabled
                                ▼
                 Vite + React Dashboard (:3000)
    1. Overview Dashboard          4. Customer Details (360° View)
    2. Customer Analytics          5. Personalized Recommendations
    3. Customer Segmentation       6. Data Integration & Spark
```

---

## Technology Stack

- **Frontend**: React 18, Vite, JavaScript, CSS3, Chart.js, react-chartjs-2, Lucide Icons
- **Backend**: Python 3.11, Flask 3.1, Flask-CORS 6.0
- **Big Data Processing**: Apache Spark (PySpark 3.5.1), Java 8 JRE, WinUtils (Windows portability)
- **Machine Learning**: Scikit-learn 1.4, SciPy, Pandas, NumPy, Joblib
- **Target Hardware**: Lightweight architecture optimized to run on standard computers with 8 GB RAM.

---

## Directory Structure

```
.
├── backend/
│   ├── app/
│   │   ├── routes/           # 15 REST endpoints (overview, analytics, segmentation, customers, recs, pipeline)
│   │   ├── services/         # Cached DataService bridging data/ML outputs to HTTP
│   │   └── __init__.py       # Flask app factory with CORS
│   ├── app.py                # Flask server entrypoint (port 5000)
│   └── requirements.txt      # Python dependencies
├── big_data/
│   ├── ingestion/            # PySpark schemas and raw data ingestion
│   ├── preprocessing/        # PySpark cleaning, deduplication, missing value imputation
│   ├── feature_engineering/  # Customer RFM, clickstream, and sentiment aggregators
│   ├── spark_session.py      # Lightweight local[2] SparkSession config
│   └── run_pipeline.py       # End-to-end PySpark batch pipeline runner
├── data/
│   ├── raw/                  # Raw immutable synthetic datasets (transactions, web, social)
│   ├── processed/            # Cleaned tables & unified customer feature matrix (CSV & Parquet)
│   └── sample/               # Lightweight sample datasets for rapid testing
├── ml/
│   ├── segmentation/         # K-Means clustering, Elbow method, Silhouette & PCA scripts
│   ├── recommendations/      # Hybrid collaborative filtering & association rule mining
│   └── models/               # Serialized models, cluster profiles, and precomputed recommendations
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI widgets (Navbar, Sidebar, MetricCard)
│   │   ├── pages/            # 6 React analytics dashboard pages
│   │   ├── services/         # Axios API client
│   │   ├── App.jsx           # React Router
│   │   └── index.css         # Modern dark tech theme styling
│   ├── package.json
│   └── vite.config.js        # Vite dev server with proxy to Flask
├── scripts/
│   ├── generate_datasets.py  # Synthetic academic dataset generator
│   ├── validate_datasets.py  # Data quality & referential integrity validator
│   ├── run_pyspark_pipeline.ps1 # One-click PySpark pipeline execution
│   ├── start_backend.ps1     # One-click Flask backend launcher
│   ├── start_frontend.ps1    # One-click React frontend launcher
│   └── test_api.py           # Automated 15-endpoint API test suite
├── tools/hadoop/bin/         # Lightweight Windows winutils binaries (zero global config needed)
└── README.md
```

---

## Quick Start Guide

### Prerequisites
- **Python**: 3.10 or 3.11 (64-bit)
- **Node.js**: v18+ or v20+ with `npm`
- **Java**: Java 8 (JRE or JDK 64-bit)

### 1. Clone the Repository
```bash
git clone https://github.com/naveend07ec/Smart-Customer-Analysis-and-Personalized-Experience-Using-Big-Data.git
cd Smart-Customer-Analysis-and-Personalized-Experience-Using-Big-Data
```

### 2. Setup Python Virtual Environment & Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r backend/requirements.txt
```

### 3. Run the Big Data & ML Pipeline (Batch Processing)
Execute the PySpark pipeline to ingest raw CSVs, perform cleaning, compute the 24 customer features, and train the ML models:
```powershell
# Run PySpark Big Data Processing
.\.venv\Scripts\python.exe big_data\run_pipeline.py

# Run K-Means Customer Segmentation
.\.venv\Scripts\python.exe ml\segmentation\train_kmeans.py

# Run Explainable Recommendation Engine
.\.venv\Scripts\python.exe ml\recommendations\recommender.py
```
*(All verified outputs will be saved in `data/processed/` and `ml/models/`).*

### 4. Verify Backend REST API
Run the automated test suite to verify all 15 endpoints:
```powershell
.\.venv\Scripts\python.exe scripts\test_api.py
```

### 5. Launch the Application

#### Terminal 1 — Start Flask Backend Server:
```powershell
.\scripts\start_backend.ps1
# Or: .\.venv\Scripts\python.exe backend/app.py
```
*Backend runs on `http://127.0.0.1:5000`.*

#### Terminal 2 — Start React + Vite Frontend:
```powershell
.\scripts\start_frontend.ps1
# Or: cd frontend; npm run dev
```
*Frontend runs on `http://localhost:3000`.*

Open your browser and navigate to `http://localhost:3000`.

---

## Dashboard Pages

1. **Overview Dashboard** (`/`): Executive KPIs, monthly sales trajectory, category revenue contribution, customer segment share doughnut.
2. **Customer Analytics** (`/analytics`): Clickstream acquisition channels, client device types, sentiment polarity breakdown, and RFM distributions.
3. **Customer Segmentation** (`/segmentation`): K-Means evaluation (Silhouette: 0.3533, Davies-Bouldin: 1.1554), Elbow curve chart, 2D PCA interactive scatter plot, and behavioral centroid profiles.
4. **Customer Details (360° View)** (`/customers`): Searchable and filterable directory of 1,200 customers with individual purchase histories, browsing touchpoints, and social reviews.
5. **Personalized Recommendations** (`/recommendations`): Top 5 personalized products per customer with confidence scores ($0 - 100\%$) and plain-language reasoning, alongside Market Basket Association Rules (Lift up to 1.18x).
6. **Data Integration & Spark** (`/pipeline`): Detailed PySpark execution audit, deduplication and cleaning counts, schema documentation, and HDFS/staged storage architecture.

---

## Academic Verification & Reproducibility Note
All datasets in `data/raw/` are synthetic academic datasets generated with a fixed random seed (`42`) to guarantee 100% reproducibility. All displayed metrics across the React dashboard originate dynamically from the PySpark batch outputs and Scikit-learn model artifacts served via the Flask REST API.
