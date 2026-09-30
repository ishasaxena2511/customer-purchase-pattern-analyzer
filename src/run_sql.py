"""
run_sql.py
----------
Purpose:
    Executes all analytical business intelligence SQL queries from sql/queries.sql
    against the SQLite database: data/processed/retail.db.
    
    Displays formatted query output tables in the terminal and returns a dictionary
    of tidy pandas DataFrames for programmatic pipeline integration and testing.
"""

import os
import sqlite3
import sys
from typing import Dict, List, Tuple
import pandas as pd

QUERY_NAMES: List[str] = [
    "1. Total Spend and Order Count per Customer",
    "2. Top 5 Cities by Sales Volume (with Running Total)",
    "3. Monthly Revenue Trend (with MoM Growth % & Cumulative YTD)",
    "4. Revenue by Category and Region (with Regional & Total Share)",
    "5. Repeat vs. One-Time Customer Comparison",
    "6. Top 10 Customers by Revenue (with Portfolio Share & Running Total)",
    "7. Customers Inactive for 90+ Days (Churn Risk)",
    "8. Average Order Value & Revenue by RFM Segment",
]


def load_queries_from_file(sql_file_path: str = "sql/queries.sql") -> List[Tuple[str, str]]:
    """
    Parse semicolon-delimited SQL queries from file and pair them with descriptive titles.
    """
    if not os.path.exists(sql_file_path):
        raise FileNotFoundError(f"SQL queries file not found at: {sql_file_path}")
        
    with open(sql_file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    raw_statements = [s.strip() for s in content.split(";") if s.strip()]
    paired_queries: List[Tuple[str, str]] = []
    
    for idx, stmt in enumerate(raw_statements):
        title = QUERY_NAMES[idx] if idx < len(QUERY_NAMES) else f"Query {idx + 1}"
        paired_queries.append((title, stmt))
        
    return paired_queries


def execute_analytical_queries(
    db_path: str = "data/processed/retail.db",
    sql_file_path: str = "sql/queries.sql",
    verbose: bool = True,
) -> Dict[str, pd.DataFrame]:
    """
    Execute all SQL queries against SQLite and return results as DataFrames.
    
    Parameters:
        db_path: Path to the SQLite retail database
        sql_file_path: Path to sql/queries.sql
        verbose: If True, prints formatted tables to stdout
        
    Returns:
        Dictionary mapping query title to resulting pandas DataFrame.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at {db_path}. Run load_db.py first.")
        
    queries = load_queries_from_file(sql_file_path)
    conn = sqlite3.connect(db_path)
    results: Dict[str, pd.DataFrame] = {}
    
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
            
    try:
        if verbose:
            print("\n" + "=" * 90)
            print("         CUSTOMER PURCHASE PATTERN ANALYZER -- SQL ANALYTICS EXECUTION")
            print("=" * 90)
            
        for title, query_sql in queries:
            df_result = pd.read_sql_query(query_sql, conn)
            results[title] = df_result
            
            if verbose:
                print(f"\n>>> {title}")
                print("-" * 90)
                # Show top 5 rows if table has many records, else show full table
                display_df = df_result.head(5) if len(df_result) > 10 else df_result
                print(display_df.to_string(index=False))
                if len(df_result) > 10:
                    print(f"... [{len(df_result)} total rows returned. Showing first 5]")
                    
        if verbose:
            print("\n" + "=" * 90)
            print("All 8 SQL queries executed successfully.")
            print("=" * 90 + "\n")
            
    finally:
        conn.close()
        
    return results


if __name__ == "__main__":
    execute_analytical_queries()
