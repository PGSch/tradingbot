#!/usr/bin/env python3
"""
Paper trading example for the Kraken trading bot

This script demonstrates how to use the TradingBot API to run paper trading
with real-time market data but without executing actual trades.
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.trading_bot import TradingBot
from src.utils.logger import setup_logger

def run_paper_trading():
    """Run paper trading simulation"""
    # Setup logging
    logger = setup_logger('paper_trading_example', log_dir='logs')
    logger.info("Starting paper trading example...")
    
    # Initialize trading bot
    bot = TradingBot()
    
    # Define paper trading parameters
    trading_interval = 5  # minutes (use a shorter interval for the example)
    duration = 30  # minutes to run the simulation
    
    logger.info(f"Running paper trading simulation for {duration} minutes with {trading_interval}-minute intervals")
    
    # Run the trading bot for a fixed duration
    end_time = time.time() + (duration * 60)
    
    trading_cycles = 0
    try:
        while time.time() < end_time:
            # Start a trading cycle
            logger.info(f"Trading cycle {trading_cycles + 1}")
            
            # Fetch market data
            data = bot.fetch_market_data(interval=trading_interval)
            
            # Generate signal
            if not data.empty:
                signal = bot.analyze_market(data)
                logger.info(f"Generated signal: {signal}")
                
                # In paper trading mode, we don't execute real trades
                logger.info(f"Paper trading - Would execute: {signal}")
            else:
                logger.warning("No market data available")
            
            trading_cycles += 1
            
            # Wait until the next interval (unless we're at the end)
            remaining_time = end_time - time.time()
            if remaining_time > 0:
                sleep_time = min(trading_interval * 60, remaining_time)
                logger.info(f"Waiting {sleep_time:.1f} seconds until next trading cycle...")
                time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        logger.info("Paper trading simulation stopped by user")
    
    logger.info(f"Paper trading simulation completed with {trading_cycles} cycles")

if __name__ == "__main__":
    run_paper_trading()