"""
Unit tests for the feature_engineer module.
"""
import pytest
import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal, assert_series_equal

# Adjust import path
from quant.data_preparation.feature_engineer import (
    calculate_daily_returns,
    calculate_moving_averages,
    calculate_volume_indicators,
    engineer_features
)

# --- Fixtures ---

@pytest.fixture
def sample_feature_data():
    """Creates a sample DataFrame suitable for feature engineering tests."""
    dates = pd.to_datetime([
        '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06', '2023-01-09',
        '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06', '2023-01-09',
    ])
    data = {
        'close':  [100, 101, 102, 101.5, 103, 50, 50.5, 51, 50.8, 51.2],
        'volume': [1000, 1100, 1050, 1200, 1150, 500, 550, 600, 580, 620],
        'stock_id': ['TESTA'] * 5 + ['TESTB'] * 5
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'datetime'
    # Add other required columns if needed by future feature functions
    df['open'] = df['close'] - 1
    df['high'] = df['close'] + 1
    df['low'] = df['close'] - 2
    # Ensure sorted by stock_id, datetime for consistent test results
    df.sort_values(['stock_id', df.index.name], inplace=True)
    return df

# --- Tests for individual feature functions ---

def test_calculate_daily_returns(sample_feature_data):
    """Test daily return calculation."""
    df = calculate_daily_returns(sample_feature_data.copy())
    assert 'daily_return' in df.columns

    # Check TESTA returns (data is sorted by stock_id, datetime in fixture)
    testa_returns = df[df['stock_id'] == 'TESTA']['daily_return']
    assert pd.isna(testa_returns.iloc[0]) # First return is NaN
    assert np.isclose(testa_returns.iloc[1], (101 - 100) / 100) # 0.01
    assert np.isclose(testa_returns.iloc[2], (102 - 101) / 101)
    assert np.isclose(testa_returns.iloc[3], (101.5 - 102) / 102)
    assert np.isclose(testa_returns.iloc[4], (103 - 101.5) / 101.5)

    # Check TESTB returns
    testb_returns = df[df['stock_id'] == 'TESTB']['daily_return']
    assert pd.isna(testb_returns.iloc[0]) # First return is NaN
    assert np.isclose(testb_returns.iloc[1], (50.5 - 50) / 50) # 0.01
    assert np.isclose(testb_returns.iloc[2], (51 - 50.5) / 50.5)

def test_calculate_moving_averages(sample_feature_data):
    """Test moving average calculation."""
    windows = [2, 3] # Use smaller windows for easier manual verification
    df = calculate_moving_averages(sample_feature_data.copy(), windows=windows)
    assert 'MA_2' in df.columns
    assert 'MA_3' in df.columns

    # Check TESTA MAs (using min_periods=1 as in implementation)
    testa_close = df[df['stock_id'] == 'TESTA']['close']
    testa_ma2 = df[df['stock_id'] == 'TESTA']['MA_2']
    testa_ma3 = df[df['stock_id'] == 'TESTA']['MA_3']
    assert np.isclose(testa_ma2.iloc[0], 100) # MA2[0] = close[0]
    assert np.isclose(testa_ma2.iloc[1], (100 + 101) / 2) # MA2[1] = (close[0]+close[1])/2
    assert np.isclose(testa_ma2.iloc[2], (101 + 102) / 2) # MA2[2] = (close[1]+close[2])/2
    assert np.isclose(testa_ma3.iloc[0], 100) # MA3[0] = close[0]
    assert np.isclose(testa_ma3.iloc[1], (100 + 101) / 2) # MA3[1] = (close[0]+close[1])/2
    assert np.isclose(testa_ma3.iloc[2], (100 + 101 + 102) / 3) # MA3[2] = (close[0]+close[1]+close[2])/3
    assert np.isclose(testa_ma3.iloc[3], (101 + 102 + 101.5) / 3) # MA3[3] = (close[1]+close[2]+close[3])/3

    # Check TESTB MAs
    testb_close = df[df['stock_id'] == 'TESTB']['close']
    testb_ma2 = df[df['stock_id'] == 'TESTB']['MA_2']
    assert np.isclose(testb_ma2.iloc[0], 50)
    assert np.isclose(testb_ma2.iloc[1], (50 + 50.5) / 2)

def test_calculate_volume_indicators(sample_feature_data):
    """Test volume indicator calculation (average volume)."""
    window = 3
    df = calculate_volume_indicators(sample_feature_data.copy(), window=window)
    col_name = f'avg_volume_{window}'
    assert col_name in df.columns

    # Check TESTA avg volume
    testa_vol = df[df['stock_id'] == 'TESTA']['volume']
    testa_avg_vol = df[df['stock_id'] == 'TESTA'][col_name]
    assert np.isclose(testa_avg_vol.iloc[0], 1000)
    assert np.isclose(testa_avg_vol.iloc[1], (1000 + 1100) / 2)
    assert np.isclose(testa_avg_vol.iloc[2], (1000 + 1100 + 1050) / 3)
    assert np.isclose(testa_avg_vol.iloc[3], (1100 + 1050 + 1200) / 3)

    # Check TESTB avg volume
    testb_vol = df[df['stock_id'] == 'TESTB']['volume']
    testb_avg_vol = df[df['stock_id'] == 'TESTB'][col_name]
    assert np.isclose(testb_avg_vol.iloc[0], 500)
    assert np.isclose(testb_avg_vol.iloc[1], (500 + 550) / 2)
    assert np.isclose(testb_avg_vol.iloc[2], (500 + 550 + 600) / 3)

# --- Test for the main engineer_features function ---

def test_engineer_features(sample_feature_data):
    """Test the main feature engineering orchestrator function."""
    df_orig = sample_feature_data.copy()
    # Ensure original is sorted same way as function output for comparison
    df_orig.sort_values(['stock_id', df_orig.index.name], inplace=True)
    df_featured = engineer_features(sample_feature_data.copy())

    # Check if all expected columns are present
    expected_new_cols = ['daily_return', 'MA_5', 'MA_20', 'avg_volume_7']
    for col in expected_new_cols:
        assert col in df_featured.columns

    # Spot check a value from each calculation to ensure they ran
    # Daily return check (e.g., TESTA, second day)
    assert np.isclose(df_featured[df_featured['stock_id'] == 'TESTA']['daily_return'].iloc[1], 0.01)
    # MA_5 check (e.g., TESTA, last day)
    testa_close = df_orig[df_orig['stock_id'] == 'TESTA']['close']
    expected_ma5_last = testa_close.iloc[-5:].mean()
    assert np.isclose(df_featured[df_featured['stock_id'] == 'TESTA']['MA_5'].iloc[-1], expected_ma5_last)
    # Avg_volume_7 check (e.g., TESTB, last day)
    testb_vol = df_orig[df_orig['stock_id'] == 'TESTB']['volume']
    # Note: Default window is 7, our sample data only has 5 points per stock.
    # The implementation uses min_periods=1, so it calculates based on available data.
    expected_vol7_last = testb_vol.iloc[-5:].mean() # Avg of last 5 points for TESTB
    assert np.isclose(df_featured[df_featured['stock_id'] == 'TESTB']['avg_volume_7'].iloc[-1], expected_vol7_last)

def test_engineer_features_missing_columns():
    """Test that functions handle missing input columns gracefully (though they log errors)."""
    # Create data missing 'close' or 'volume'
    dates = pd.to_datetime(['2023-01-03', '2023-01-04'])
    data_no_close = {'open': [10, 11], 'volume': [100, 110], 'stock_id': ['NOCLS'] * 2}
    df_no_close = pd.DataFrame(data_no_close, index=dates)
    df_no_close.index.name = 'datetime'

    data_no_volume = {'open': [10, 11], 'close': [10.5, 11.5], 'stock_id': ['NOVOL'] * 2}
    df_no_volume = pd.DataFrame(data_no_volume, index=dates)
    df_no_volume.index.name = 'datetime'

    # --- Test case: Missing 'close' ---
    res_main_no_close = engineer_features(df_no_close.copy())
    # Expected: daily_return, MA_5, MA_20 should NOT be added
    # Expected: avg_volume_7 SHOULD be added
    assert 'daily_return' not in res_main_no_close.columns
    assert 'MA_5' not in res_main_no_close.columns
    assert 'MA_20' not in res_main_no_close.columns
    assert 'avg_volume_7' in res_main_no_close.columns
    # Check that original columns are preserved
    for col in df_no_close.columns:
        assert col in res_main_no_close.columns
        assert_series_equal(res_main_no_close[col], df_no_close[col])
    # Check shape
    assert res_main_no_close.shape == (df_no_close.shape[0], df_no_close.shape[1] + 1) # +1 for avg_volume_7

    # --- Test case: Missing 'volume' ---
    res_main_no_vol = engineer_features(df_no_volume.copy())
    # Expected: daily_return, MA_5, MA_20 SHOULD be added
    # Expected: avg_volume_7 should NOT be added
    assert 'daily_return' in res_main_no_vol.columns
    assert 'MA_5' in res_main_no_vol.columns
    assert 'MA_20' in res_main_no_vol.columns
    assert 'avg_volume_7' not in res_main_no_vol.columns
    # Check that original columns are preserved
    for col in df_no_volume.columns:
        assert col in res_main_no_vol.columns
        assert_series_equal(res_main_no_vol[col], df_no_volume[col])
     # Check shape
    assert res_main_no_vol.shape == (df_no_volume.shape[0], df_no_volume.shape[1] + 3) # +3 for return, MA_5, MA_20