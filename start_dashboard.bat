@echo off
REM ILI Data Alignment System - Dashboard Startup Script (Windows)
REM This script starts the Streamlit dashboard

echo ==========================================
echo ILI Data Alignment System
echo Starting Dashboard...
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if requirements are installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Check if .env file exists
if not exist .env (
    echo Warning: .env file not found
    echo Some features (NLP, Agentic AI) require GOOGLE_API_KEY
    echo Create .env file with: GOOGLE_API_KEY=your_key_here
    echo.
)

REM Start Streamlit
echo Starting dashboard...
echo Dashboard will open at: http://localhost:8501
echo.
echo Press Ctrl+C to stop
echo.

streamlit run src/dashboard/app.py
