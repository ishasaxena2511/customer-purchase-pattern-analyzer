"""
features.py
-----------
Purpose:
    Performs feature engineering on cleaned transaction data: computes RFM
    (Recency, Frequency, Monetary) metrics per customer, customer tenure,
    average order value, purchase intervals, and customer level aggregates.
"""

from typing import Tuple
import pandas as pd


def engineer_features(df_clean: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate customer-level features (RFM, tenure, etc.) and enrich transaction data."""
    pass


if __name__ == "__main__":
    pass
