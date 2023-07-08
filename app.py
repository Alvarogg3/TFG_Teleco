## LIBRARIES
# Framework
from flask import Flask, render_template, jsonify, redirect, url_for, send_from_directory, send_file, request, session

# Data API
from alpha_vantage.timeseries import TimeSeries
# Database
from pymongo import MongoClient
# Util
import pandas as pd
import requests
import json
import bcrypt
import pickle
from io import BytesIO
import xlsxwriter
import re

# Backtesting
from backtesting import Backtest, Strategy
# Custom module import
import os
import pkgutil
import inspect
from importlib import import_module

## CONSTANTS
KEY_INDICATORS = ["Return (Ann.) [%]", "Exposure Time [%]", "Volatility (Ann.) [%]", "Return [%]", "Sharpe Ratio", "Buy & Hold Return [%]"]

## ALPHAVANTAGE API KEYS
# Load the keys from the json file
with open('static/tokens.json') as file:
    keys_data = json.load(file)
# Access the keys
ALPHAVANTAGE_KEY = keys_data['ALPHAVANTAGE_KEY']
ALPHAVANTAGE_KEY_2 = keys_data['ALPHAVANTAGE_KEY_2']

## STRATEGY METHODS
# Get the directory where the strategy modules are located
modules_dir = 'modules'

# Create an empty dictionary to store the strategy classes
strategy_classes = {}

# Iterate over the strategy modules in the directory
for _, module_name, _ in pkgutil.iter_modules([modules_dir]):
    # Import the strategy module dynamically
    module = import_module(f'{modules_dir}.{module_name}')

    # Get the strategy class from the module
    strategy_class = next((cls for _, cls in inspect.getmembers(module, inspect.isclass) if issubclass(cls, Strategy)), None)

    # Add the strategy class to the dictionary with the module name as key
    if strategy_class is not None:
        strategy_classes[module_name] = strategy_class

## DATABASE
# Establish a connection to MongoDB
client = MongoClient('mongodb://localhost:27017/')

# Access the stock cach database
stock_cache_db = client['stock_cache_db']

# Access the collection for the strategies info
db = client['strategies']
strategies_collection = db['default_strategies']

# Access the collection for the users
db = client['user_database']
users_collection = db['users']

# Access the collection for the backtests
db = client['backtests_db']
bt_collection = db['backtests']

## FLASK APP
app = Flask(__name__)

# Load configuration from JSON file
with open('static/config.json', 'r') as config_file:
    config_data = json.load(config_file)

app.config['SECRET_KEY'] = config_data['SECRET_KEY']
app.config['SESSION_COOKIE_SECURE'] = config_data['SESSION_COOKIE_SECURE']
app.config['SESSION_COOKIE_HTTPONLY'] = config_data['SESSION_COOKIE_HTTPONLY']
app.config['SESSION_COOKIE_SAMESITE'] = config_data['SESSION_COOKIE_SAMESITE']
app.config['PERMANENT_SESSION_LIFETIME'] = config_data['PERMANENT_SESSION_LIFETIME']  # 1 week in seconds
app.permanent_session_lifetime = app.config['PERMANENT_SESSION_LIFETIME']

## ROUTES
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_stocks/<string:id>')
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
  backtest_id = request.args.get('backtestId')
  # Pass the parameters to the strategy_results.html template
  return render_template('strategy_results.html', 
                         strategy_id=strategy_id, start_date=start_date, end_date=end_date, 
                         ticker=ticker, frequency=frequency, commission=commission, backtest_id=backtest_id)

# Protected Route - Backend
@app.route('/backtests')
def backtests_library():
    if 'username' in session:
        # Only allow access for authenticated users
        return render_template('backtests.html')
    else:
        return render_template('login.html')

## AUTHENTICATION METHODS
# Render Signup Form
@app.route('/signup', methods=['GET'])
def render_signup_form():
    return render_template('signup.html')

# Handle Signup Form Submission
@app.route('/signup', methods=['POST'])
def handle_signup_form():
    username = request.form['username']
    password = request.form['password']

    # Check if the username already exists in the collection
    if users_collection.find_one({'username': username}):
        return render_template('signup.html', error='Username already exists. Please choose another.')

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Store the user credentials in the collection
    users_collection.insert_one({'username': username, 'password': hashed_password})

    session['username'] = username
    return redirect(url_for('index'))

# Render Login Form
@app.route('/login', methods=['GET'])
def render_login_form():
    return render_template('login.html')

# Handle Login Form Submission
@app.route('/login', methods=['POST'])
def handle_login_form():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Retrieve the user from the collection based on the username
        user = users_collection.find_one({'username': username})
        if user:
            # Check if the password matches the stored hashed password
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                session['username'] = username
                return redirect(url_for('index'))

        error = 'Invalid credentials. Please try again.'
        return render_template('login.html', error=error)

    return render_template('login.html')

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

## GENERAL METHODS
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
    # Get strategies for all users
    strategies = strategies_collection.find({"users": "all"}, {"_id": 0})  # Exclude the _id field from the result

    return jsonify(list(strategies))

