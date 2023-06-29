# Backtesting library documentation: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy
from backtesting import Strategy
# Technical Indicators library documentation: https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#
import talib as ta

# Strategy Description:
    # The Mean Reversion strategy is a popular mean-reversion trading strategy that identifies potential
    # price reversals. It calculates the z-score of the current closing price based on the mean and standard deviation
    # over a specified lookback period. When the z-score exceeds a certain threshold (positive or negative), indicating
    # an extreme deviation from the mean, it generates a sell or buy signal, respectively.

class MeanReversion(Strategy):
     # Lookback Period:
        # The lookback period is the number of bars used to calculate the mean and standard deviation. A longer period
        # provides a more stable estimate of the mean and standard deviation but may make the strategy less responsive
        # to recent price changes.
    lookback_period = 21
    
    # Z-Score Threshold:
        # The z-score threshold determines the level at which an extreme deviation from the mean is considered for
        # generating sell or buy signals. A higher threshold generates signals less frequently but captures more
        # significant deviations, while a lower threshold increases the frequency of signals but may include smaller
        # deviations.
    z_score_threshold = 3.0
    
    def init(self):
        close = self.data.Close
        # Calculate the moving average over the loopback period
        self.mean = self.I(ta.SMA, close, self.lookback_period)
        # Calculate the moving standard deviation over the loopback period
        self.std = self.I(ta.STDDEV, close, self.lookback_period)

    def next(self):
        # Calculate the z-score:
        z_score = (self.data.Close[-1] - self.mean[-1]) / self.std[-1]
        # Sell signal: Z-score exceeds the positive threshold
        if z_score > self.z_score_threshold:
            self.sell()
        # Buy signal: Z-score falls below the negative threshold
        elif z_score < -self.z_score_threshold:
            self.buy()
