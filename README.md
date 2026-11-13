# Smart Customer Analysis and Personalized Experience Using Big Data

An end-to-end Big Data & Machine Learning system designed for academic demonstration and reproducible customer behavioral analytics. The application ingests multi-source data (transactions, website interactions, social media sentiment), runs distributed batch transformations, generates customer behavioral segments via K-Means, computes explainable personalized product recommendations, and delivers live analytics through a modular React dashboard.

---

## System Architecture Overview

```
 Multi-Source Data
 (Transactions, Web Logs, Social Media)
                  │
                  ▼
   Storage & Ingestion Layer
   (HDFS / Structured File Store)
                  │
                  ▼
   Big Data Processing Layer
   (PySpark DataFrames & Batch Transformations)
                  │
                  ▼
   Feature Store & ML Pipeline
   (Customer Behavioral Features, K-Means Segmentation, Recommendations)
                  │
                  ▼
   Backend REST Service
   (Python Flask REST API)
                  │
                  ▼
   Frontend Dashboard
   (React + Vite + Chart.js)
```

---

## Directory Structure & Purpose

```
.
├── big_data/                 # Big data processing pipeline (PySpark & HDFS integration)
│   ├── ingestion/            # Dataset loading and HDFS storage ingestion
│   ├── preprocessing/        # Data cleaning, missing value handling, schema validation
│   └── feature_engineering/  # Customer RFM and engagement behavioral feature extraction
├── ml/                       # Machine Learning models & pipelines
│   ├── segmentation/         # K-Means clustering model training, elbow method, evaluation
│   ├── recommendations/      # Collaborative filtering / association rule mining engines
│   └── models/               # Persisted trained models and cluster profiles
├── data/                     # Data storage directory
│   ├── raw/                  # Original raw input datasets
│   ├── processed/            # PySpark-processed structured outputs
│   ├── hdfs_store/           # HDFS storage / simulated HDFS namespace for local setups
│   └── sample/               # Sample mini-datasets for quick local testing and verification
├── backend/                  # Flask REST API server
│   ├── app/
│   │   ├── routes/           # API endpoints (overview, segmentation, recommendations, etc.)
│   │   ├── services/         # Business logic layer interfacing processed data and ML
│   │   └── utils/            # Data formatting and helper utilities
│   ├── app.py                # Flask application entry point
│   └── requirements.txt      # Backend Python dependencies
├── frontend/                 # React (Vite) Analytics Dashboard
│   ├── public/               # Static public assets
│   └── src/
│       ├── components/       # Reusable UI components (Navbar, Sidebar, Metric Cards, Charts)
│       ├── pages/            # 6 Core Dashboard pages
│       │   ├── OverviewDashboard/
│       │   ├── CustomerAnalytics/
│       │   ├── CustomerSegmentation/
│       │   ├── CustomerDetails/
│       │   ├── PersonalizedRecommendations/
│       │   └── DataProcessing/
│       └── services/         # API integration layer
├── docs/                     # Project documentation, system diagrams, and reports
├── scripts/                  # Automation scripts for data pipeline execution
└── README.md                 # Project guide and execution manual
```

---

## Technology Stack

- **Frontend:** React 18+, Vite, JavaScript/TypeScript, CSS3, Chart.js / react-chartjs-2
- **Backend:** Python 3.11, Flask, Flask-CORS
- **Big Data:** Apache Spark (PySpark), Apache Hadoop / HDFS (local cluster or standalone single-node setup)
- **Machine Learning:** Scikit-learn (K-Means, metrics), SciPy/Pandas/NumPy
- **Target Hardware:** Lightweight architecture optimized for 8 GB RAM systems

