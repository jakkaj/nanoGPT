"""
Creates fixed-size time series windows and target labels for model training/evaluation.
"""
import pandas as pd
import numpy as np
import logging
from tqdm import tqdm
import functools # Import functools for partial

# Configure logging AND print for immediate feedback during tests
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s') # Set level to DEBUG

def create_target(df, prediction_days=7):
    """
    Calculates the binary target variable for each potential prediction point.
    Target = 1 if close price 'prediction_days' calendar days later > close price, else 0.

    Args:
        df (pd.DataFrame): DataFrame with stock data, must include 'close',
                           'stock_id', and be indexed by datetime.
        prediction_days (int): The number of calendar days to look ahead for target calculation.

    Returns:
        pd.DataFrame: DataFrame with an added 'target' column, sorted by
                      stock_id, datetime. Rows where the target cannot be
                      calculated (due to insufficient future data) will have NaN.
    """
    logging.info(f"Calculating target variable ({prediction_days}-calendar day lookahead)...")
    print(f"\n[DEBUG create_target] Initial df shape: {df.shape}")

    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        logging.error("DataFrame index must be a DatetimeIndex for target calculation.")
        return None # Return None on critical error

    # Ensure the main df is sorted by stock_id and then datetime *before* any operation
    # This is crucial for aligning results back correctly.
    df.sort_values(['stock_id', df.index.name], inplace=True)
    print(f"[DEBUG create_target] df shape after initial sort: {df.shape}")

    # Define a function to apply per group to find the future close price
    def find_future_close_for_group(group, pred_days):
        stock_id = group['stock_id'].iloc[0] if not group.empty else "UNKNOWN"
        print(f"\n--- [DEBUG find_future_close] Processing group: {stock_id} ---")
        print(f"[DEBUG find_future_close] Input group shape: {group.shape}")
        # print("[DEBUG find_future_close] Input group head:\n", group.head())

        group = group.copy() # Avoid SettingWithCopyWarning
        group['future_lookup_date'] = group.index + pd.Timedelta(days=pred_days)

        # Prepare left side (prediction dates and lookup dates)
        date_map = group[['future_lookup_date']].reset_index() # Columns: 'datetime', 'future_lookup_date'
        print(f"[DEBUG find_future_close] date_map shape: {date_map.shape}")
        # print("[DEBUG find_future_close] date_map head:\n", date_map.head())


        # Prepare right side (all dates and close prices for the group)
        close_data = group[['close']].reset_index() # Columns: 'datetime', 'close'
        print(f"[DEBUG find_future_close] close_data shape: {close_data.shape}")
        # print("[DEBUG find_future_close] close_data head:\n", close_data.head())

        # Perform the merge with explicit suffixes
        print("[DEBUG find_future_close] Performing merge_asof...")
        merged = pd.merge_asof(date_map.sort_values('datetime'), # Sort left side just in case
                               close_data.sort_values('datetime'), # Sort right side
                               left_on='future_lookup_date',
                               right_on='datetime', # This is the date we match against
                               direction='forward',
                               suffixes=('_pred', '_future')) # Explicit suffixes
        print(f"[DEBUG find_future_close] merged shape after merge_asof: {merged.shape}")
        print(f"[DEBUG find_future_close] merged columns after merge_asof: {merged.columns.tolist()}")
        # print("[DEBUG find_future_close] merged head after merge_asof:\n", merged.head())


        # Rename columns for clarity and set index
        # 'datetime_pred' is the original prediction date from date_map
        # 'close' is the future close price from close_data (the right df)
        # Rename 'close' to 'future_close' and 'datetime_pred' to 'prediction_date'
        merged.rename(columns={'close': 'future_close', # *** CORRECTED: Target the actual 'close' column ***
                               'datetime_pred': 'prediction_date'},
                      inplace=True)
        print(f"[DEBUG find_future_close] merged columns after rename: {merged.columns.tolist()}")
        # print("[DEBUG find_future_close] merged head after rename:\n", merged.head())


        # Check if 'prediction_date' column exists before setting index
        if 'prediction_date' not in merged.columns:
             logging.warning(f"Column 'prediction_date' not found after merge_asof for group {stock_id}. Merge might have failed.")
             print(f"[DEBUG find_future_close] *** 'prediction_date' column missing! ***")
             return pd.Series(np.nan, index=group.index) # Return NaNs aligned with group

        print("[DEBUG find_future_close] Setting index to 'prediction_date'...")
        try:
            # Ensure prediction_date is suitable for index (e.g., handle potential NaTs if merge failed)
            merged.dropna(subset=['prediction_date'], inplace=True)
            merged.set_index('prediction_date', inplace=True)
            print(f"[DEBUG find_future_close] merged shape after set_index: {merged.shape}")
            # print("[DEBUG find_future_close] merged head after set_index:\n", merged.head())
        except KeyError as e:
            print(f"[DEBUG find_future_close] *** KeyError during set_index: {e} ***")
            print(f"[DEBUG find_future_close] merged columns before error: {merged.columns.tolist()}")
            return pd.Series(np.nan, index=group.index)


        # Check if 'future_close' column exists before reindexing
        if 'future_close' not in merged.columns:
            logging.warning(f"Column 'future_close' not found after merge_asof for group {stock_id}. Returning NaNs.")
            print(f"[DEBUG find_future_close] *** 'future_close' column missing! ***")
            return pd.Series(np.nan, index=group.index) # Return NaNs aligned with group


        # Ensure the result aligns with the original group's index and return only the series
        print("[DEBUG find_future_close] Reindexing result series...")
        try:
            # Reindex using the original group's index to ensure alignment and fill missing with NaN
            result_series = merged['future_close'].reindex(group.index)
            print(f"[DEBUG find_future_close] result_series shape: {result_series.shape}")
            # print("[DEBUG find_future_close] result_series head:\n", result_series.head())
            return result_series
        except KeyError as e:
             print(f"[DEBUG find_future_close] *** KeyError during reindex access: {e} ***")
             print(f"[DEBUG find_future_close] merged columns before error: {merged.columns.tolist()}")
             return pd.Series(np.nan, index=group.index)


    # Apply the lookup function per stock
    logging.info("Applying future close lookup (this may take time)...")
    find_future_close_partial = functools.partial(find_future_close_for_group, pred_days=prediction_days)

    # Apply the function. The result should align with the sorted df's index.
    future_close_series = df.groupby('stock_id', group_keys=False).apply(find_future_close_partial)
    print(f"[DEBUG create_target] future_close_series shape after apply: {future_close_series.shape}")
    # print("[DEBUG create_target] future_close_series head after apply:\n", future_close_series.head())


    # Assign the calculated future close prices back to the *sorted* DataFrame
    print("[DEBUG create_target] Assigning future_close_series to df['future_close']...")
    try:
        # Ensure indices match before direct assignment
        if not df.index.equals(future_close_series.index):
             print("[DEBUG create_target] Indices differ, attempting alignment via reindex...")
             df['future_close'] = future_close_series.reindex(df.index)
        else:
             df['future_close'] = future_close_series
        print("[DEBUG create_target] Assignment successful.")
    except Exception as e:
        print(f"[DEBUG create_target] *** Error during assignment: {e} ***")
        print(f"[DEBUG create_target] df index:\n{df.index}")
        print(f"[DEBUG create_target] future_close_series index:\n{future_close_series.index}")
        return None # Abort if assignment fails critically


    # Calculate the binary target
    print("[DEBUG create_target] Calculating binary target...")
    df['target'] = np.where(df['future_close'] > df['close'], 1, 0)

    # Handle cases where future_close is NaN (not enough future data)
    df.loc[df['future_close'].isna(), 'target'] = np.nan

    # Clean up temporary column
    df.drop(columns=['future_close'], inplace=True)

    logging.info(f"Target calculation complete. NaN count: {df['target'].isna().sum()}")
    print(f"[DEBUG create_target] Final df shape: {df.shape}")
    # Return the DataFrame, which is now sorted by stock_id, datetime
    return df


