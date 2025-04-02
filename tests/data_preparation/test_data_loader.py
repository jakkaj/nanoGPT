"""
Unit tests for the data_loader module.
"""
import pytest
import pandas as pd
from pathlib import Path
import os

# Adjust the import path based on the project structure
# Assumes tests are run from the project root (where 'quant' and 'tests' directories are)
from quant.data_preparation.data_loader import load_all_stock_data
from quant.data_preparation.data_utils import load_csv_data

# --- Fixtures ---

@pytest.fixture
def temp_data_dir(tmp_path):
    """Creates a temporary directory and populates it with sample CSV files."""
    data_dir = tmp_path / "hist_data"
    data_dir.mkdir()

    # Valid file 1 (AAPL)
    aapl_path = data_dir / "AAPL.csv"
    aapl_content = """datetime,open,high,low,close,volume
2023-01-04,130.0,131.0,129.0,130.5,110000
2023-01-03,129.5,130.5,128.5,129.8,100000
2023-01-05,130.2,132.0,130.0,131.8,120000
"""
    aapl_path.write_text(aapl_content)

    # Valid file 2 (MSFT) - different date range
    msft_path = data_dir / "MSFT.csv"
    msft_content = """datetime,open,high,low,close,volume
2023-01-05,280.0,282.0,279.0,281.0,90000
2023-01-06,281.5,283.0,280.5,282.5,95000
"""
    msft_path.write_text(msft_content)

    # Empty file
    empty_path = data_dir / "EMPTY.csv"
    empty_path.write_text("")

    # File with missing columns
    bad_format_path = data_dir / "BADFMT.csv"
    bad_format_content = """datetime,open,close
2023-01-03,10,11
"""
    bad_format_path.write_text(bad_format_content)

    # Non-CSV file
    other_file = data_dir / "notes.txt"
    other_file.write_text("This is not a CSV.")

    return data_dir

# --- Tests for load_csv_data (from data_utils) ---

def test_load_csv_data_valid(temp_data_dir):
    """Test loading a single valid CSV file."""
    file_path = temp_data_dir / "AAPL.csv"
    df = load_csv_data(file_path, "AAPL")
    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (3, 6) # 3 rows, 5 original cols + stock_id
    assert 'stock_id' in df.columns
    assert df['stock_id'].iloc[0] == "AAPL"
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.name == 'datetime'
    # Check sorting (oldest first)
    assert df.index.tolist() == [pd.Timestamp('2023-01-03'), pd.Timestamp('2023-01-04'), pd.Timestamp('2023-01-05')]

def test_load_csv_data_nonexistent():
    """Test loading a non-existent file."""
    df = load_csv_data(Path("nonexistent/path/NOSUCH.csv"), "NOSUCH")
    assert df is None

def test_load_csv_data_empty(temp_data_dir):
    """Test loading an empty CSV file."""
    file_path = temp_data_dir / "EMPTY.csv"
    df = load_csv_data(file_path, "EMPTY")
    assert df is None

def test_load_csv_data_missing_columns(temp_data_dir):
    """Test loading a CSV with missing required columns."""
    file_path = temp_data_dir / "BADFMT.csv"
    df = load_csv_data(file_path, "BADFMT")
    assert df is None

# --- Tests for load_all_stock_data ---

def test_load_all_stock_data_valid(temp_data_dir):
    """Test loading all valid and invalid files from a directory."""
    combined_df = load_all_stock_data(temp_data_dir)
    assert combined_df is not None
    assert isinstance(combined_df, pd.DataFrame)
    # Should contain data from AAPL (3 rows) and MSFT (2 rows) = 5 rows total
    assert combined_df.shape == (5, 6) # 5 rows, 5 original cols + stock_id
    assert 'stock_id' in combined_df.columns
    assert set(combined_df['stock_id'].unique()) == {"AAPL", "MSFT"}
    assert isinstance(combined_df.index, pd.DatetimeIndex)
    assert combined_df.index.name == 'datetime'
    # Check overall sorting
    expected_index = pd.to_datetime(['2023-01-03', '2023-01-04', '2023-01-05', '2023-01-05', '2023-01-06']).sort_values()
    assert combined_df.index.sort_values().tolist() == expected_index.tolist() # Sort before comparing

def test_load_all_stock_data_invalid_dir():
    """Test loading from a non-existent directory."""
    combined_df = load_all_stock_data(Path("nonexistent/path"))
    assert combined_df is None

def test_load_all_stock_data_empty_dir(tmp_path):
    """Test loading from an empty directory."""
    empty_dir = tmp_path / "empty_data"
    empty_dir.mkdir()
    combined_df = load_all_stock_data(empty_dir)
    assert combined_df is None

def test_load_all_stock_data_no_valid_files(tmp_path):
    """Test loading from a directory with only invalid files."""
    invalid_dir = tmp_path / "invalid_data"
    invalid_dir.mkdir()
    (invalid_dir / "notes.txt").write_text("hello")
    (invalid_dir / "EMPTY.csv").write_text("")
    combined_df = load_all_stock_data(invalid_dir)
    assert combined_df is None