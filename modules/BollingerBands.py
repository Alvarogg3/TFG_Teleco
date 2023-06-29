# Backtesting library documentation: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy
from backtesting import Strategy
# Technical Indicators library documentation: https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#
import talib as ta

# Strategy Description:
    # The Bollinger Bands strategy is a mean-reversion strategy that utilizes the Bollinger Bands indicator.
    # It generates a buy signal when the closing price falls below or touches the lower Bollinger Band,
    # suggesting a potential price reversal or bounce. Conversely, it generates a sell signal when the closing
    # price rises above or touches the upper Bollinger Band, indicating a possible overbought condition.

class BollingerBands(Strategy):
    # Bollinger Bands Period:
        # The Bollinger Bands period determines the number of bars used to calculate the indicator. A shorter period
        # makes the strategy more responsive to recent price changes, while a longer period provides a smoother
        # Bollinger Bands line.
        # Adjust this parameter to suit the market and timeframes you are trading.
    period = 30

    # Bollinger Bands Standard Deviations:
        # The standard deviations parameter controls the width of the Bollinger Bands. It determines the distance
        # between the middle band (usually a simple moving average) and the upper and lower bands. Increasing the
        # standard deviations widens the bands, while decreasing it narrows them.
        # Adjust this parameter based on the market's volatility and the desired sensitivity of the strategy.
    std_devs = 3

    def init(self):
        close = self.data.Close
        # Calculate Bollinger Bands using TA-Lib
        self.bollinger_high, self.bollinger_mid, self.bollinger_low = self.I(ta.BBANDS, close, self.period, self.std_devs)

    def next(self):
        # Buy signal: Closing price falls below or touches the lower Bollinger Band
        if self.data.Close[-1] <= self.bollinger_low[-1]:
            self.buy()
        
        # Sell signal: Closing price rises above or touches the upper Bollinger Band
        elif self.data.Close[-1] >= self.bollinger_high[-1]:
            self.sell()
