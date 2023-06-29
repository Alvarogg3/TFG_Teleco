# Backtesting library documentation: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy
from backtesting import Strategy
# Technical Indicators library documentation: https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#
import talib as ta

# Strategy Description:
    # The Relative Strength Index (RSI) strategy is a momentum-based strategy that uses the RSI indicator to generate
    # buy and sell signals. The RSI measures the magnitude of recent price changes to determine whether an asset is
    # overbought or oversold. This strategy generates a sell signal when the RSI value exceeds a sell threshold,
    # indicating overbought conditions. Conversely, it generates a buy signal when the RSI value falls below a buy
    # threshold, suggesting oversold conditions.

class RelativeStrengthIndex(Strategy):
    # RSI Period:
        # The RSI period determines the number of bars used to calculate the RSI indicator. A shorter period makes the RSI
        # more responsive to recent price changes, capturing shorter-term momentum. A longer period provides a smoother
        # RSI line and may be more suitable for identifying longer-term trends.
        # Adjust this parameter based on the market's volatility and the desired sensitivity of the strategy.
    rsi_period = 21
    # Sell Threshold:
        # The sell threshold is the RSI value above which a sell signal is generated. It indicates the level at which an
        # asset is considered overbought and suggests a potential reversal or pullback.
        # Adjust this parameter based on the market's behavior and the desired sensitivity of the strategy.
    sell_threshold = 75
    # Buy Threshold:
        # The buy threshold is the RSI value below which a buy signal is generated. It indicates the level at which an
        # asset is considered oversold and suggests a potential price recovery or bounce.
        # Adjust this parameter based on the market's behavior and the desired sensitivity of the strategy.
    buy_threshold = 40

    def init(self):
        close = self.data.Close
        # Calculate the Relative Strength Index (RSI) using the specified period
        self.rsi = self.I(ta.RSI, close, self.rsi_period)

    def next(self):
        # Sell signal: RSI value exceeds the sell threshold (overbought)
        if self.rsi[-1] > self.sell_threshold:
            self.sell()
        # Buy signal: RSI value falls below the buy threshold (oversold)
        elif self.rsi[-1] < self.buy_threshold:
            self.buy()
