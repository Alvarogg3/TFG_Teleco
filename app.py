## LIBRARIES
from flask import Flask, render_template, jsonify, redirect, request
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from pymongo import MongoClient, UpdateOne
import requests
import pickle

## CONSTANT
ALPHAVANTAGE_KEY = "99ZHWN89YKD8GTCT"

## DATABASE
# Establish a connection to MongoDB
client = MongoClient('mongodb://localhost:27017/')

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

@app.route('/execute_strategy/<int:strategy_id>')
def execute_strategy(strategy_id):
    # Retrieve the strategy function from MongoDB based on the strategy ID
    strategy_data = client['strategies_db']['prebuilt'].find_one({'strategy_id': strategy_id})

    if strategy_data:
        strategy_pickle = strategy_data['pickle']
        inputs = {
            'start_date': request.args.get('startDate'),
            'end_date': request.args.get('endDate'),
            'tickers': request.args.get('tickers').split(',')
        }
        
        # Retrieve the data for the tickers from MongoDB
        ticker_data = {}
        for ticker in inputs['tickers']:
            ticker_data[ticker] = get_stock_data_from_mongodb(ticker, inputs['start_date'], inputs['end_date'])
        
        # Load the strategy function from the pickled object
        strategy_function = pickle.loads(strategy_pickle)
        
        # Execute the strategy function with the ticker data
        result = strategy_function(ticker_data)
        
        # Return the result as a JSON response
        return jsonify(result)
    else:
        # Return an error response if the strategy is not found
        return jsonify({'error': 'Strategy not found'})
    
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

# Get the stock data from the cache or the AlphaVantage API
def get_stock_data(ticker, start_date, end_date):
    # Access the collection for the specific ticker
    collection = client['stock_cache_db'][ticker]

    # Check if the data exists for the end date in the collection
    existing_data = collection.find_one({'Date': end_date})
    if existing_data:
        # Retrieve the stock data from MongoDB
        query = {'Date': {'$gte': start_date, '$lte': end_date}}
        projection = {'_id': 0, 'Date': 1, 'Open': 1, 'High': 1, 'Low': 1, 'Close': 1, 'Volume': 1}
        cursor = collection.find(query, projection)

        stock_data = {document['Date']: {
            'Open': document['Open'],
            'High': document['High'],
            'Low': document['Low'],
            'Close': document['Close'],
            'Volume': document['Volume']
        } for document in cursor}

        return stock_data

    # If data doesn't exist for the end date in the collection, proceed with API call
    app = TimeSeries(ALPHAVANTAGE_KEY)
    stock_data, _ = app.get_daily_adjusted(symbol=ticker, outputsize='full')

    # Convert stock_data to DataFrame
    df = pd.DataFrame.from_dict(stock_data, orient='index').astype(float)

    # Adjust the stock data
    adjusted_df = adjust_stock_data(df)

    # Delete the existing collection for the ticker
    client['stock_cache_db'].drop_collection(ticker)

    # Store the adjusted data in a new collection
    collection.insert_many(adjusted_df.reset_index().rename(columns={'index': 'Date'}).to_dict(orient='records'))

    # Retrieve the adjusted stock data within the date range
    filtered_adjusted_data = adjusted_df.loc[start_date:end_date].to_dict(orient='index')

    return filtered_adjusted_data

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