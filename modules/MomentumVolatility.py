# Backtesting library documentation: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy
from backtesting import Strategy
# Technical Indicators library documentation: https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#
import talib as ta

# Strategy Description:
    # The Momentum Volatility strategy is a trend-following strategy that combines momentum and volatility indicators.
    # It calculates the momentum based on the rate of change over a specified lookback period and checks if it is
    # positive or negative. Additionally, it calculates the Average True Range (ATR) to measure volatility. The strategy
    # generates sell signals when the momentum is positive and the ATR exceeds a threshold, suggesting high volatility.
    # Conversely, it generates buy signals when the momentum is negative and the ATR surpasses the threshold.

class MomentumVolatility(Strategy):
    # Lookback Period:
        # The lookback period is the number of bars used to calculate the momentum. A shorter period makes the strategy
        # more responsive to recent price changes, while a longer period provides a smoother momentum line.
        # Adjust this parameter to suit the market and timeframe you are trading.
    lookback_period = 10

    # ATR Period:
        # The ATR period determines the number of bars used to calculate the Average True Range (ATR) indicator. The ATR
        # measures the volatility of an asset based on the range of price movements. A longer period provides a more
        # smoothed ATR value, while a shorter period reflects more recent price volatility.
        # Adjust this parameter based on the market's volatility and the desired sensitivity of the strategy.
    atr_period = 15

    # ATR Threshold:
        # The ATR threshold is the level above which the ATR value must exceed to generate a buy or sell signal. It
        # indicates the minimum volatility required to trigger a trade. A higher threshold filters out low-volatility
        # periods and reduces the frequency of trades, while a lower threshold allows more trades but may include
        # lower-quality signals.
        # Adjust this parameter based on the market's volatility and the desired sensitivity of the strategy.
    atr_threshold = 2.5    
    
    def init(self):
        close = self.data.Close
        # Calculate momentum based on rate of change over the lookback period
        self.returns = self.I(ta.MOM, close, self.lookback_period)
        # Calculate Average True Range (ATR) using high, low, close prices over the ATR period
        self.atr = self.I(ta.ATR, self.data.High, self.data.Low, close, self.atr_period)

    def next(self):
        # Sell signal: Momentum is positive and ATR exceeds the threshold
        if self.returns[-1] > 0 and self.atr[-1] > self.atr_threshold:
            self.sell()
        # Buy signal: Momentum is negative and ATR surpasses the threshold
        elif self.returns[-1] < 0 and self.atr[-1] > self.atr_threshold:
            self.buy()
