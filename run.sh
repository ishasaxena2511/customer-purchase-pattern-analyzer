#!/usr/bin/env bash
# run.sh - CLI launcher for Customer Purchase Pattern Analyzer
# Usage: ./run.sh [setup|pipeline|dashboard|test|clean]

set -e

# Detect local virtual environment if present
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
    PYTEST=".venv/bin/pytest"
    STREAMLIT=".venv/bin/streamlit"
elif [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
    PYTEST=".venv/Scripts/pytest.exe"
    STREAMLIT=".venv/Scripts/streamlit.exe"
else
    PYTHON="python"
    PYTEST="pytest"
    STREAMLIT="streamlit"
fi

COMMAND="${1:-help}"

case "$COMMAND" in
    setup)
        echo "Setting up virtual environment & installing dependencies..."
        if [ ! -d ".venv" ]; then
            python -m venv .venv
            if [ -f ".venv/bin/python" ]; then
                PYTHON=".venv/bin/python"
            else
                PYTHON=".venv/Scripts/python.exe"
            fi
        fi
        $PYTHON -m pip install --upgrade pip
        $PYTHON -m pip install -r requirements.txt
        echo "Setup complete. Virtual environment ready."
        ;;
    pipeline)
        echo "Running end-to-end analytics pipeline using $PYTHON..."
        $PYTHON src/run_pipeline.py
        ;;
    dashboard)
        echo "Launching Streamlit executive dashboard using $STREAMLIT..."
        $STREAMLIT run dashboard/app.py
        ;;
    test)
        echo "Running automated test suite using $PYTEST..."
        $PYTEST -v
        ;;
    clean)
        echo "Cleaning cache files..."
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
        echo "Clean complete."
        ;;
    help|*)
        echo "======================================================================"
        echo "CUSTOMER PURCHASE PATTERN ANALYZER - RUN SCRIPT"
        echo "======================================================================"
        echo "Usage: ./run.sh <command>"
        echo ""
        echo "Commands:"
        echo "  setup      - Install dependencies into .venv from requirements.txt"
        echo "  pipeline   - Run complete pipeline (generate -> clean -> segment -> load -> insights)"
        echo "  dashboard  - Launch the Streamlit dashboard on http://localhost:8501"
        echo "  test       - Run pytest test suite"
        echo "  clean      - Remove __pycache__ and pytest cache directories"
        echo "======================================================================"
        ;;
esac
