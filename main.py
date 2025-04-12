#!/usr/bin/env python3
"""
Kraken Trading Bot - Main Entry Point

This script provides a command-line interface for running the trading bot
in different modes: live trading, paper trading, or backtesting.

The program flow is as follows:
1. Parse command-line arguments to determine operating mode and options
2. Set up logging based on verbosity level
3. Initialize the trading bot with configuration
4. Run the bot in the specified mode (live trading, paper trading, or backtesting)
5. Display results or keep running until interrupted

Usage examples:
- Paper trading: python main.py --paper -i 60
- Live trading: python main.py --live -i 60
- Backtesting: python main.py --backtest --start 2024-01-01 --end 2024-03-31
"""

import os
import sys
import argparse
import logging
import time
import platform
from pathlib import Path

from src.trading_bot import TradingBot
from src.utils.logger import setup_logger, log_exception

def parse_arguments():
    """
    Parse command-line arguments to configure the bot's operation.
    
    This function defines all available command-line options and their defaults.
    It uses Python's argparse to handle argument validation and help message generation.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(description='Kraken Trading Bot')
    
    # Operating mode - these options are mutually exclusive
    # The bot can only run in one mode at a time
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--paper', action='store_true', 
                          help='Run in paper trading mode (default) - simulates trades without using real funds')
    mode_group.add_argument('--live', action='store_true', 
                          help='Run in live trading mode - executes real trades with actual funds')
    mode_group.add_argument('--backtest', action='store_true', 
                          help='Run in backtesting mode - tests strategy against historical data')
    
    # General options that apply to all modes
    parser.add_argument('-c', '--config', help='Path to configuration file with API keys and trading parameters', 
                      default='config/.env')
    parser.add_argument('-i', '--interval', type=int, 
                      help='Trading interval in minutes - how often to analyze the market and make decisions', 
                      default=60)
    parser.add_argument('-v', '--verbose', action='store_true', 
                      help='Enable verbose (DEBUG) logging - includes detailed debugging information')
    
    # Options specific to backtesting mode
    parser.add_argument('--start', help='Start date for backtest (format: YYYY-MM-DD)')
    parser.add_argument('--end', help='End date for backtest (format: YYYY-MM-DD)')
    parser.add_argument('--no-plot', action='store_true', 
                      help='Disable plotting in backtest mode - skip generating visualization charts')
    
    return parser.parse_args()

def main():
    """
    Main function that orchestrates the execution of the trading bot.
    
    This function:
    1. Sets up logging based on verbosity level
    2. Determines the operating mode (live/paper/backtest)
    3. Initializes the trading bot with configuration
    4. Runs the bot in the specified mode
    5. Handles and logs any exceptions that occur
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    # Record start time to track total execution time
    start_time = time.time()
    
    # Parse command-line arguments to determine how the bot should run
    args = parse_arguments()
    
    # Setup logging with appropriate verbosity level
    # DEBUG level includes more detailed logs compared to INFO level
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger('main', log_level=log_level, log_dir='logs')
    
    # Log system information for troubleshooting and documentation
    system_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'start_time': time.strftime("%Y-%m-%d %H:%M:%S")
    }
    logger.info(f"Starting Kraken Trading Bot on {system_info['platform']}, Python {system_info['python_version']}")
    
    # Determine operating mode based on command-line arguments
    # Default to paper trading if no mode is specified
    if args.live:
        mode = 'live'
    elif args.backtest:
        mode = 'backtest'
    else:
        # Paper trading is the default mode for safety
        mode = 'paper'
    
    logger.info(f"Operating mode: {mode.upper()}")
    
    # Show a clear warning when using live trading mode since real funds are at stake
    if mode == 'live':
        logger.warning("LIVE TRADING MODE - Real funds will be used for trading!")
    
    try:
        # Log configuration details and check if the config file exists
        config_path = args.config
        if os.path.exists(config_path):
            logger.info(f"Using configuration from {config_path}")
        else:
            logger.warning(f"Configuration file {config_path} not found, using default values")
        
        # Initialize the trading bot with the specified configuration
        logger.debug("Initializing trading bot...")
        bot = TradingBot(config_path=config_path)
        
        # Run the bot in the selected mode with appropriate parameters
        if mode == 'backtest':
            # Run backtest with the specified date range
            logger.info(f"Running backtest from {args.start or 'earliest'} to {args.end or 'latest'}")
            results = bot.backtest(
                start_date=args.start,
                end_date=args.end,
                interval=args.interval,
                plot=not args.no_plot
            )
            
            # Print backtest results in a formatted way
            if results['status'] == 'success':
                metrics = results['metrics']
                logger.info("======== BACKTEST RESULTS ========")
                logger.info(f"Total trades: {metrics['total_trades']}")
                logger.info(f"Win rate: {metrics['win_rate']:.2%}")
                logger.info(f"Average win: {metrics['avg_win']:.2%}")
                logger.info(f"Average loss: {metrics['avg_loss']:.2%}")
                logger.info(f"Cumulative return: {metrics['cumulative_return']:.2%}")
                logger.info("=================================")
            else:
                logger.error(f"Backtest failed: {results.get('reason', 'Unknown error')}")
        else:
            # Run live or paper trading with the specified interval
            logger.info(f"Starting {mode} trading with {args.interval}-minute intervals")
            # This call is blocking and will run until the bot is stopped or encounters an error
            bot.start(interval_minutes=args.interval, mode=mode)
        
        # Log the total execution time
        elapsed_time = time.time() - start_time
        logger.info(f"Bot execution completed in {elapsed_time:.2f} seconds")
        return 0
        
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully with a clean exit message
        logger.info("Bot stopped by user (KeyboardInterrupt)")
        return 0
        
    except Exception as e:
        # Catch and log any unhandled exceptions
        log_exception(logger, e, "Bot execution failed with an unhandled exception")
        return 1


# Standard Python idiom to ensure main() is only called when this script is run directly
if __name__ == "__main__":
    sys.exit(main())