@app.route('/get_backtests')
def get_backtests():
    if 'username' in session:
        username = session['username']
        backtests = bt_collection.find({'username': username}, {'_id': 0, 'bt_object': 0})  # Exclude the _id and bt_object fields from the result
        return jsonify(list(backtests))
    else:
        return jsonify({'error': 'You need to be logged in to access your backtests.'}), 401
    
@app.route('/delete_non_permanent_backtests', methods=['POST'])
def delete_non_permanent_backtests():
    if 'username' in session:
        username = session['username']
        result = bt_collection.delete_many({'username': username, 'permanent': {'$ne': True}})
        return jsonify({'deleted_count': result.deleted_count})
    else:
        return jsonify({'error': 'User not logged in'})
    
@app.route('/delete_backtest/<backtest_id>', methods=['DELETE'])
def delete_backtest(backtest_id):
    if 'username' in session:
        username = session['username']
        result = bt_collection.delete_one({'username': username, 'name': backtest_id})
        if result.deleted_count == 1:
            return jsonify({'message': 'Backtest deleted successfully.'}), 200
        else:
            return jsonify({'error': 'Backtest not found.'}), 404
    else:
        return jsonify({'error': 'You need to be logged in to delete a backtest.'}), 401

# Download the strategy code to practice
@app.route('/download_strategy/<string:strategyFilename>')
def download_strategy(strategyFilename):
    # Logic to locate and retrieve the strategy module file based on the strategyId

    # Assuming the strategy modules are stored in the `strategy_modules` directory
    strategy_file_path = f'modules/{strategyFilename}'

    try:
        # Send the strategy module file as a download
        return send_file(strategy_file_path, as_attachment=True,  download_name=strategyFilename)
    except Exception as e:
        # Handle the case if the strategy module file is not found or any other error occurs
        return jsonify({'error': str(e)}), 404

# Execute a trading strategy
@app.route('/execute_strategy', methods=['GET'])
def execute_strategy():
    # Get the input parameters from the query string
    strategy_id = request.args.get('strategyId')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    ticker = request.args.get('ticker')
    frequency = int(request.args.get('frequency'))
    commission = float(request.args.get("commission"))
    backtestId = request.args.get("backtestId")

    # Get the strategy class based on the strategy ID
    selected_strategy_class = strategy_classes.get(strategy_id)
    if strategy_class is None:
        return jsonify({'error': f"Invalid strategy ID: {strategy_id}"}), 404

    if backtestId == "":
        # Get stock data for the ticker from MongoDB
        stock_data = get_stock_data_from_mongodb(ticker, start_date, end_date)

        # Resample to correct freuency
        data =  stock_data.iloc[::frequency]

        # Execute the strategy with the stock data
        bt = Backtest(data, selected_strategy_class, cash=10000, commission=commission, exclusive_orders=True)

        # Save the bt object in the MongoDB collection if the user is authenticated
        if 'username' in session:
            username = session['username']
            bt_pickled = pickle.dumps(bt)
            name = f"{username}_{strategy_id}"
            bt_document = {
                'username': username,
                'name': name,
                'strategy_id': strategy_id,
                'start_date': start_date,
                'end_date': end_date,
                'ticker': ticker,
                'frequency': frequency,
                'commission': commission,
                'bt_object': bt_pickled,
                'permanent': False
            }
            bt_collection.update_one(
                {'username': username, 'name': name},
                {'$set': bt_document},
                upsert=True
            )
            backtest = {'a':0}
    else:
        # Get the backtest object from MongoDB
        backtest = bt_collection.find_one({'username': session['username'], 'name': backtestId})
        bt = pickle.loads(backtest['bt_object'])

    try:
        # Check if the 'opt_values' field exists in the backtest document
        if 'opt_values' in backtest:
            opt_values = backtest['opt_values']
            result = bt.optimize(**opt_values, maximize='Equity Final [$]')
            # Use optimized values for further processing
        else:
            result = bt.run()
        # Check if there are trades
        if result["# Trades"] > 1:
            # Generate the plot and save it as HTML
            plot_filename = f"static/html_outputs/{selected_strategy_class.__name__}.html"
            bt.plot(filename=plot_filename, open_browser=False)
            # Pass the plot filename and strategy results
            return jsonify({'output': json.dumps(result[:-3].to_dict(), default=str),
                            'key_indicators': json.dumps(result[KEY_INDICATORS].to_dict(), default=str), 
                             'plot_filename': plot_filename}) 
        else: 
            return jsonify({'error': 'There are not enough trades for this strategy.'}), 404
    except Exception as e:
        # Return an error message
        return jsonify({'error': 'Error executing strategy.'}), 404
    
