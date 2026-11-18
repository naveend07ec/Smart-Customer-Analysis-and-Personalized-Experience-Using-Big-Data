"""
Supervised Customer Churn Prediction Module
Project: Smart Customer Analysis and Personalized Experience Using Big Data

Point-in-Time Prediction Architecture:
- Prediction Cutoff: 2024-10-01 00:00:00
- Historical Feature Window: 180 days prior to cutoff (2024-04-04 to 2024-10-01)
- Future Observation Window: 90 days after cutoff (2024-10-01 to 2024-12-30)
- Target: churn_label = 1 if no qualifying completed purchase in future window, else 0.
"""

