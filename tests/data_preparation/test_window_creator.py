"""
Unit tests for the window_creator module.
"""
import pytest
import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal, assert_series_equal

# Adjust import path
from quant.data_preparation.window_creator import create_target, create_windows_and_target

# --- Fixtures ---

@pytest.fixture
def sample_window_data():
    """Creates a longer sample DataFrame for windowing and target tests."""
    # Create enough data for several windows + target lookahead
    dates = pd.date_range(start='2023-01-01', periods=30, freq='B') # ~1.5 months
    stock1_dates = dates[:20] # Stock 1 has 20 days (Jan 2 to Jan 27)
    stock2_dates = dates[5:25] # Stock 2 has 20 days (Jan 9 to Feb 3)

    data1 = {
        'close': np.linspace(10, 19.5, 20), # Simple increasing trend for Stock 1
        'stock_id': ['STOCK1'] * 20
    }
    df1 = pd.DataFrame(data1, index=stock1_dates)

    data2 = {
        'close': np.linspace(50, 40.5, 20), # Simple decreasing trend for Stock 2
        'stock_id': ['STOCK2'] * 20
    }
    df2 = pd.DataFrame(data2, index=stock2_dates)

    df = pd.concat([df1, df2])
    df.index.name = 'datetime'

    # Add other necessary columns (can be simple for testing windowing logic)
    df['open'] = df['close'] - 0.1
    df['high'] = df['close'] + 0.1
    df['low'] = df['close'] - 0.1
    df['volume'] = 1000
    # Add dummy features - assume they are already calculated and non-NaN for valid windows
    # Ensure sorting before calculating features
    df.sort_values(['stock_id', df.index.name], inplace=True)
    df['MA_5'] = df.groupby('stock_id')['close'].transform(lambda x: x.rolling(5, min_periods=1).mean())
    df['daily_return'] = df.groupby('stock_id')['close'].transform(lambda x: x.pct_change())
    df['avg_volume_7'] = 1000 # Keep it simple

    # Introduce a NaN feature value in one potential window to test skipping
    # Apply NaN *after* sorting and feature calculation
    nan_date_stock1 = df[df['stock_id'] == 'STOCK1'].index[8] # 9th day for STOCK1
    df.loc[nan_date_stock1, 'MA_5'] = np.nan

    df.sort_index(inplace=True) # Sort back by date for overall consistency if needed
    return df

# --- Tests for create_target ---

def test_create_target_calculation(sample_window_data):
    """Test basic target calculation (increase/decrease)."""
    prediction_days = 7 # Calendar days
    df = create_target(sample_window_data.copy(), prediction_days=prediction_days) # df is now sorted by stock_id, datetime

    assert 'target' in df.columns

    # STOCK1: Generally increasing, target should mostly be 1
    stock1_df = df[df['stock_id'] == 'STOCK1']
    stock1_target_dropna = stock1_df.dropna(subset=['target']) # Drop NaNs at the end
    assert not stock1_target_dropna.empty, "STOCK1 should have some valid targets"
    # Check a specific point where target should be 1
    # Example: Predict from 2023-01-03, look at close on or after 2023-01-10
    pred_date1 = pd.Timestamp('2023-01-03')
    target_date1_min = pred_date1 + pd.Timedelta(days=prediction_days)
    # Find target date within STOCK1's data
    actual_target_date1 = stock1_df[stock1_df.index >= target_date1_min].index.min()
    # Use .loc with boolean indexing for safety with potential duplicate dates across stocks
    # Use .item() to extract scalar value assuming unique date per stock
    close_pred1 = stock1_df.loc[stock1_df.index == pred_date1, 'close'].item()
    close_target1 = stock1_df.loc[stock1_df.index == actual_target_date1, 'close'].item()
    expected_target1 = 1 if close_target1 > close_pred1 else 0
    assert stock1_df.loc[stock1_df.index == pred_date1, 'target'].item() == expected_target1
    assert expected_target1 == 1 # Based on linspace data

    # STOCK2: Generally decreasing, target should mostly be 0
    stock2_df = df[df['stock_id'] == 'STOCK2']
    stock2_target_dropna = stock2_df.dropna(subset=['target'])
    assert not stock2_target_dropna.empty, "STOCK2 should have some valid targets"
    # Example: Predict from 2023-01-10, look at close on or after 2023-01-17
    pred_date2 = pd.Timestamp('2023-01-10')
    target_date2_min = pred_date2 + pd.Timedelta(days=prediction_days)
    actual_target_date2 = stock2_df[stock2_df.index >= target_date2_min].index.min()
    close_pred2 = stock2_df.loc[stock2_df.index == pred_date2, 'close'].item()
    close_target2 = stock2_df.loc[stock2_df.index == actual_target_date2, 'close'].item()
    expected_target2 = 1 if close_target2 > close_pred2 else 0
    assert stock2_df.loc[stock2_df.index == pred_date2, 'target'].item() == expected_target2
    assert expected_target2 == 0 # Based on linspace data

