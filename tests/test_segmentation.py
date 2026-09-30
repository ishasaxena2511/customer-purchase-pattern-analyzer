"""
test_segmentation.py
--------------------
Purpose:
    Unit test suite validating RFM scoring, behavioral segment mapping,
    unsupervised K-Means clustering, cluster profiling, and marketing actions.
"""

import os
import pandas as pd
import pytest

from src.segmentation import (
    compute_rfm_scores,
    map_rfm_segments,
    run_kmeans_clustering,
    profile_clusters,
    assign_marketing_actions,
    get_segment_size_table,
    SEGMENT_MARKETING_ACTIONS,
)


@pytest.fixture
def sample_cust_for_segmentation():
    """Provides a synthetic customer cohort across various spending and frequency profiles."""
    return pd.DataFrame([
        {
            "Customer_ID": f"C{i:03d}",
            "Customer_Name": f"Customer {i}",
            "Recency": int(rec),
            "Purchase_Frequency": int(freq),
            "Total_Revenue": float(rev),
            "Average_Order_Value": float(rev / freq),
            "Basic_CLV": float(rev * 3.0),
            "Customer_Segment": "Standard",
        }
        for i, (rec, freq, rev) in enumerate([
            (5, 25, 120000.0),  # Champion / VIP
            (10, 20, 85000.0),  # Champion
            (15, 15, 50000.0),  # Loyal
            (25, 12, 35000.0),  # Loyal
            (8, 2, 8000.0),     # Potential Loyalist
            (12, 1, 3000.0),    # New Customer
            (75, 14, 45000.0),  # Can't Lose Them
            (80, 5, 15000.0),   # At Risk
            (180, 2, 4000.0),   # Hibernating
            (250, 1, 1500.0),   # Hibernating
        ], start=1)
    ])


def test_compute_rfm_scores(sample_cust_for_segmentation):
    """Verify RFM quintile scores are bounded between 1 and 5."""
    df_scored = compute_rfm_scores(sample_cust_for_segmentation)
    
    assert "R_Score" in df_scored.columns
    assert "F_Score" in df_scored.columns
    assert "M_Score" in df_scored.columns
    assert df_scored["R_Score"].between(1, 5).all()
    assert df_scored["F_Score"].between(1, 5).all()
    assert df_scored["M_Score"].between(1, 5).all()


def test_map_rfm_segments(sample_cust_for_segmentation):
    """Verify mapped segments match allowed taxonomy."""
    valid_segments = set(SEGMENT_MARKETING_ACTIONS.keys())
    df_scored = compute_rfm_scores(sample_cust_for_segmentation)
    df_mapped = map_rfm_segments(df_scored)
    
    assert "RFM_Segment" in df_mapped.columns
    assert set(df_mapped["RFM_Segment"]).issubset(valid_segments)


def test_kmeans_clustering_and_plots(sample_cust_for_segmentation, tmp_path):
    """Verify K-Means clustering execution and diagnostic plot artifact generation."""
    img_dir = str(tmp_path / "images")
    df_clustered, meta = run_kmeans_clustering(sample_cust_for_segmentation, n_clusters=3, image_dir=img_dir)
    
    assert "Cluster" in df_clustered.columns
    assert "Cluster_Name" in df_clustered.columns
    assert df_clustered["Cluster"].nunique() == 3
    assert os.path.exists(meta["elbow_plot_path"])
    assert os.path.exists(meta["silhouette_plot_path"])


def test_profile_clusters(sample_cust_for_segmentation, tmp_path):
    """Verify cluster profiling calculations."""
    img_dir = str(tmp_path / "images")
    df_clustered, _ = run_kmeans_clustering(sample_cust_for_segmentation, n_clusters=3, image_dir=img_dir)
    profiles = profile_clusters(df_clustered)
    
    assert len(profiles) == 3
    assert "Size" in profiles.columns
    assert "Avg_Revenue" in profiles.columns
    assert profiles["Size"].sum() == len(sample_cust_for_segmentation)


def test_marketing_actions(sample_cust_for_segmentation):
    """Verify every customer row receives an actionable marketing strategy."""
    df_scored = compute_rfm_scores(sample_cust_for_segmentation)
    df_mapped = map_rfm_segments(df_scored)
    df_actions = assign_marketing_actions(df_mapped)
    
    assert "Marketing_Action" in df_actions.columns
    assert (df_actions["Marketing_Action"].str.len() > 10).all()
