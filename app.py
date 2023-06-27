## LIBRARIES
# Framework
from flask import Flask, render_template, jsonify, redirect, url_for, send_from_directory, send_file, request
 
# Data API
from alpha_vantage.timeseries import TimeSeries
# Database
from pymongo import MongoClient
# Util
import pandas as pd
import requests
import json
import os
import io

# Backtesting
from backtesting import Backtest, Strategy
# Custom module
from importlib import import_module
import inspect
from modules.default_strategies import *

## ALPHAVANTAGE API KEYS
# Load the keys from the json file
with open('static/tokens.json') as file:
    keys_data = json.load(file)
# Access the keys
ALPHAVANTAGE_KEY = keys_data['ALPHAVANTAGE_KEY']
ALPHAVANTAGE_KEY_2 = keys_data['ALPHAVANTAGE_KEY_2']

## STRATEGY METHODS
# Get the strategies module dynamically
strategies_module = import_module('modules.default_strategies')
# Get all classes from the strategies module in the order they appear in the file
strategy_classes = [cls for name, cls in inspect.getmembers(strategies_module, inspect.isclass) if issubclass(cls, Strategy) and cls.__module__ == strategies_module.__name__]

## DATABASE
# Establish a connection to MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Access the stock cach database
stock_cache_db = client['stock_cache_db']

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

@app.route('/display_results', methods=['GET'])
def display_results():
  strategy_id = request.args.get('strategyId')
  start_date = request.args.get('startDate')
  end_date = request.args.get('endDate')
  ticker = request.args.get('ticker')
  frequency = request.args.get('frequency')
  commission = request.args.get("commission")

  # Pass the parameters to the strategy_results.html template
  return render_template('strategy_results.html', 
                         strategy_id=strategy_id, start_date=start_date, end_date=end_date, 
                         ticker=ticker, frequency=frequency, commission=commission)

## METHODS
@app.route('/search_ticker')
def search_ticker():
    query = request.args.get('query')
    url = f'https://ticker-2e1ica8b9.now.sh/keyword/{query}'
    data = requests.get(url).json()
    return data

@app.route('/get_stock_info', methods=['GET'])
def get_stock_info():
    ticker = request.args.get('ticker')
    url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHAVANTAGE_KEY_2}'
    
    response = requests.get(url)
    data = response.json()
    
    # Check if the response is empty
    if not data:
        return jsonify({'error': f'Currently we do not have information about the "{ticker}" ticker.'}), 404
    else:
        return data

@app.route('/check_data_availability', methods=['POST'])
def check_data_availability():
    end_date = request.json['endDate']
    ticker = request.json['ticker']

    if not check_and_save_stock_data(ticker, end_date):
        return jsonify({'error': f'Ticker "{ticker}" not found.'}), 404
    else:
        return jsonify({'success': True})

@app.route('/get_strategies')
def get_strategies():
    # Establish a connection to MongoDB
    client = MongoClient('mongodb://localhost:27017/')

    # Access the collection for the strategies
    db = client['strategies']
    dfstrat_collection = db['default_strategies']

    strategies = dfstrat_collection.find({}, {"_id": 0})  # Exclude the _id field from the result
    return jsonify(list(strategies))

# Execute a trading strategy
@app.route('/execute_strategy', methods=['GET'])
def execute_strategy():
    # Get the input parameters from the query string
    strategy_id = int(request.args.get('strategyId'))
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    ticker = request.args.get('ticker')
    frequency = int(request.args.get('frequency'))
    commission = float(request.args.get("commission"))

    # Get the strategy class based on the strategy ID
    if strategy_id < 0 or strategy_id >= len(strategy_classes):
        return jsonify({'error': f"Invalid strategy ID: {strategy_id}"}), 404

    selected_strategy_class = strategy_classes[strategy_id - 1]

    # Get stock data for the ticker from MongoDB
    stock_data = get_stock_data_from_mongodb(ticker, start_date, end_date)

    # Resample to correct freuency
    data =  stock_data.iloc[::frequency]

    # Execute the strategy with the stock data
    bt = Backtest(data, selected_strategy_class, cash=10000, commission=commission, exclusive_orders=True)

    try:
        result = bt.run()
        if result["# Trades"] > 1:
            # Generate the plot and save it as HTML
            plot_filename = f"static/html_outputs/{selected_strategy_class.__name__}.html"
            bt.plot(filename=plot_filename, open_browser=False)
            # Pass the plot filename and strategy results
            return jsonify({'output': json.dumps(result[:-3].to_dict(), indent=4, default=str), 'plot_filename': plot_filename}) 
        else: 
            return jsonify({'error': 'There are not enough trades for this strategy.'}), 404
    except Exception as e:
        # Return an error message
        return jsonify({'error': 'Error executing strategy.'}), 404
    
