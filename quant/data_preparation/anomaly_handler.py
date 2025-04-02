"""
Handles data anomalies such as missing trading days and provides placeholders
for stock split/dividend adjustments.
"""
import pandas as pd
import numpy as np
import logging
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def adjust_prices_for_splits_dividends(df):
    """
    Placeholder function to adjust OHLC prices for stock splits and dividends.

    NOTE: Accurate adjustment requires historical split/dividend data or
    using pre-adjusted data from the source. This implementation is a placeholder
    and does NOT perform adjustments. It should be replaced with a proper
    implementation if unadjusted data is used and high accuracy is required.

    Args:
        df (pd.DataFrame): DataFrame with stock data, indexed by datetime,
                           containing 'open', 'high', 'low', 'close' columns.

    Returns:
        pd.DataFrame: The input DataFrame, potentially with adjusted prices
                      (currently returns the DataFrame unchanged).
    """
    logging.warning("Stock split/dividend adjustment is NOT implemented. "
                    "Using raw prices. Ensure input data is adjusted or implement "
                    "adjustment logic here using external split/dividend data.")
    # TODO: Implement actual split/dividend adjustment logic here if needed.
    # Example heuristic (highly unreliable without external data):
    # - Calculate daily returns.
    # - Identify returns below a threshold (e.g., -20%) without corresponding market moves.
    # - Apply reverse adjustment factor based on the drop.
    # This is complex and error-prone. Using adjusted data source is preferred.
    return df

def handle_missing_trading_days(df):
    """
    Identifies and fills missing trading days within each stock's history
    using interpolation.

    Args:
        df (pd.DataFrame): Combined DataFrame for all stocks, indexed by datetime,
                           and containing a 'stock_id' column. Assumes data is
                           sorted by datetime.

    Returns:
        pd.DataFrame: DataFrame with missing trading days filled for each stock.
    """
    logging.info("Handling missing trading days...")
    all_stocks_filled = []

    # Handle empty input DataFrame gracefully
    if df.empty:
        logging.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df

    original_index_name = df.index.name # Store original index name

    unique_stocks = df['stock_id'].unique()
    total_stocks = len(unique_stocks)

    # Define US business days, excluding weekends and federal holidays
    us_business_days = CustomBusinessDay(calendar=USFederalHolidayCalendar())

    for i, stock_id in enumerate(unique_stocks):
        stock_df = df[df['stock_id'] == stock_id].copy()
        if stock_df.empty:
            continue

        logging.debug(f"Processing missing days for {stock_id} ({i+1}/{total_stocks})...")

        # Determine the full date range for this stock based on available data
        start_date = stock_df.index.min()
        end_date = stock_df.index.max()

        # Create the expected full range of business days
        expected_date_range = pd.date_range(start=start_date, end=end_date, freq=us_business_days)
        expected_date_range.name = original_index_name # Assign name to the new range

        # Reindex the DataFrame to include all expected business days, marking missing ones as NaN
        # The new index will have the name assigned above.
        stock_df_reindexed = stock_df.reindex(expected_date_range)

        # Forward-fill stock_id for the newly added NaN rows
        stock_df_reindexed['stock_id'] = stock_id

        # Identify rows that were originally missing
        missing_rows_mask = stock_df_reindexed['open'].isna() # Check one column like 'open'

        # Interpolate numerical columns (OHLCV)
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        cols_to_interpolate = [col for col in numeric_cols if col in stock_df_reindexed.columns]

        if not cols_to_interpolate:
             logging.warning(f"No numeric columns found to interpolate for {stock_id}. Skipping interpolation.")
        else:
            if missing_rows_mask.any():
                 logging.debug(f"Interpolating {missing_rows_mask.sum()} missing trading days for {stock_id}.")
                 stock_df_reindexed[cols_to_interpolate] = stock_df_reindexed[cols_to_interpolate].interpolate(method='linear', limit_direction='forward', axis=0)
                 stock_df_reindexed[cols_to_interpolate] = stock_df_reindexed[cols_to_interpolate].bfill(axis=0)
            else:
                 logging.debug(f"No missing trading days found for {stock_id}.")


        # Drop any remaining rows that couldn't be filled
        stock_df_filled = stock_df_reindexed.dropna(subset=cols_to_interpolate)

        all_stocks_filled.append(stock_df_filled)

        if (i + 1) % 100 == 0:
            logging.info(f"Processed missing days for {i+1}/{total_stocks} stocks...")

    if not all_stocks_filled:
        logging.warning("No stock data could be processed for missing days. Returning empty DataFrame.")
        # Return an empty DataFrame with the original structure
        empty_filled_df = pd.DataFrame(columns=df.columns).astype(df.dtypes)
        empty_filled_df = empty_filled_df.set_index(pd.DatetimeIndex([]))
        empty_filled_df.index.name = original_index_name
        return empty_filled_df


    logging.info("Combining data after handling missing days...")
    combined_filled_df = pd.concat(all_stocks_filled)
    combined_filled_df.sort_index(inplace=True) # Ensure final sort order
    combined_filled_df.index.name = original_index_name # Ensure final index name is preserved

    logging.info(f"Finished handling missing days. Resulting shape: {combined_filled_df.shape}")
    return combined_filled_df


# Example usage (can be run standalone for testing)
if __name__ == '__main__':
    # Create a sample DataFrame with missing days
    dates = pd.to_datetime(['2023-01-03', '2023-01-04', '2023-01-06', '2023-01-09']) # Skip Jan 5th (Thurs), Jan 7/8 (Weekend)
    data = {'open': [10, 11, 13, 14], 'close': [10.5, 11.5, 13.5, 14.5], 'volume': [100, 110, 130, 140], 'stock_id': ['TEST'] * 4}
    sample_df = pd.DataFrame(data, index=dates)
    sample_df.index.name = 'datetime'

    print("--- Original Sample DataFrame ---")
    print(sample_df)

    # Handle missing days
    filled_df = handle_missing_trading_days(sample_df.copy()) # Pass a copy

    print("\n--- Sample DataFrame After Handling Missing Days ---")
    if filled_df is not None:
        print(filled_df)
        print(f"Index name: {filled_df.index.name}") # Check index name
        # Check if Jan 5th was added and interpolated
        if pd.Timestamp('2023-01-05') in filled_df.index:
            print("\nMissing day 2023-01-05 was successfully interpolated.")
            print(filled_df.loc['2023-01-05'])
        else:
            print("\nMissing day 2023-01-05 was NOT found.")
    else:
        print("Failed to process sample data.")

    # Test empty input
    print("\n--- Testing Empty DataFrame Input ---")
    empty_input = pd.DataFrame(columns=['open', 'close', 'volume', 'stock_id']).set_index(pd.DatetimeIndex([]))
    empty_input.index.name = 'datetime'
    empty_output = handle_missing_trading_days(empty_input)
    print("Output for empty input:")
    print(empty_output)
    print(f"Is empty: {empty_output.empty}")
    print(f"Index name: {empty_output.index.name}")


    # Placeholder for split adjustment testing (currently does nothing)
    if filled_df is not None:
        adjusted_df = adjust_prices_for_splits_dividends(filled_df)
        print("\n--- Sample DataFrame After Placeholder Adjustment ---")
        print(adjusted_df)