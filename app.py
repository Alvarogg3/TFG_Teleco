## LIBRARIES
# Framework
from flask import Flask, render_template, jsonify, redirect, request
# Data API
from alpha_vantage.timeseries import TimeSeries
# Database
from pymongo import MongoClient
# Util
import pandas as pd
import requests
import pickle
# Backtesting
from backtesting import Backtest, Strategy
# Custom module
from importlib import import_module
import inspect
from modules.default_strategies import *

## CONSTANT
ALPHAVANTAGE_KEY = "99ZHWN89YKD8GTCT"

## STRATEGY METHODS
# Get the strategies module dynamically
strategies_module = import_module('modules.default_strategies')
# Get all classes from the strategies module in the order they appear in the file
strategy_classes = [cls for name, cls in inspect.getmembers(strategies_module, inspect.isclass) if issubclass(cls, Strategy) and cls.__module__ == strategies_module.__name__]

## DATABASE
# Establish a connection to MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Access the collection for the strategies info
db = client['strategies']
dfstrat_collection = db['default_strategies']

## FLASK APP
app = Flask(__name__)

## ROUTES
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_stocks/<int:id>')
def select_stocks(id):
    # Logic for rendering the create strategy page with the provided strategy ID
    return render_template('select_stocks.html', strategy_id=id)

@app.route('/check_strategies')
def check_strategies():
    # Logic for rendering the test strategy page
    return render_template('check_strategies.html')

## METHODS
@app.route('/search_ticker')
def search_ticker():
    query = request.args.get('query')
    url = f'https://ticker-2e1ica8b9.now.sh/keyword/{query}'
    data = requests.get(url).json()
    return data

@app.route('/check_data_availability', methods=['POST'])
def check_data_availability():
    end_date = request.json['endDate']
    tickers = request.json['tickers']

    missing_tickers = []
    for ticker in tickers:
        if not check_and_fetch_stock_data(ticker, end_date):
            missing_tickers.append(ticker)
    return jsonify({'missingTickers': missing_tickers})

@app.route('/get_strategies')
def get_strategies():
    # Establish a connection to MongoDB
    client = MongoClient('mongodb://localhost:27017/')

    # Access the collection for the strategies
    db = client['strategies']
    dfstrat_collection = db['default_strategies']

    strategies = dfstrat_collection.find({}, {"_id": 0})  # Exclude the _id field from the result
    return jsonify(list(strategies))

@app.route('/execute_strategy/<int:strategy_id>')
def execute_strategy(strategy_id):
    # Retrieve the strategy from the MongoDB collection
    strategy_id = int(request.json['strategy_id'])

    # Get the strategy class based on the strategy ID
    if strategy_id < 0 or strategy_id >= len(strategy_classes):
        return f"Invalid strategy ID: {strategy_id}"
        
    selected_strategy_class = strategy_classes[strategy_id]

    # Get the input parameters from the query string
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    ticker = request.args.get('ticker')

    # Fetch stock data for the ticker
    stock_data = get_stock_data_from_mongodb(ticker, start_date, end_date)

    # Prepare the data for backtesting
    data = pd.DataFrame.from_dict(stock_data, orient='index').astype(float)
    data.index = pd.to_datetime(data.index)

    # Execute the strategy with the stock data
    bt = Backtest(stock_data, selected_strategy_class, cash=10000, commission=.002, exclusive_orders=True)

    try:    
        result = bt.run(stock_data)
        # Process the result as needed
        return jsonify({'result': result})
    except Exception as e:
        return jsonify({'error': str(e)})
    
## FUNCTIONS
# Check if the stock data exists in MongoDB, if not fetch from API and save to MongoDB
def check_and_fetch_stock_data(ticker, end_date):
    # Access the collection for the specific ticker
    collection = client['stock_cache_db'][ticker]

    # Check if the data exists for the end date in the collection
    existing_data = collection.find_one({'date': end_date})
    if existing_data:
        return True  # Data already exists in MongoDB

    try:
        # Fetch stock data from the AlphaVantage API
        app = TimeSeries(ALPHAVANTAGE_KEY)
        stock_data, meta_data = app.get_daily_adjusted(symbol=ticker, outputsize='full')

        # Convert stock_data to DataFrame
        df = pd.DataFrame.from_dict(stock_data, orient='index').astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index(ascending=True)

        # Adjust the stock data
        adjusted_df = adjust_stock_data(df)

        # Delete the existing collection for the ticker
        client['stock_cache_db'].drop_collection(ticker)

        # Store the adjusted data in a new collection
        collection.insert_many(adjusted_df.reset_index().to_dict(orient='records'))

        return True  # Data fetched from API and saved to MongoDB

    except ValueError as e:
        print(f"Error fetching data for ticker '{ticker}': {str(e)}")
        return False  # Error occurred while fetching data
    
# Get the stock data from MongoDB
def get_stock_data_from_mongodb(ticker, start_date, end_date):
    # Access the collection for the specific ticker
    collection = client['stock_cache_db'][ticker]

    # Retrieve the stock data from MongoDB
    query = {'date': {'$gte': start_date, '$lte': end_date}}
    projection = {'_id': 0, 'date': 1, 'open': 1, 'high': 1, 'low': 1, 'close': 1, 'volume': 1}
    cursor = collection.find(query, projection)

    stock_data = {document['date']: {
        'Open': document['open'],
        'High': document['high'],
        'Low': document['low'],
        'Close': document['close'],
        'Volume': document['volume']
    } for document in cursor}

    return stock_data

# Calculate the adjustment factor and create adjusted DataFrame
def adjust_stock_data(df):
    df['factor'] = df['4. close'] / df['5. adjusted close']
    adjusted_df = pd.DataFrame({
        'Open': df['1. open'] / df['factor'],
        'High': df['2. high'] / df['factor'],
        'Low': df['3. low'] / df['factor'],
        'Close': df['4. close'] / df['factor'],
        'Volume': df['6. volume'] * df['factor']
    })
    return adjusted_df

if __name__ == '__main__':
    app.run(debug=True)