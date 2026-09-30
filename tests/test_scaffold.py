"""
test_scaffold.py
----------------
Purpose:
    Validates that core dependencies and project modules import cleanly.
"""

def test_imports():
    """Verify core third-party dependencies can be imported without errors."""
    import pandas
    import numpy
    import sklearn
    import plotly
    import streamlit
    import sqlite3
    import pytest
    assert pandas.__version__ is not None
    assert numpy.__version__ is not None
    assert sklearn.__version__ is not None
    assert plotly.__version__ is not None
    assert streamlit.__version__ is not None
    assert sqlite3.sqlite_version is not None
    assert pytest.__version__ is not None
