#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

echo "=============================================="
echo "  AI Fitness Platform — Local Dev Setup"
echo "=============================================="
echo

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found"; exit 1
fi

# Auto-create .env if missing
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
    echo "IMPORTANT: Add your GEMINI_API_KEY to .env"
    echo "Get a free key at: https://aistudio.google.com/app/apikey"
    echo
fi

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
echo "Activated venv."

pip install -r requirements.txt --quiet

docker compose up -d postgres redis influxdb minio
echo "Waiting for services..."
sleep 8

alembic upgrade head
python scripts/seed_db.py

echo
echo "=============================================="
echo "  API:       http://localhost:8000"
echo "  API docs:  http://localhost:8000/docs"
echo "  Demo:      demo@fitnessplatform.com / Demo1234!"
echo "=============================================="
echo
python main.py
