import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Optional, List
import matplotlib.pyplot as plt
import logging
import re
import datetime
from glob import glob

logger = logging.getLogger(__name__)

def save_data(data: pd.DataFrame, file_path: str, format: str = 'csv') -> bool:
    """
    Save market data to a file for persistence and later analysis.
    
    This function saves trading data (like OHLC price data, indicators, signals)
    to disk in either CSV or pickle format. CSV is human-readable but slower,
    while pickle preserves exact DataFrame structure but is Python-specific.
    
    The function automatically creates any necessary directories in the path,
    making it convenient for organizing data storage hierarchically.
    
    Args:
        data: DataFrame containing market data, typically with DateTimeIndex
             and columns for prices, indicators, signals, etc.
        file_path: Path (absolute or relative) where data should be saved
                  Example: 'data/market_20250412_182041.csv'
        format: File format to use - either 'csv' for human-readable text
               or 'pickle' for binary Python-specific format (faster/more precise)
    
    Returns:
        Boolean indicating success (True) or failure (False)
        
    Notes:
        - CSV format is better for data you might want to view or use in other tools
        - Pickle format preserves exact DataFrame structure including dtypes
        - The function logs the outcome (success or error message)
    """
    try:
        # Create directory if it doesn't exist
        # This ensures we don't get "directory not found" errors
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save data using the specified format
        if format.lower() == 'csv':
            # CSV: Human-readable text format, compatible with many tools
            data.to_csv(file_path)
        elif format.lower() == 'pickle':
            # Pickle: Binary Python-specific format that preserves exact object structure
            data.to_pickle(file_path)
        else:
            # Log error for unsupported format and return failure
            logger.error(f"Unsupported format: {format}")
            return False
            
        # Log success and return True
        logger.info(f"Data saved to {file_path}")
        return True
        
    except Exception as e:
        # Log any errors that occur during saving
        logger.error(f"Error saving data: {e}")
        return False

