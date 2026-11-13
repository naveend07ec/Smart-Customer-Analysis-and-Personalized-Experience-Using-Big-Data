"""
Automated Backend REST API Test Suite
Project: Smart Customer Analysis and Personalized Experience Using Big Data
"""

import os
import sys

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import create_app


def run_tests():
    print("=" * 70)
    print("STARTING FLASK REST API VERIFICATION TESTS")
    print("=" * 70)

    app = create_app()
    app.testing = True
    client = app.test_client()

    endpoints = [
        ("/api/health", 200, "Health Check"),
        ("/api/overview/kpis", 200, "Overview KPIs"),
        ("/api/overview/segment-distribution", 200, "Segment Distribution"),
        ("/api/overview/revenue-by-category", 200, "Revenue by Category"),
        ("/api/overview/monthly-trends", 200, "Monthly Trends"),
        ("/api/analytics/channel-attribution", 200, "Channel Attribution"),
        ("/api/analytics/sentiment-analysis", 200, "Sentiment Analysis"),
        ("/api/analytics/rfm-distributions", 200, "RFM Distributions"),
        ("/api/segmentation/evaluation", 200, "Segmentation Evaluation"),
        ("/api/segmentation/pca-scatter?limit=100", 200, "PCA 2D Scatter"),
        ("/api/customers?page=1&pageSize=10", 200, "Paginated Customers"),
        ("/api/customers/CUST_0001", 200, "Customer 360 Detail"),
        ("/api/recommendations/CUST_0001", 200, "Personalized Recommendations"),
        ("/api/recommendations/rules?limit=10", 200, "Association Rules"),
        ("/api/pipeline/summary", 200, "Pipeline Execution Summary")
    ]

    passed = 0
    failed = 0

    for path, expected_code, name in endpoints:
        resp = client.get(path)
        if resp.status_code == expected_code:
            passed += 1
            data = resp.get_json()
            data_preview = str(data)[:60] + "..." if data else "empty"
            print(f"  [PASS] {name:<30} ({path:<35}) -> {resp.status_code} | {data_preview}")
        else:
            failed += 1
            print(f"  [FAIL] {name:<30} ({path:<35}) -> {resp.status_code} (Expected {expected_code})")

    print("\n" + "=" * 70)
    print(f"API TESTS COMPLETED: {passed} PASSED, {failed} FAILED.")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
