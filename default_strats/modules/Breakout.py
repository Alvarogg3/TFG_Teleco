from backtesting import Strategy
import talib as ta

class Breakout(Strategy):
    lookback_period = 20

    def init(self):
        self.range_high = self.I(ta.MAX, self.data.High, self.lookback_period)
        self.range_low = self.I(ta.MIN, self.data.Low, self.lookback_period)

    def next(self):
        if self.data.Close[-1] > self.range_high[-1]:
            self.buy()
        elif self.data.Close[-1] < self.range_low[-1]:
            self.sell()