# Save Backtest
@app.route('/save_backtest', methods=['POST'])
def save_backtest():
    # Check if the user is authenticated
    if 'username' not in session:
        return jsonify({'error': 'You need to be logged in to save the Backtest.'}), 401

    # Get the input parameters from the request
    data = request.get_json()
    backtest_name = data.get('backtestName')
    strategy_id = data.get('strategyId')
    old_backtest_name = data.get('backtestID')

    # Generate the new Backtest name
    username = session['username']
    if old_backtest_name == "":
        old_backtest_name = f"{username}_{strategy_id}"

    # Perform the update operation in MongoDB
    result = bt_collection.update_one(
        {'name': old_backtest_name},
        {'$set': {'name': backtest_name, 'permanent': True}}
    )

    if result.modified_count > 0:
        # Redirect to the display_results route with the updated backtest_id parameter
        return jsonify({"backtestId": backtest_name})
    else:
        return jsonify({'error': 'Failed to update the Backtest name.'}), 500
    
# Route to download all statistics in Excel
@app.route('/download_data', methods=['GET'])
def download_data():
    if 'username' in session:
        username = session['username']
        strategy_id = request.args.get('strategy_id')
        backtest_name = request.args.get('backtestId')

        # Check if the strategy is not saved
        if backtest_name == "":
            backtest_name = f"{username}_{strategy_id}"

        # Fetch the bt object from MongoDB
        bt_document = bt_collection.find_one({'name': backtest_name})
        if bt_document:
            bt_pickled = bt_document['bt_object']
            bt = pickle.loads(bt_pickled)

            # Run the bt object to obtain the output
            result = bt.run()

            # Create an ExcelWriter object
            with pd.ExcelWriter('statistics.xlsx', engine='xlsxwriter') as excel_writer:
                # Write the DataFrame to the Excel file
                result[:-2].to_excel(excel_writer, sheet_name='Statistics')
            # Send the Excel file as a response
            return send_file('statistics.xlsx', as_attachment=True)
    return jsonify({'error': 'Unauthorized.'}), 401

@app.route('/get_optim_parameters', methods=['GET'])
def get_parameter_descriptions():
    strategy_id = request.args.get('strategyId')
    username = session.get('username')

    parameter_descriptions = {}
    
    # Fetch the document from MongoDB based on the strategy_id and username
    document = strategies_collection.find_one({'strategy_id': strategy_id, 'users': {'$in': [username, 'all']}})
    
    if document:
        # Extract the parameters dictionary from the document
        parameters = document.get('parameters', {})
        
        # Loop through the parameters and descriptions
        for parameter, description in parameters.items():
            value = description.get('value')
            param_description = description.get('description')
            
            # Create the parameter description dictionary
            parameter_description = {
                'value': value,
                'description': param_description
            }
            
            # Add the parameter description to the result dictionary
            parameter_descriptions[parameter] = parameter_description

    return jsonify(parameter_descriptions)

# Optimize a trading strategy
@app.route('/optimize_strategy', methods=['POST'])
def optimize_strategy():
    try:
        # Get the strategy parameters from the request body
        strategy_params = request.json['formData']

        # Set up the optimization ranges for each parameter
        param_ranges = {}
        for param, value in strategy_params.items():
            min_value = int(value['min'])
            max_value = int(value['max']) + 1
            step_value = int(value['step'])
            param_ranges[param] = range(min_value, max_value + 1, step_value)

        # Get the backtest object from MongoDB
        backtest_id = request.json['backtestId']
        strategy_id = request.json['strategyId']
        # Check if the strategy is not saved
        if backtest_id == "":
            backtest_id = f"{session['username']}_{strategy_id}"
        backtest = bt_collection.find_one({'username': session['username'], 'name': backtest_id})
        if backtest is None:
            return jsonify({'error': 'Backtest not found.'}), 404

        bt = pickle.loads(backtest['bt_object'])

        # Optimize the backtest using the parameter ranges
        res = bt.optimize(**param_ranges, maximize='Equity Final [$]')
        opt_values = get_opt_values(str(res._strategy))

        # Create the optimized backtest document
        optimized_backtest = {
            'username': backtest['username'],
            'name': backtest_id + "_opt",
            'strategy_id': backtest['strategy_id'],
            'start_date': backtest['start_date'],
            'end_date': backtest['end_date'],
            'ticker': backtest['ticker'],
            'frequency': backtest['frequency'],
            'commission': backtest['commission'],
            'bt_object': backtest['bt_object'],
            'opt_values': opt_values,
            'permanent': False
        }

        # Update the backtest object in MongoDB with upsert=True
        bt_collection.update_one(
            {'username': backtest['username'], 'name': optimized_backtest['name']},
            {'$set': optimized_backtest},
            upsert=True
        )

        # Return the name of the optimized backtest object as JSON
        return jsonify({'backtestId': optimized_backtest['name'], "opt_values": opt_values})

    except Exception as e:
        # Return an error message
        return jsonify({'error': 'Error optimizing strategy.'}), 500
    
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

def get_opt_values(string):
    parameters_str = re.search(r'\((.*?)\)', string).group(1)
    parameters = {}
    for param in parameters_str.split(','):
        name, value = param.split('=')
        parameters[name.strip()] = int(value.strip())
    return parameters

if __name__ == '__main__':
    app.run(debug=True)