@echo off
setlocal EnableDelayedExpansion

echo ==============================================
echo   AI Fitness Platform -- Windows Setup
echo ==============================================
echo.

REM ── Navigate to project root (one level up from scripts\) ─────────────────
cd /d "%~dp0.."
echo Working directory: %CD%
echo.

REM ── Check Python ──────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ from python.org
    pause & exit /b 1
)

REM ── Create .env if missing ────────────────────────────────────────────────
if not exist ".env" (
    echo Creating .env from .env.example ...
    copy ".env.example" ".env" >nul
    echo.
    echo IMPORTANT: Open .env and set your GEMINI_API_KEY before continuing.
    echo Get a free key at: https://aistudio.google.com/app/apikey
    echo.
    notepad .env
    pause
)

REM ── Virtual environment ───────────────────────────────────────────────────
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Activated venv.
echo.

REM ── Install packages ──────────────────────────────────────────────────────
echo Installing Python packages...
pip install -r requirements.txt --quiet

REM ── Start Docker services ─────────────────────────────────────────────────
echo Starting Docker services (Postgres, Redis, InfluxDB, MinIO)...
docker compose up -d postgres redis influxdb minio
echo Waiting for services...
timeout /t 8 /nobreak >nul

REM ── Migrations + seed ─────────────────────────────────────────────────────
echo Running database migrations...
alembic upgrade head

echo Seeding demo data...
python scripts\seed_db.py

echo.
echo ==============================================
echo   API:       http://localhost:8000
echo   API docs:  http://localhost:8000/docs
echo   Demo login: demo@fitnessplatform.com
echo   Password:   Demo1234!
echo ==============================================
echo.
python main.py