def create_windows_and_target(df, window_size=60, prediction_days=7):
    """
    Creates sliding windows of historical data and aligns them with the target variable.
    Adds positional embedding ('time_idx').

    Args:
        df (pd.DataFrame): Combined DataFrame with features. Target will be calculated if missing.
                           Must have datetime index and 'stock_id' column.
        window_size (int): Number of time steps (trading days) in each input window.
        prediction_days (int): Number of calendar days used for target lookahead.

    Returns:
        pd.DataFrame: A DataFrame where each row represents a time step within a
                      specific window for a stock. Includes columns for features,
                      'stock_id', 'prediction_date', 'time_idx', and 'target'.
                      Returns None if processing fails.
    """
    # Calculate target if not present. create_target now returns a sorted df.
    if 'target' not in df.columns:
        logging.info("Target column not found. Calculating target first...")
        df_copy = df.copy() # Work on a copy
        df_copy = create_target(df_copy, prediction_days)
        if df_copy is None or 'target' not in df_copy.columns:
             logging.error("Failed to create target column. Cannot create windows.")
             return None
        df = df_copy # Use the result with target column
    else:
        # Ensure df is sorted if target was pre-calculated
        df.sort_values(['stock_id', df.index.name], inplace=True)


    logging.info(f"Creating windows (size: {window_size} days)...")
    print(f"[DEBUG create_windows] Input df shape: {df.shape}")

    all_windows_data = []
    unique_stocks = df['stock_id'].unique()

    # Define feature columns (exclude id and target) - do this once
    feature_cols = [col for col in df.columns if col not in ['stock_id', 'target']]
    print(f"[DEBUG create_windows] Feature columns: {feature_cols}")

    # Use tqdm for progress bar
    for stock_id in tqdm(unique_stocks, desc="Creating Windows"):
        # Extract stock data - it's already sorted
        stock_df = df[df['stock_id'] == stock_id]

        # Check if there's enough data for at least one window
        if len(stock_df) < window_size:
            logging.debug(f"Skipping {stock_id}: Not enough data ({len(stock_df)}) for a full window ({window_size}).")
            continue

        # Iterate through possible prediction end dates to form windows
        skipped_nan_target = 0
        skipped_nan_feature = 0
        created_count = 0
        for end_iloc in range(window_size - 1, len(stock_df)):
            start_iloc = end_iloc - (window_size - 1)
            prediction_date = stock_df.index[end_iloc]

            # Check if the target is available *before* extracting the window
            target_value = stock_df.loc[prediction_date, 'target']
            if pd.isna(target_value):
                skipped_nan_target += 1
                continue

            # Extract the window data using iloc
            window_df = stock_df.iloc[start_iloc : end_iloc + 1].copy()

            # Check for NaNs within the window's features
            if window_df[feature_cols].isnull().values.any():
                 skipped_nan_feature += 1
                 continue

            # Add positional embedding
            window_df['time_idx'] = np.arange(window_size)

            # Add prediction date identifier
            window_df['prediction_date'] = prediction_date

            # Add the target
            window_df['target'] = int(target_value)

            all_windows_data.append(window_df)
            created_count += 1

        logging.debug(f"Stock {stock_id}: Created={created_count}, Skipped (NaN Target)={skipped_nan_target}, Skipped (NaN Feature)={skipped_nan_feature}")


    if not all_windows_data:
        logging.error("No valid windows could be created.")
        return None

    logging.info("Combining all window data...")
    final_windowed_df = pd.concat(all_windows_data)

    # Reorder columns for clarity
    id_cols = ['stock_id', 'prediction_date', 'time_idx']
    target_col = ['target']
    current_cols = final_windowed_df.columns.tolist()
    feature_cols_final = [col for col in current_cols if col not in id_cols + target_col]
    final_windowed_df = final_windowed_df[id_cols + feature_cols_final + target_col]

    logging.info(f"Window creation complete. Final shape: {final_windowed_df.shape}")
    logging.info(f"Number of unique windows created: {len(final_windowed_df[['stock_id', 'prediction_date']].drop_duplicates())}")

    return final_windowed_df