def test_create_target_edge_cases(sample_window_data):
    """Test target calculation near the end of the data where lookahead fails."""
    prediction_days = 7
    df = create_target(sample_window_data.copy(), prediction_days=prediction_days)

    # Check STOCK1 near the end
    stock1_df = df[df['stock_id'] == 'STOCK1']
    last_date_s1 = stock1_df.index.max()
    # Dates within `prediction_days` of the end should have NaN target
    cutoff_date_s1 = last_date_s1 - pd.Timedelta(days=prediction_days - 1) # Approx cutoff
    assert stock1_df[stock1_df.index > cutoff_date_s1]['target'].isna().all()
    # Check a date just before the cutoff has a valid target
    valid_target_date_s1 = stock1_df[stock1_df.index <= cutoff_date_s1].index[-1]
    assert not pd.isna(stock1_df.loc[stock1_df.index == valid_target_date_s1, 'target'].item()), f"Target for {valid_target_date_s1} should not be NaN"

    # Check STOCK2 near the end
    stock2_df = df[df['stock_id'] == 'STOCK2']
    last_date_s2 = stock2_df.index.max()
    cutoff_date_s2 = last_date_s2 - pd.Timedelta(days=prediction_days - 1)
    assert stock2_df[stock2_df.index > cutoff_date_s2]['target'].isna().all()
    valid_target_date_s2 = stock2_df[stock2_df.index <= cutoff_date_s2].index[-1]
    assert not pd.isna(stock2_df.loc[stock2_df.index == valid_target_date_s2, 'target'].item()), f"Target for {valid_target_date_s2} should not be NaN"


# --- Tests for create_windows_and_target ---

def test_create_windows_basic(sample_window_data):
    """Test basic window creation, size, and structure."""
    window_size = 10
    prediction_days = 5 # Use smaller prediction days to have more valid targets
    # Prepare input data: remove manually added NaN and initial feature NaNs
    test_data = sample_window_data.copy()
    nan_date_stock1 = test_data[test_data['MA_5'].isna()].index
    if not nan_date_stock1.empty:
         test_data.loc[nan_date_stock1, 'MA_5'] = 1.0 # Fill with dummy value
    test_data.dropna(subset=['daily_return'], inplace=True) # Drop initial NaNs

    # Calculate target on this cleaned data
    df_with_target = create_target(test_data, prediction_days=prediction_days)
    # df_with_target is now sorted by stock_id, datetime

    windowed_df = create_windows_and_target(df_with_target.copy(), window_size=window_size, prediction_days=prediction_days)

    assert windowed_df is not None, "Windowed DataFrame should not be None"
    assert isinstance(windowed_df, pd.DataFrame)

    # Check columns
    assert 'stock_id' in windowed_df.columns
    assert 'prediction_date' in windowed_df.columns
    assert 'time_idx' in windowed_df.columns
    assert 'target' in windowed_df.columns
    assert 'close' in windowed_df.columns # Example feature
    assert 'MA_5' in windowed_df.columns # Example feature

    # Check window properties for a specific window
    stock1_windows = windowed_df[windowed_df['stock_id'] == 'STOCK1']
    if not stock1_windows.empty:
        first_pred_date_s1 = stock1_windows['prediction_date'].min()
        first_window_s1 = stock1_windows[stock1_windows['prediction_date'] == first_pred_date_s1]
        assert len(first_window_s1) == window_size
        assert first_window_s1['time_idx'].tolist() == list(range(window_size))
        assert first_window_s1['prediction_date'].nunique() == 1
        assert first_window_s1['target'].nunique() == 1

    # Check total number of windows created (Recalculated based on clean input)
    # STOCK1: 19 days (after dropna daily_return). Prediction dates: Jan 16-27. Valid target dates end Jan 20. Valid prediction dates: Jan 16-20 (5 dates). Windows = 5.
    # STOCK2: 19 days (after dropna daily_return). Prediction dates: Jan 23-Feb 3. Valid target dates end Jan 27. Valid prediction dates: Jan 23-27 (5 dates). Windows = 5.
    # Expected rows = (5 + 5) * 10 = 100.
    expected_total_rows = 100 # *** CORRECTED EXPECTED VALUE BASED ON ANALYSIS ***
    assert len(windowed_df) == expected_total_rows, f"Expected {expected_total_rows} rows, got {len(windowed_df)}"


