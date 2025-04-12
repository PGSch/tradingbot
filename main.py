#!/usr/bin/env python3
"""
Kraken Trading Bot - Main Entry Point

This script provides a command-line interface for running the trading bot
in different modes: live trading, paper trading, or backtesting.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

from src.trading_bot import TradingBot
from src.utils.logger import setup_logger

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Kraken Trading Bot')
    
    # Mode options (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--paper', action='store_true', help='Run in paper trading mode (default)')
    mode_group.add_argument('--live', action='store_true', help='Run in live trading mode')
    mode_group.add_argument('--backtest', action='store_true', help='Run in backtesting mode')
    
    # General options
    parser.add_argument('-c', '--config', type=str, help='Path to configuration file')
    parser.add_argument('-i', '--interval', type=int, default=60,
                        help='Trading interval in minutes (default: 60)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    # Backtest options
    parser.add_argument('--start', type=str, help='Start date for backtest (format: YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date for backtest (format: YYYY-MM-DD)')
    parser.add_argument('--no-plot', action='store_true', help='Disable plotting in backtest mode')
    
    return parser.parse_args()

def main():
    """Main function"""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger('main', log_level=log_level, log_dir='logs')
    logger.info("Starting Kraken Trading Bot")
    
    # Determine operating mode
    if args.live:
        mode = 'live'
    elif args.backtest:
        mode = 'backtest'
    else:
        # Default to paper trading
        mode = 'paper'
    
    logger.info(f"Operating mode: {mode}")
    
    try:
        # Initialize trading bot
        bot = TradingBot(config_path=args.config)
        
        if mode == 'backtest':
            # Run backtest
            logger.info(f"Running backtest from {args.start or 'earliest'} to {args.end or 'latest'}")
            results = bot.backtest(
                start_date=args.start,
                end_date=args.end,
                interval=args.interval,
                plot=not args.no_plot
            )
            
            # Print backtest results
            if results['status'] == 'success':
                metrics = results['metrics']
                print("\n===== Backtest Results =====")
                print(f"Total trades: {metrics['total_trades']}")
                print(f"Win rate: {metrics['win_rate']:.2%}")
                print(f"Average win: {metrics['avg_win']:.2%}")
                print(f"Average loss: {metrics['avg_loss']:.2%}")
                print(f"Cumulative return: {metrics['cumulative_return']:.2%}")
                print("===========================\n")
            else:
                logger.error(f"Backtest failed: {results.get('reason')}")
                
        else:  # paper or live trading
            # Run trading bot
            logger.info(f"Starting {mode} trading with {args.interval}m interval")
            bot.start(interval_minutes=args.interval, mode=mode)
    
    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user")
    except Exception as e:
        logger.exception(f"Error running trading bot: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())