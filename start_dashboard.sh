#!/bin/bash

# ILI Data Alignment System - Dashboard Startup Script
# This script starts the Streamlit dashboard

echo "=========================================="
echo "ILI Data Alignment System"
echo "Starting Dashboard..."
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if requirements are installed
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Some features (NLP, Agentic AI) require GOOGLE_API_KEY"
    echo "Create .env file with: GOOGLE_API_KEY=your_key_here"
    echo ""
fi

# Start Streamlit
echo "🚀 Starting dashboard..."
echo "Dashboard will open at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

streamlit run src/dashboard/app.py
