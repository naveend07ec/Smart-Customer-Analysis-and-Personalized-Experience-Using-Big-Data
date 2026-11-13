"""
Flask REST API Entry Point
Project: Smart Customer Analysis and Personalized Experience Using Big Data
"""

import os
import sys

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Flask REST API server on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
