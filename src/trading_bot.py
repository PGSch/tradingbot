import os
import time
import schedule
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Optional, Any, Union
import pandas as pd
import uuid

from .api.kraken_client import KrakenClient
from .strategies.moving_average import MovingAverageCrossover
from .utils.logger import setup_logger, log_exception, log_trade_execution, log_strategy_signal
from .utils.data_utils import save_data, load_data, plot_strategy

class TradingBot:
    """
    Trading bot that integrates exchange API with trading strategies
    to execute trades based on market conditions.
    
    This is the main class that orchestrates the entire trading process:
    1. Fetches market data from the exchange
    2. Analyzes the data using a trading strategy
    3. Makes trading decisions based on the analysis
    4. Executes trades on the exchange
    5. Logs all activities and maintains state
    
    The bot supports three modes of operation:
    - Live trading: Executes real trades with actual funds
    - Paper trading: Simulates trading without using real funds
    - Backtesting: Tests strategies against historical data
    """
    def __init__(self, config_path: str = None):
        """
        Initialize the trading bot with configuration and setup required components.
        
        This method:
        1. Creates a unique bot instance ID for tracking
        2. Sets up logging
        3. Loads configuration from environment variables
        4. Initializes the API client for exchange communication
        5. Sets up trading parameters and the selected strategy
        6. Initializes state variables to track bot status
        
        Args:
            config_path: Path to .env configuration file (optional)
                         If not provided, looks for .env in current directory
        """
        # Generate unique bot instance ID for tracking multiple instances
        # This is useful for distinguishing logs when running multiple bots simultaneously
        self.bot_id = str(uuid.uuid4())[:8]  # First 8 chars of UUID
        
        # Setup logging with the unique bot ID in the logger name
        self.logger = setup_logger(f'trading_bot_{self.bot_id}', log_dir='logs')
        
        # Load configuration from .env file
        # This includes API keys, trading parameters, strategy settings, etc.
        if config_path:
            load_dotenv(config_path)
            self.logger.info(f"Loaded configuration from {config_path}")
        else:
            load_dotenv()
            self.logger.info("Loaded configuration from default .env file")
            
        # Initialize API client for connecting to the exchange
        try:
            self.client = KrakenClient(config_path)
            self.logger.info("API client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize API client: {e}")
            log_exception(self.logger, e, "API client initialization failed")
            raise
        
        # Load trading parameters from environment variables
        # TRADING_PAIR: The cryptocurrency pair to trade (e.g., BTC/USD)
        # TRADE_VOLUME: The amount to buy/sell in each trade
        self.trading_pair = os.getenv('TRADING_PAIR', 'XXBTZUSD')
        self.trade_volume = float(os.getenv('TRADE_VOLUME', '0.001'))
        
        self.logger.debug(f"Trading parameters: PAIR={self.trading_pair}, VOLUME={self.trade_volume}")
        
        # Initialize the trading strategy based on configuration
        strategy_name = os.getenv('STRATEGY', 'simple_ma')
        self._init_strategy(strategy_name)
        
        # State variables to track bot status and history
        self.is_running = False  # Flag to control the bot's main loop
        self.last_action = 'none'  # Last trade action (buy/sell/none)
        self.data_cache = None  # Cache for the most recent market data
        self.trades_history = []  # List to track all trades executed by this bot instance
        
        self.logger.info(f"Trading bot initialized for {self.trading_pair} with ID: {self.bot_id}")
        
    def _init_strategy(self, strategy_name: str):
        """
        Initialize the trading strategy based on the specified name.
        
        This is an internal method that creates the appropriate strategy object
        and configures it with parameters from environment variables.
        
        Currently supported strategies:
        - simple_ma: Moving Average Crossover strategy
        
        Args:
            strategy_name: Name of the strategy to initialize
                          (must match one of the supported strategies)
        
        Raises:
            ValueError: If the strategy name is unknown
        """
        self.logger.debug(f"Initializing strategy: {strategy_name}")
        
        if strategy_name == 'simple_ma':
            # Get strategy parameters from environment variables
            # SHORT_WINDOW: Period for the short-term moving average (in candles)
            # LONG_WINDOW: Period for the long-term moving average (in candles)
            short_window = int(os.getenv('SHORT_WINDOW', '20'))
            long_window = int(os.getenv('LONG_WINDOW', '50'))
            
            # Create the strategy instance with the specified parameters
            self.strategy = MovingAverageCrossover({
                'short_window': short_window,
                'long_window': long_window
            })
            
            self.logger.info(f"Initialized Moving Average Crossover strategy with "
                           f"short_window={short_window}, long_window={long_window}")
        else:
            # If the strategy name is unknown, log an error and raise an exception
            self.logger.error(f"Unknown strategy: {strategy_name}")
            raise ValueError(f"Unknown strategy: {strategy_name}")
            
    def fetch_market_data(self, interval: int = 60, since: int = None) -> pd.DataFrame:
        """
        Fetch OHLC (Open-High-Low-Close) market data from the exchange.
        
        This method:
        1. Requests candle data from the exchange API
        2. Processes the response into a pandas DataFrame
        3. Caches the data for future use
        4. Saves the data to a CSV file for record-keeping
        
        Args:
            interval: Candle interval in minutes (e.g., 1, 5, 15, 60, 240, 1440)
            since: Timestamp to fetch data from (optional)
            
        Returns:
            DataFrame with OHLC market data, containing columns:
            - open: Opening price for each candle
            - high: Highest price during the candle period
            - low: Lowest price during the candle period
            - close: Closing price for each candle
            - volume: Trading volume during the candle period
        """
        # Track execution time for performance monitoring
        start_time = time.time()
        self.logger.info(f"Fetching {interval}m candles for {self.trading_pair}")
        
        try:
            # Call the API client to get the market data
            data = self.client.get_ohlc_data(self.trading_pair, interval=interval, since=since)
            
            # Check if we got any data back
            if data.empty:
                self.logger.warning(f"No data received from API for {self.trading_pair}")
                return pd.DataFrame()
                
            # Log performance metrics
            elapsed = time.time() - start_time
            self.logger.info(f"Received {len(data)} candles in {elapsed:.2f} seconds")
            
            # Save data to a CSV file for later analysis
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"data/market_{timestamp}.csv"
            save_data(data, filename)
            self.logger.debug(f"Market data saved to {filename}")
            
            # Cache the data for future use
            self.data_cache = data
            return data
            
        except Exception as e:
            # Log any errors that occur during data fetching
            self.logger.error(f"Error fetching market data: {e}")
            log_exception(self.logger, e, "Market data fetch failed")
            return pd.DataFrame()  # Return empty DataFrame on error
            
    def analyze_market(self, data: Optional[pd.DataFrame] = None) -> str:
        """
        Analyze market data and generate trading signal using the configured strategy.
        
        This method:
        1. Ensures we have data to analyze (using provided, cached, or fetched data)
        2. Applies the strategy to calculate indicators and generate a signal
        3. Logs the analysis results and indicators
        
        Args:
            data: Market data DataFrame (if None, uses cached data or fetches new data)
            
        Returns:
            Trading signal ('buy', 'sell', or 'hold') indicating the recommended action
        """
        self.logger.debug("Starting market analysis")
        
        # Use provided data, cached data, or fetch new data if needed
        if data is None:
            if self.data_cache is None:
                self.logger.debug("No data provided or cached, fetching new data")
                data = self.fetch_market_data()
            else:
                self.logger.debug("Using cached market data")
                data = self.data_cache
                
        if data.empty:
            self.logger.warning("Empty dataset for analysis, returning HOLD signal")
            return 'hold'  # Cannot make a decision without data
            
        # Generate trading signal using the configured strategy
        try:
            # Calculate indicators for logging and analysis
            indicators_data = self.strategy.calculate_indicators(data)
            last_row = indicators_data.iloc[-1]  # Get the most recent indicators
            
            # Extract key indicators based on strategy type for logging
            if hasattr(self.strategy, '__class__') and self.strategy.__class__.__name__ == 'MovingAverageCrossover':
                # For Moving Average strategy, log the relevant moving averages
                indicators = {
                    'short_ma': last_row.get('short_ma', None),
                    'long_ma': last_row.get('long_ma', None),
                    'close': last_row.get('close', None)
                }
            else:
                # For other strategies, log any calculated indicators
                indicators = {k: v for k, v in last_row.items() if k not in ['signal', 'open', 'high', 'low', 'volume']}
            
            # Get the final signal from the strategy
            signal = self.strategy.generate_signal(data)
            
            # Log the strategy signal with indicator values for transparency
            strategy_name = self.strategy.__class__.__name__
            log_strategy_signal(self.logger, strategy_name, signal, indicators)
            
            return signal
            
        except Exception as e:
            # Log any errors during analysis and default to 'hold' for safety
            self.logger.error(f"Error during market analysis: {e}")
            log_exception(self.logger, e, "Market analysis failed")
            return 'hold'  # Default to hold on error (do nothing)
            
    def execute_trade(self, signal: str) -> Dict:
        """
        Execute a trade based on the signal generated by the strategy.
        
        This method:
        1. Validates the signal and compares it with the last action
        2. Gets the current market price for logging
        3. Creates appropriate buy/sell order through the exchange API
        4. Logs the trade execution details
        5. Updates the bot's state and trade history
        
        Args:
            signal: Trading signal ('buy', 'sell', or 'hold') indicating action to take
            
        Returns:
            Dictionary with trade execution result:
            - status: 'success', 'error', or 'no_trade'
            - action: The executed action (if applicable)
            - result: Raw response from the exchange API (if applicable)
            - reason: Explanation if no trade was executed or if an error occurred
        """
        # Skip trading if signal is hold or same as last action
        # This prevents duplicate trades or unnecessary actions
        if signal == 'hold' or signal == self.last_action:
            self.logger.info(f"No trade executed - Signal: {signal}, Last action: {self.last_action}")
            return {'status': 'no_trade', 'reason': f"Signal: {signal}, Last action: {self.last_action}"}
            
        # Get current price for logging and reference
        try:
            ticker = self.client.get_ticker(self.trading_pair)
            current_price = float(ticker.get('c', [0])[0]) if ticker and 'c' in ticker else None
        except Exception:
            current_price = None  # Continue even if we can't get the current price
            
        # Generate a unique trade ID for tracking this specific trade
        trade_id = f"trade_{time.strftime('%Y%m%d%H%M%S')}_{self.bot_id}"
        
        if signal == 'buy':
            # Log the trade initiation before executing
            log_trade_execution(
                self.logger, 
                "buy", 
                self.trading_pair, 
                self.trade_volume, 
                price=current_price, 
                order_id=trade_id, 
                status="initiated"
            )
            
            try:
                # Execute the buy order through the exchange API
                result = self.client.create_order(
                    pair=self.trading_pair,
                    order_type='market',  # Market order executes at current best price
                    side='buy',
                    volume=self.trade_volume
                )
                
                # Check for errors in the API response
                if 'error' in result and result['error']:
                    log_trade_execution(
                        self.logger, 
                        "buy", 
                        self.trading_pair, 
                        self.trade_volume, 
                        price=current_price, 
                        order_id=trade_id, 
                        status="failed"
                    )
                    return {'status': 'error', 'reason': result['error']}
                    
                # Log the successful trade execution
                order_id = result.get('txid', [trade_id])[0] if result and 'txid' in result else trade_id
                log_trade_execution(
                    self.logger, 
                    "buy", 
                    self.trading_pair, 
                    self.trade_volume, 
                    price=current_price, 
                    order_id=order_id, 
                    status="completed"
                )
                
                # Store trade details in history for later analysis
                self.trades_history.append({
                    'time': time.time(),
                    'type': 'buy',
                    'pair': self.trading_pair,
                    'volume': self.trade_volume,
                    'price': current_price,
                    'order_id': order_id
                })
                
            except Exception as e:
                # Handle and log any exceptions that occur during trade execution
                log_exception(self.logger, e, f"Buy order execution failed")
                log_trade_execution(
                    self.logger, 
                    "buy", 
                    self.trading_pair, 
                    self.trade_volume, 
                    price=current_price, 
                    status="failed"
                )
                return {'status': 'error', 'reason': str(e)}
                
        elif signal == 'sell':
            # Log the trade initiation before executing
            log_trade_execution(
                self.logger, 
                "sell", 
                self.trading_pair, 
                self.trade_volume, 
                price=current_price, 
                order_id=trade_id, 
                status="initiated"
            )
            
            try:
                # Execute the sell order through the exchange API
                result = self.client.create_order(
                    pair=self.trading_pair,
                    order_type='market',  # Market order executes at current best price
                    side='sell',
                    volume=self.trade_volume
                )
                
                # Check for errors in the API response
                if 'error' in result and result['error']:
                    log_trade_execution(
                        self.logger, 
                        "sell", 
                        self.trading_pair, 
                        self.trade_volume, 
                        price=current_price, 
                        order_id=trade_id, 
                        status="failed"
                    )
                    return {'status': 'error', 'reason': result['error']}
                
                # Log the successful trade execution
                order_id = result.get('txid', [trade_id])[0] if result and 'txid' in result else trade_id
                log_trade_execution(
                    self.logger, 
                    "sell", 
                    self.trading_pair, 
                    self.trade_volume, 
                    price=current_price, 
                    order_id=order_id, 
                    status="completed"
                )
                
                # Store trade details in history for later analysis
                self.trades_history.append({
                    'time': time.time(),
                    'type': 'sell',
                    'pair': self.trading_pair,
                    'volume': self.trade_volume,
                    'price': current_price,
                    'order_id': order_id
                })
                
            except Exception as e:
                # Handle and log any exceptions that occur during trade execution
                log_exception(self.logger, e, f"Sell order execution failed")
                log_trade_execution(
                    self.logger, 
                    "sell", 
                    self.trading_pair, 
                    self.trade_volume, 
                    price=current_price, 
                    status="failed"
                )
                return {'status': 'error', 'reason': str(e)}
                
        else:
            # Handle unknown signals
            self.logger.warning(f"Unknown signal: {signal}")
            return {'status': 'error', 'reason': f"Unknown signal: {signal}"}
            
        # Update last action to prevent duplicate trades
        self.last_action = signal
        self.logger.info(f"Trade executed successfully: {signal}")
        return {'status': 'success', 'action': signal, 'result': result}
    
    def backtest(self, start_date: str = None, end_date: str = None,
                interval: int = 60, plot: bool = True) -> Dict:
        """
        Run a backtest of the strategy against historical market data.
        
        This method:
        1. Fetches or filters historical market data for the specified period
        2. Applies the strategy to generate signals for each data point
        3. Simulates trades based on these signals
        4. Calculates performance metrics (returns, win rate, etc.)
        5. Optionally generates a visualization plot of the results
        
        Args:
            start_date: Start date for backtest (format: 'YYYY-MM-DD')
            end_date: End date for backtest (format: 'YYYY-MM-DD')
            interval: Candle interval in minutes to use for analysis
            plot: Whether to generate a visualization plot of the results
            
        Returns:
            Dictionary with backtest results:
            - status: 'success' or 'error'
            - metrics: Performance metrics if successful
            - data: Strategy indicators and signals if successful
            - reason: Error explanation if failed
        """
        self.logger.info(f"Starting backtest from {start_date or 'earliest'} to {end_date or 'latest'} with {interval}m interval")
        
        # Fetch or use cached historical market data
        try:
            data = self.fetch_market_data(interval=interval)
            
            if data.empty:
                self.logger.error("No data available for backtest")
                return {'status': 'error', 'reason': 'No data available'}
                
            # Filter data to the specified date range if provided
            if start_date:
                self.logger.debug(f"Filtering data from {start_date}")
                data = data.loc[data.index >= start_date]
            if end_date:
                self.logger.debug(f"Filtering data to {end_date}")
                data = data.loc[data.index <= end_date]
            
            self.logger.info(f"Backtest running on {len(data)} data points")
            
            # Apply strategy to calculate indicators and generate signals
            self.logger.debug("Calculating strategy indicators")
            strategy_data = self.strategy.calculate_indicators(data)
            
            # Extract signals and prices from the strategy data
            signals = strategy_data['signal']
            prices = strategy_data['close']
            
            # Initialize variables for the simulation
            # returns: Series to track trade returns
            # position: Current position (0=no position, 1=has position)
            returns = pd.Series(index=signals.index)
            position = 0
            
            # Log beginning of the backtest simulation
            self.logger.debug("Starting backtest simulation")
            
            # Simulate trades based on strategy signals
            trades = []
            for i in range(1, len(signals)):
                if signals.iloc[i-1] == 'buy' and position == 0:
                    # Buy signal when we have no position
                    entry_price = prices.iloc[i-1]
                    position = 1  # Now we have a position
                    trade_time = signals.index[i-1]
                    
                    self.logger.debug(f"BUY signal at {trade_time}, price: {entry_price}")
                    trades.append({
                        'time': trade_time,
                        'action': 'BUY',
                        'price': entry_price
                    })
                    
                elif signals.iloc[i-1] == 'sell' and position == 1:
                    # Sell signal when we have a position
                    exit_price = prices.iloc[i-1]
                    returns.iloc[i] = (exit_price / entry_price) - 1  # Calculate return
                    position = 0  # Now we don't have a position
                    trade_time = signals.index[i-1]
                    
                    profit = (exit_price / entry_price) - 1
                    self.logger.debug(f"SELL signal at {trade_time}, price: {exit_price}, profit: {profit:.2%}")
                    trades.append({
                        'time': trade_time,
                        'action': 'SELL',
                        'price': exit_price,
                        'profit': profit
                    })
            
            # Calculate performance metrics
            total_trades = len(returns[returns != 0])
            winning_trades = len(returns[returns > 0])
            losing_trades = len(returns[returns < 0])
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            avg_win = returns[returns > 0].mean() if winning_trades > 0 else 0
            avg_loss = returns[returns < 0].mean() if losing_trades > 0 else 0
            
            cumulative_return = (1 + returns).prod() - 1  # Compound return calculation
            
            # Compile performance metrics into a results dictionary
            results = {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'cumulative_return': cumulative_return
            }
            
            # Log the backtest results
            self.logger.info(f"Backtest completed - Total return: {cumulative_return:.2%}")
            self.logger.info(f"Win rate: {win_rate:.2%} ({winning_trades}/{total_trades})")
            self.logger.info(f"Avg win: {avg_win:.2%}, Avg loss: {avg_loss:.2%}")
            
            # Generate and save a visualization plot if requested
            if plot:
                self.logger.debug("Generating backtest plot")
                plot_path = f"data/backtest_{time.strftime('%Y%m%d_%H%M%S')}.png"
                plot_strategy(strategy_data, save_path=plot_path)
                self.logger.info(f"Backtest plot saved to {plot_path}")
                
            return {'status': 'success', 'metrics': results, 'data': strategy_data}
            
        except Exception as e:
            # Handle and log any exceptions during backtest
            self.logger.error(f"Backtest failed: {e}")
            log_exception(self.logger, e, "Backtest execution failed")
            return {'status': 'error', 'reason': str(e)}
    
    def start(self, interval_minutes: int = 60, mode: str = 'live'):
        """
        Start the trading bot in either live or paper trading mode.
        
        This method:
        1. Sets up a recurring trading cycle at specified intervals
        2. Continuously monitors the market, analyzes data, and executes trades
        3. Runs until stopped by the user or an error occurs
        
        The trading cycle:
        1. Fetch latest market data
        2. Analyze the data and generate a signal
        3. Execute a trade if appropriate (in live mode) or simulate it (in paper mode)
        4. Wait for the next cycle
        
        Args:
            interval_minutes: Time between trading cycles in minutes
            mode: Operation mode ('live' or 'paper')
        """
        # Check if bot is already running
        if self.is_running:
            self.logger.warning("Trading bot is already running")
            return
            
        # Set bot as running and log the start
        self.is_running = True
        self.logger.info(f"Starting trading bot in {mode} mode, interval: {interval_minutes}m")
        
        # Define the trading cycle function that will run at each interval
        def trading_cycle():
            """Inner function that executes one complete trading cycle"""
            # Generate a unique ID for this cycle for tracking
            cycle_id = time.strftime("%Y%m%d%H%M%S")
            self.logger.info(f"Starting trading cycle {cycle_id}")
            
            try:
                # Fetch latest market data for analysis
                self.logger.debug("Fetching market data for analysis")
                data = self.fetch_market_data(interval=interval_minutes)
                
                if data.empty:
                    self.logger.warning("No data available, skipping cycle")
                    return
                    
                # Analyze market data and get trading signal
                self.logger.debug("Analyzing market data")
                signal = self.analyze_market(data)
                
                # Execute or simulate trade based on mode
                if mode == 'live':
                    # In live mode, execute real trades
                    self.logger.debug(f"Executing trade based on signal: {signal}")
                    result = self.execute_trade(signal)
                    self.logger.info(f"Trade execution result: {result}")
                else:
                    # In paper mode, just log the signal (no real trades)
                    self.logger.info(f"Paper trading - Signal: {signal} (no actual trade executed)")
                    
                # Save market data for later analysis
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                save_data(data, f"data/market_{timestamp}.csv")
                self.logger.debug(f"Market data saved to data/market_{timestamp}.csv")
                
                # Get current account status in live mode
                if mode == 'live':
                    try:
                        balance = self.get_account_balance()
                        self.logger.info(f"Current account balance: {balance}")
                    except Exception as e:
                        self.logger.warning(f"Could not retrieve account balance: {e}")
                
            except Exception as e:
                # Handle and log any exceptions during the trading cycle
                self.logger.error(f"Error in trading cycle {cycle_id}: {e}")
                log_exception(self.logger, e, f"Trading cycle {cycle_id} failed")
                
            self.logger.info(f"Completed trading cycle {cycle_id}")
        
        # Run initial cycle immediately
        trading_cycle()
        
        # Schedule regular cycles at the specified interval
        self.logger.info(f"Scheduling regular trading cycles every {interval_minutes} minutes")
        schedule.every(interval_minutes).minutes.do(trading_cycle)
        
        try:
            # Main loop - keep running until stopped
            self.logger.info("Trading bot running - press Ctrl+C to stop")
            while self.is_running:
                schedule.run_pending()  # Run any scheduled tasks that are due
                time.sleep(1)  # Sleep to prevent high CPU usage
        except KeyboardInterrupt:
            # Handle user interruption gracefully
            self.logger.info("KeyboardInterrupt detected")
            self.stop()
    
    def stop(self):
        """
        Stop the trading bot and clean up.
        
        This method:
        1. Sets the bot's running state to False
        2. Logs a summary of trades executed during the session
        3. Performs any necessary cleanup operations
        """
        # Set bot as not running
        self.is_running = False
        self.logger.info("Trading bot stopped")
        
        # Log a summary of the trading session
        if hasattr(self, 'trades_history') and self.trades_history:
            num_trades = len(self.trades_history)
            buys = sum(1 for t in self.trades_history if t['type'] == 'buy')
            sells = sum(1 for t in self.trades_history if t['type'] == 'sell')
            self.logger.info(f"Trading session summary: {num_trades} trades ({buys} buys, {sells} sells)")
        
    def get_account_balance(self) -> Dict:
        """
        Get the current account balance from the exchange.
        
        This method queries the exchange API to get the current balance
        of all assets in the account.
        
        Returns:
            Dictionary mapping asset names to their current balances
            
        Raises:
            Logs exceptions but doesn't raise them to prevent critical failures
            Returns an error dict if balance retrieval fails
        """
        self.logger.debug("Fetching account balance")
        try:
            # Query the exchange API for account balance
            balance = self.client.get_account_balance()
            return balance
        except Exception as e:
            # Handle and log any exceptions during balance retrieval
            self.logger.error(f"Failed to get account balance: {e}")
            log_exception(self.logger, e, "Account balance retrieval failed")
            return {"error": str(e)}
