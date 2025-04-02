#!/usr/bin/env python3
"""
stock_data.py - Retrieves daily OHLCV data for a stock over the past 12 months.

Usage:
    python quant/stock_data.py SYMBOL [--output OUTPUT_FILE]

Example:
    python quant/stock_data.py MSFT --output quant/msft_data.csv
"""

import os
import argparse
import datetime
import pandas as pd
from twelvedata import TDClient
from dotenv import load_dotenv

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Pull daily stock data for the last 12 months.')
    parser.add_argument('symbol', type=str, help='Stock symbol to retrieve data for (e.g., MSFT)')
    parser.add_argument('--output', type=str, help='Output CSV filename (default: quant/<symbol>_daily_data.csv)')
    return parser.parse_args()

def get_date_range():
    """Calculate the date range for the past 12 months."""
    end_date = datetime.datetime.now().date()
    start_date = end_date - datetime.timedelta(days=365)  # Approximately 12 months
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def fetch_stock_data(api_key, symbol, start_date, end_date):
    """Fetch daily stock data from Twelve Data API."""
    # Initialize client
    td = TDClient(apikey=api_key)

    # Create time series query
    ts = td.time_series(
        symbol=symbol,
        interval="1day",
        start_date=start_date,
        end_date=end_date,
        outputsize=5000 # Ensure we get all data points for the year
    )

    # Return data as pandas DataFrame
    return ts.as_pandas()

def save_to_csv(dataframe, filename):
    """Save the stock data to a CSV file."""
    # Ensure the directory exists if the filename includes a path
    output_dir = os.path.dirname(filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    dataframe.to_csv(filename)
    print(f"Data saved to {filename}")

def main():
    """Main function to orchestrate the stock data retrieval."""
    # Parse arguments
    args = parse_arguments()
    symbol = args.symbol.upper()
    
    # Default output path within the quant directory
    default_output_file = os.path.join('quant', f"{symbol}_daily_data.csv")
    output_file = args.output if args.output else default_output_file

    # Load API key from .env in the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(script_dir, '.env')
    load_dotenv(dotenv_path=dotenv_path)
    api_key = os.getenv("TWELVEKEY")

    if not api_key:
        print(f"ERROR: API key 'TWELVEKEY' not found in {dotenv_path}")
        return 1

    try:
        # Get date range
        start_date, end_date = get_date_range()
        print(f"Fetching daily data for {symbol} from {start_date} to {end_date}")

        # Fetch data
        data = fetch_stock_data(api_key, symbol, start_date, end_date)

        # Check if data is empty
        if data is None or data.empty:
            print(f"No data found for symbol {symbol} in the specified date range.")
            return 1

        # Save to CSV
        save_to_csv(data, output_file)

        return 0

    except Exception as e:
        print(f"ERROR: An error occurred: {e}")
        return 1

if __name__ == "__main__":
    exit(main())