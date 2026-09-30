<#
.SYNOPSIS
    Cross-platform CLI helper script for Customer Purchase Pattern Analyzer.
.DESCRIPTION
    Provides targets: setup, pipeline, dashboard, test, clean.
    Automatically detects and prioritizes the project .venv environment.
.EXAMPLE
    .\run.ps1 pipeline
    .\run.ps1 test
    .\run.ps1 dashboard
#>

param (
    [Parameter(Position=0)]
    [ValidateSet("setup", "pipeline", "dashboard", "test", "clean", "help")]
    [string]$Target = "help"
)

$ErrorActionPreference = "Stop"

# Auto-detect project virtual environment
$PythonCmd = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
$PytestCmd = if (Test-Path ".\.venv\Scripts\pytest.exe") { ".\.venv\Scripts\pytest.exe" } else { "pytest" }
$StreamlitCmd = if (Test-Path ".\.venv\Scripts\streamlit.exe") { ".\.venv\Scripts\streamlit.exe" } else { "streamlit" }

switch ($Target) {
    "setup" {
        Write-Host "Setting up virtual environment & installing dependencies..." -ForegroundColor Cyan
        if (-not (Test-Path ".\.venv")) {
            python -m venv .venv
            $PythonCmd = ".\.venv\Scripts\python.exe"
            $PytestCmd = ".\.venv\Scripts\pytest.exe"
            $StreamlitCmd = ".\.venv\Scripts\streamlit.exe"
        }
        & $PythonCmd -m pip install --upgrade pip
        & $PythonCmd -m pip install -r requirements.txt
        Write-Host "Setup complete. Virtual environment ready in .\.venv" -ForegroundColor Green
    }
    "pipeline" {
        Write-Host "Running end-to-end analytics pipeline using $PythonCmd..." -ForegroundColor Cyan
        & $PythonCmd src/run_pipeline.py
    }
    "dashboard" {
        Write-Host "Launching Streamlit executive dashboard using $StreamlitCmd..." -ForegroundColor Cyan
        & $StreamlitCmd run dashboard/app.py
    }
    "test" {
        Write-Host "Running automated test suite using $PytestCmd..." -ForegroundColor Cyan
        & $PytestCmd -v
    }
    "clean" {
        Write-Host "Cleaning cache directories..." -ForegroundColor Yellow
        Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path . -Recurse -Directory -Filter ".pytest_cache" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Clean complete." -ForegroundColor Green
    }
    Default {
        Write-Host "======================================================================" -ForegroundColor Cyan
        Write-Host "CUSTOMER PURCHASE PATTERN ANALYZER - POWERSHELL RUNNER" -ForegroundColor Cyan
        Write-Host "======================================================================" -ForegroundColor Cyan
        Write-Host "Usage: .\run.ps1 <target>"
        Write-Host ""
        Write-Host "Targets:"
        Write-Host "  setup      - Install dependencies into .venv from requirements.txt"
        Write-Host "  pipeline   - Run complete pipeline (generate -> clean -> segment -> load -> insights)"
        Write-Host "  dashboard  - Launch the Streamlit dashboard on http://localhost:8501"
        Write-Host "  test       - Run pytest test suite"
        Write-Host "  clean      - Remove __pycache__ and pytest cache directories"
        Write-Host "======================================================================" -ForegroundColor Cyan
    }
}
