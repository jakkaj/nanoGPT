#!/usr/bin/env python3
"""
top_performers.py - Downloads 12-month historical data for stocks and calculates top performers.

Usage:
  # Mode 1: Download historical data for all stocks
  python quant/top_performers.py download [--hist-dir HIST_DIR] [--exchanges EXCHANGES [EXCHANGES ...]] [--use-cache]

  # Mode 2: Calculate top performers from downloaded data
  python quant/top_performers.py calculate [--hist-dir HIST_DIR] [--limit LIMIT] [--output OUTPUT_FILE]

Examples:
  # Download data for NYSE & NASDAQ stocks to quant/data/historical/
  python quant/top_performers.py download --hist-dir quant/data/historical --use-cache

  # Calculate top 500 performers from quant/data/historical/ and save to quant/data/top500_performers.csv
  python quant/top_performers.py calculate --hist-dir quant/data/historical --limit 500 --output quant/data/top500_performers.csv
"""

import os
import time
import argparse
import datetime
import pandas as pd
import logging
import sys
from twelvedata import TDClient
from twelvedata.exceptions import TwelveDataError
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
LOOKBACK_DAYS = 365
API_CALLS_PER_MINUTE = 377 # Updated limit
SECONDS_PER_MINUTE = 60
# Add a small buffer to the delay to be safe
# DELAY_BETWEEN_CALLS = (SECONDS_PER_MINUTE / API_CALLS_PER_MINUTE) + 0.5 # No longer needed with high rate limit
DEFAULT_HIST_DIR = 'quant/data/historical'
DEFAULT_OUTPUT_FILE = 'quant/data/top_performers.csv'
STOCK_LIST_CACHE_FILE = 'quant/data/stock_list_cache.json'

def parse_arguments():
    """Parse command-line arguments with subcommands."""
    parser = argparse.ArgumentParser(description='Download stock data and calculate top performers.')
    subparsers = parser.add_subparsers(dest='mode', required=True, help='Operation mode: download or calculate')

    # --- Download Mode Arguments ---
    parser_download = subparsers.add_parser('download', help='Download 12-month historical data for stocks.')
    parser_download.add_argument('--hist-dir', type=str, default=DEFAULT_HIST_DIR,
                                 help=f'Directory to save historical CSV files (default: {DEFAULT_HIST_DIR})')
    parser_download.add_argument('--exchanges', nargs='+', default=['NYSE', 'NASDAQ'],
                                 help='List of exchanges to query (default: NYSE NASDAQ)')
    parser_download.add_argument('--use-cache', action='store_true',
                                 help=f'Use cached stock list ({STOCK_LIST_CACHE_FILE}) if available')

    # --- Calculate Mode Arguments ---
    parser_calculate = subparsers.add_parser('calculate', help='Calculate top performers from downloaded data.')
    parser_calculate.add_argument('--hist-dir', type=str, default=DEFAULT_HIST_DIR,
                                  help=f'Directory containing historical CSV files (default: {DEFAULT_HIST_DIR})')
    parser_calculate.add_argument('--limit', type=int, default=500,
                                  help='Number of top performers to retrieve (default: 500)')
    parser_calculate.add_argument('--output', type=str, default=DEFAULT_OUTPUT_FILE,
                                  help=f'Output CSV filename for top performers (default: {DEFAULT_OUTPUT_FILE})')

    return parser.parse_args()

def load_api_key():
    """Load Twelve Data API key from .env file."""
    # Look for .env in the script's directory or parent directories if needed
    script_dir = Path(__file__).parent.resolve()
    dotenv_path = script_dir / '.env'
    if not dotenv_path.exists() and script_dir.parent:
         # Try parent directory if not found in script dir (e.g., running from project root)
         dotenv_path_parent = script_dir.parent / '.env'
         if dotenv_path_parent.exists():
              dotenv_path = dotenv_path_parent
         else:
              # Check project root specifically if structure is /project/quant/.env
              project_root_env = script_dir.parent / '.env' # Assuming script is in quant/
              if project_root_env.exists():
                   dotenv_path = project_root_env

    if not dotenv_path.exists():
         logging.error(f".env file not found in {script_dir} or its parent.")
         raise ValueError("API key .env file not found.")

    load_dotenv(dotenv_path=dotenv_path)
    api_key = os.getenv("TWELVEKEY")
    if not api_key:
        logging.error(f"API key 'TWELVEKEY' not found in {dotenv_path}")
        raise ValueError("API key 'TWELVEKEY' not found in .env file.")
    logging.info(f"Loaded API key from {dotenv_path}")
    return api_key