def test_create_windows_skips_nan_features(sample_window_data):
    """Test that windows containing NaN feature values are skipped."""
    window_size = 10
    prediction_days = 5
    # Use the original fixture data which has a NaN in MA_5 for STOCK1
    test_data = sample_window_data.copy()
    test_data.dropna(subset=['daily_return'], inplace=True) # Drop initial daily_return NaNs first
    df_with_target = create_target(test_data, prediction_days=prediction_days)

    # Find the prediction dates for STOCK1 that would include the NaN date
    nan_date_stock1 = df_with_target[(df_with_target['stock_id'] == 'STOCK1') & (df_with_target['MA_5'].isna())].index
    assert not nan_date_stock1.empty, "Test setup error: NaN date not found"
    nan_date_stock1 = nan_date_stock1[0]

    stock1_dates = df_with_target[df_with_target['stock_id'] == 'STOCK1'].index
    potential_nan_pred_dates = stock1_dates[(stock1_dates >= nan_date_stock1) & (stock1_dates < nan_date_stock1 + pd.Timedelta(days=window_size))]

    windowed_df = create_windows_and_target(df_with_target.copy(), window_size=window_size, prediction_days=prediction_days)

    assert windowed_df is not None
    affected_windows = windowed_df[(windowed_df['stock_id'] == 'STOCK1') & (windowed_df['prediction_date'].isin(potential_nan_pred_dates))]
    assert affected_windows.empty, f"Windows containing NaN feature at {nan_date_stock1} were not skipped."


def test_create_windows_skips_nan_target(sample_window_data):
    """Test that windows where the target is NaN are skipped."""
    window_size = 5
    prediction_days = 15 # Make prediction days large enough to cause NaNs at the end
    # Prepare clean feature data
    test_data = sample_window_data.copy()
    nan_date_stock1_ma5 = test_data[test_data['MA_5'].isna()].index
    if not nan_date_stock1_ma5.empty:
         test_data.loc[nan_date_stock1_ma5, 'MA_5'] = 1.0 # Fill dummy value
    test_data.dropna(subset=['daily_return'], inplace=True) # Drop initial NaNs

    df_with_target = create_target(test_data, prediction_days=prediction_days)

    # Find prediction dates where target is NaN
    nan_target_pred_dates_s1 = df_with_target[(df_with_target['stock_id'] == 'STOCK1') & df_with_target['target'].isna()].index
    nan_target_pred_dates_s2 = df_with_target[(df_with_target['stock_id'] == 'STOCK2') & df_with_target['target'].isna()].index

    windowed_df = create_windows_and_target(df_with_target.copy(), window_size=window_size, prediction_days=prediction_days)

    assert windowed_df is not None
    # Check that no windows exist *for the specific stock* for prediction dates where the target was NaN
    overlapping_s1 = windowed_df[(windowed_df['prediction_date'].isin(nan_target_pred_dates_s1)) & (windowed_df['stock_id'] == 'STOCK1')]
    overlapping_s2 = windowed_df[(windowed_df['prediction_date'].isin(nan_target_pred_dates_s2)) & (windowed_df['stock_id'] == 'STOCK2')]

    print(f"\nDEBUG: Dates with NaN target for STOCK1: {nan_target_pred_dates_s1.tolist()}")
    print(f"DEBUG: Prediction dates present in windowed_df for STOCK1: {windowed_df[windowed_df['stock_id']=='STOCK1']['prediction_date'].unique().tolist()}")
    print(f"DEBUG: Overlapping dates for STOCK1: {overlapping_s1['prediction_date'].unique().tolist()}")

    print(f"\nDEBUG: Dates with NaN target for STOCK2: {nan_target_pred_dates_s2.tolist()}")
    print(f"DEBUG: Prediction dates present in windowed_df for STOCK2: {windowed_df[windowed_df['stock_id']=='STOCK2']['prediction_date'].unique().tolist()}")
    print(f"DEBUG: Overlapping dates for STOCK2: {overlapping_s2['prediction_date'].unique().tolist()}")


    assert overlapping_s1.empty, "Windows found for STOCK1 with NaN target"
    assert overlapping_s2.empty, "Windows found for STOCK2 with NaN target"


def test_create_windows_insufficient_data():
    """Test window creation with data shorter than window size."""
    window_size = 10
    prediction_days = 5
    dates = pd.date_range(start='2023-01-01', periods=8, freq='B') # Only 8 days
    data = {'close': np.linspace(10, 15, 8), 'stock_id': ['SHORT'] * 8}
    df_short = pd.DataFrame(data, index=dates)
    df_short.index.name = 'datetime'
    # Add dummy columns
    df_short['open'] = df_short['close']
    df_short['high'] = df_short['close']
    df_short['low'] = df_short['close']
    df_short['volume'] = 100
    df_short['MA_5'] = df_short['close'] # Assume features are calculated
    df_short['daily_return'] = df_short['close'].pct_change() # Add feature

    # Calculate target (might result in all NaNs if lookahead is too long)
    df_with_target = create_target(df_short.copy(), prediction_days=prediction_days)
    # Handle case where create_target returns None or df is empty after target calc
    if df_with_target is None or df_with_target.empty:
         windowed_df = None
    else:
         # Drop initial NaNs before windowing
         df_with_target.dropna(subset=['daily_return'], inplace=True)
         windowed_df = create_windows_and_target(df_with_target.copy(), window_size=window_size, prediction_days=prediction_days)

    assert windowed_df is None # Should return None as no windows can be formed