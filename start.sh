#!/bin/bash

echo "====================================================================="
echo "  SMART Big Data Platform - Starting Services..."
echo "====================================================================="

# Check venv
if [ ! -f ".venv/bin/python" ]; then
    echo "[ERROR] .venv not found. Run ./setup.sh first."
    exit 1
fi

# 1. Start Flask in background
echo "[1/2] Starting Flask Backend REST API on http://127.0.0.1:5000 ..."
.venv/bin/python backend/app.py > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend running (PID: $BACKEND_PID)"

# 2. Start Vite
echo "[2/2] Starting Vite React Frontend on http://localhost:3000 ..."
cd frontend
npm run dev

