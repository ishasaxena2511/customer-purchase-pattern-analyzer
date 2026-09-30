"""
load_db.py
----------
Purpose:
    Loads processed transaction and customer analytical datasets into a structured
    SQLite database: data/processed/retail.db.
    
    Creates:
      - 'transactions' table (full transaction records with calendar & profitability features)
      - 'customers' table (360-degree customer profiles with RFM segments & CLV)
      - Performance indexes on primary lookup columns (Customer_ID, Purchase_Date, City, Region, Category)
"""

import os
import sqlite3
from typing import Tuple
import pandas as pd


def load_to_sqlite(
    trans_csv_path: str = "data/processed/transactions_features.csv",
    cust_csv_path: str = "data/processed/customer_features.csv",
    db_path: str = "data/processed/retail.db",
) -> Tuple[int, int]:
    """
    Ingest processed CSV data into SQLite database and create analytical indexes.
    
    Parameters:
        trans_csv_path: Path to transactions_features.csv
        cust_csv_path: Path to customer_features.csv
        db_path: Destination SQLite database file path
        
    Returns:
        Tuple of (transactions_row_count, customers_row_count)
    """
    if not os.path.exists(trans_csv_path):
        raise FileNotFoundError(f"Transactions dataset not found at {trans_csv_path}. Run features.py first.")
    if not os.path.exists(cust_csv_path):
        raise FileNotFoundError(f"Customer dataset not found at {cust_csv_path}. Run features.py and segmentation.py first.")
        
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    df_trans = pd.read_csv(trans_csv_path)
    df_cust = pd.read_csv(cust_csv_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print(f"Loading {len(df_trans)} transactions into '{db_path}' (table: transactions)...")
        df_trans.to_sql("transactions", conn, if_exists="replace", index=False)
        
        print(f"Loading {len(df_cust)} customer records into '{db_path}' (table: customers)...")
        df_cust.to_sql("customers", conn, if_exists="replace", index=False)
        
        # Create database indexes for optimized analytical queries
        print("Creating analytical performance indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_trans_cust_id ON transactions (Customer_ID);",
            "CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions (Purchase_Date);",
            "CREATE INDEX IF NOT EXISTS idx_trans_cat ON transactions (Product_Category);",
            "CREATE INDEX IF NOT EXISTS idx_trans_city ON transactions (City);",
            "CREATE INDEX IF NOT EXISTS idx_trans_region ON transactions (Region);",
            "CREATE INDEX IF NOT EXISTS idx_cust_id ON customers (Customer_ID);",
            "CREATE INDEX IF NOT EXISTS idx_cust_segment ON customers (RFM_Segment);",
        ]
        for idx_sql in indexes:
            cursor.execute(idx_sql)
            
        conn.commit()
        print(f"Database successfully updated at: {db_path}")
        
    finally:
        conn.close()
        
    return len(df_trans), len(df_cust)


if __name__ == "__main__":
    load_to_sqlite()
