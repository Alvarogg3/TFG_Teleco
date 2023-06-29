# Backtesting library documentation: https://kernc.github.io/backtesting.py/doc/backtesting/backtesting.html#backtesting.backtesting.Strategy
from backtesting import Strategy
# Technical Indicators library documentation: https://technical-analysis-library-in-python.readthedocs.io/en/latest/ta.html#
import talib as ta

# Strategy Description:
    # The Stochastic Overbought/Oversold strategy is a momentum-based strategy that uses the Stochastic Oscillator
    # to identify overbought and oversold conditions. It generates a buy signal when the Stochastic Oscillator (%K)
    # falls below the oversold threshold and then crosses above it, suggesting a potential price reversal. Similarly,
    # it generates a sell signal when the Stochastic Oscillator (%K) rises above the overbought threshold and then
    # crosses below it, indicating a potential price pullback.

class StochasticOverboughtOversold(Strategy):
    # Stochastic Period:
        # The stochastic period is the number of bars used to calculate the Stochastic Oscillator. It determines the
        # lookback period for identifying high and low price levels. A longer period provides a smoother oscillator line,
        # while a shorter period makes it more responsive to recent price changes.
        # Adjust this parameter based on the market's volatility and the desired sensitivity of the strategy.
    stoch_period = 14

    # Stochastic Threshold (Oversold):
        # The oversold threshold is the level below which the Stochastic Oscillator (%K) is considered oversold. It
        # indicates that the price may be due for a potential reversal or bounce. Crossing above this threshold after being
        # below it generates a buy signal.
        # Adjust this parameter based on the market's behavior and the desired sensitivity of the strategy.
    stoch_threshold_oversold = 45

    # Stochastic Threshold (Overbought):
        # The overbought threshold is the level above which the Stochastic Oscillator (%K) is considered overbought. It
        # suggests that the price may be due for a potential pullback or reversal. Crossing below this threshold after
        # being above it generates a sell signal.
        # Adjust this parameter based on the market's behavior and the desired sensitivity of the strategy.
    stoch_threshold_overbought = 80

    def init(self):
        # Calculate the Stochastic Oscillator (%K) and (%D) using the specified period
        self.slowk, self.slowd = self.I(ta.STOCH, self.data.High, self.data.Low, self.data.Close,
                                        fastk_period=self.stoch_period, slowk_period=self.stoch_period,
                                        slowd_period=self.stoch_period)

    def next(self):
        # Buy signal: Stochastic Oscillator (%K) falls below the oversold threshold and then crosses above it
        if self.slowk[-1] < self.stoch_threshold_oversold and self.slowk[-2] > self.stoch_threshold_oversold:
            self.buy()
        # Sell signal: Stochastic Oscillator (%K) rises above the overbought threshold and then crosses below it
        elif self.slowk[-1] > self.stoch_threshold_overbought and self.slowk[-2] < self.stoch_threshold_overbought:
            self.sell()
