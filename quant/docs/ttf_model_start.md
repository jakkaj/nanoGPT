## Detailed Technical Specification: Stock Increase Prediction Model

### Overview:
Develop a predictive model capable of determining the likelihood that a given stock's price will increase during the next calendar week. Given inputs of two months (approximately 60 calendar days) of combined historical stock data, the model should predict whether the closing price exactly 7 calendar days after the prediction date will be higher than the closing price on the prediction date. The system should support dynamic querying for predictions on any stock at any arbitrary date within the provided historical data period.

### Problem Definition:
The model addresses a binary classification problem, explicitly defined as:
- **Input**: Historical stock performance data spanning the previous 60 calendar days.
- **Target Output**: Predict the likelihood (probability) that the stock’s closing price exactly 7 calendar days into the future will exceed the closing price on the prediction date.

### Input Data:
- **Dataset structure**:
  - CSV files, one per stock, named `{stock_code}.csv`
  - Columns: `datetime`, `open`, `high`, `low`, `close`, `volume`
  - Historical coverage: 2 years per stock
  - Frequency: Daily

### Data Preparation:
- Combine all CSV files into a single dataset with an additional `stock_id` column representing each stock.
- Convert `datetime` to proper datetime objects and ensure chronological sorting.
- Compute the following features for each daily entry:
  - Daily returns (% change from previous close)
  - Moving averages (5-day, 20-day)
  - Volume-based indicators (average volume over the past week)

### Model Input Specification:
- **Historical Window**: Use the previous 60 calendar days (~2 months) of data from the requested prediction date.
- **Features to include**:
  - Daily returns
  - Moving averages (5-day, 20-day)
  - Volume indicators
  - Categorical stock embedding (`stock_id`)
  - Positional embedding representing relative day position (0-59)

### Prediction Task:
- Binary classification: Predict if the stock’s closing price exactly 7 calendar days after the prediction date will be higher (label=1) or not (label=0) compared to the closing price on the prediction date.

### Model Architecture:
- Use a Temporal Fusion Transformer (TFT):
  - Capable of handling sequence input and categorical embeddings
  - Output: Binary prediction with probability (sigmoid)

### Output Specification:
- **Primary Output**:
  - Probability of price increase for each stock/date query
  - Binary classification (1 or 0 based on 0.5 threshold)

### Interface Requirements:
- A callable function (API-style) with parameters:
  - `stock_code` (string): stock to predict
  - `prediction_date` (datetime): the date from which to predict next week’s increase
- Returns:
  - Predicted probability of increase
  - Binary classification result (increase/no increase)

### Operational Requirements:
- Support on-demand predictions for any stock/date combination, provided the historical data (prior 2 months) is available.
- Efficient data indexing for quick historical data retrieval at runtime.

### Evaluation Metrics:
- Accuracy, precision, recall, F1-score, and ROC-AUC on a withheld test set spanning the final 3 months of historical data.

### Deliverables:
- Fully documented Python code for:
  - Data preparation and feature engineering
  - Model training and evaluation
  - Inference function
- Trained TFT model weights
- Example notebook demonstrating model usage

