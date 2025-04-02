"""
Loads historical stock data from multiple CSV files into a single DataFrame.
"""
import os
import pandas as pd
import logging
from pathlib import Path
from .data_utils import load_csv_data

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_all_stock_data(data_dir):
    """
    Loads all stock CSV files from the specified directory, combines them,
    and performs initial preprocessing.

    Args:
        data_dir (str or Path): The directory containing the historical stock CSV files.
                                Each file should be named '{stock_id}.csv'.

    Returns:
        pd.DataFrame: A single DataFrame containing data for all stocks,
                      sorted chronologically, with 'stock_id' column,
                      and 'datetime' as the index. Returns None if the directory
                      is invalid or no valid data is found.
    """
    data_path = Path(data_dir)
    if not data_path.is_dir():
        logging.error(f"Data directory not found or is not a directory: {data_dir}")
        return None

    all_dataframes = []
    csv_files = list(data_path.glob('*.csv'))
    total_files = len(csv_files)
    logging.info(f"Found {total_files} CSV files in {data_dir}. Starting load process...")

    processed_count = 0
    error_count = 0

    for i, file_path in enumerate(csv_files):
        stock_id = file_path.stem  # Get stock ID from filename without extension
        logging.debug(f"Processing file {i+1}/{total_files}: {file_path.name}")

        df = load_csv_data(file_path, stock_id)
        if df is not None:
            all_dataframes.append(df)
            processed_count += 1
        else:
            error_count += 1
            logging.warning(f"Failed to load or process {file_path.name}")

        # Optional: Log progress periodically
        if (i + 1) % 100 == 0:
            logging.info(f"Processed {i+1}/{total_files} files...")

    logging.info(f"Finished loading files. Successfully loaded: {processed_count}, Errors/Skipped: {error_count}")

    if not all_dataframes:
        logging.error("No valid stock data loaded. Cannot proceed.")
        return None

    # Combine all dataframes
    logging.info("Combining all loaded stock data into a single DataFrame...")
    combined_df = pd.concat(all_dataframes)

    # Ensure the final DataFrame is sorted by datetime index
    combined_df.sort_index(inplace=True)

    logging.info(f"Combined DataFrame created with shape: {combined_df.shape}")
    logging.info(f"Date range: {combined_df.index.min()} to {combined_df.index.max()}")
    logging.info(f"Unique stocks loaded: {combined_df['stock_id'].nunique()}")

    return combined_df

# Example usage (can be run standalone for testing)
if __name__ == '__main__':
    # Assuming the script is run from the project root (e.g., /workspaces/nanoGPT)
    # Adjust the path if necessary
    hist_data_directory = 'quant/data/historical'
    combined_data = load_all_stock_data(hist_data_directory)

    if combined_data is not None:
        print("\n--- Combined DataFrame Info ---")
        combined_data.info()
        print("\n--- Combined DataFrame Head ---")
        print(combined_data.head())
        print("\n--- Combined DataFrame Tail ---")
        print(combined_data.tail())
        print(f"\nTotal unique stocks loaded: {combined_data['stock_id'].nunique()}")
    else:
        print("Failed to load combined stock data.")