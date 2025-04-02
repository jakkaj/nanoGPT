"""
Calculates financial features for the stock data.
"""
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_daily_returns(df):
    """
    Calculates the daily percentage return based on the 'close' price.
    Handles calculations per stock_id.

    Args:
        df (pd.DataFrame): DataFrame with stock data, must include 'close'
                           and 'stock_id' columns. The DataFrame will be sorted
                           internally by stock_id, datetime.

    Returns:
        pd.DataFrame: DataFrame with an added 'daily_return' column.
                      The first entry for each stock will have NaN return.
                      The DataFrame will be returned sorted by stock_id, datetime.
    """
    if 'close' not in df.columns or 'stock_id' not in df.columns:
        logging.error("Required columns 'close' and 'stock_id' not found for daily return calculation.")
        return df

    logging.info("Calculating daily returns...")
    # Ensure data is sorted by stock_id and then datetime for correct pct_change
    # Perform calculation on a sorted copy to avoid modifying original order if not desired
    # Or, modify the input df directly if sorted output is acceptable. Let's modify directly.
    df.sort_values(['stock_id', df.index.name], inplace=True)
    df['daily_return'] = df.groupby('stock_id', group_keys=False)['close'].pct_change() # group_keys=False is slightly cleaner

    logging.info("Daily returns calculated.")
    return df

def calculate_moving_averages(df, windows=[5, 20]):
    """
    Calculates moving averages for the 'close' price for specified window sizes.
    Handles calculations per stock_id.

    Args:
        df (pd.DataFrame): DataFrame with stock data, must include 'close'
                           and 'stock_id' columns. The DataFrame will be sorted
                           internally by stock_id, datetime.
        windows (list): A list of integers representing the window sizes
                        for the moving averages (e.g., [5, 20]).

    Returns:
        pd.DataFrame: DataFrame with added moving average columns (e.g., 'MA_5', 'MA_20').
                      Initial rows for each stock will have NaN values depending on window size.
                      The DataFrame will be returned sorted by stock_id, datetime.
    """
    if 'close' not in df.columns or 'stock_id' not in df.columns:
        logging.error("Required columns 'close' and 'stock_id' not found for moving average calculation.")
        return df

    logging.info(f"Calculating moving averages for windows: {windows}...")
    # Ensure data is sorted by stock_id and then datetime for correct rolling calculation
    df.sort_values(['stock_id', df.index.name], inplace=True)

    for window in windows:
        ma_col_name = f'MA_{window}'
        logging.debug(f"Calculating {ma_col_name}...")
        # Use transform with rolling mean. Transform ensures the result aligns with the original index.
        df[ma_col_name] = df.groupby('stock_id', group_keys=False)['close'].transform(
            lambda x: x.rolling(window=window, min_periods=1).mean()
        )

    logging.info("Moving averages calculated.")
    return df

def calculate_volume_indicators(df, window=7):
    """
    Calculates volume-based indicators, specifically the average volume over a past window.
    Handles calculations per stock_id.

    Args:
        df (pd.DataFrame): DataFrame with stock data, must include 'volume'
                           and 'stock_id' columns. The DataFrame will be sorted
                           internally by stock_id, datetime.
        window (int): The window size (in days) for calculating the average volume.

    Returns:
        pd.DataFrame: DataFrame with an added 'avg_volume_{window}' column.
                      Initial rows for each stock will have NaN values.
                      The DataFrame will be returned sorted by stock_id, datetime.
    """
    if 'volume' not in df.columns or 'stock_id' not in df.columns:
        logging.error("Required columns 'volume' and 'stock_id' not found for volume indicator calculation.")
        return df

    vol_col_name = f'avg_volume_{window}'
    logging.info(f"Calculating average volume indicator ({vol_col_name})...")
    # Ensure data is sorted by stock_id and then datetime for correct rolling calculation
    df.sort_values(['stock_id', df.index.name], inplace=True)

    # Use transform with rolling mean for volume
    df[vol_col_name] = df.groupby('stock_id', group_keys=False)['volume'].transform(
        lambda x: x.rolling(window=window, min_periods=1).mean()
    )

    logging.info("Volume indicators calculated.")
    return df

def engineer_features(df):
    """
    Applies all feature engineering steps to the DataFrame.
    Ensures the DataFrame is sorted by stock_id, datetime before calculations.

    Args:
        df (pd.DataFrame): The combined, cleaned stock data DataFrame.

    Returns:
        pd.DataFrame: DataFrame with all engineered features added, sorted by
                      stock_id, datetime index.
    """
    logging.info("Starting feature engineering process...")
    # Sort by stock_id and datetime index - crucial for correct group-wise calculations
    df.sort_values(['stock_id', df.index.name], inplace=True)

    df = calculate_daily_returns(df)
    df = calculate_moving_averages(df, windows=[5, 20]) # As per spec
    df = calculate_volume_indicators(df, window=7) # As per spec (past week)

    # The DataFrame is already sorted by stock_id, datetime from the functions above.
    logging.info("Feature engineering process completed.")
    return df

# Example usage (can be run standalone for testing)
if __name__ == '__main__':
    # Create a sample DataFrame (index might be unsorted initially)
    dates = pd.to_datetime(['2023-01-04', '2023-01-03', '2023-01-05', '2023-01-06', '2023-01-09',
                           '2023-01-03', '2023-01-05', '2023-01-04', '2023-01-06', '2023-01-09'])
    data = {'close': [11, 10, 10.5, 12, 11.5, 50, 50.5, 51, 52, 51.5],
            'volume': [110, 100, 90, 120, 105, 200, 190, 210, 220, 205],
            'stock_id': ['TEST1'] * 5 + ['TEST2'] * 5}
    sample_df = pd.DataFrame(data, index=dates)
    sample_df.index.name = 'datetime'
    # Need open, high, low for full compatibility if other functions were added
    sample_df['open'] = sample_df['close'] - 0.5
    sample_df['high'] = sample_df['close'] + 0.5
    sample_df['low'] = sample_df['close'] - 1.0

    print("--- Original Unsorted Sample DataFrame ---")
    print(sample_df)

    # Engineer features
    featured_df = engineer_features(sample_df.copy()) # Pass a copy

    print("\n--- Sample DataFrame After Feature Engineering (Sorted by stock_id, datetime) ---")
    if featured_df is not None:
        print(featured_df)
        print("\nColumns added:", [col for col in featured_df.columns if col not in sample_df.columns])
    else:
        print("Failed to engineer features.")