# Backtesting library documentation: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy
from backtesting import Strategy
# Technical Indicators library documentation: https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#
import talib as ta

# Strategy Description:
    # The Volatility Breakout strategy aims to capture price breakouts based on recent volatility. It calculates the
    # highest high and lowest low over a specified lookback period and applies a volatility factor to determine breakout
    # levels. When the current closing price exceeds the breakout high level, it generates a buy signal, expecting a
    # continuation of an upward breakout. Conversely, when the current closing price falls below the breakout low level,
    # it generates a sell signal, anticipating a continuation of a downward breakout.

class VolatilityBreakout(Strategy):
    # Lookback Period:
        # The lookback period is the number of bars used to calculate the highest high and lowest low. It determines the
        # historical range for identifying breakout levels.
        # Adjust this parameter based on the market's behavior and the desired sensitivity of the strategy.
    lookback_period = 20
    
    # Volatility Factor:
        # The volatility factor scales the breakout levels derived from the highest high and lowest low. It allows for
        # adjustments to capture breakouts of different magnitudes based on recent volatility.
        # Adjust this parameter based on the market's volatility and the desired sensitivity of the strategy.
    volatility_factor = 1.5
    
    # Stop Loss Percentage:
        # The stop loss percentage determines the level at which a stop loss order will be placed after entering a position.
        # It represents the percentage below the entry price for long positions and above the entry price for short
        # positions, acting as a risk management tool to limit potential losses.
        # Adjust this parameter based on the risk tolerance and desired maximum loss per trade.
    stop_loss_percentage = 0.02

    # Take Profit Percentage:
        # The take profit percentage determines the level at which a take profit order will be placed after entering a
        # position. It represents the percentage above the entry price for long positions and below the entry price for
        # short positions, aiming to secure a profit level before a potential reversal or price retracement.
        # Adjust this parameter based on the desired profit target and the balance between risk and reward.
    take_profit_percentage = 0.02

    def init(self):
        # Calculate the highest high and lowest low over the lookback period
        self.high_high = self.I(ta.MAX, self.data.High, self.lookback_period)
        self.low_low = self.I(ta.MIN, self.data.Low, self.lookback_period)

    def next(self):
        close = self.data.Close[-1]
        # Calculate stop loss adn take profit signals
        long_sl = close * (1 - self.stop_loss_percentage)
        long_tp = close * (1 + self.take_profit_percentage)
        short_sl = close * (1 + self.stop_loss_percentage)
        short_tp = close * (1 - self.take_profit_percentage)
        # Calculate breakout levels
        breakout_high = self.high_high[-2] * self.volatility_factor
        breakout_low = self.low_low[-2] * self.volatility_factor

        # Buy signal: Close price exceeds the breakout high level, and include stop loss adn take profit signals on the order
        if close > breakout_high:
            self.buy(sl=long_sl, tp=long_tp)
        # Sell signal: Close price falls below the breakout low level, and include stop loss adn take profit signals on the order
        elif close < breakout_low:
            self.sell(sl=short_sl, tp=short_tp)
