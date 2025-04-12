#!/usr/bin/env python3
"""
Paper Trading Example for the Kraken Trading Bot

This script demonstrates how to use the TradingBot API to run paper trading
with real-time market data but without executing actual trades.

Paper trading allows you to:
1. Test trading strategies with real market data in real-time
2. Simulate trading behavior without financial risk
3. Verify the bot's decision-making before using real funds
4. Debug and monitor the trading logic and system performance

Usage:
    python paper_trading.py
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path so we can import from src
# This is a common pattern when running scripts from a subdirectory
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trading_bot import TradingBot
from src.utils.logger import setup_logger

def run_paper_trading():
    """
    Run a paper trading simulation using the trading bot.
    
    This function demonstrates the complete workflow of using the trading bot:
    1. Setting up logging to track all activities
    2. Initializing the trading bot with default configuration
    3. Defining simulation parameters (interval and duration)
    4. Running multiple trading cycles in a timed loop
    5. Fetching market data, analyzing it, and simulating trades
    6. Properly handling interruptions and cleanup
    
    The simulation runs for a fixed duration with periodic trading cycles,
    demonstrating how the bot would behave in a real trading environment
    but without executing actual trades.
    """
    # Setup logging with a specific name for this example
    # This creates both console output and log files in the logs directory
    logger = setup_logger('paper_trading_example', log_dir='logs')
    logger.info("Starting paper trading example...")
    
    # Initialize trading bot with default configuration
    # This will:
    # - Load parameters from .env file
    # - Initialize the API client (but won't use it for actual trades)
    # - Setup the specified trading strategy (default is moving average)
    bot = TradingBot()
    
    # Define paper trading simulation parameters
    # Using shorter intervals for the example to see more activity
    trading_interval = 5  # minutes between trading decisions (shorter for demonstration)
    duration = 30  # total minutes to run the simulation
    
    logger.info(f"Running paper trading simulation for {duration} minutes with {trading_interval}-minute intervals")
    
    # Calculate the end time for the simulation
    # This gives us a fixed duration rather than a fixed number of cycles
    end_time = time.time() + (duration * 60)
    
    # Keep track of how many trading cycles we complete
    trading_cycles = 0
    
    try:
        # Main simulation loop - run until we reach the end time
        while time.time() < end_time:
            # Log the start of a new trading cycle
            logger.info(f"Trading cycle {trading_cycles + 1}")
            
            # Step 1: Fetch the latest market data
            # This gets real market data from the exchange via the API
            data = bot.fetch_market_data(interval=trading_interval)
            
            # Step 2: Analyze the data and generate a trading signal
            if not data.empty:
                # Use the bot's strategy to determine what action to take
                signal = bot.analyze_market(data)
                logger.info(f"Generated signal: {signal}")
                
                # Step 3: In paper trading, we simulate the trade but don't execute it
                # In live trading, we would call bot.execute_trade(signal) here
                logger.info(f"Paper trading - Would execute: {signal}")
                
                # Additional step: In a real implementation, you might want to
                # track simulated portfolio value and performance metrics here
            else:
                # Handle the case where no data is available (API error, etc.)
                logger.warning("No market data available")
            
            # Increment the cycle counter
            trading_cycles += 1
            
            # Calculate how long to wait until the next cycle
            # This ensures we maintain the specified interval between cycles
            remaining_time = end_time - time.time()
            if remaining_time > 0:
                # Wait either for one full interval or until the end time, whichever is shorter
                sleep_time = min(trading_interval * 60, remaining_time)
                logger.info(f"Waiting {sleep_time:.1f} seconds until next trading cycle...")
                time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        # Handle the case where the user interrupts the simulation (Ctrl+C)
        # This provides a clean exit without error traceback
        logger.info("Paper trading simulation stopped by user")
    
    # Log summary information about the completed simulation
    logger.info(f"Paper trading simulation completed with {trading_cycles} cycles")
    
    # Note: In a more comprehensive implementation, you would calculate and
    # display performance metrics here (profit/loss, win rate, etc.)

# Standard Python idiom to ensure this code only runs when executed directly
if __name__ == "__main__":
    run_paper_trading()