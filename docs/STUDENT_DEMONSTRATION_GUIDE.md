# SMART Project — Student Demonstration & Operations Guide
**Project Title:** Smart Customer Analysis and Personalized Experience Using Big Data  
**Target Audience:** Students, Evaluators, Academic Reviewers  
**Platform Architecture:** React 18 + Vite | Flask 3.1 REST API | PySpark 3.5.1 (`local[2]`) | Hadoop 3.3.6 HDFS | Scikit-Learn

See complete details in [docs/STUDENT_PROJECT_DEMONSTRATION_GUIDE.md](file:///d:/Infynux/big%20data%20project/docs/STUDENT_PROJECT_DEMONSTRATION_GUIDE.md).

---

## 1. Quick-Start Demonstration Steps

1. **Access Data Pipeline:** Navigate to `/pipeline` in the browser (`http://localhost:3000/pipeline`).
2. **Multi-Format Upload:** Select Multi-Format Ingestion mode, drag and drop CSV, JSON, JSONL, TXT, or LOG files, and click **Stage & Discover Batch**.
3. **Inspect Schema & Map Fields:** Open the **Active Batch Files Registry**, click **Map Fields**, review inferred types and sample records, map to canonical targets, and save.
4. **Commit to HDFS:** Click **2. Commit to HDFS** to store original bytes in `/customer-analytics/raw/uploads/<batch_id>/`.
5. **Run PySpark Processing:** Click **3. Run PySpark Batch** to clean data and generate the unified 23-column customer feature matrix.
6. **Retrain ML Models:** Click **4. Retrain Models** to train K-Means, Recommender, and Churn models, comparing benchmarks against baseline.
7. **Preview Analytics & Promotion/Rollback:** Inspect analytics in the preview modal; click **Promote** to make it active, or **Rollback to Baseline** to restore original data.
8. **Export Data:** Use the **Data Export & Canonical Templates Center** to download templates, raw files, processed datasets, and telemetry reports.

