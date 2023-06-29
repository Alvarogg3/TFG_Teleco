# Backtesting library documentation: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy
from backtesting import Strategy
# Technical Indicators library documentation: https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#
import talib as ta

# Strategy Description:
    # The Turtle strategy is a trend-following strategy based on breakout levels. It identifies potential entry points
    # by detecting breakouts above the highest high or below the lowest low over a specified lookback period. Once a
    # breakout occurs, it enters a long or short position accordingly. The strategy then waits for a specified number
    # of bars to elapse before checking for exit conditions, which include prices crossing back below the lowest low
    # (for long positions) or above the highest high (for short positions).
    
class Turtle(Strategy): 
    # Entry Lookback:
        # The entry lookback is the number of bars used to determine the highest high and lowest low for breakout
        # detection. It sets the lookback period for identifying potential entry points based on breakouts.
        # Adjust this parameter based on the market's behavior and the desired sensitivity of the strategy.
    entry_lookback = 10

    # Exit Lookback:
        # The exit lookback is the number of bars to wait before checking for exit conditions. Once in a position, the
        # strategy waits for the specified number of bars to elapse before considering an exit based on price crossing
        # back below the lowest low (for long positions) or above the highest high (for short positions).
        # Adjust this parameter based on the market's behavior and the desired holding period of positions.
    exit_lookback = 20

    def init(self):
        # Calculate the highest high and lowest low over the entry lookback period
        self.high_high = self.I(ta.MAX, self.data.High, self.entry_lookback)
        self.low_low = self.I(ta.MIN, self.data.Low, self.entry_lookback)
        self.position_entered = False

    def next(self):
        if not self.position_entered:
            # Entry conditions for long position: Close price crosses above the highest high
            if self.data.Close[-1] > self.high_high[-2]:
                self.buy()
                self.position_entered = True
            # Entry conditions for short position: Close price crosses below the lowest low
            elif self.data.Close[-1] < self.low_low[-2]:
                self.sell()
                self.position_entered = True
        else:
            # Exit conditions: Price crosses back below the lowest low (long position) or above the highest high (short position)
            if len(self.data) >= self.trades[0].entry_bar + self.exit_lookback:
                if self.data.Close[-1] < self.low_low[-2] or self.data.Close[-1] > self.high_high[-2]:
                    self.position.close()
                    self.position_entered = False
