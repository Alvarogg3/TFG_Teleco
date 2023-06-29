from backtesting import Strategy
from backtesting.lib import crossover
import talib as ta

class MovingAverageConvergenceDivergence(Strategy):
    fast_period = 50
    slow_period = 150
    signal_period = 50

    def init(self):
        close = self.data.Close
        self.macd_line, self.signal_line, self.macd_hist = self.I(ta.MACD, close, self.fast_period, self.slow_period, self.signal_period)

    def next(self):
        if crossover(self.macd_hist, 0):
            self.buy()
        elif crossover(0, self.macd_hist):
            self.sell()