@app.route('/html_outputs/<path:filename>')
def serve_output(filename):
    root_dir = os.path.dirname(os.getcwd())
    return send_from_directory(os.path.join(root_dir, 'static', 'html_outputs'), filename)

@app.route('/download_data')
def download_data():
    strategy_id = request.args.get('strategy_id')
    data_type = request.args.get('data_type')

    if data_type == 'output':
        # Process output data
        output = request.args.get('output')

        # Generate Excel file
        filename = f"output_{strategy_id}.xlsx"
        output_data = {'output': output}  # Replace with the actual output data
        df_output = pd.DataFrame(output_data)
        df_output.to_excel(filename, index=False)

    elif data_type == 'equity_curve':
        # Process equity curve data
        equity_curve = request.args.get('equity_curve')

        # Generate Excel file
        filename = f"equity_curve_{strategy_id}.xlsx"
        equity_curve_data = {'equity_curve': equity_curve}  # Replace with the actual equity curve data
        df_equity_curve = pd.DataFrame(equity_curve_data)
        df_equity_curve.to_excel(filename, index=False)

    elif data_type == 'trades':
        # Process trades data
        trades = request.args.get('trades')

        # Generate Excel file
        filename = f"trades_{strategy_id}.xlsx"
        trades_data = {'trades': trades}  # Replace with the actual trades data
        df_trades = pd.DataFrame(trades_data)
        df_trades.to_excel(filename, index=False)

    else:
        return jsonify({'error': f"Invalid data type: {data_type}"})

    # Send the file for download
    return send_file(filename, as_attachment=True)
    
## FUNCTIONS
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

# Check if the stock data exists in MongoDB, if not fetch from API and save to MongoDB
def check_and_save_stock_data(ticker, end_date):
    collection = stock_cache_db[ticker]

    # Check if the data exists for the end date in the collection
    existing_data = collection.find_one({'date': end_date})
    if existing_data:
        return True  # Data already exists in MongoDB

    try:
        # Fetch stock data from the AlphaVantage API
        app = TimeSeries(ALPHAVANTAGE_KEY)
        stock_data, _ = app.get_daily_adjusted(symbol=ticker, outputsize='full')

        # Convert stock_data to DataFrame
        df = pd.DataFrame.from_dict(stock_data, orient='index').astype(float)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index(ascending=True)

        # Adjust the stock data
        adjusted_df = adjust_stock_data(df)

        # Convert the index (date) to strings before saving to MongoDB
        adjusted_df.index = adjusted_df.index.strftime('%Y-%m-%d')

        # Delete the existing collection for the ticker
        client['stock_cache_db'].drop_collection(ticker)

        # Store the adjusted data in a new collection
        collection.insert_many(adjusted_df.rename_axis('Date').reset_index().to_dict(orient='records'))

        return True  # Data fetched from API and saved to MongoDB

    except ValueError as e:
        print(f"Error fetching data for ticker '{ticker}': {str(e)}")
        return False  # Error occurred while fetching data
    
# Get the stock data from MongoDB
def get_stock_data_from_mongodb(ticker, start_date, end_date):
    # Access the collection for the specific ticker
    collection = stock_cache_db[ticker]

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

    # Prepare the data for backtesting
    data = pd.DataFrame.from_dict(stock_data, orient='index').astype(float)
    data.index = pd.to_datetime(data.index)
    data = data.sort_index(ascending=True)

    return data

if __name__ == '__main__':
    app.run(debug=True)