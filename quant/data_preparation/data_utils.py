"""
Utility functions for the data preparation pipeline.
"""
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_csv_data(file_path, stock_id):
    """
    Loads a single stock CSV file, adds stock_id, parses dates, and sorts.

    Args:
        file_path (str or Path): Path to the CSV file.
        stock_id (str): The stock identifier (ticker symbol).

    Returns:
        pd.DataFrame: Loaded and preprocessed DataFrame, or None if error.
    """
    try:
        df = pd.read_csv(file_path)
        required_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            logging.warning(f"Skipping {stock_id}: Missing required columns in {file_path}")
            return None

        df['datetime'] = pd.to_datetime(df['datetime'])
        df.sort_values('datetime', inplace=True)
        df.set_index('datetime', inplace=True)
        df['stock_id'] = stock_id
        return df
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return None
    except pd.errors.EmptyDataError:
        logging.warning(f"Skipping {stock_id}: Empty CSV file {file_path}")
        return None
    except Exception as e:
        logging.error(f"Error loading {stock_id} from {file_path}: {e}")
        return None

# Add more utility functions here as needed, e.g., for saving data, logging setup, etc.