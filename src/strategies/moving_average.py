import pandas as pd
import numpy as np
from typing import Dict, Any
from .base_strategy import Strategy

class MovingAverageCrossover(Strategy):
    """
    Moving Average Crossover Strategy
    
    Generates buy/sell signals based on the crossing of a short-term moving average
    and a long-term moving average
    """
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize the MovingAverageCrossover strategy
        
        Args:
            params: Strategy parameters including:
                - short_window: Period for short moving average (default: 20)
                - long_window: Period for long moving average (default: 50)
        """
        default_params = {
            'short_window': 20,
            'long_window': 50
        }
        
        # Update default params with provided params
        if params:
            default_params.update(params)
            
        super().__init__(default_params)
        
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Generate buy/sell/hold signal based on moving average crossover
        
        Args:
            data: OHLC data with 'close' price column
            
        Returns:
            Signal: 'buy', 'sell', or 'hold'
        """
        if len(data) < self.params['long_window']:
            return 'hold'  # Not enough data
            
        # Calculate moving averages
        short_ma = data['close'].rolling(window=self.params['short_window']).mean()
        long_ma = data['close'].rolling(window=self.params['long_window']).mean()
        
        # Get current and previous values
        current_short_ma = short_ma.iloc[-1]
        previous_short_ma = short_ma.iloc[-2]
        current_long_ma = long_ma.iloc[-1]
        previous_long_ma = long_ma.iloc[-2]
        
        # Generate signal
        if (previous_short_ma <= previous_long_ma) and (current_short_ma > current_long_ma):
            return 'buy'  # Bullish crossover
        elif (previous_short_ma >= previous_long_ma) and (current_short_ma < current_long_ma):
            return 'sell'  # Bearish crossover
        else:
            return 'hold'  # No crossover
            
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate and add strategy indicators to the dataframe
        
        Args:
            data: OHLC data with 'close' price column
            
        Returns:
            DataFrame with added indicators
        """
        # Create a copy to avoid modifying the original dataframe
        result = data.copy()
        
        # Calculate moving averages
        result['short_ma'] = result['close'].rolling(window=self.params['short_window']).mean()
        result['long_ma'] = result['close'].rolling(window=self.params['long_window']).mean()
        
        # Calculate signals
        result['signal'] = 'hold'
        
        # Identify crossovers
        result.loc[(result['short_ma'] > result['long_ma']) & 
                   (result['short_ma'].shift(1) <= result['long_ma'].shift(1)), 'signal'] = 'buy'
                   
        result.loc[(result['short_ma'] < result['long_ma']) & 
                   (result['short_ma'].shift(1) >= result['long_ma'].shift(1)), 'signal'] = 'sell'
        
        return result