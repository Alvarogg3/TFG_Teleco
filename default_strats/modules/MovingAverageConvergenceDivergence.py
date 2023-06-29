# Backtesting library documentation: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy
from backtesting import Strategy
from backtesting.lib import crossover
# Technical Indicators library documentation: https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#
import talib as ta

# Strategy Description:
    # The Moving Average Convergence Divergence (MACD) strategy is a trend-following strategy that utilizes the MACD
    # indicator to generate buy and sell signals. It calculates the MACD line, signal line, and histogram based on the
    # closing prices over different periods. The strategy generates a buy signal when the MACD histogram crosses above
    # the zero line (crossover), indicating a bullish trend. Conversely, it generates a sell signal when the histogram
    # crosses below the zero line, suggesting a bearish trend.

class MovingAverageConvergenceDivergence(Strategy):
    # Fast Period:
        # The fast period is the number of bars used to calculate the fast moving average component of the MACD indicator.
        # A shorter period makes the MACD more responsive to recent price changes, capturing shorter-term trends.
        # Adjust this parameter based on the market's volatility and the desired sensitivity of the strategy.
    fast_period = 50
    # Slow Period:
        # The slow period is the number of bars used to calculate the slow moving average component of the MACD indicator.
        # A longer period smoothens out the MACD line and provides a more robust indication of the underlying trend.
        # Adjust this parameter based on the market's volatility and the desired sensitivity of the strategy.
    slow_period = 150
    # Signal Period:
        # The signal period is the number of bars used to calculate the signal line, which is a moving average of the MACD
        # line. It helps to identify potential buy and sell signals by generating crossovers with the MACD line.
        # Adjust this parameter based on the market's volatility and the desired sensitivity of the strategy.
    signal_period = 50

    def init(self):
        close = self.data.Close
        # Calculate MACD line, signal line, and histogram using the specified periods
        self.macd_line, self.signal_line, self.macd_hist = self.I(ta.MACD, close, self.fast_period, self.slow_period, self.signal_period)

    def next(self):
        # Buy signal: MACD histogram crosses above zero line
        if crossover(self.macd_hist, 0):
            self.buy()
        # Sell signal: MACD histogram crosses below zero line
        elif crossover(0, self.macd_hist):
            self.sell()
