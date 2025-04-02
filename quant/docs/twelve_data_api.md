# Twelve Data Python API – Retrieving Daily Historical Stock Data

This guide demonstrates how to use the **Twelve Data** Python API to pull daily historical stock data. It assumes you already have a Twelve Data API key, but no prior experience with Twelve Data. We’ll cover setting up the Python client, authenticating with your API key, and retrieving daily time series (OHLCV) data for a stock symbol. Code examples are provided for both retrieving the last N days of data and fetching data for a specific date range. We also explain the response format and important limitations (like free plan usage limits and ticker symbol formats).

## Introduction to Twelve Data

Twelve Data is a financial data platform providing real-time and historical market data for stocks, forex, crypto, and more ([Master the Twelve Data API with Python: A Comprehensive Tutorial - Analyzing Alpha](https://analyzingalpha.com/twelve-data-api-python-tutorial#:~:text=What%20Is%20Twelve%20Data%3F)). It offers a unified, user-friendly API and official SDKs (including a Python client) to easily integrate market data into applications ([Master the Twelve Data API with Python: A Comprehensive Tutorial - Analyzing Alpha](https://analyzingalpha.com/twelve-data-api-python-tutorial#:~:text=Setting%20Up%20Twelve%20Data%20Python,API%20Library)). For historical stock prices, Twelve Data’s API can return **daily OHLCV** (Open, High, Low, Close, Volume) values over many years of trading history ([Historical data | Twelve Data Support](https://support.twelvedata.com/en/articles/5194454-historical-data#:~:text=The%20depth%20of%20historical%20data,few%20months%20to%20a%20year)) ([Free Market Data for Python using Twelve Data API - DEV Community](https://dev.to/midassss/free-market-data-for-python-using-twelve-data-api-4ij2#:~:text=The%20Twelve%20Data%20API%20provides,the%20following%20features)). The free _Basic_ plan is generous, allowing up to 8 API calls per minute and 800 calls per day ([API credits limits | Twelve Data Support](https://support.twelvedata.com/en/articles/5194820-api-credits-limits#:~:text=Basic%20plan)) – more than enough for most data retrieval tasks.

## Installation and Setup

Before coding, install the official Twelve Data Python SDK. You can install it via pip:

```bash
pip install twelvedata
```

This will install the base library. (Optionally, you can install extras like Pandas support via `pip install twelvedata[pandas]` if you plan to use dataframes ([Master the Twelve Data API with Python: A Comprehensive Tutorial - Analyzing Alpha](https://analyzingalpha.com/twelve-data-api-python-tutorial#:~:text=pip%C2%A0install%C2%A0twelvedata)).) After installation, import the `TDClient` class and initialize it with your API key:

```python
from twelvedata import TDClient

# Initialize the Twelve Data client with your API key
td = TDClient(apikey="YOUR_API_KEY_HERE")
```

The `TDClient` object is the base for all API calls ([Get High-Quality Financial Data Directly into Python](https://twelvedata.com/blog/get-high-quality-financial-data-directly-into-python#:~:text=The%20base%20object%20for%20all,it%20throughout%20the%20whole%20application)). You should create it once at the start of your script or application, and reuse it for all data requests. The `apikey` parameter is required to authenticate your requests with Twelve Data ([GitHub - twelvedata/twelvedata-python: Twelve Data Python Client - Financial data API & WebSocket](https://github.com/twelvedata/twelvedata-python#:~:text=from%20twelvedata%20import%20TDClient)). (Ensure you replace `"YOUR_API_KEY_HERE"` with your actual API key. For security, you might store the key in an environment variable and read it in Python, rather than hardcoding it.)

## Fetching Daily Historical Stock Data

Once the client is set up, you can retrieve historical time series data using the `TDClient.time_series()` method. This method accepts parameters to specify **which symbol** and **what timeframe** and returns an object you can convert to various formats (JSON, CSV, Pandas DataFrame, etc.) ([GitHub - twelvedata/twelvedata-python: Twelve Data Python Client - Financial data API & WebSocket](https://github.com/twelvedata/twelvedata-python#:~:text=,return%20list%20of%20URLs%20used)) ([GitHub - twelvedata/twelvedata-python: Twelve Data Python Client - Financial data API & WebSocket](https://github.com/twelvedata/twelvedata-python#:~:text=ts%20%3D%20td.time_series%28%20symbol%3D,)). For daily historical prices, the key parameters are:

- **`symbol`** – The stock ticker symbol. For example `"AAPL"` for Apple Inc.
- **`interval`** – The data frequency. Use `"1day"` for daily data (valid interval values include 1min, 5min, 15min, 1h, 1day, 1week, 1month, etc. ([Master the Twelve Data API with Python: A Comprehensive Tutorial - Analyzing Alpha](https://analyzingalpha.com/twelve-data-api-python-tutorial#:~:text=The%20interval%20parameter%20of%20the,4h%2C%208h%2C%201day%2C%201week%2C%201month))).
- **`outputsize`** – _(Optional)_ The number of data points (days) to return. If not specified, the API returns the last **30** trading days by default ([First introduction: getting an advantage in a few minutes](https://twelvedata.com/blog/first-introduction-getting-an-advantage-in-a-few-minutes#:~:text=All%20requests%20are%20available%20in,by%20default%20equals%2030)). You can set `outputsize` to request more days (e.g. 100 or 500 days).
- **`start_date`** and **`end_date`** – _(Optional)_ Specific date range for the query, in `"YYYY-MM-DD"` (or `"YYYY-MM-DD HH:MM:SS"`) format ([Master the Twelve Data API with Python: A Comprehensive Tutorial - Analyzing Alpha](https://analyzingalpha.com/twelve-data-api-python-tutorial#:~:text=You%20can%20also%20pass%20values,to%20filter%20the%20sampling%20period)). Use these if you want data between certain dates. If provided, the API will return data from the start date up to the end date (or the latest available date).
- **`timezone`** – _(Optional)_ Time zone for date/times in the output. By default, data is in the asset’s exchange timezone, but you can specify one (e.g. `"America/New_York"`) if needed ([GitHub - twelvedata/twelvedata-python: Twelve Data Python Client - Financial data API & WebSocket](https://github.com/twelvedata/twelvedata-python#:~:text=ts%20%3D%20td.time_series%28%20symbol%3D,)).

Below we show how to pull daily historical data in two ways: by requesting the last N days and by specifying an exact date range.

### Example 1: Retrieve the Last N Days of Daily Data

To get the most recent N days of daily prices for a stock, use the `outputsize` parameter. For example, the code below fetches the last 100 trading days of daily data for Apple (AAPL):

```python
# Fetch the last 100 days of daily OHLCV data for AAPL
ts = td.time_series(
    symbol="AAPL",
    interval="1day",
    outputsize=100  # number of days of data to retrieve
)
data = ts.as_json()  # get the data in JSON (dict) format
```

In this code, `td.time_series()` creates a time series query for AAPL with daily interval. We specify `outputsize=100` to request the 100 most recent daily data points. Without `outputsize`, it would default to 30 days ([First introduction: getting an advantage in a few minutes](https://twelvedata.com/blog/first-introduction-getting-an-advantage-in-a-few-minutes#:~:text=)). Calling `.as_json()` on the result executes the API call and returns the data in JSON format (as a Python dictionary) ([GitHub - twelvedata/twelvedata-python: Twelve Data Python Client - Financial data API & WebSocket](https://github.com/twelvedata/twelvedata-python#:~:text=,return%20list%20of%20URLs%20used)).

> **Note:** Instead of JSON, you can also retrieve the data directly as a Pandas DataFrame with `.as_pandas()` or as CSV text with `.as_csv()` ([GitHub - twelvedata/twelvedata-python: Twelve Data Python Client - Financial data API & WebSocket](https://github.com/twelvedata/twelvedata-python#:~:text=,return%20list%20of%20URLs%20used)). Using a DataFrame is convenient for analysis and plotting, whereas JSON is useful for programmatic parsing. In this guide, we use JSON to illustrate the response structure.

### Example 2: Retrieve Daily Data for a Date Range

If you need historical data for a specific period (e.g. a particular year or month), use the `start_date` and `end_date` parameters. For example, the code below fetches daily OHLCV data for AAPL from October 1, 2020 through December 31, 2020:

```python
# Fetch daily data for AAPL within a specific date range
ts = td.time_series(
    symbol="AAPL",
    interval="1day",
    start_date="2020-10-01",
    end_date="2020-12-31"
)
data = ts.as_json()  # get the data for that date range in JSON format
```

Here, we specify `interval="1day"` and provide `start_date` and `end_date` in `YYYY-MM-DD` format. The Twelve Data API will return all daily records from the start date up to the end date (inclusive) ([Master the Twelve Data API with Python: A Comprehensive Tutorial - Analyzing Alpha](https://analyzingalpha.com/twelve-data-api-python-tutorial#:~:text=You%20can%20also%20pass%20values,to%20filter%20the%20sampling%20period)). You could also include an `outputsize` in this query (the API allows combining both date range and output size ([Get High-Quality Financial Data Directly into Python](https://twelvedata.com/blog/get-high-quality-financial-data-directly-into-python#:~:text=To%20select%20all%20data%20between,01%60%2C%20we%20set%20date%20parameters)) ([Get High-Quality Financial Data Directly into Python](https://twelvedata.com/blog/get-high-quality-financial-data-directly-into-python#:~:text=Both%20,may%20also%20be%20used%20simultaneously))), but when a date range is given, it usually isn’t necessary to use `outputsize` unless you want to impose an additional limit on the number of points.

After constructing the query with `td.time_series(...)`, we again call `.as_json()` to execute it and retrieve the results as a dictionary.

## Understanding the Response Format

When you call `.as_json()`, the Twelve Data client returns a Python dictionary representing the JSON response. The **structure** of this response is typically:

- A **"meta"** field containing metadata about the request (e.g. the symbol, interval, currency, exchange, and other information about the time series) ([Twelve Data | Stock, Forex, and Crypto Market Data APIs](https://twelvedata.com/#:~:text=timeSeries.meta%5B,close)).
- A **"values"** field containing a list of data points (each data point is a dictionary of OHLCV values with a timestamp).
- A **"status"** field indicating the result of the request (e.g. `"ok"` for success). If there was an error, you would get an error code/message instead of the values.

For example, `data = ts.as_json()` for the above queries would yield a dictionary `data` with `data["meta"]` and `data["values"]` keys (and a status). Each entry in `data["values"]` represents one trading day’s record, including the date/time and prices. You can iterate through this list to access individual days. A single daily data point might look like this (illustrative format):

```python
# Example of accessing the returned data
meta_info = data["meta"]
print("Retrieved symbol:", meta_info["symbol"])         # e.g. "AAPL"
print("Data interval:", meta_info["interval"])          # e.g. "1day"
print("Currency:", meta_info.get("currency", "USD"))    # e.g. "USD"

# List of daily values:
values_list = data["values"]
print("Number of days returned:", len(values_list))
# Print the most recent day (first in the list)
latest_day = values_list[0]
print("Date:", latest_day["datetime"])
print("Open:", latest_day["open"])
print("High:", latest_day["high"])
print("Low:", latest_day["low"])
print("Close:", latest_day["close"])
print("Volume:", latest_day["volume"])
```

In the `values_list`, each element is a dictionary with keys like `"datetime"`, `"open"`, `"high"`, `"low"`, `"close"`, and `"volume"`. These represent the date/time of the quote and the OHLCV prices for that day ([Free Market Data for Python using Twelve Data API - DEV Community](https://dev.to/midassss/free-market-data-for-python-using-twelve-data-api-4ij2#:~:text=The%20Twelve%20Data%20API%20provides,the%20following%20features)). The snippet above shows how you might access the latest day's data. (Note: The `"datetime"` is typically in UTC or the specified timezone, formatted as a string like `"2020-12-31"` for daily data.)

If you chose `.as_pandas()` instead, the data would come back as a Pandas DataFrame, with each row representing a date (indexed by the date) and columns for open, high, low, close, volume ([GitHub - twelvedata/twelvedata-python: Twelve Data Python Client - Financial data API & WebSocket](https://github.com/twelvedata/twelvedata-python#:~:text=)). For many, the DataFrame format can be easier to work with (you can directly call `ts.as_pandas()` to get it). Under the hood, both formats contain the same information.

## Additional Notes and Limitations

When using Twelve Data’s API for daily stock data, keep in mind the following:

- **API Key Authentication:** Always provide your API key when initializing `TDClient` ([Get High-Quality Financial Data Directly into Python](https://twelvedata.com/blog/get-high-quality-financial-data-directly-into-python#:~:text=The%20base%20object%20for%20all,it%20throughout%20the%20whole%20application)). Without a valid key, requests will fail authentication. The examples above show passing it directly; in practice you may use a secure method (like environment variables) to handle the key.

- **Free Plan Limits:** The free _Basic_ plan allows up to **8 API calls per minute** and **800 calls per day** ([API credits limits | Twelve Data Support](https://support.twelvedata.com/en/articles/5194820-api-credits-limits#:~:text=Basic%20plan)). Each time_series request counts as one API call. If you need to fetch a very long history day-by-day, you may need to pause between batches to stay within rate limits. (Higher-tier plans remove the daily cap and have higher per-minute limits ([API credits limits | Twelve Data Support](https://support.twelvedata.com/en/articles/5194820-api-credits-limits#:~:text=Premium%20plans)).) The data itself for daily intervals is not truncated in free plan – you can retrieve decades of daily data, subject to the call limits. In fact, for stocks, **daily data goes back to the stock’s first trading day** ([Historical data | Twelve Data Support](https://support.twelvedata.com/en/articles/5194454-historical-data#:~:text=The%20depth%20of%20historical%20data,few%20months%20to%20a%20year)), providing a complete price history (you might retrieve it in chunks if it's very large).

- **Symbol Formats:** For US stocks and many popular tickers, you can just use the ticker symbol (e.g. `"AAPL"` or `"MSFT"`). Twelve Data will default to the primary exchange for that symbol. If a ticker is ambiguous or traded on multiple exchanges, you can specify the exchange or country. The `time_series` method accepts `exchange` and `country` parameters for stocks ([Get High-Quality Financial Data Directly into Python](https://twelvedata.com/blog/get-high-quality-financial-data-directly-into-python#:~:text=Stocks%20also%20accept%20,exchange)). For example, to get Toyota stock in Tokyo you might use `symbol="7203"` with `exchange="TSE"` or `country="Japan"`. In the Python client, you can also specify a composite symbol string like `"BTC/USD:Huobi"` for crypto with a specific exchange ([GitHub - twelvedata/twelvedata-python: Twelve Data Python Client - Financial data API & WebSocket](https://github.com/twelvedata/twelvedata-python#:~:text=ts%20%3D%20td.time_series%28%20symbol%3D,)), but for clarity it's usually better to use the separate `exchange` argument. (Cryptocurrency pairs require an exchange since they trade on multiple markets ([Get High-Quality Financial Data Directly into Python](https://twelvedata.com/blog/get-high-quality-financial-data-directly-into-python#:~:text=Stocks%20also%20accept%20,exchange)).) Always ensure the symbol is in the correct format as per Twelve Data’s documentation – you can consult Twelve Data’s reference data endpoints (like `get_stocks_list`) to find exact ticker and exchange codes if needed.

- **Time Zone and Data Timing:** Daily stock data typically includes only trading days. Weekends and holidays will be skipped (no entries for those dates). The `"datetime"` for daily data usually appears as the date (with time 00:00:00 or no time component). By default, data is aligned to the exchange’s time zone. If you need the timestamps in a specific time zone (for example, all dates in GMT or in New York time), use the `timezone` parameter as shown earlier ([GitHub - twelvedata/twelvedata-python: Twelve Data Python Client - Financial data API & WebSocket](https://github.com/twelvedata/twelvedata-python#:~:text=ts%20%3D%20td.time_series%28%20symbol%3D,)). This affects how the datetime is reported, not the values themselves.

- **Data Quality and Adjustments:** Twelve Data’s daily OHLCV data is typically adjusted for splits and dividends (i.e., **adjusted close** prices) by default. If you require raw prices, check Twelve Data’s documentation for parameters related to adjustments. Also note that **extended hours** data (pre-market or after-hours) is not included in the normal daily interval; it can be accessed via separate endpoints or parameters if needed ([First introduction: getting an advantage in a few minutes](https://twelvedata.com/blog/first-introduction-getting-an-advantage-in-a-few-minutes#:~:text=,FAQs)) (this is advanced usage beyond the scope of this basic guide).

By following this guide, you should be able to set up the Twelve Data Python API client and confidently retrieve daily historical stock data. The examples covered initializing the client, querying daily time series for a symbol with either a recent period or specific date range, and understanding the output format for further processing. With this foundation, you can integrate Twelve Data into your projects to power analysis, backtesting, or any application that needs reliable historical market data. Happy coding!

**Sources:**

1. Twelve Data Official Blog – _Get High-Quality Financial Data Directly into Python_ ([Get High-Quality Financial Data Directly into Python](https://twelvedata.com/blog/get-high-quality-financial-data-directly-into-python#:~:text=The%20base%20object%20for%20all,it%20throughout%20the%20whole%20application)) ([Get High-Quality Financial Data Directly into Python](https://twelvedata.com/blog/get-high-quality-financial-data-directly-into-python#:~:text=To%20select%20all%20data%20between,01%60%2C%20we%20set%20date%20parameters)) ([Get High-Quality Financial Data Directly into Python](https://twelvedata.com/blog/get-high-quality-financial-data-directly-into-python#:~:text=ts%20%3D%20td.time_series%28%20symbol%3D,01%22%20%29.as_pandas))
2. _Master the Twelve Data API with Python_ – Analyzing Alpha (Tutorial, Oct 2023) ([Master the Twelve Data API with Python: A Comprehensive Tutorial - Analyzing Alpha](https://analyzingalpha.com/twelve-data-api-python-tutorial#:~:text=The%20interval%20parameter%20of%20the,4h%2C%208h%2C%201day%2C%201week%2C%201month)) ([Master the Twelve Data API with Python: A Comprehensive Tutorial - Analyzing Alpha](https://analyzingalpha.com/twelve-data-api-python-tutorial#:~:text=You%20can%20also%20pass%20values,to%20filter%20the%20sampling%20period))
3. Twelve Data Developer Documentation and Support ([First introduction: getting an advantage in a few minutes](https://twelvedata.com/blog/first-introduction-getting-an-advantage-in-a-few-minutes#:~:text=)) ([API credits limits | Twelve Data Support](https://support.twelvedata.com/en/articles/5194820-api-credits-limits#:~:text=Basic%20plan)) ([Historical data | Twelve Data Support](https://support.twelvedata.com/en/articles/5194454-historical-data#:~:text=The%20depth%20of%20historical%20data,few%20months%20to%20a%20year)) ([Get High-Quality Financial Data Directly into Python](https://twelvedata.com/blog/get-high-quality-financial-data-directly-into-python#:~:text=Stocks%20also%20accept%20,exchange))
4. Twelve Data Python SDK GitHub – Usage Examples ([GitHub - twelvedata/twelvedata-python: Twelve Data Python Client - Financial data API & WebSocket](https://github.com/twelvedata/twelvedata-python#:~:text=from%20twelvedata%20import%20TDClient)) ([GitHub - twelvedata/twelvedata-python: Twelve Data Python Client - Financial data API & WebSocket](https://github.com/twelvedata/twelvedata-python#:~:text=ts%20%3D%20td.time_series%28%20symbol%3D,))
5. DEV Community – _Free Market Data for Python using Twelve Data API_ ([Free Market Data for Python using Twelve Data API - DEV Community](https://dev.to/midassss/free-market-data-for-python-using-twelve-data-api-4ij2#:~:text=The%20Twelve%20Data%20API%20provides,the%20following%20features))
