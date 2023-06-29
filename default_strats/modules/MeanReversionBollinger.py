# Backtesting library documentation: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy
from backtesting import Strategy
# Technical Indicators library documentation: https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#
import talib as ta

    # Strategy Description:
        # The Mean Reversion Bollinger strategy is a mean-reversion strategy that combines the concepts of mean reversion
        # and Bollinger Bands. It calculates the z-score of the current closing price based on the mean and standard deviation
        # over a specified lookback period. It then uses the z-score to define upper and lower bands around the mean,
        # considering deviations from the mean as potential entry or exit points.

class MeanReversionBollinger(Strategy):
    # Lookback Period:
        # The lookback period is the number of bars used to calculate the mean and standard deviation. A longer period
        # provides a more stable estimate of the mean and standard deviation but may make the strategy less responsive
        # to recent price changes.
        # Adjust this parameter to suit the market and timeframe you are trading.
    lookback_period = 40
    # Z-Score Threshold:
        # The z-score threshold determines the level at which an extreme deviation from the mean is considered for
        # generating sell or buy signals. A higher threshold generates signals less frequently but captures more
        # significant deviations, while a lower threshold increases the frequency of signals but may include smaller
        # deviations.
        # Adjust this parameter based on the market's volatility and the desired sensitivity of the strategy.
    z_score_threshold = 3

    def init(self):
        close = self.data.Close

        # Calculate the moving average over the lookback period
        self.mean = self.I(ta.SMA, close, self.lookback_period)

        # Calculate the moving standard deviation over the lookback period
        self.std = self.I(ta.STDDEV, close, self.lookback_period)

        # Calculate the upper and lower bands using the mean and z-score threshold
        self.upper_band = self.mean + self.z_score_threshold * self.std
        self.lower_band = self.mean - self.z_score_threshold * self.std

    def next(self):
        # Sell signal: Closing price rises above the upper band
        if self.data.Close[-1] > self.upper_band[-1]:
            self.sell()

        # Buy signal: Closing price falls below the lower band
        elif self.data.Close[-1] < self.lower_band[-1]:
            self.buy()