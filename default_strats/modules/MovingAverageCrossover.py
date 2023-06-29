# Backtesting library documentation: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy
from backtesting import Strategy
from backtesting.lib import crossover
# Technical Indicators library documentation: https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#
import talib as ta

# Strategy Description:
    # The Moving Average Crossover strategy is a trend-following strategy that generates buy and sell signals based on
    # the crossover of two moving averages. It calculates a short-term moving average and a long-term moving average
    # based on the closing prices. When the short-term moving average crosses above the long-term moving average, it
    # generates a buy signal, indicating a potential bullish trend. Conversely, when the short-term moving average
    # crosses below the long-term moving average, it generates a sell signal, suggesting a potential bearish trend.

class MovingAverageCrossover(Strategy):
    # Short Period:
        # The short period is the number of bars used to calculate the short-term moving average. A shorter period makes
        # the moving average more responsive to recent price changes, capturing shorter-term trends.
        # Adjust this parameter based on the market's volatility and the desired sensitivity of the strategy.
    short_period = 50
    # Long Period:
        # The long period is the number of bars used to calculate the long-term moving average. A longer period smoothens
        # out the moving average and provides a more robust indication of the underlying trend.
        # Adjust this parameter based on the market's volatility and the desired sensitivity of the strategy.
    long_period = 200

    def init(self):
        close = self.data.Close
        # Calculate short-term moving average
        self.short_ma = self.I(ta.SMA, close, self.short_period)
        # Calculate long-term moving average
        self.long_ma = self.I(ta.SMA, close, self.long_period)

    def next(self):
        # Buy signal: Short-term moving average crosses above long-term moving average
        if crossover(self.short_ma, self.long_ma):
            self.buy()
        # Sell signal: Short-term moving average crosses below long-term moving average
        elif crossover(self.long_ma, self.short_ma):
            self.sell()
