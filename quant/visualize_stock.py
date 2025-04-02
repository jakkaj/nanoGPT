#!/usr/bin/env python3
"""
visualize_stock.py - Creates a candlestick chart for stock data.

Usage:
    python quant/visualize_stock.py [--input INPUT_CSV] [--output OUTPUT_PNG]

Example:
    python quant/visualize_stock.py --input quant/data/msft_data.csv --output quant/data/msft_visualization.png
"""

import os
import argparse
import pandas as pd
import mplfinance as mpf
import matplotlib

# Use a non-interactive backend suitable for saving files
matplotlib.use('Agg')

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Generate a candlestick chart for stock data.')
    parser.add_argument('--input', type=str, default='quant/data/msft_data.csv',
                        help='Input CSV filename (default: quant/data/msft_data.csv)')
    parser.add_argument('--output', type=str, default='quant/data/msft_visualization.png',
                        help='Output PNG filename (default: quant/data/msft_visualization.png)')
    parser.add_argument('--symbol', type=str, default='MSFT',
                        help='Stock symbol for the chart title (default: MSFT)')
    return parser.parse_args()

def prepare_data(csv_file):
    """Read and prepare the stock data from a CSV file."""
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"ERROR: Input file not found at {csv_file}")
        return None

    # Ensure required columns exist
    required_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
    if not all(col in df.columns for col in required_columns):
        print(f"ERROR: Input CSV must contain columns: {', '.join(required_columns)}")
        return None

    # Convert datetime to proper format and set as index
    try:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
    except Exception as e:
        print(f"ERROR: Could not parse datetime column: {e}")
        return None

    # Sort data chronologically (oldest to newest)
    df.sort_index(inplace=True)

    # Calculate moving averages
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA50'] = df['close'].rolling(window=50).mean()

    # Drop rows with NaN values created by rolling function
    df.dropna(inplace=True)

    return df

def create_visualization(df, output_file, symbol):
    """Create and save the candlestick visualization."""
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            print(f"ERROR: Could not create output directory {output_dir}: {e}")
            return False

    # Set up style for the chart
    mc = mpf.make_marketcolors(
        up='green', down='red',
        edge='inherit',
        wick={'up':'green', 'down':'red'}, # Use color for wicks too
        volume='inherit'
    )

    s = mpf.make_mpf_style(
        marketcolors=mc,
        gridstyle='--',
        y_on_right=False
    )

    # Create additional plots for moving averages
    additional_plots = [
        mpf.make_addplot(df['MA20'], color='blue', width=1, panel=0), # panel=0 for price panel
        mpf.make_addplot(df['MA50'], color='orange', width=1, panel=0) # panel=0 for price panel
    ]

    # Create the plot with volume and moving averages
    try:
        fig, axes = mpf.plot(
            df,
            type='candle',
            style=s,
            title=f'{symbol} Stock Price (1 Year)',
            ylabel='Price ($)',
            volume=True, # Automatically adds volume subplot
            ylabel_lower='Volume', # Label for volume subplot
            figsize=(14, 8), # Adjusted size for better readability
            addplot=additional_plots,
            mav=(20, 50), # Let mplfinance handle MAs directly if preferred, but addplot gives more control
            panel_ratios=(3,1), # Give more space to price chart
            returnfig=True
        )

        # Save the figure
        fig.savefig(output_file)
        print(f"Visualization saved to {output_file}")
        return True

    except Exception as e:
        print(f"ERROR: Failed to create or save visualization: {e}")
        return False

def main():
    """Main function to orchestrate the visualization generation."""
    args = parse_arguments()

    # Prepare the data
    print(f"Loading data from: {args.input}")
    df = prepare_data(args.input)

    if df is None or df.empty:
        print("Exiting due to data preparation errors.")
        return 1

    # Create the visualization
    print(f"Generating visualization for {args.symbol}...")
    success = create_visualization(df, args.output, args.symbol)

    if success:
        print("Visualization generated successfully.")
        return 0
    else:
        print("Visualization generation failed.")
        return 1

if __name__ == "__main__":
    exit(main())