# Makefile for Customer Purchase Pattern Analyzer
# Supported targets: setup, pipeline, dashboard, test, clean

ifeq ($(OS),Windows_NT)
    VENV_BIN := .venv/Scripts
    EXE := .exe
else
    VENV_BIN := .venv/bin
    EXE :=
endif

PYTHON := $(if $(wildcard $(VENV_BIN)/python$(EXE)),$(VENV_BIN)/python$(EXE),python)
PYTEST := $(if $(wildcard $(VENV_BIN)/pytest$(EXE)),$(VENV_BIN)/pytest$(EXE),pytest)
STREAMLIT := $(if $(wildcard $(VENV_BIN)/streamlit$(EXE)),$(VENV_BIN)/streamlit$(EXE),streamlit)

.PHONY: help setup pipeline dashboard test clean

help:
	@echo "======================================================================"
	@echo "CUSTOMER PURCHASE PATTERN ANALYZER - COMMAND RUNNER"
	@echo "======================================================================"
	@echo "Available commands:"
	@echo "  make setup      - Install Python dependencies into .venv"
	@echo "  make pipeline   - Execute full end-to-end data & analytics pipeline"
	@echo "  make dashboard  - Launch interactive Streamlit executive dashboard"
	@echo "  make test       - Run complete test suite with pytest"
	@echo "  make clean      - Clean Python cache artifacts and temporary files"
	@echo "======================================================================"

setup:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

pipeline:
	$(PYTHON) src/run_pipeline.py

dashboard:
	$(STREAMLIT) run dashboard/app.py

test:
	$(PYTEST) -v --durations=10

clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('.pytest_cache')]"
