# Backtesting library documentation: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy
from backtesting import Strategy
# Technical Indicators library documentation: https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#
import talib as ta

# Strategy Description:
    # The Average Directional Movement (ADX) strategy is a trend-following strategy that uses the ADX indicator
    # to identify strong trending markets. The strategy generates a buy signal when the ADX crosses above a threshold
    # value, indicating the start of a new trend. It generates a sell signal when the ADX falls below the threshold,
    # suggesting a weakening trend or a range-bound market.

class AverageDirectionalMovement(Strategy):
    # ADX Period:
        # The ADX period determines the number of bars used to calculate the ADX indicator. A shorter period makes
        # the strategy more responsive to recent price changes, while a longer period provides a smoother ADX line.
    adx_period = 7

    # ADX Threshold:
        # The ADX threshold is the level above which the ADX value must cross to generate a buy signal. It determines
        # the strength of the trend required to trigger a trade. A higher threshold filters out weaker trends and
        # reduces the frequency of trades, while a lower threshold allows more trades but may result in entering
        # weaker trends.
    adx_threshold = 15

    def init(self):
        high, low, close = self.data.High, self.data.Low, self.data.Close
        # Calculate Average Directional Index (ADX) using TA-Lib
        self.adx = self.I(ta.ADX, high, low, close, self.adx_period)

    def next(self):
        # Check if ADX value is above the threshold
        if self.adx[-1] > self.adx_threshold:
            # Check if the previous ADX value was below the threshold
            if self.adx[-2] < self.adx_threshold:
                # Generate a buy signal when ADX crosses above the threshold
                self.buy()
        else:
            # Generate a sell signal when ADX falls below the threshold
            self.sell()
