"""
run_pipeline.py
---------------
Purpose:
    Master orchestration script that executes the complete retail analytics pipeline
    in sequential order:
      1. Data Generation  (generate realistic synthetic transaction dataset)
      2. Data Cleaning    (handle missing values, outliers, typos, and formatting)
      3. Feature Eng      (calculate transaction-level & customer-level metrics)
      4. Segmentation     (RFM quintiles + K-Means clustering + marketing actions)
      5. Database Loading (load into SQLite retail.db and run verification queries)
      6. Insights & Reps  (generate reports/insights.md, Project_Report.md & PDF)

Logging:
    Uses standard library `logging` configured for high-visibility terminal output
    and optional log persistence.

Execution:
    python src/run_pipeline.py
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import pipeline stage modules
from src.generate_data import generate_raw_dataset
from src.clean_data import clean_dataset
from src.features import engineer_features
from src.segmentation import run_segmentation
from src.load_db import load_to_sqlite
from src.run_sql import execute_analytical_queries
from src.metrics import print_headline_summary
from src.insights import main as generate_insights_and_reports

# Configure logging
LOG_DIR = BASE_DIR / "reports"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger("RetailPipeline")


def run_pipeline(force_generate: bool = True) -> bool:
    """
    Execute complete end-to-end customer purchase pattern pipeline.
    
    Args:
        force_generate (bool): If True, regenerates the raw data from scratch
                               with fixed seed 42 to guarantee a clean state.
                               
    Returns:
        bool: True if pipeline completed without errors.
    """
    logger.info("=" * 70)
    logger.info("STARTING CUSTOMER PURCHASE PATTERN ANALYTICS PIPELINE")
    logger.info("=" * 70)
    pipeline_start = time.time()

    try:
        # -------------------------------------------------------------
        # Stage 1: Generate Raw Data
        # -------------------------------------------------------------
        t0 = time.time()
        raw_csv_path = BASE_DIR / "data" / "raw" / "customer_purchases_raw.csv"
        logger.info("[Stage 1/6] Generating synthetic raw customer transaction dataset...")
        
        if force_generate or not raw_csv_path.exists():
            df_raw = generate_raw_dataset(output_path=str(raw_csv_path), seed=42)
            logger.info(
                f"✓ Raw dataset generated successfully: {df_raw.shape[0]} rows, "
                f"{df_raw.shape[1]} columns -> {raw_csv_path.name} ({time.time() - t0:.2f}s)"
            )
        else:
            logger.info(f"✓ Existing raw dataset verified at {raw_csv_path.name} ({time.time() - t0:.2f}s)")

        # -------------------------------------------------------------
        # Stage 2: Clean Data & Audit Quality Defects
        # -------------------------------------------------------------
        t0 = time.time()
        logger.info("[Stage 2/6] Executing data cleaning & quality remediation pipeline...")
        clean_df, audit = clean_dataset()
        logger.info(
            f"✓ Data cleaning complete: {clean_df.shape[0]} valid transactions, "
            f"{clean_df.shape[1]} columns ({time.time() - t0:.2f}s)"
        )
        dropped_total = sum(s.get("rows_dropped", 0) for s in audit.step_logs)
        modified_total = sum(s.get("values_modified", 0) for s in audit.step_logs)
        logger.info(
            f"  - Cleaning steps executed: {len(audit.step_logs)} | "
            f"Total rows dropped: {dropped_total} | "
            f"Values imputed/standardized: {modified_total}"
        )

        # -------------------------------------------------------------
        # Stage 3: Feature Engineering
        # -------------------------------------------------------------
        t0 = time.time()
        logger.info("[Stage 3/6] Generating transactional and customer-level features...")
        tx_df, cust_df = engineer_features()
        logger.info(
            f"✓ Feature engineering complete: {tx_df.shape[0]} transactional rows, "
            f"{cust_df.shape[0]} customer records ({time.time() - t0:.2f}s)"
        )

        # -------------------------------------------------------------
        # Stage 4: Customer Segmentation (RFM + K-Means)
        # -------------------------------------------------------------
        t0 = time.time()
        logger.info("[Stage 4/6] Executing RFM quintile scoring and K-Means clustering (k=4)...")
        segmented_cust_df, cluster_profiles = run_segmentation()
        logger.info(
            f"✓ Segmentation complete: {len(segmented_cust_df)} customers segmented into "
            f"{segmented_cust_df['RFM_Segment'].nunique()} RFM cohorts and "
            f"{segmented_cust_df['Cluster'].nunique()} K-Means clusters ({time.time() - t0:.2f}s)"
        )

        # -------------------------------------------------------------
        # Stage 5: Relational Database Loading (SQLite)
        # -------------------------------------------------------------
        t0 = time.time()
        logger.info("[Stage 5/6] Loading processed datasets into SQLite relational database...")
        n_tx, n_cust = load_to_sqlite()
        execute_analytical_queries(verbose=False)
        logger.info(
            f"✓ SQLite database synced: data/processed/retail.db ({n_tx} transactions, "
            f"{n_cust} customers, 8 analytical queries verified) ({time.time() - t0:.2f}s)"
        )

        # Print headline metrics for verification
        print_headline_summary(tx_df, segmented_cust_df)

        # -------------------------------------------------------------
        # Stage 6: Automated Insights & Executive Reporting
        # -------------------------------------------------------------
        t0 = time.time()
        logger.info("[Stage 6/6] Synthesizing data-driven insights and compiling executive reports...")
        generate_insights_and_reports()
        logger.info(
            f"✓ Reports generated: reports/insights.md, reports/Project_Report.md, "
            f"reports/Project_Report.pdf ({time.time() - t0:.2f}s)"
        )

        # -------------------------------------------------------------
        # Pipeline Complete
        # -------------------------------------------------------------
        total_time = time.time() - pipeline_start
        logger.info("=" * 70)
        logger.info(f"✅ PIPELINE EXECUTED SUCCESSFULLY IN {total_time:.2f} SECONDS")
        logger.info("=" * 70)
        logger.info("Next steps:")
        logger.info("  - Run automated tests:       pytest -v")
        logger.info("  - Launch Streamlit dashboard: streamlit run dashboard/app.py")
        return True

    except Exception as e:
        logger.exception(f"❌ PIPELINE EXECUTION FAILED: {str(e)}")
        return False


def main():
    """Parse CLI options and trigger the end-to-end analytics pipeline."""
    parser = argparse.ArgumentParser(
        description="Run the end-to-end Customer Purchase Pattern Analyzer analytics pipeline."
    )
    parser.add_argument(
        "--keep-raw",
        action="store_true",
        help="Skip regenerating raw data if customer_purchases_raw.csv already exists.",
    )
    args = parser.parse_args()

    success = run_pipeline(force_generate=not args.keep_raw)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
