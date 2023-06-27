from backtesting import Strategy
import pandas as pd

class Turtle(Strategy):
    lookback_period = 100

    def DonchianChannels(self, data, period):
        df = pd.DataFrame()
        df["High"] = data.High
        df["Low"] = data.Low
        upperDon = df["High"].rolling(period).max().values
        lowerDon = df["Low"].rolling(period).min().values
        return upperDon, lowerDon

    def init(self):
        self.upperDon, self.lowerDon = self.DonchianChannels(self.data, self.lookback_period)

    def next(self):
        if self.data.Close > self.upperDon[-1]:
            self.sell()
        elif self.data.Close < self.lowerDon[-1]:
            self.buy()
