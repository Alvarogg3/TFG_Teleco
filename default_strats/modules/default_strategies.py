import numpy as np
import talib as ta
from backtesting import Strategy
from backtesting.lib import crossover

class MeanReversion(Strategy):
    lookback_period = 20
    z_score_threshold = 1.0

    def init(self):
        close = self.data.Close
        self.mean = self.I(np.mean, close, self.lookback_period)
        self.std = self.I(np.std, close, self.lookback_period)

    def next(self):
        z_score = (self.data.Close[-1] - self.mean[-1]) / self.std[-1]
        if z_score > self.z_score_threshold:
            self.sell()
        elif z_score < -self.z_score_threshold:
            self.buy()

class Momentum(Strategy):
    lookback_period = 10

    def init(self):
        close = self.data.Close
        self.returns = self.I(lambda x: x[-1] / x[0], close, self.lookback_period)

    def next(self):
        if self.returns[-1] > 1:
            self.buy()
        elif self.returns[-1] < 1:
            self.sell()

class MovingAverageCrossover(Strategy):
    short_period = 50
    long_period = 200

    def init(self):
        close = self.data.Close
        self.short_ma = self.I(ta.SMA, close, self.short_period)
        self.long_ma = self.I(ta.SMA, close, self.long_period)

    def next(self):
        if crossover(self.short_ma, self.long_ma):
            self.buy()
        elif crossover(self.long_ma, self.short_ma):
            self.sell()

class Breakout(Strategy):
    lookback_period = 20

    def init(self):
        self.range_high = self.I(np.max, self.data.High, self.lookback_period)
        self.range_low = self.I(np.min, self.data.Low, self.lookback_period)

    def next(self):
        if self.data.Close[-1] > self.range_high[-1]:
            self.buy()
        elif self.data.Close[-1] < self.range_low[-1]:
            self.sell()

class RelativeStrengthIndex(Strategy):
    rsi_period = 14
    sell_threshold = 70
    buy_threshold = 30

    def init(self):
        close = self.data.Close
        self.rsi = self.I(ta.RSI, close, self.rsi_period)

    def next(self):
        if self.rsi[-1] > self.sell_threshold:
            self.sell()
        elif self.rsi[-1] < self.buy_threshold:
            self.buy()

class BollingerBands(Strategy):
    period = 20
    std_devs = 2

    def init(self):
        close = self.data.Close
        self.bollinger_high, self.bollinger_mid, self.bollinger_low = self.I(ta.BBANDS, close, self.period, self.std_devs)

    def next(self):
        if self.data.Close[-1] <= self.bollinger_low[-1]:
            self.buy()
        elif self.data.Close[-1] >= self.bollinger_high[-1]:
            self.sell()

class MeanReversionBollinger(Strategy):
    lookback_period = 20
    z_score_threshold = 1.0

    def init(self):
        close = self.data.Close
        self.mean = self.I(np.mean, close, self.lookback_period)
        self.std = self.I(np.std, close, self.lookback_period)
        self.upper_band = self.mean + self.z_score_threshold * self.std
        self.lower_band = self.mean - self.z_score_threshold * self.std

    def next(self):
        if self.data.Close[-1] > self.upper_band[-1]:
            self.sell()
        elif self.data.Close[-1] < self.lower_band[-1]:
            self.buy()

class MACD(Strategy):
    fast_period = 12
    slow_period = 26
    signal_period = 9

    def init(self):
        close = self.data.Close
        self.macd_line, self.signal_line, self.macd_hist = self.I(ta.MACD, close, self.fast_period, self.slow_period, self.signal_period)

    def next(self):
        if crossover(self.macd_hist, 0):
            self.buy()
        elif crossover(0, self.macd_hist):
            self.sell()

class AverageDirectionalMovement(Strategy):
    adx_period = 14
    adx_threshold = 25

    def init(self):
        high, low, close = self.data.High, self.data.Low, self.data.Close
        self.adx = self.I(ta.ADX, high, low, close, self.adx_period)

    def next(self):
        if self.adx[-1] > self.adx_threshold:
            if self.adx[-2] < self.adx_threshold:
                self.buy()
        else:
            self.sell()

class Turtle(Strategy):
    lookback_period = 20

    def init(self):
        self.high_high = self.I(np.max, self.data.High, self.lookback_period)
        self.low_low = self.I(np.min, self.data.Low, self.lookback_period)

    def next(self):
        if self.data.Close[-1] > self.high_high[-1]:
            self.buy()
        elif self.data.Close[-1] < self.low_low[-1]:
            self.sell()

class VolatilityBreakout(Strategy):
    lookback_period = 20
    volatility_factor = 1.5

    def init(self):
        self.high_high = self.I(np.max, self.data.High, self.lookback_period)
        self.low_low = self.I(np.min, self.data.Low, self.lookback_period)

    def next(self):
        breakout_high = self.high_high[-1] * self.volatility_factor
        breakout_low = self.low_low[-1] * self.volatility_factor
        if self.data.Close[-1] > breakout_high:
            self.buy()
        elif self.data.Close[-1] < breakout_low:
            self.sell()