def get_stock_list(td_client, exchanges, use_cache=False):
    """Get list of all stocks from specified exchanges, using cache if requested."""
    cache_path = Path(STOCK_LIST_CACHE_FILE)
    if use_cache and cache_path.exists():
        logging.info(f"Loading stock list from cache: {cache_path}")
        try:
            stock_df = pd.read_json(cache_path)
            if 'symbol' in stock_df.columns and 'exchange' in stock_df.columns:
                # Filter by requested exchanges from the cached list
                filtered_stocks = stock_df[stock_df['exchange'].isin(exchanges)]
                logging.info(f"Loaded {len(filtered_stocks)} stocks for {exchanges} from cache.")
                return filtered_stocks.to_dict('records')
            else:
                logging.warning("Cache file format unexpected. Fetching fresh list.")
        except Exception as e:
            logging.warning(f"Failed to load stock list from cache: {e}. Fetching fresh list.")

    logging.info(f"Fetching stock list for exchanges: {exchanges}")
    all_stocks_data = []
    api_call_count = 0
    minute_start_time = time.time()

    for exchange in exchanges:
        try:
            # --- Rate Limiting Check ---
            current_time = time.time()
            if api_call_count >= API_CALLS_PER_MINUTE and (current_time - minute_start_time) < SECONDS_PER_MINUTE:
                sleep_time = SECONDS_PER_MINUTE - (current_time - minute_start_time) + 1 # Buffer
                logging.info(f"Rate limit reached fetching stock list. Sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
                minute_start_time = time.time() # Reset timer
                api_call_count = 0 # Reset count

            logging.info(f"Fetching stocks for {exchange}...")
            stocks = td_client.get_stocks_list(exchange=exchange)
            api_call_count += 1
            stock_data = stocks.as_json()

            if isinstance(stock_data, list):
                for stock in stock_data:
                    stock['exchange'] = exchange # Add exchange info
                all_stocks_data.extend(stock_data)
                logging.info(f"Fetched {len(stock_data)} stocks for {exchange}.")
            else:
                logging.warning(f"Received unexpected data type for {exchange}: {type(stock_data)}")

            # Small delay between exchange list calls
            time.sleep(0.2) # Reduced delay with higher rate limit

        except TwelveDataError as e:
            logging.error(f"API error fetching stocks for {exchange}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error fetching stocks for {exchange}: {e}")

    # Save to cache if fetched successfully
    if all_stocks_data:
        try:
            stock_df = pd.DataFrame(all_stocks_data)
            cache_path.parent.mkdir(parents=True, exist_ok=True) # Ensure dir exists
            stock_df.to_json(cache_path, orient='records', indent=4)
            logging.info(f"Saved stock list to cache: {cache_path}")
        except Exception as e:
            logging.error(f"Failed to save stock list to cache: {e}")

    return all_stocks_data

def download_historical_data(td_client, stock_list, hist_dir):
    """Downloads 12-month historical data for each stock in the list."""
    hist_path = Path(hist_dir)
    hist_path.mkdir(parents=True, exist_ok=True) # Ensure directory exists
    logging.info(f"Starting download of historical data to {hist_path}...")

    total_stocks = len(stock_list)
    api_call_count = 0
    minute_start_time = time.time()
    downloaded_count = 0
    skipped_count = 0
    error_count = 0

    end_date = datetime.datetime.now().date()
    start_date = end_date - datetime.timedelta(days=LOOKBACK_DAYS)
    end_date_str = end_date.strftime('%Y-%m-%d')
    start_date_str = start_date.strftime('%Y-%m-%d')

    for i, stock in enumerate(stock_list):
        symbol = stock.get('symbol')
        exchange = stock.get('exchange')
        country = stock.get('country') # Optional

        if not symbol or not exchange:
            logging.warning(f"Skipping stock {i+1}/{total_stocks} due to missing symbol/exchange: {stock}")
            skipped_count += 1
            continue

        # Sanitize symbol for filename if necessary (though usually not needed for tickers)
        safe_symbol = "".join(c for c in symbol if c.isalnum() or c in ('-', '.'))
        output_csv = hist_path / f"{safe_symbol}.csv"

        # --- Check if file already exists (Resume capability) ---
        if output_csv.exists():
            logging.debug(f"Skipping {symbol} ({i+1}/{total_stocks}): Already downloaded ({output_csv})")
            skipped_count += 1
            continue

        # --- Rate Limiting ---
        current_time = time.time()
        if api_call_count >= API_CALLS_PER_MINUTE:
             elapsed_time = current_time - minute_start_time
             if elapsed_time < SECONDS_PER_MINUTE:
                  sleep_time = SECONDS_PER_MINUTE - elapsed_time + 0.1 # Small buffer
                  logging.info(f"Rate limit reached ({api_call_count} calls). Sleeping for {sleep_time:.2f} seconds before processing {symbol}.")
                  time.sleep(sleep_time)
             # Reset timer and count for the new minute window
             minute_start_time = time.time()
             api_call_count = 0

        # --- Fetch Data ---
        logging.info(f"Processing {i+1}/{total_stocks}: Downloading {symbol} ({exchange})...")
        try:
            ts = td_client.time_series(
                symbol=symbol,
                exchange=exchange,
                country=country,
                interval="1day",
                start_date=start_date_str,
                end_date=end_date_str,
                outputsize=5000 # Ensure we get all data points for the year
            )
            api_call_count += 1
            data = ts.as_pandas()

            if data is not None and not data.empty:
                data.to_csv(output_csv)
                logging.debug(f"Successfully downloaded and saved data for {symbol} to {output_csv}")
                downloaded_count += 1
            else:
                logging.warning(f"No data returned for {symbol}. Skipping save.")
                # Optionally create an empty file or log separately
                skipped_count += 1

        except TwelveDataError as e:
            error_count += 1
            # Handle common API errors gracefully
            if "rate limit" in str(e).lower():
                 # This might still happen if the burst limit is hit, or daily limit
                 logging.error(f"Rate limit error during download for {symbol}: {e}. Check daily limits if applicable. Stopping.")
                 sys.exit(1) # Exit immediately if rate limit error occurs unexpectedly
            elif "not found" in str(e).lower() or "invalid symbol" in str(e).lower():
                 logging.warning(f"Symbol {symbol} not found or invalid: {e}")
                 # Optionally create an empty file or log separately
            else:
                 logging.error(f"API error downloading {symbol}: {e}")
        except Exception as e:
            error_count += 1
            logging.error(f"Unexpected error downloading {symbol}: {e}")

        # --- Delay between calls ---
        # With a high rate limit, a fixed delay is less critical,
        # but a very small one can still be polite to the API.
        # time.sleep(0.05) # Optional tiny delay

    logging.info(f"Download process finished.")
    logging.info(f"Total Stocks: {total_stocks}")
    logging.info(f"Successfully Downloaded: {downloaded_count}")
    logging.info(f"Skipped (Already Existed or No Data): {skipped_count}")
    logging.info(f"Errors: {error_count}")


def calculate_performance(hist_dir, limit, output_file):
    """Calculates performance from downloaded CSVs and saves top performers."""
    hist_path = Path(hist_dir)
    if not hist_path.is_dir():
        logging.error(f"Historical data directory not found: {hist_path}")
        return

    logging.info(f"Calculating performance from CSV files in {hist_path}...")
    results = []
    processed_count = 0
    error_count = 0

    csv_files = list(hist_path.glob('*.csv'))
    total_files = len(csv_files)
    logging.info(f"Found {total_files} CSV files to process.")

    for i, csv_file in enumerate(csv_files):
        symbol = csv_file.stem # Get symbol from filename
        logging.debug(f"Processing file {i+1}/{total_files}: {csv_file.name}")

        try:
            df = pd.read_csv(csv_file, index_col='datetime', parse_dates=True)

            if df.empty or len(df) < 2:
                logging.warning(f"Skipping {symbol}: Not enough data in CSV.")
                continue

            # Ensure data is sorted by date
            df.sort_index(inplace=True)

            # Find the earliest and latest data points within the approximate 12-month window
            # (Data might not cover the full 365 days exactly)
            end_date_target = df.index.max()
            start_date_target = end_date_target - pd.Timedelta(days=LOOKBACK_DAYS - 1) # Look back ~1 year from latest point

            # Find closest available points
            start_data = df[df.index >= start_date_target]
            end_data = df[df.index <= end_date_target] # Should just be the last point

            if start_data.empty or end_data.empty:
                 logging.warning(f"Skipping {symbol}: Could not find data points within the ~12 month range.")
                 continue

            start_price_row = start_data.iloc[0]
            end_price_row = end_data.iloc[-1]

            start_price = start_price_row['close']
            end_price = end_price_row['close']

            if pd.isna(start_price) or pd.isna(end_price) or start_price == 0 or start_price < 0:
                logging.warning(f"Skipping {symbol}: Invalid start/end price (Start: {start_price}, End: {end_price})")
                continue

            increase_percent = ((end_price - start_price) / start_price) * 100
            results.append({'symbol': symbol, 'increase_pct': increase_percent})
            processed_count += 1

        except pd.errors.EmptyDataError:
             logging.warning(f"Skipping {symbol}: CSV file is empty ({csv_file.name}).")
             error_count += 1
        except KeyError as e:
             logging.warning(f"Skipping {symbol}: Missing expected column ('datetime' or 'close') in {csv_file.name}. Error: {e}")
             error_count += 1
        except Exception as e:
            logging.error(f"Error processing file {csv_file.name} for symbol {symbol}: {e}")
            error_count += 1

    logging.info(f"Calculation process finished.")
    logging.info(f"Successfully Calculated: {processed_count}")
    logging.info(f"Errors/Skipped during calculation: {error_count}")

    if not results:
        logging.error("No valid performance results were calculated.")
        return

    # Sort and filter results
    results_df = pd.DataFrame(results)
    results_df['increase_pct'] = pd.to_numeric(results_df['increase_pct'], errors='coerce')
    results_df.dropna(subset=['increase_pct'], inplace=True)
    sorted_df = results_df.sort_values(by='increase_pct', ascending=False)
    top_performers = sorted_df.head(limit)

    logging.info(f"Selected top {len(top_performers)} performers.")

    # Save to CSV
    output_df = top_performers[['symbol']] # Select only the symbol column

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True) # Ensure output directory exists
    output_df.to_csv(output_path, index=False)
    logging.info(f"Top {limit} stock symbols saved to {output_path}")


def main():
    """Main function to dispatch based on mode."""
    args = parse_arguments()

    try:
        if args.mode == 'download':
            api_key = load_api_key()
            td = TDClient(apikey=api_key)
            stock_list = get_stock_list(td, args.exchanges, args.use_cache)
            if not stock_list:
                logging.error("Failed to retrieve stock list. Exiting.")
                return 1
            logging.info(f"Retrieved {len(stock_list)} unique stock symbols for download.")
            download_historical_data(td, stock_list, args.hist_dir)

        elif args.mode == 'calculate':
            calculate_performance(args.hist_dir, args.limit, args.output)

        return 0

    except ValueError as e: # Catch API key error
        logging.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}") # Log full traceback
        return 1

if __name__ == "__main__":
    exit_code = main()
    logging.info(f"Script finished with exit code {exit_code}.")
    exit(exit_code)