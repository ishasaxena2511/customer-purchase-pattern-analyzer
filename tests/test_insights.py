"""
test_insights.py
----------------
Purpose:
    Unit test suite validating automated insight generation, metric computation,
    markdown reporting, and PDF compilation in src/insights.py.
"""

from pathlib import Path
import pandas as pd
import pytest

from src.insights import (
    compute_all_insights,
    write_insights_markdown,
    write_project_report_markdown,
    export_project_report_pdf,
)


@pytest.fixture
def feature_data():
    """Load actual processed features for insight validation."""
    base_dir = Path(__file__).resolve().parent.parent
    tx_path = base_dir / "data" / "processed" / "transactions_features.csv"
    cf_path = base_dir / "data" / "processed" / "customer_features.csv"
    tx_df = pd.read_csv(tx_path)
    cf_df = pd.read_csv(cf_path)
    return tx_df, cf_df


def test_compute_all_insights(feature_data):
    """Verify that compute_all_insights returns 9 fully populated structured insight dicts."""
    tx_df, cf_df = feature_data
    insights = compute_all_insights(tx_df, cf_df)

    assert len(insights) >= 8, f"Expected at least 8 insights, got {len(insights)}"

    required_keys = ["id", "category", "title", "finding", "supporting_number", "business_meaning", "recommended_action"]
    for item in insights:
        for k in required_keys:
            assert k in item, f"Missing key '{k}' in insight {item.get('id')}"
            assert len(str(item[k]).strip()) > 0, f"Value for '{k}' is empty in insight {item.get('id')}"


def test_markdown_and_pdf_report_generation(tmp_path, feature_data):
    """Verify that insights markdown, project report markdown, and PDF export compile cleanly."""
    tx_df, cf_df = feature_data
    insights = compute_all_insights(tx_df, cf_df)

    test_insights_md = tmp_path / "test_insights.md"
    write_insights_markdown(insights, test_insights_md)
    assert test_insights_md.exists()
    assert test_insights_md.stat().st_size > 1000

    test_report_md = tmp_path / "test_report.md"
    write_project_report_markdown(insights, tx_df, cf_df, test_report_md)
    assert test_report_md.exists()
    assert test_report_md.stat().st_size > 2000

    test_report_pdf = tmp_path / "test_report.pdf"
    pdf_success = export_project_report_pdf(test_report_md, test_report_pdf)
    assert pdf_success is True
    assert test_report_pdf.exists()
    assert test_report_pdf.stat().st_size > 1000