# Example usage (can be run standalone for testing)
if __name__ == '__main__':
    # Create a longer sample DataFrame for windowing
    dates = pd.date_range(start='2023-01-01', periods=80, freq='B') # ~4 months of business days
    data1 = {'close': np.linspace(10, 25, 80) + np.random.randn(80) * 0.5,
             'volume': np.linspace(100, 150, 80).astype(int),
             'stock_id': ['TESTW'] * 80}
    sample_df_long = pd.DataFrame(data1, index=dates)
    sample_df_long.index.name = 'datetime'
    sample_df_long['open'] = sample_df_long['close'] - 0.2
    sample_df_long['high'] = sample_df_long['close'] + 0.3
    sample_df_long['low'] = sample_df_long['close'] - 0.4

    # Add dummy features for testing (use transform for robustness)
    # Ensure sorting before feature engineering if done separately
    sample_df_long.sort_values(['stock_id', sample_df_long.index.name], inplace=True)
    sample_df_long['daily_return'] = sample_df_long.groupby('stock_id')['close'].transform(lambda x: x.pct_change())
    sample_df_long['MA_5'] = sample_df_long.groupby('stock_id')['close'].transform(lambda x: x.rolling(window=5, min_periods=1).mean())
    sample_df_long['avg_volume_7'] = sample_df_long.groupby('stock_id')['volume'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
    sample_df_long.dropna(inplace=True) # Drop initial NaNs from features

    print("--- Original Sample DataFrame (Long, Sorted & Featured) ---")
    print(sample_df_long.head())
    print(f"Shape: {sample_df_long.shape}")


    # Create windows and target
    windowed_data = create_windows_and_target(sample_df_long.copy(), window_size=10, prediction_days=5) # Smaller window/pred for test

    print("\n--- Windowed DataFrame ---")
    if windowed_data is not None:
        print(windowed_data.head(15)) # Show first 1.5 windows
        print(windowed_data.tail(15)) # Show last 1.5 windows
        print(f"\nWindowed data shape: {windowed_data.shape}")
        print(f"Unique windows: {len(windowed_data[['stock_id', 'prediction_date']].drop_duplicates())}")
        print("\nColumns:", windowed_data.columns.tolist())
        print("\nSample window details:")
        # Ensure there are enough unique prediction dates before accessing index 5
        unique_pred_dates = windowed_data['prediction_date'].unique()
        if len(unique_pred_dates) > 5:
             sample_pred_date = unique_pred_dates[5]
             sample_window = windowed_data[(windowed_data['stock_id'] == 'TESTW') & (windowed_data['prediction_date'] == sample_pred_date)]
             print(sample_window)
             print(f"Target for this window: {sample_window['target'].iloc[0]}")
        else:
             print("Not enough unique prediction dates to display sample window at index 5.")
    else:
        print("Failed to create windowed data.")