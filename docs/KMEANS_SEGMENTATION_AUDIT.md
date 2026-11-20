# SMART — Customer Segmentation Module: Comprehensive Audit Report

**Date**: 2026-11-19  
**Auditor**: Antigravity Autonomous Engineering Agent  
**Environment**: SMART Big Data & Customer Analytics Platform  
**Active Dataset Version**: `v_batch_20261118_131539_cb5c` (1,444 Customers)  
**Baseline Dataset Version**: `baseline` (1,200 Customers)  

---

## 1. Executive Summary & Objective

This audit evaluates the machine learning segmentation pipeline, mathematical evaluation metrics, cluster assignment integrity, PCA projections, and frontend visualization consistency across the SMART platform. The audit identifies root causes for observed UI discrepancies (e.g., K=5 labels on K=7 models, repeated "At-Risk & Churned Customers" legend labels, and hardcoded chart variance labels), provides reproducible evaluation benchmarks across $K \in [2, 8]$, and defines a controlled remediation plan.

---

## 2. Provenance of Active Datasets & Models

| Artifact Description | File Path | Record Count / Dimension | Provenance / Active Status |
| :--- | :--- | :--- | :--- |
| **Active Unified Features** | `data/processed/unified_customer_features.parquet` | 1,444 rows $\times$ 23 cols (22 numeric features + `customer_id`) | Active production dataset (`v_batch_20261118_131539_cb5c`). |
| **Active Customer Segments** | `data/processed/customer_segments.parquet` | 1,444 rows $\times$ 27 cols | Active production assignments containing `cluster_id` (0..6), `cluster_name`, `pca_x`, `pca_y`. |
| **Active Cluster Profiles** | `ml/models/cluster_profiles.json` | 7 clusters ($K=7$) | Active model profiles produced by `ModelTrainingService.train_kmeans`. |
| **Active Elbow Evaluation** | `ml/models/elbow_metrics.json` | 7 evaluated K values ($K \in [2, 8]$) | Produced during retraining on 1,444 customers. |
| **Active Fitted KMeans** | `ml/models/kmeans_model.joblib` | `KMeans(n_clusters=7, random_state=42)` | Serialized Scikit-learn estimator. |
| **Active Fitted Scaler** | `ml/models/scaler.joblib` | `StandardScaler()` fitted on 22 features | Serialized feature transformer. |
| **Active Fitted PCA** | `ml/models/pca_model.joblib` | `PCA(n_components=2, random_state=42)` | Fitted on 1,444 customer standardized features. |
| **Baseline Backup Features** | `data/_baseline_backup/unified_customer_features.parquet` | 1,200 rows $\times$ 23 cols | Immutable baseline reference (1,200 customers). |
| **Baseline Backup Profiles** | `ml/models/_baseline_backup/cluster_profiles.json` | 5 clusters ($K=5$) | Original baseline model profiles. |

---

## 3. Discovered Defects & Root Cause Analysis

### Defect 1: Discrepancy Between Plotted K Curve ($K=7$) and UI Headings ($K=5$)
* **Symptom**: The left chart plots an Elbow/Silhouette curve peaking at $K=7$ (Silhouette = 0.3493), and the model has 7 clusters. However, page headers and subtitles explicitly say *"Unsupervised K-Means clustering (K=5)"* and *"Detailed Cluster Behavioral Centroids (K=5)"*.
* **Root Cause**: The React component (`CustomerSegmentation.jsx`) had static strings hardcoded (`K=5`) originally written for the 1,200-customer baseline. When the dataset was expanded to 1,444 customers and retrained, `ModelTrainingService.train_kmeans` selected $K=7$ via `argmax(silhouette_score)`. The frontend did not bind its header to the active model's `metrics.selected_k`.

### Defect 2: Duplicate Persona Labels in Legend and Cluster Profiles
* **Symptom**: The 2D PCA legend repeated the label `"At-Risk & Churned Customers"` three separate times.
* **Root Cause**: In `ModelTrainingService.train_kmeans` (lines 148–167), cluster naming was handled via a sequential `if/elif` structure with fixed heuristic thresholds:
  ```python
  if spend > 2500 and sentiment > 0.3:
      name = "High-Value VIP Tech Spenders"
  elif recency > 180:
      name = "At-Risk & Churned Customers"
  elif social_acts > 8 and sentiment > 0.4:
      name = "Active Brand Advocates & Influencers"
  elif web_acts > 100:
      name = "High-Activity Bargain Hunters"
  else:
      name = "Casual & Occasional Shoppers"
  ```
  When $K=7$, three distinct clusters (Cluster 1, Cluster 2, and Cluster 5) all satisfied `recency > 180`. Consequently, all three were assigned the exact same string `"At-Risk & Churned Customers"`, despite having fundamentally different behaviors:
  - **Cluster 1 (70 custs)**: Characterized by an extreme **cancellation rate of 69.4%** and negative sentiment ($-0.40$).
  - **Cluster 2 (65 custs)**: Characterized by **dormant / zero-activity accounts** (spend $\$11.60$, web touchpoints $1.26$, recency $331$ days).
  - **Cluster 5 (124 custs)**: Characterized by **long-term churned buyers** with severe negative sentiment ($-0.63$).

