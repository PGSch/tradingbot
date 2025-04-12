from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    This class defines the interface that all trading strategies must implement.
    It uses Python's Abstract Base Class (ABC) to create a contract that ensures
    all derived strategies provide the required functionality.
    
    The Strategy pattern allows the trading bot to:
    1. Switch between different strategies at runtime
    2. Implement new strategies without changing the core trading logic
    3. Maintain consistent interfaces for all strategies
    4. Test and compare different strategies with the same data
    
    All concrete strategy implementations should inherit from this class
    and implement the required abstract methods.
    """
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize the strategy with parameters.
        
        This constructor stores the strategy parameters, which can be used
        to customize the behavior of the strategy without changing code.
        
        Args:
            params: Dictionary of strategy parameters, which varies based on strategy type.
                   Common parameters might include:
                   - lookback_period: Number of data points to consider
                   - thresholds: Values that trigger signals
                   - weights: Importance factors for different indicators
        
        Example:
            # RSI strategy with custom parameters
            strategy = RSIStrategy({'overbought': 70, 'oversold': 30, 'period': 14})
        """
        self.params = params or {}  # Default to empty dict if no params provided
        
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Generate buy/sell/hold signal based on market data.
        
        This is the core method of any strategy that must be implemented by all subclasses.
        It analyzes market data and returns a trading signal that the bot will act upon.
        
        Args:
            data: Market data as DataFrame, typically containing OHLC (Open-High-Low-Close)
                 price data and possibly volume or other market indicators
        
        Returns:
            Signal string: Must be one of:
            - 'buy': Recommend opening a long position
            - 'sell': Recommend closing a long position or opening a short position
            - 'hold': Recommend maintaining current position (no action)
        
        Notes:
            - This method should focus on the most recent data points to generate a signal
            - Implementation must be provided by concrete strategy subclasses
            - Should handle edge cases like insufficient data
        """
        pass
    
    def set_params(self, params: Dict[str, Any]) -> None:
        """
        Update strategy parameters dynamically.
        
        This method allows changing strategy parameters without recreating the object.
        Useful for:
        - Parameter tuning during optimization
        - Adapting the strategy to changing market conditions
        - A/B testing different parameter sets
        
        Args:
            params: Dictionary of strategy parameters to update
                   Only updates specified parameters, leaving others unchanged
        
        Example:
            # Adjust RSI thresholds based on market volatility
            strategy.set_params({'overbought': 80, 'oversold': 20})
        """
        self.params.update(params)
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicators and signals for the entire dataset.
        
        This method is primarily used for backtesting and visualization.
        Unlike generate_signal() which produces a single signal for current data,
        this method processes the entire historical dataset.
        
        Concrete strategies should override this method to add their specific
        indicators to the dataframe.
        
        Args:
            data: Market data as DataFrame with OHLC data
            
        Returns:
            DataFrame with added indicator columns and signal column
            
        Notes:
            The base implementation returns data unchanged, but
            subclasses should add their specific indicators and signals.
        """
        # Default implementation just returns the data unchanged
        # Subclasses should override this with their specific indicators
        return data