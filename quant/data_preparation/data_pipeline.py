"""
Main pipeline script to orchestrate the data preparation process for the TFT model.

Loads raw data, cleans it, engineers features, creates time series windows,
and saves the processed data.
"""
import argparse
import logging
import time
import pandas as pd
from pathlib import Path

# Import necessary functions from other modules in the package
from .data_loader import load_all_stock_data
from .anomaly_handler import handle_missing_trading_days, adjust_prices_for_splits_dividends
from .feature_engineer import engineer_features
from .window_creator import create_windows_and_target

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Data preparation pipeline for stock prediction model.')
    parser.add_argument('--data-dir', type=str, required=True,
                        help='Directory containing raw historical stock CSV files (e.g., quant/data/historical).')
    parser.add_argument('--output-dir', type=str, required=True,
                        help='Directory to save the processed data (e.g., quant/data/processed).')
    parser.add_argument('--output-filename', type=str, default='processed_windowed_data.parquet',
                        help='Filename for the final processed Parquet file.')
    parser.add_argument('--window-size', type=int, default=60,
                        help='Number of time steps (trading days) in each input window.')
    parser.add_argument('--prediction-days', type=int, default=7,
                        help='Number of calendar days to look ahead for target calculation.')
    # Add flag for skipping split adjustment if needed
    parser.add_argument('--skip-split-adjustment', action='store_true',
                        help='Skip the (placeholder) split/dividend adjustment step.')

    return parser.parse_args()

def main():
    """Runs the full data preparation pipeline."""
    args = parse_arguments()
    start_time = time.time()

    logging.info("--- Starting Data Preparation Pipeline ---")
    logging.info(f"Raw data directory: {args.data_dir}")
    logging.info(f"Output directory: {args.output_dir}")
    logging.info(f"Window size: {args.window_size}")
    logging.info(f"Prediction lookahead: {args.prediction_days} calendar days")

    # --- 1. Load Data ---
    logging.info("Step 1: Loading all stock data...")
    combined_df = load_all_stock_data(args.data_dir)
    if combined_df is None:
        logging.error("Pipeline failed: Could not load initial data.")
        return 1
    logging.info(f"Initial data loaded. Shape: {combined_df.shape}")

    # --- 2. Handle Anomalies ---
    # 2a. Adjust for Splits/Dividends (Placeholder)
    if not args.skip_split_adjustment:
        logging.info("Step 2a: Applying split/dividend adjustments (placeholder)...")
        # Note: This currently does nothing unless implemented in anomaly_handler.py
        combined_df = adjust_prices_for_splits_dividends(combined_df)
        logging.info("Split/dividend adjustment step completed.")
    else:
        logging.info("Step 2a: Skipping split/dividend adjustments.")

    # 2b. Handle Missing Trading Days
    logging.info("Step 2b: Handling missing trading days...")
    combined_df = handle_missing_trading_days(combined_df)
    if combined_df is None:
        logging.error("Pipeline failed: Could not handle missing trading days.")
        return 1
    logging.info(f"Missing days handled. Shape after interpolation: {combined_df.shape}")

    # --- 3. Feature Engineering ---
    logging.info("Step 3: Engineering features...")
    combined_df = engineer_features(combined_df)
    # Drop rows with NaNs introduced by feature engineering (e.g., initial MA values)
    initial_rows = len(combined_df)
    combined_df.dropna(inplace=True)
    rows_dropped = initial_rows - len(combined_df)
    logging.info(f"Features engineered. Shape after dropping NaNs: {combined_df.shape} ({rows_dropped} rows dropped)")
    if combined_df.empty:
        logging.error("Pipeline failed: No data remaining after feature engineering and NaN removal.")
        return 1


    # --- 4. Window Creation & Target Generation ---
    # Note: Target calculation is now integrated within create_windows_and_target
    logging.info("Step 4: Creating windows and target variable...")
    windowed_df = create_windows_and_target(combined_df,
                                            window_size=args.window_size,
                                            prediction_days=args.prediction_days)
    if windowed_df is None:
        logging.error("Pipeline failed: Could not create windows.")
        return 1
    logging.info(f"Windows created successfully. Final shape: {windowed_df.shape}")

    # --- 5. Save Output ---
    logging.info("Step 5: Saving processed data...")
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True) # Ensure output directory exists
    output_file = output_path / args.output_filename

    try:
        windowed_df.to_parquet(output_file, index=False) # Save without index as it's part of the columns now
        logging.info(f"Processed data saved successfully to: {output_file}")
    except Exception as e:
        logging.error(f"Failed to save processed data to {output_file}: {e}")
        return 1

    end_time = time.time()
    total_time = end_time - start_time
    logging.info(f"--- Data Preparation Pipeline Finished ---")
    logging.info(f"Total execution time: {total_time:.2f} seconds")

    return 0

if __name__ == "__main__":
    exit_code = main()
    if exit_code == 0:
        print("Pipeline completed successfully.")
    else:
        print("Pipeline failed.")
    exit(exit_code)