### Defect 3: Fixed 5-Color Palette in Frontend
* **Symptom**: Clusters beyond ID 4 fell back to a default blue color (`#6E9FCB`), causing multiple clusters in the PCA scatter plot to appear visually merged.
* **Root Cause**: `CustomerSegmentation.jsx` defined a dictionary `clusterColors` containing only 5 color keys (0 to 4). It lacked an extensible palette or backend-provided colors.

### Defect 4: Hardcoded PCA Axis Variances and Truncated Customer Scatter
* **Symptom**: The PCA chart displayed `Principal Component 1 (40.85% Variance)` and `Principal Component 2 (16.11% Variance)` in its axis titles, and `2D PCA Projection (1,200 Customers)`.
* **Root Cause**:
  1. The axis labels in `CustomerSegmentation.jsx` had static text strings `"40.85%"` and `"16.11%"` from the baseline 1,200 model. In the active 1,444 model, the actual explained variance ratios are **41.80% (PC1)** and **14.38% (PC2)**.
  2. The API route `/api/segmentation/pca-scatter` had a default parameter `limit=1200`, and the frontend called `api.getPCAScatter(1200)`, truncating 244 customers from the scatter plot visualization.

### Defect 5: Missing Quality Metrics in Backend Evaluation Payload
* **Symptom**: The Calinski-Harabasz score was missing from `metrics` in `cluster_profiles.json`, and Davies-Bouldin was named `davies_bouldin` in one endpoint and `davies_bouldin_index` in another.
* **Root Cause**: `ModelTrainingService.train_kmeans` did not serialize `calinski_harabasz_score` or `pca_explained_variance_ratio` into `profiles_payload["metrics"]`.

---

## 4. Reproducible Evaluation Benchmarks ($K=2$ to $8$)

Evaluated on the exact same 22 standardized features (StandardScaler, `random_state=42`, `n_init=10`, `customer_id` excluded):

### A. Active Production Dataset (1,444 Customers)
| K | Inertia (WCSS) | Silhouette Score | Davies-Bouldin Index | Calinski-Harabasz Score | Non-Empty Clusters | Cluster Customer Distribution |
| :-: | :-: | :-: | :-: | :-: | :-: | :--- |
| **2** | 20,439.88 | 0.3352 | 1.2654 | 799.18 | 2 | `[742, 702]` |
| **3** | 17,039.21 | 0.3147 | 1.2466 | 622.80 | 3 | `[411, 701, 332]` |
| **4** | 14,339.14 | 0.3176 | 1.3565 | 583.43 | 4 | `[512, 411, 332, 189]` |
| **5** | 12,558.26 | 0.3246 | 1.2510 | 550.29 | 5 | `[196, 512, 327, 220, 189]` |
| **6** | 10,918.46 | 0.3478 | 1.1607 | 549.19 | 6 | `[220, 66, 196, 446, 189, 327]` |
| **7** | **10,169.65** | **0.3493** | **1.1912** | **508.65** | **7** | `[196, 70, 65, 219, 442, 124, 328]` |
| **8** | 9,553.61 | 0.3229 | 1.2415 | 477.01 | 8 | `[196, 86, 328, 219, 71, 48, 121, 375]` |

* **Analysis**:
  - **Inertia Elbow**: A prominent rate-of-decay change occurs around $K=4$ and $K=5$, followed by another elbow at $K=6$ and $K=7$.
  - **Silhouette Peak**: Silhouette score peaks at **$K=7$ ($0.3493$)**, closely followed by **$K=6$ ($0.3478$)**.
  - **Davies-Bouldin**: Minimum (best compactness) is achieved at $K=6$ ($1.1607$) and $K=7$ ($1.1912$).

### B. Baseline Reference Dataset (1,200 Customers)
| K | Inertia (WCSS) | Silhouette Score | Davies-Bouldin Index | Calinski-Harabasz Score | Non-Empty Clusters | Cluster Customer Distribution |
| :-: | :-: | :-: | :-: | :-: | :-: | :--- |
| **2** | 17,452.15 | 0.3239 | 1.3205 | 614.22 | 2 | `[517, 683]` |
| **3** | 14,038.41 | 0.3150 | 1.2405 | 527.01 | 3 | `[516, 378, 306]` |
| **4** | 11,234.19 | 0.3365 | 1.2481 | 538.19 | 4 | `[350, 376, 306, 168]` |
| **5** | **9,612.77** | **0.3451** | **1.1759** | **521.72** | **5** | `[348, 204, 305, 168, 175]` |
| **6** | 8,990.12 | 0.3416 | 1.2824 | 462.45 | 6 | `[175, 347, 305, 114, 204, 55]` |
| **7** | 8,587.49 | 0.3428 | 1.2433 | 412.43 | 7 | `[54, 175, 305, 204, 106, 22, 334]` |
| **8** | 8,211.03 | 0.2759 | 1.4495 | 377.21 | 8 | `[20, 161, 305, 175, 109, 52, 174, 204]` |

