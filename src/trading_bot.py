import os
import time
import schedule
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Optional, Any, Union
import pandas as pd

from .api.kraken_client import KrakenClient
from .strategies.moving_average import MovingAverageCrossover
from .utils.logger import setup_logger
from .utils.data_utils import save_data, load_data, plot_strategy

class TradingBot:
    """
    Trading bot that integrates exchange API with trading strategies
    to execute trades based on market conditions.
    """
    def __init__(self, config_path: str = None):
        """
        Initialize the trading bot
        
        Args:
            config_path: Path to .env configuration file (optional)
        """
        # Setup logging
        self.logger = setup_logger('trading_bot', log_dir='logs')
        
        # Load configuration
        if config_path:
            load_dotenv(config_path)
        else:
            load_dotenv()
            
        # Initialize API client
        self.client = KrakenClient(config_path)
        
        # Trading parameters
        self.trading_pair = os.getenv('TRADING_PAIR', 'XXBTZUSD')
        self.trade_volume = float(os.getenv('TRADE_VOLUME', '0.001'))
        
        # Initialize strategy
        strategy_name = os.getenv('STRATEGY', 'simple_ma')
        self._init_strategy(strategy_name)
        
        # State variables
        self.is_running = False
        self.last_action = 'none'
        self.data_cache = None
        
        self.logger.info(f"Trading bot initialized for {self.trading_pair}")
        
    def _init_strategy(self, strategy_name: str):
        """
        Initialize the trading strategy
        
        Args:
            strategy_name: Name of the strategy to initialize
        """
        if strategy_name == 'simple_ma':
            # Get parameters from environment variables
            short_window = int(os.getenv('SHORT_WINDOW', '20'))
            long_window = int(os.getenv('LONG_WINDOW', '50'))
            
            self.strategy = MovingAverageCrossover({
                'short_window': short_window,
                'long_window': long_window
            })
            
            self.logger.info(f"Initialized Moving Average Crossover strategy with "
                            f"short_window={short_window}, long_window={long_window}")
        else:
            self.logger.error(f"Unknown strategy: {strategy_name}")
            raise ValueError(f"Unknown strategy: {strategy_name}")
            
    def fetch_market_data(self, interval: int = 60, since: int = None) -> pd.DataFrame:
        """
        Fetch OHLC market data from the exchange
        
        Args:
            interval: Candle interval in minutes
            since: Timestamp to fetch data from (optional)
            
        Returns:
            DataFrame with OHLC market data
        """
        self.logger.info(f"Fetching {interval}m candles for {self.trading_pair}")
        data = self.client.get_ohlc_data(self.trading_pair, interval=interval, since=since)
        
        if data.empty:
            self.logger.warning("No data received from API")
            return pd.DataFrame()
            
        self.logger.info(f"Received {len(data)} candles")
        self.data_cache = data
        return data
        
    def analyze_market(self, data: Optional[pd.DataFrame] = None) -> str:
        """
        Analyze market data and generate trading signal
        
        Args:
            data: Market data (if None, uses cached data or fetches new data)
            
        Returns:
            Trading signal ('buy', 'sell', or 'hold')
        """
        # Use provided data, cached data, or fetch new data
        if data is None:
            if self.data_cache is None:
                data = self.fetch_market_data()
            else:
                data = self.data_cache
                
        if data.empty:
            self.logger.warning("No data available for analysis")
            return 'hold'
            
        # Generate trading signal using strategy
        signal = self.strategy.generate_signal(data)
        self.logger.info(f"Analysis complete - Signal: {signal}")
        return signal
        
    def execute_trade(self, signal: str) -> Dict:
        """
        Execute a trade based on the signal
        
        Args:
            signal: Trading signal ('buy', 'sell', or 'hold')
            
        Returns:
            Trade execution result
        """
        if signal == 'hold' or signal == self.last_action:
            self.logger.info(f"No trade executed - Signal: {signal}, Last action: {self.last_action}")
            return {'status': 'no_trade', 'reason': f"Signal: {signal}, Last action: {self.last_action}"}
            
        if signal == 'buy':
            self.logger.info(f"Executing BUY order for {self.trade_volume} {self.trading_pair}")
            result = self.client.create_order(
                pair=self.trading_pair,
                order_type='market',
                side='buy',
                volume=self.trade_volume
            )
        elif signal == 'sell':
            self.logger.info(f"Executing SELL order for {self.trade_volume} {self.trading_pair}")
            result = self.client.create_order(
                pair=self.trading_pair,
                order_type='market',
                side='sell',
                volume=self.trade_volume
            )
        else:
            self.logger.warning(f"Unknown signal: {signal}")
            return {'status': 'error', 'reason': f"Unknown signal: {signal}"}
            
        if 'error' in result:
            self.logger.error(f"Trade execution failed: {result['error']}")
            return result
            
        self.last_action = signal
        self.logger.info(f"Trade executed successfully: {signal}")
        return {'status': 'success', 'action': signal, 'result': result}
        
    def backtest(self, start_date: str = None, end_date: str = None,
                interval: int = 60, plot: bool = True) -> Dict:
        """
        Run a backtest of the strategy
        
        Args:
            start_date: Start date for backtest (format: 'YYYY-MM-DD')
            end_date: End date for backtest (format: 'YYYY-MM-DD')
            interval: Candle interval in minutes
            plot: Whether to generate a plot
            
        Returns:
            Backtest results
        """
        self.logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # Fetch data or use cached data
        data = self.fetch_market_data(interval=interval)
        
        if data.empty:
            self.logger.error("No data available for backtest")
            return {'status': 'error', 'reason': 'No data available'}
            
        # Filter date range if provided
        if start_date:
            data = data.loc[data.index >= start_date]
        if end_date:
            data = data.loc[data.index <= end_date]
            
        # Apply strategy to get signals
        strategy_data = self.strategy.calculate_indicators(data)
        
        # Calculate performance metrics
        signals = strategy_data['signal']
        prices = strategy_data['close']
        
        # Simple returns calculation (not accounting for fees/slippage)
        returns = pd.Series(index=signals.index)
        position = 0
        
        for i in range(1, len(signals)):
            if signals.iloc[i-1] == 'buy' and position == 0:
                # Buy at previous price
                entry_price = prices.iloc[i-1]
                position = 1
            elif signals.iloc[i-1] == 'sell' and position == 1:
                # Sell at previous price
                exit_price = prices.iloc[i-1]
                returns.iloc[i] = (exit_price / entry_price) - 1
                position = 0
        
        # Calculate metrics
        total_trades = len(returns[returns != 0])
        winning_trades = len(returns[returns > 0])
        losing_trades = len(returns[returns < 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        avg_win = returns[returns > 0].mean() if winning_trades > 0 else 0
        avg_loss = returns[returns < 0].mean() if losing_trades > 0 else 0
        
        cumulative_return = (1 + returns).prod() - 1
        
        # Save results
        results = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'cumulative_return': cumulative_return
        }
        
        self.logger.info(f"Backtest completed - Total return: {cumulative_return:.2%}")
        self.logger.info(f"Win rate: {win_rate:.2%} ({winning_trades}/{total_trades})")
        
        # Plot results if requested
        if plot:
            plot_path = f"data/backtest_{time.strftime('%Y%m%d_%H%M%S')}.png"
            plot_strategy(strategy_data, save_path=plot_path)
            
        return {'status': 'success', 'metrics': results, 'data': strategy_data}
        
    def start(self, interval_minutes: int = 60, mode: str = 'live'):
        """
        Start the trading bot
        
        Args:
            interval_minutes: Time between trading cycles in minutes
            mode: Operation mode ('live' or 'paper')
        """
        if self.is_running:
            self.logger.warning("Trading bot is already running")
            return
            
        self.is_running = True
        self.logger.info(f"Starting trading bot in {mode} mode, interval: {interval_minutes}m")
        
        # Define trading cycle function
        def trading_cycle():
            try:
                self.logger.info("Starting trading cycle")
                
                # Fetch latest market data
                data = self.fetch_market_data(interval=interval_minutes)
                
                if data.empty:
                    self.logger.warning("No data available, skipping cycle")
                    return
                    
                # Analyze market and get signal
                signal = self.analyze_market(data)
                
                # Execute trade in live mode, just log in paper mode
                if mode == 'live':
                    result = self.execute_trade(signal)
                    self.logger.info(f"Trade execution result: {result}")
                else:
                    self.logger.info(f"Paper trading - Signal: {signal}")
                    
                # Save data for analysis
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                save_data(data, f"data/market_{timestamp}.csv")
                
            except Exception as e:
                self.logger.error(f"Error in trading cycle: {e}")
        
        # Run initial cycle
        trading_cycle()
        
        # Schedule regular cycles
        schedule.every(interval_minutes).minutes.do(trading_cycle)
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
            
    def stop(self):
        """Stop the trading bot"""
        self.is_running = False
        self.logger.info("Trading bot stopped")
        
    def get_account_balance(self) -> Dict:
        """
        Get account balance
        
        Returns:
            Account balance information
        """
        return self.client.get_account_balance()
        