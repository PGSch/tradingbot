import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.strategies.moving_average import MovingAverageCrossover

class TestMovingAverageStrategy(unittest.TestCase):
    """Test cases for the Moving Average Crossover strategy"""
    
    def generate_test_data(self, trend='up'):
        """
        Generate test price data with a specific trend
        
        Args:
            trend: 'up', 'down', or 'sideways'
            
        Returns:
            DataFrame with test price data
        """
        # Create date index
        dates = [datetime.now() - timedelta(days=i) for i in range(100, 0, -1)]
        
        # Generate price data based on trend
        if trend == 'up':
            close = np.linspace(100, 200, 100) + np.random.normal(0, 5, 100)
        elif trend == 'down':
            close = np.linspace(200, 100, 100) + np.random.normal(0, 5, 100)
        else:  # sideways
            close = np.ones(100) * 150 + np.random.normal(0, 10, 100)
            
        # Create DataFrame
        data = pd.DataFrame(index=dates, data={'close': close})
        return data
    
    def test_buy_signal_in_uptrend(self):
        """Test if strategy correctly identifies a buy signal in an uptrend"""
        # Initialize strategy with test parameters
        strategy = MovingAverageCrossover({'short_window': 10, 'long_window': 30})
        
        # Generate test data with uptrend and a crossover
        data = self.generate_test_data(trend='up')
        
        # Force a buy signal by ensuring short MA crosses above long MA
        data_with_indicators = strategy.calculate_indicators(data)
        
        # Create a scenario where the short MA crosses above the long MA
        # We manually adjust the last few points to ensure a crossover
        data_with_indicators.loc[data_with_indicators.index[-5], 'short_ma'] = data_with_indicators.loc[data_with_indicators.index[-5], 'long_ma'] - 1
        data_with_indicators.loc[data_with_indicators.index[-3:], 'short_ma'] = data_with_indicators.loc[data_with_indicators.index[-3:], 'long_ma'] + 1
        
        # Generate signal from the adjusted data
        signal = strategy.generate_signal(data_with_indicators)
        
        # Assert that we get a buy signal
        self.assertEqual(signal, 'buy')
    
    def test_sell_signal_in_downtrend(self):
        """Test if strategy correctly identifies a sell signal in a downtrend"""
        # Initialize strategy with test parameters
        strategy = MovingAverageCrossover({'short_window': 10, 'long_window': 30})
        
        # Generate test data with downtrend
        data = self.generate_test_data(trend='down')
        
        # Calculate indicators
        data_with_indicators = strategy.calculate_indicators(data)
        
        # Create a scenario where the short MA crosses below the long MA
        data_with_indicators.loc[data_with_indicators.index[-5], 'short_ma'] = data_with_indicators.loc[data_with_indicators.index[-5], 'long_ma'] + 1
        data_with_indicators.loc[data_with_indicators.index[-3:], 'short_ma'] = data_with_indicators.loc[data_with_indicators.index[-3:], 'long_ma'] - 1
        
        # Generate signal
        signal = strategy.generate_signal(data_with_indicators)
        
        # Assert that we get a sell signal
        self.assertEqual(signal, 'sell')
    
    def test_hold_signal_no_crossover(self):
        """Test if strategy correctly gives hold signal when there's no crossover"""
        # Initialize strategy with test parameters
        strategy = MovingAverageCrossover({'short_window': 10, 'long_window': 30})
        
        # Generate test data
        data = self.generate_test_data(trend='sideways')
        
        # Calculate indicators
        data_with_indicators = strategy.calculate_indicators(data)
        
        # Ensure no crossover in the last few points
        data_with_indicators.loc[data_with_indicators.index[-10:], 'short_ma'] = data_with_indicators.loc[data_with_indicators.index[-10:], 'long_ma'] + 5
        
        # Generate signal
        signal = strategy.generate_signal(data_with_indicators)
        
        # Assert that we get a hold signal
        self.assertEqual(signal, 'hold')
        
    def test_hold_signal_insufficient_data(self):
        """Test if strategy correctly gives hold signal when there's insufficient data"""
        # Initialize strategy with test parameters
        strategy = MovingAverageCrossover({'short_window': 10, 'long_window': 30})
        
        # Create small dataset (less than the long window)
        dates = [datetime.now() - timedelta(days=i) for i in range(20, 0, -1)]
        close = np.linspace(100, 120, 20)
        data = pd.DataFrame(index=dates, data={'close': close})
        
        # Generate signal
        signal = strategy.generate_signal(data)
        
        # Assert that we get a hold signal due to insufficient data
        self.assertEqual(signal, 'hold')

if __name__ == '__main__':
    unittest.main()