* **Key Takeaway**: In the original baseline (1,200 customers), $K=5$ was unanimously optimal across both Silhouette ($0.3451$) and Davies-Bouldin ($1.1759$). In the expanded 1,444 customer universe, $K=7$ achieves the highest Silhouette ($0.3493$). The application must transparently reflect whichever $K$ is active in the model.

---

## 5. Authoritative Cluster-to-Persona Mapping Specification

To eliminate duplicate persona labels while preserving behavioral rigor, the cluster naming logic is refined to map every cluster ID to a distinct business segment:

| Cluster ID | Customer Count | Share (%) | Centroid Behavior | Authoritative Persona Name | Hex Color | Description |
| :-: | :-: | :-: | :--- | :--- | :--- | :--- |
| **0** | 196 | 13.57% | Social acts $18.1$, Sentiment $+0.79$, Spend $\$1,198$ | **Active Brand Advocates & Influencers** | `#A394BF` | High brand affinity, top viral reach, consistent purchase frequency. |
| **1** | 70 | 4.85% | Cancellation rate **69.4%**, Recency $320$d, Sentiment $-0.40$ | **High-Friction Cancelled Accounts** | `#E57373` | Extreme order cancellation rate and checkout friction requiring operational review. |
| **2** | 65 | 4.50% | Spend $\$11.60$, Web acts $1.3$, Recency $331$d | **Dormant & Inactive Registrations** | `#90A4AE` | Inactive accounts with near-zero web touchpoints and no purchases for 11+ months. |
| **3** | 219 | 15.17% | Spend $\$4,864$, Transactions $22.1$, AOV $\$220$ | **High-Value VIP Tech Spenders** | `#D0A16E` | Top revenue contributors, highest basket size, frequent purchases. |
| **4** | 442 | 30.61% | Spend $\$433$, Transactions $3.4$, Recency $147$d | **Casual & Occasional Shoppers** | `#6E96CE` | Standard basket size, moderate purchase intervals, balanced sentiment. |
| **5** | 124 | 8.59% | Recency $311$d, Sentiment **$-0.63$**, Spend $\$451$ | **At-Risk & Lapsed Churned Customers** | `#C77F83` | Previously active customers with severe negative sentiment and long inactivity. |
| **6** | 328 | 22.71% | Web acts **$191.2$**, Transactions $12.1$, Spend $\$1,405$ | **High-Activity Bargain Hunters** | `#70AFA6` | High session volume, deal-oriented browsing, frequent low-basket checkouts. |

* **Verification of Mathematical Invariants**:
  - $\sum \text{Customer Counts} = 196 + 70 + 65 + 219 + 442 + 124 + 328 = 1,444$ ($100\%$ coverage, $0$ missing, $0$ duplicates).
  - $\sum \text{Percentages} = 13.57 + 4.85 + 4.50 + 15.17 + 30.61 + 8.59 + 22.71 = 100.00\%$.
  - Bijective mapping: Each cluster ID maps to exactly 1 persona name; each persona name maps to exactly 1 cluster ID.

---

## 6. PCA 2D Transformation Verification

* **Input**: Standardized 22 behavioral features for all 1,444 customers.
* **Component 1 (PC1)**: Captures **41.80%** of total dataset variance (monetary spend, transaction frequency, cart additions, session count).
* **Component 2 (PC2)**: Captures **14.38%** of total dataset variance (social interactions, sentiment polarity, dwell time).
* **Cumulative Explained Variance**: **56.18%**.
* **Scatter Points**: 1,444 distinct customer projections with no duplicate keys.

---

## 7. Controlled Remediation Plan

1. **Backend Standardization**:
   - Update `ModelTrainingService.train_kmeans` to calculate and export `calinski_harabasz_score`, `pca_explained_variance_ratio`, `non_empty_clusters`, and cluster-specific `color` and `description`.
   - Implement the multi-tier disambiguated persona naming logic to guarantee unique segment names.
   - Update `DataService.get_pca_scatter` to accept `limit=None` and return all active customer points.
   - Update `/api/segmentation/` and `/api/segmentation/evaluation` responses to include version provenance.
2. **Frontend UI Remediation**:
   - Make all cluster count references dynamic: `selected_k` and `clusters.length` instead of hardcoded `K=5`.
   - Dynamically bind PCA axis titles to actual `pca_explained_variance_ratio` percentages.
   - Dynamically display actual customer count in the PCA chart title.
   - Provide an extensible 10-color palette matching backend cluster assignments.
   - Add concise, academically accurate metric explanation cards for **Inertia (WCSS)**, **Silhouette Score**, **Davies-Bouldin Index**, and **2D PCA Projection**.
   - Accurately describe Silhouette $\approx 0.35$ as moderate/robust separation without unsupported universal claims.
3. **Automated Verification**:
   - Author a test suite verifying all 15 audit criteria (K=2..8 evaluation, unique persona names, bijective mapping, PCA point counts, variance ratios, and zero regressions).
4. **Documentation**:
   - Finalize `docs/KMEANS_SEGMENTATION_AUDIT.md` and `docs/KMEANS_SEGMENTATION_REMEDIATION.md`.

