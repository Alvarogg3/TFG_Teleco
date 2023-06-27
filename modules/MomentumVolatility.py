from backtesting import Strategy
import talib as ta

class MomentumVolatility(Strategy):
    lookback_period = 10
    atr_period = 15
    atr_threshold = 2.5

    def init(self):
        close = self.data.Close
        self.returns = self.I(ta.MOM, close, self.lookback_period)
        self.atr = self.I(ta.ATR, self.data.High, self.data.Low, close, self.atr_period)

    def next(self):
        if self.returns[-1] > 0 and self.atr[-1] > self.atr_threshold:
            self.sell()
        elif self.returns[-1] < 0 and self.atr[-1] > self.atr_threshold:
            self.buy()