def load_data(file_path: str, format: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Load market data from a saved file.
    
    This function loads previously saved trading data from disk, either from
    CSV or pickle format. It can automatically detect the format based on file
    extension if not explicitly specified.
    
    For CSV files, it automatically sets the first column as the index and
    parses dates, which is the typical format for time series data.
    
    Args:
        file_path: Path to the data file to load
                  Example: 'data/market_20250412_182041.csv'
        format: File format ('csv' or 'pickle')
               If None, format will be inferred from file extension
    
    Returns:
        DataFrame containing the loaded market data
        None if loading fails (file not found, wrong format, etc.)
        
    Notes:
        - When loading CSV, assumes the first column is the DateTimeIndex
        - For data exchange with other systems, CSV is more portable
        - If working exclusively in Python, pickle preserves DataFrame precisely
    """
    try:
        # Check if the file exists before attempting to load it
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
            
        # If no format specified, try to determine from file extension
        if format is None:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.csv':
                format = 'csv'
            elif ext in ['.pkl', '.pickle']:
                format = 'pickle'
            else:
                logger.error(f"Unsupported file extension: {ext}")
                return None
        
        # Load data based on the determined format
        if format.lower() == 'csv':
            # For CSV, set the first column as the index and parse dates
            data = pd.read_csv(file_path, index_col=0, parse_dates=True)
        elif format.lower() == 'pickle':
            # For pickle, load the serialized DataFrame directly
            data = pd.read_pickle(file_path)
        else:
            # Log error for unsupported format
            logger.error(f"Unsupported format: {format}")
            return None
            
        # Log success and return the loaded data
        logger.info(f"Data loaded from {file_path}")
        return data
        
    except Exception as e:
        # Log any errors that occur during loading
        logger.error(f"Error loading data: {e}")
        return None

def plot_strategy(data: pd.DataFrame, save_path: Optional[str] = None) -> None:
    """
    Create a visualization of trading strategy performance with buy/sell signals.
    
    This function generates a comprehensive chart showing:
    1. Price movements over time
    2. Technical indicators (like moving averages)
    3. Buy/sell signals at their respective price points
    4. Trading volume (if available)
    
    The visualization helps in:
    - Understanding how the strategy performs visually
    - Identifying patterns in successful/unsuccessful trades
    - Sharing results with stakeholders
    - Documenting strategy behavior for future reference
    
    Args:
        data: DataFrame with OHLC price data and strategy indicators
             Must contain at least a 'close' price column
             May include 'short_ma', 'long_ma', 'signal', 'volume' columns
        save_path: Path to save the generated plot image (optional)
                  If provided, saves the plot to this file path
                  Example: 'results/backtest_20250412_182041.png'
    
    Notes:
        - Creates a figure with two subplots: price/signals and volume
        - Buy signals are shown as green up-arrows
        - Sell signals are shown as red down-arrows
        - The function automatically detects which indicators are available in the data
    """
    try:
        # Create a new figure with specific dimensions
        plt.figure(figsize=(12, 8))  # Width: 12 inches, Height: 8 inches
        
        # Top subplot: Price and indicators with buy/sell signals
        plt.subplot(2, 1, 1)  # 2 rows, 1 column, first plot
        
        # Plot the closing price as a semi-transparent line
        plt.plot(data.index, data['close'], label='Close Price', alpha=0.5)
        
        # If available, plot the short-term moving average
        if 'short_ma' in data.columns:
            plt.plot(data.index, data['short_ma'], label='Short MA')
        
        # If available, plot the long-term moving average
        if 'long_ma' in data.columns:
            plt.plot(data.index, data['long_ma'], label='Long MA')
        
        # Plot buy/sell signals if available
        if 'signal' in data.columns:
            # Extract points where buy signals occurred
            buys = data.loc[data['signal'] == 'buy']
            # Extract points where sell signals occurred
            sells = data.loc[data['signal'] == 'sell']
            
            # Plot buy signals as green up-arrows
            plt.scatter(buys.index, buys['close'], marker='^', color='g', label='Buy', s=100)
            # Plot sell signals as red down-arrows
            plt.scatter(sells.index, sells['close'], marker='v', color='r', label='Sell', s=100)
        
        # Add title and labels
        plt.title('Trading Strategy')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()  # Show legend with all plotted elements
        plt.grid(True)  # Add grid for easier reading
        
        # Bottom subplot: Volume chart (if available)
        if 'volume' in data.columns:
            plt.subplot(2, 1, 2)  # 2 rows, 1 column, second plot
            plt.bar(data.index, data['volume'], color='blue', alpha=0.5)
            plt.title('Volume')
            plt.xlabel('Date')
            plt.ylabel('Volume')
            plt.grid(True)
        
        # Ensure proper spacing between subplots
        plt.tight_layout()
        
        # Save the plot to file if a path was provided
        if save_path:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path)
            logger.info(f"Plot saved to {save_path}")
        
        # Display the plot (typically shown in a window)
        plt.show()
        
    except Exception as e:
        # Log any errors that occur during plotting
        logger.error(f"Error plotting strategy: {e}")

def resample_ohlc(data: pd.DataFrame, interval: str) -> pd.DataFrame:
    """
    Resample OHLC (Open, High, Low, Close) data to a different time interval.
    
    This function allows changing the timeframe of price data, for example:
    - Converting 1-minute candles to 5-minute candles
    - Converting hourly data to daily data
    - Aggregating intraday data to weekly summaries
    
    This is useful for:
    - Testing strategies on multiple timeframes
    - Reducing noise in high-frequency data
    - Performing multi-timeframe analysis
    
    Args:
        data: DataFrame containing OHLC price data with DateTimeIndex
              Must have 'open', 'high', 'low', 'close', and 'volume' columns
        interval: Target interval as pandas offset string
                 Examples: '5min', '1H', '1D', '1W'
    
    Returns:
        DataFrame with resampled OHLC data at the specified interval
        
    Notes:
        - Open: First price in the interval
        - High: Highest price in the interval
        - Low: Lowest price in the interval
        - Close: Last price in the interval
        - Volume: Sum of all volume in the interval
    """
    try:
        # Create a resampler object with the specified interval
        resampler = data.resample(interval)
        
        # Apply appropriate aggregation functions for each column
        resampled_data = pd.DataFrame({
            'open': resampler['open'].first(),      # First price in interval
            'high': resampler['high'].max(),        # Highest price in interval
            'low': resampler['low'].min(),          # Lowest price in interval
            'close': resampler['close'].last(),     # Last price in interval
            'volume': resampler['volume'].sum()     # Sum of volume in interval
        })
        
        logger.info(f"Data resampled from {len(data)} to {len(resampled_data)} periods ({interval})")
        return resampled_data
        
    except Exception as e:
        logger.error(f"Error resampling data to {interval}: {e}")
        # Return original data on error
        return data

def cleanup_data_files(data_dir: str, file_pattern: str = 'market_*.csv', 
                       max_files: int = 100, days_to_keep: int = 7) -> int:
    """
    Clean up data files to prevent excessive accumulation in the data directory.
    
    This function manages the data directory by removing old files while keeping 
    a configurable number of the most recent files. It can filter by both age and 
    maximum quantity to ensure your storage doesn't grow unbounded.
    
    The function identifies files to delete using these rules (applied in order):
    1. Keep all files that are newer than days_to_keep
    2. Of the older files, keep the most recent ones up to max_files total
    
    Args:
        data_dir: Path to the data directory to clean up
        file_pattern: Glob pattern to match files (default: 'market_*.csv')
        max_files: Maximum number of files to keep (default: 100)
        days_to_keep: Keep all files newer than this many days (default: 7)
    
    Returns:
        Number of files deleted
        
    Example:
        # Clean up market data files, keeping only 50 most recent files
        # that are older than 3 days
        cleanup_data_files('data/', max_files=50, days_to_keep=3)
    """
    try:
        # Ensure data directory exists
        if not os.path.exists(data_dir):
            logger.warning(f"Data directory not found: {data_dir}")
            return 0
            
        # Get all files matching the pattern
        file_path = os.path.join(data_dir, file_pattern)
        all_files = glob(file_path)
        
        if not all_files:
            logger.info(f"No files matching '{file_pattern}' found in {data_dir}")
            return 0
            
        # Extract dates from filenames and create a list of (file, datetime) tuples
        file_dates = []
        date_pattern = re.compile(r'(\d{8})_(\d{6})')
        
        for file_path in all_files:
            filename = os.path.basename(file_path)
            match = date_pattern.search(filename)
            
            if match:
                # Extract date components
                date_str = match.group(1)
                time_str = match.group(2)
                
                # Parse the datetime
                try:
                    file_date = datetime.datetime.strptime(
                        f"{date_str}_{time_str}", "%Y%m%d_%H%M%S"
                    )
                    file_dates.append((file_path, file_date))
                except ValueError:
                    # If date parsing fails, use file modification time as fallback
                    mod_time = os.path.getmtime(file_path)
                    file_date = datetime.datetime.fromtimestamp(mod_time)
                    file_dates.append((file_path, file_date))
            else:
                # If filename doesn't match pattern, use file modification time
                mod_time = os.path.getmtime(file_path)
                file_date = datetime.datetime.fromtimestamp(mod_time)
                file_dates.append((file_path, file_date))
                
        # Sort files by date, newest first
        file_dates.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate the cutoff date for days_to_keep
        now = datetime.datetime.now()
        cutoff_date = now - datetime.timedelta(days=days_to_keep)
        
        # Separate recent files (to keep) from older files (candidates for deletion)
        recent_files = []
        older_files = []
        
        for file_path, file_date in file_dates:
            if file_date > cutoff_date:
                recent_files.append(file_path)
            else:
                older_files.append(file_path)
                
        # Calculate how many older files to keep
        older_files_to_keep = max(0, max_files - len(recent_files))
        files_to_delete = older_files[older_files_to_keep:]
        
        # Delete the excess files
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                deleted_count += 1
                logger.debug(f"Deleted old data file: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
                
        if deleted_count > 0:
            logger.info(f"Cleaned up data directory: {deleted_count} old files removed, "
                       f"{len(recent_files) + min(older_files_to_keep, len(older_files))} files kept")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")
        return 0

def merge_data_files(data_dir: str, output_file: str, file_pattern: str = 'market_*.csv') -> bool:
    """
    Merge multiple market data files into a single consolidated file.
    
    This function combines data from multiple smaller files into a single larger file,
    which can be useful for later analysis or to reduce the number of files after
    a cleanup operation. Duplicate timestamps will be removed, keeping only the first
    occurrence.
    
    Args:
        data_dir: Path to the data directory containing files to merge
        output_file: Path to the output merged file
        file_pattern: Glob pattern to match files (default: 'market_*.csv')
    
    Returns:
        Boolean indicating success (True) or failure (False)
    """
    try:
        # Get all files matching the pattern
        file_path = os.path.join(data_dir, file_pattern)
        all_files = glob(file_path)
        
        if not all_files:
            logger.warning(f"No files to merge matching '{file_pattern}' in {data_dir}")
            return False
            
        # Read and concatenate all data files
        dfs = []
        for file in all_files:
            try:
                df = pd.read_csv(file, index_col=0, parse_dates=True)
                dfs.append(df)
            except Exception as e:
                logger.warning(f"Could not read file {file}: {e}")
                
        if not dfs:
            logger.warning("No valid data files to merge")
            return False
            
        # Concatenate all dataframes and sort by index (timestamp)
        merged_data = pd.concat(dfs)
        
        # Remove duplicates, keeping the first occurrence
        merged_data = merged_data.loc[~merged_data.index.duplicated(keep='first')]
        
        # Sort by time
        merged_data = merged_data.sort_index()
        
        # Save merged data
        output_path = os.path.join(data_dir, output_file)
        merged_data.to_csv(output_path)
        
        logger.info(f"Merged {len(dfs)} files into {output_path}, total records: {len(merged_data)}")
        return True
        
    except Exception as e:
        logger.error(f"Error merging data files: {e}")
        return False