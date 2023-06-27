from backtesting import Strategy
import talib as ta

class BollingerBands(Strategy):
    period = 30
    std_devs = 3

    def init(self):
        close = self.data.Close
        self.bollinger_high, self.bollinger_mid, self.bollinger_low = self.I(ta.BBANDS, close, self.period, self.std_devs)

    def next(self):
        if self.data.Close[-1] <= self.bollinger_low[-1]:
            self.buy()
        elif self.data.Close[-1] >= self.bollinger_high[-1]:
            self.sell()
