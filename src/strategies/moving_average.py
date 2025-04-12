import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import Strategy

class MovingAverageCrossover(Strategy):
    """
    Moving Average Crossover Strategy
    
    This strategy generates trading signals based on crossovers between two moving averages:
    1. A short-term moving average (faster, more responsive to recent price changes)
    2. A long-term moving average (slower, represents longer-term trend)
    
    Trading Logic:
    - BUY signal: When the short-term MA crosses above the long-term MA (bullish)
    - SELL signal: When the short-term MA crosses below the long-term MA (bearish)
    - HOLD signal: When there is no crossover
    
    This is a trend-following strategy based on the premise that when shorter-term
    price momentum (short MA) crosses the longer-term trend (long MA), it indicates
    a potential continuation in that direction.
    """
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize the Moving Average Crossover strategy with customizable parameters.
        
        This constructor sets up the strategy with either default or custom parameters.
        The key parameters are the periods (number of candles/data points) used to
        calculate the short and long moving averages.
        
        Args:
            params: Dictionary of strategy parameters:
                - short_window: Period for short moving average (default: 20)
                    Fewer periods make this MA more responsive to recent price changes
                - long_window: Period for long moving average (default: 50)
                    More periods make this MA smoother and represent longer-term trends
        
        Example:
            # Create strategy with default parameters (20, 50)
            strategy = MovingAverageCrossover()
            
            # Create strategy with custom parameters (10, 30)
            strategy = MovingAverageCrossover({'short_window': 10, 'long_window': 30})
        """
        # Set default parameter values
        default_params = {
            'short_window': 20,  # Default short MA period (faster moving)
            'long_window': 50    # Default long MA period (slower moving)
        }
        
        # Update default params with provided params if any
        # This allows users to customize only specific parameters
        if params:
            default_params.update(params)
            
        # Initialize the base Strategy class with our parameters
        super().__init__(default_params)
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Generate a single buy/sell/hold signal based on most recent data.
        
        This method analyzes the most recent price data to determine if a
        moving average crossover has occurred and returns the appropriate signal.
        It's designed to be called in real-time trading to make a decision
        based on the latest market data.
        
        Algorithm:
        1. Check if there's enough data for calculation
        2. Calculate short and long moving averages
        3. Compare current and previous positions of the MAs
        4. Identify crossovers and return the corresponding signal
        
        Args:
            data: DataFrame containing OHLC (Open-High-Low-Close) price data
                 Must contain a 'close' column with closing prices
                 
        Returns:
            Signal string: 'buy', 'sell', or 'hold'
            
        Notes:
            - Returns 'hold' if there's insufficient data for calculation
            - Uses the two most recent data points to detect crossovers
        """
        # Ensure we have enough data for the moving averages
        # We need at least as many data points as the long window requires
        if len(data) < self.params['long_window']:
            return 'hold'  # Not enough data, so we can't make a decision
            
        # Calculate moving averages using pandas built-in functions
        # These create Series objects with the same index as the original data
        short_ma = data['close'].rolling(window=self.params['short_window']).mean()
        long_ma = data['close'].rolling(window=self.params['long_window']).mean()
        
        # Get the current and previous values to detect crossovers
        # We use the last two points to determine if a crossover just happened
        current_short_ma = short_ma.iloc[-1]    # Most recent short MA value
        previous_short_ma = short_ma.iloc[-2]   # Previous short MA value
        current_long_ma = long_ma.iloc[-1]      # Most recent long MA value
        previous_long_ma = long_ma.iloc[-2]     # Previous long MA value
        
        # Generate trading signal based on crossover detection
        if (previous_short_ma <= previous_long_ma) and (current_short_ma > current_long_ma):
            # Bullish crossover: Short MA crossed above Long MA
            # This suggests upward momentum is now stronger than the longer-term trend
            return 'buy'
            
        elif (previous_short_ma >= previous_long_ma) and (current_short_ma < current_long_ma):
            # Bearish crossover: Short MA crossed below Long MA
            # This suggests downward momentum is now stronger than the longer-term trend
            return 'sell'
            
        else:
            # No crossover detected, maintain current position
            return 'hold'
            
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all strategy indicators and signals for the entire dataset.
        
        This method is primarily used for:
        1. Backtesting - to generate signals for each historical data point
        2. Visualization - to plot indicators alongside price data
        3. Analysis - to examine the performance of different parameter settings
        
        Unlike generate_signal() which gives a single signal for the most recent data,
        this method processes the entire dataset and adds indicator columns.
        
        Args:
            data: DataFrame containing OHLC (Open-High-Low-Close) price data
                 Must contain a 'close' column with closing prices
                 
        Returns:
            Enhanced DataFrame with added columns:
            - 'short_ma': Short-term moving average values
            - 'long_ma': Long-term moving average values
            - 'signal': Trading signal at each data point ('buy', 'sell', 'hold')
            
        Notes:
            This implementation uses vectorized operations for improved performance
            compared to iterating through each data point individually.
        """
        # Create a copy to avoid modifying the original dataframe
        # This ensures we don't accidentally modify caller's data
        result = data.copy()
        
        # Calculate moving averages and add them as new columns
        result['short_ma'] = result['close'].rolling(window=self.params['short_window']).mean()
        result['long_ma'] = result['close'].rolling(window=self.params['long_window']).mean()
        
        # Initialize all signals as 'hold'
        result['signal'] = 'hold'
        
        # Identify bullish crossovers (short MA crosses above long MA)
        # Current: short_ma > long_ma
        # Previous: short_ma <= long_ma
        # This creates a boolean mask we can use to set signal values
        result.loc[(result['short_ma'] > result['long_ma']) & 
                   (result['short_ma'].shift(1) <= result['long_ma'].shift(1)), 'signal'] = 'buy'
        
        # Identify bearish crossovers (short MA crosses below long MA)
        # Current: short_ma < long_ma
        # Previous: short_ma >= long_ma
        result.loc[(result['short_ma'] < result['long_ma']) & 
                   (result['short_ma'].shift(1) >= result['long_ma'].shift(1)), 'signal'] = 'sell'
        
        return result