from backtesting import Strategy
import numpy as np

class VolatilityBreakout(Strategy):
    lookback_period = 20
    volatility_factor = 1.5
    stop_loss_percentage = 0.02
    take_profit_percentage = 0.02

    def init(self):
        self.high_high = self.I(np.max, self.data.High, self.lookback_period)
        self.low_low = self.I(np.min, self.data.Low, self.lookback_period)

    def next(self):
        close = self.data.Close[-1]
        long_sl = close*(1-self.stop_loss_percentage)
        long_tp = close*(1+self.take_profit_percentage)
        short_sl = close*(1+self.stop_loss_percentage)
        short_tp = close*(1-self.take_profit_percentage)

        breakout_high = self.high_high[-1] * self.volatility_factor
        breakout_low = self.low_low[-1] * self.volatility_factor
        if close > breakout_high:
            self.buy(sl=long_sl, tp=long_tp)
        elif close < breakout_low:
            self.sell(sl=short_sl, tp=short_tp)
