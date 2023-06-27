from backtesting import Strategy
import talib as ta

class RelativeStrengthIndex(Strategy):
    rsi_period = 21
    sell_threshold = 90
    buy_threshold = 30

    def init(self):
        close = self.data.Close
        self.rsi = self.I(ta.RSI, close, self.rsi_period)

    def next(self):
        if self.rsi[-1] > self.sell_threshold:
            self.sell()
        elif self.rsi[-1] < self.buy_threshold:
            self.buy()
