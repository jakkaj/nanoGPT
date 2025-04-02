"""
Unit tests for the anomaly_handler module.
"""
import pytest
import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal

# Adjust import path
from quant.data_preparation.anomaly_handler import handle_missing_trading_days, adjust_prices_for_splits_dividends

# --- Fixtures ---

@pytest.fixture
def sample_stock_data():
    """Creates a sample DataFrame with potential missing days."""
    dates = pd.to_datetime([
        '2023-01-03', '2023-01-04', '2023-01-06', # Missing Jan 5th (Thu)
        '2023-01-09', '2023-01-10', '2023-01-13', # Missing Jan 11th, 12th (Wed, Thu)
        '2023-01-03', '2023-01-04', '2023-01-05', # Stock 2 has no missing days initially
    ])
    data = {
        'open':   [10, 11, 13, 14, 15, 18, 50, 51, 52],
        'high':   [10.5, 11.5, 13.5, 14.5, 15.5, 18.5, 50.5, 51.5, 52.5],
        'low':    [9.5, 10.5, 12.5, 13.5, 14.5, 17.5, 49.5, 50.5, 51.5],
        'close':  [10.2, 11.2, 13.2, 14.2, 15.2, 18.2, 50.2, 51.2, 52.2],
        'volume': [100, 110, 130, 140, 150, 180, 200, 210, 220],
        'stock_id': ['TEST1'] * 6 + ['TEST2'] * 3
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'datetime'
    df.sort_index(inplace=True) # Ensure sorted for processing
    return df

@pytest.fixture
def data_no_missing_days():
    """Creates sample data with no missing business days."""
    dates = pd.to_datetime(['2023-01-03', '2023-01-04', '2023-01-05'])
    data = {'open': [50, 51, 52], 'close': [50.2, 51.2, 52.2], 'volume': [200, 210, 220], 'stock_id': ['TEST3'] * 3}
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'datetime'
    # Add other required columns
    df['high'] = df['close'] + 0.5
    df['low'] = df['close'] - 0.5
    return df

# --- Tests for handle_missing_trading_days ---

def test_handle_missing_days_interpolation(sample_stock_data):
    """Test if missing business days are correctly identified and interpolated."""
    original_len_test1 = len(sample_stock_data[sample_stock_data['stock_id'] == 'TEST1'])
    original_len_test2 = len(sample_stock_data[sample_stock_data['stock_id'] == 'TEST2'])

    filled_df = handle_missing_trading_days(sample_stock_data.copy())

    assert filled_df is not None
    assert isinstance(filled_df, pd.DataFrame)

    # Check TEST1
    filled_test1 = filled_df[filled_df['stock_id'] == 'TEST1']
    assert len(filled_test1) > original_len_test1 # Rows should have been added
    # Check specific interpolated dates for TEST1
    assert pd.Timestamp('2023-01-05') in filled_test1.index
    assert pd.Timestamp('2023-01-11') in filled_test1.index
    assert pd.Timestamp('2023-01-12') in filled_test1.index
    # Check interpolation values (simple linear interpolation check)
    # Jan 5th should be halfway between Jan 4th and Jan 6th
    assert np.isclose(filled_test1.loc['2023-01-05', 'open'], (11 + 13) / 2)
    assert np.isclose(filled_test1.loc['2023-01-05', 'close'], (11.2 + 13.2) / 2)
    assert np.isclose(filled_test1.loc['2023-01-05', 'volume'], (110 + 130) / 2)
    # Jan 11th should be 1/3 way between Jan 10th and Jan 13th
    assert np.isclose(filled_test1.loc['2023-01-11', 'open'], 15 + (18 - 15) / 3 * 1)
    # Jan 12th should be 2/3 way between Jan 10th and Jan 13th
    assert np.isclose(filled_test1.loc['2023-01-12', 'open'], 15 + (18 - 15) / 3 * 2)
    # Check that weekends are NOT added (e.g., Jan 7th, 8th)
    assert pd.Timestamp('2023-01-07') not in filled_test1.index
    assert pd.Timestamp('2023-01-08') not in filled_test1.index

    # Check TEST2 (should remain unchanged as it had no missing days in its range)
    filled_test2 = filled_df[filled_df['stock_id'] == 'TEST2']
    assert len(filled_test2) == original_len_test2
    expected_test2 = sample_stock_data[sample_stock_data['stock_id'] == 'TEST2']
    # Need to select same columns for comparison as filled_df might have extra internal cols
    assert_frame_equal(filled_test2[expected_test2.columns], expected_test2, check_dtype=False)


def test_handle_missing_days_no_missing(data_no_missing_days):
    """Test the function with data that has no missing business days."""
    original_df = data_no_missing_days.copy()
    filled_df = handle_missing_trading_days(data_no_missing_days.copy())

    assert filled_df is not None
    # Reset freq for comparison as reindexing might add it
    filled_df.index.freq = None
    # The DataFrame should be identical (or very close due to float precision if any ops happened)
    assert_frame_equal(filled_df, original_df, check_dtype=False)

def test_handle_missing_days_empty_input():
    """Test with an empty DataFrame."""
    empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume', 'stock_id'])
    empty_df = empty_df.set_index(pd.to_datetime([]))
    empty_df.index.name = 'datetime'

    filled_df = handle_missing_trading_days(empty_df)
    assert filled_df is not None
    assert filled_df.empty
    # Check if the returned empty df has the correct index name
    assert filled_df.index.name == 'datetime'


def test_handle_missing_days_single_stock_all_missing():
    """Test case where a stock has data but it's sparse."""
    dates = pd.to_datetime(['2023-01-03', '2023-01-10']) # Missing many days
    data = {'open': [10, 20], 'close': [11, 21], 'volume': [100, 200], 'stock_id': ['SPARSE'] * 2}
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'datetime'
    df['high'] = df['close'] + 0.5
    df['low'] = df['close'] - 0.5

    filled_df = handle_missing_trading_days(df.copy())
    assert filled_df is not None
    assert len(filled_df) > 2 # Should have interpolated rows
    assert pd.Timestamp('2023-01-04') in filled_df.index
    assert pd.Timestamp('2023-01-09') in filled_df.index


# --- Tests for adjust_prices_for_splits_dividends (Placeholder) ---

def test_adjust_prices_placeholder(sample_stock_data):
    """Test that the placeholder function returns the DataFrame unchanged."""
    original_df = sample_stock_data.copy()
    adjusted_df = adjust_prices_for_splits_dividends(sample_stock_data.copy())
    # Ensure it returns the same DataFrame object or an identical copy
    assert_frame_equal(adjusted_df, original_df)