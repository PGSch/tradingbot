import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

def save_data(data: pd.DataFrame, file_path: str, format: str = 'csv') -> bool:
    """
    Save market data to a file
    
    Args:
        data: DataFrame containing market data
        file_path: Path to save the file
        format: File format ('csv' or 'pickle')
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save data
        if format.lower() == 'csv':
            data.to_csv(file_path)
        elif format.lower() == 'pickle':
            data.to_pickle(file_path)
        else:
            logger.error(f"Unsupported format: {format}")
            return False
            
        logger.info(f"Data saved to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        return False

def load_data(file_path: str, format: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Load market data from a file
    
    Args:
        file_path: Path to the data file
        format: File format ('csv' or 'pickle'), if None, will be inferred from extension
    
    Returns:
        DataFrame containing market data or None if error
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        # Infer format from file extension if not provided
        if format is None:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.csv':
                format = 'csv'
            elif ext in ['.pkl', '.pickle']:
                format = 'pickle'
            else:
                logger.error(f"Unsupported file extension: {ext}")
                return None
        
        # Load data
        if format.lower() == 'csv':
            data = pd.read_csv(file_path, index_col=0, parse_dates=True)
        elif format.lower() == 'pickle':
            data = pd.read_pickle(file_path)
        else:
            logger.error(f"Unsupported format: {format}")
            return None
            
        logger.info(f"Data loaded from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None

def plot_strategy(data: pd.DataFrame, save_path: Optional[str] = None) -> None:
    """
    Visualize trading strategy with buy/sell signals
    
    Args:
        data: DataFrame with OHLC and strategy indicators
        save_path: Path to save the plot (optional)
    """
    try:
        # Create a new figure
        plt.figure(figsize=(12, 8))
        
        # Plot price and moving averages
        plt.subplot(2, 1, 1)
        plt.plot(data.index, data['close'], label='Close Price', alpha=0.5)
        
        if 'short_ma' in data.columns:
            plt.plot(data.index, data['short_ma'], label='Short MA')
        
        if 'long_ma' in data.columns:
            plt.plot(data.index, data['long_ma'], label='Long MA')
        
        # Plot buy/sell signals
        if 'signal' in data.columns:
            buys = data.loc[data['signal'] == 'buy']
            sells = data.loc[data['signal'] == 'sell']
            
            plt.scatter(buys.index, buys['close'], marker='^', color='g', label='Buy', s=100)
            plt.scatter(sells.index, sells['close'], marker='v', color='r', label='Sell', s=100)
        
        plt.title('Trading Strategy')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        
        # Volume subplot
        if 'volume' in data.columns:
            plt.subplot(2, 1, 2)
            plt.bar(data.index, data['volume'], color='blue', alpha=0.5)
            plt.title('Volume')
            plt.xlabel('Date')
            plt.ylabel('Volume')
            plt.grid(True)
        
        plt.tight_layout()
        
        # Save plot if path is provided
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path)
            logger.info(f"Plot saved to {save_path}")
        
        plt.show()
    except Exception as e:
        logger.error(f"Error plotting strategy: {e}")