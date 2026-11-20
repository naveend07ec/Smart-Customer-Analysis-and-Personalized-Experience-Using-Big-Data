#!/bin/bash
set -e

echo "====================================================================="
echo "  SMART Big Data Customer Analytics - Linux/macOS Setup Script"
echo "====================================================================="
echo ""

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed. Please install Python 3.10+."
    exit 1
fi
echo "[OK] Python detected: $(python3 --version)"

# 2. Check Node & npm
if ! command -v npm &> /dev/null; then
    echo "[ERROR] npm is not installed. Please install Node.js (v18+)."
    exit 1
fi
echo "[OK] Node.js detected: $(node --version)"

# 3. Check Java
if ! command -v java &> /dev/null; then
    echo "[WARNING] java not found in PATH. PySpark requires OpenJDK 8 or 11."
else
    echo "[OK] Java runtime detected: $(java -version 2>&1 | head -n 1)"
fi

# 4. Create venv
if [ ! -d ".venv" ]; then
    echo "[INFO] Creating virtual environment .venv..."
    python3 -m venv .venv
fi
echo "[OK] Virtual environment ready."

# 5. Install Python dependencies
echo "[INFO] Installing Python dependencies..."
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet
echo "[OK] Python packages installed."

# 6. Install npm packages
echo "[INFO] Installing Frontend npm dependencies..."
cd frontend
npm install --silent
cd ..
echo "[OK] Frontend packages installed."

# 7. Environment file
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[OK] Created .env configuration file."
fi

echo ""
echo "====================================================================="
echo "  SETUP COMPLETED SUCCESSFULLY!"
echo "  To launch: ./start.sh"
echo "  Or manually:"
echo "    Backend:  .venv/bin/python backend/app.py"
echo "    Frontend: cd frontend && npm run dev"
echo "====================================================================="

