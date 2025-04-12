from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class Strategy(ABC):
    """
    Abstract base class for all trading strategies
    """
    def __init__(self, params: Dict[str, Any] = None):
        """
        Initialize the strategy with parameters
        
        Args:
            params: Strategy parameters
        """
        self.params = params or {}
        
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> str:
        """
        Generate buy/sell/hold signal based on market data
        
        Args:
            data: Market data as DataFrame
        
        Returns:
            Signal: 'buy', 'sell', or 'hold'
        """
        pass
    
    def set_params(self, params: Dict[str, Any]) -> None:
        """
        Update strategy parameters
        
        Args:
            params: Strategy parameters to update
        """
        self.params.update(params)