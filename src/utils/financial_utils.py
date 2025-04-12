import os
import json
import time
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)

class ProfitLossTracker:
    """
    Tracks trading account profit and loss metrics over time.
    
    This class manages financial metrics including:
    - Current funds/balance
    - Overall profit/loss since tracking began
    - Daily profit/loss
    - Current session profit/loss
    
    The tracker persists data between bot sessions using a JSON file.
    """
    
    def __init__(self, storage_path: str = 'data/financial_history.json'):
        """
        Initialize the profit/loss tracker.
        
        Args:
            storage_path: Path to store the financial history JSON file
        """
        self.storage_path = storage_path
        self.session_start_time = time.time()
        self.session_start_balance = {}
        self.previous_balance = {}
        self.current_balance = {}
        self.daily_snapshots = []
        
        # Ensure storage directory exists
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # Load existing financial history if available
        self.financial_history = self._load_history()
        
        # Set session start balance
        if self.financial_history.get('latest_balance'):
            self.session_start_balance = self.financial_history['latest_balance'].copy()
            self.previous_balance = self.financial_history['latest_balance'].copy()
            self.current_balance = self.financial_history['latest_balance'].copy()
            
        # Initialize today's snapshot if needed
        self._ensure_daily_snapshot()
        
        logger.info(f"ProfitLossTracker initialized, data stored at: {storage_path}")
        
    def _load_history(self) -> Dict[str, Any]:
        """Load financial history from storage file"""
        if not os.path.exists(self.storage_path):
            # Return default structure if no history exists
            return {
                'first_recorded_balance': {},
                'latest_balance': {},
                'daily_snapshots': [],
                'profit_loss_history': []
            }
            
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                
            # If daily_snapshots exist, convert string dates back to datetime objects
            if 'daily_snapshots' in data and isinstance(data['daily_snapshots'], list):
                self.daily_snapshots = data['daily_snapshots']
                
            return data
            
        except Exception as e:
            logger.error(f"Error loading financial history: {e}")
            # Return default structure if loading fails
            return {
                'first_recorded_balance': {},
                'latest_balance': {},
                'daily_snapshots': [],
                'profit_loss_history': []
            }
            
    def _save_history(self):
        """Save current financial history to storage file"""
        try:
            # Copy the history to avoid modifying the original
            data_to_save = self.financial_history.copy()
            
            # Add daily snapshots
            data_to_save['daily_snapshots'] = self.daily_snapshots
            
            with open(self.storage_path, 'w') as f:
                json.dump(data_to_save, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving financial history: {e}")
            
    def _ensure_daily_snapshot(self):
        """Ensure we have a snapshot for today"""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Check if we already have today's snapshot
        if not any(s.get('date') == today for s in self.daily_snapshots):
            # Create new snapshot for today using the latest balance
            if self.financial_history.get('latest_balance'):
                self.daily_snapshots.append({
                    'date': today,
                    'starting_balance': self.financial_history['latest_balance'].copy(),
                    'ending_balance': self.financial_history['latest_balance'].copy()
                })
                logger.debug(f"Created new daily snapshot for {today}")
                
    def update_balance(self, new_balance: Dict[str, float]):
        """
        Update the current balance and calculate profit/loss metrics.
        
        Args:
            new_balance: Dictionary mapping asset names to amounts
        """
        # Store previous balance before updating
        self.previous_balance = self.current_balance.copy()
        self.current_balance = new_balance.copy()
        
        # Initialize first recorded balance if not set
        if not self.financial_history.get('first_recorded_balance'):
            self.financial_history['first_recorded_balance'] = new_balance.copy()
            self.session_start_balance = new_balance.copy()
            logger.info(f"Set initial balance: {new_balance}")
            
        # Update latest balance in history
        self.financial_history['latest_balance'] = new_balance.copy()
        
        # Update today's snapshot
        self._ensure_daily_snapshot()
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        for snapshot in self.daily_snapshots:
            if snapshot['date'] == today:
                snapshot['ending_balance'] = new_balance.copy()
                break
                
        # Record this balance update in history
        self.financial_history['profit_loss_history'].append({
            'timestamp': time.time(),
            'balance': new_balance.copy()
        })
        
        # Save the updated history
        self._save_history()
        
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculate current profit/loss metrics.
        
        Returns:
            Dictionary containing:
            - current_funds: Current balance
            - overall_pl: Overall profit/loss since tracking began
            - daily_pl: Profit/loss for the current day
            - session_pl: Profit/loss for the current session
        """
        metrics = {
            'current_funds': self.current_balance,
            'overall_pl': self._calculate_pl(
                self.financial_history.get('first_recorded_balance', {}),
                self.current_balance
            ),
            'daily_pl': {},
            'session_pl': self._calculate_pl(
                self.session_start_balance,
                self.current_balance
            )
        }
        
        # Calculate daily P/L if we have today's snapshot
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        for snapshot in self.daily_snapshots:
            if snapshot['date'] == today:
                metrics['daily_pl'] = self._calculate_pl(
                    snapshot['starting_balance'],
                    snapshot['ending_balance']
                )
                break
                
        return metrics
        
    def _calculate_pl(self, start_balance: Dict[str, float], 
                      end_balance: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate profit/loss between two balance states.
        
        Args:
            start_balance: Starting balance dictionary
            end_balance: Ending balance dictionary
            
        Returns:
            Dictionary with absolute and percentage changes
        """
        result = {'absolute': {}, 'percentage': {}}
        
        # Handle empty balances
        if not start_balance or not end_balance:
            return result
            
        # Calculate for each asset
        all_assets = set(list(start_balance.keys()) + list(end_balance.keys()))
        
        for asset in all_assets:
            start_amount = start_balance.get(asset, 0)
            end_amount = end_balance.get(asset, 0)
            
            # Calculate absolute change
            absolute_change = end_amount - start_amount
            result['absolute'][asset] = absolute_change
            
            # Calculate percentage change (avoid division by zero)
            if start_amount != 0:
                pct_change = (absolute_change / start_amount) * 100
                result['percentage'][asset] = pct_change
            else:
                result['percentage'][asset] = float('inf') if end_amount > 0 else 0
                
        return result
        
    def log_metrics(self, logger_instance):
        """
        Log current financial metrics.
        
        Args:
            logger_instance: Logger to use for output
        """
        metrics = self.calculate_metrics()
        
        # Format the logs for better readability
        logger_instance.info("===== FINANCIAL METRICS =====")
        
        # Log current funds
        for asset, amount in metrics['current_funds'].items():
            logger_instance.info(f"Current Balance: {amount:.8f} {asset}")
            
        # Log overall P/L
        logger_instance.info("===== OVERALL PROFIT/LOSS =====")
        for asset, abs_change in metrics['overall_pl']['absolute'].items():
            pct = metrics['overall_pl']['percentage'].get(asset, 0)
            if abs_change != 0:
                direction = "PROFIT" if abs_change > 0 else "LOSS"
                logger_instance.info(f"Overall {direction}: {abs(abs_change):.8f} {asset} ({abs(pct):.2f}%)")
                
        # Log daily P/L
        logger_instance.info("===== DAILY PROFIT/LOSS =====")
        for asset, abs_change in metrics['daily_pl'].get('absolute', {}).items():
            pct = metrics['daily_pl'].get('percentage', {}).get(asset, 0)
            if abs_change != 0:
                direction = "PROFIT" if abs_change > 0 else "LOSS"
                logger_instance.info(f"Today's {direction}: {abs(abs_change):.8f} {asset} ({abs(pct):.2f}%)")
                
        # Log session P/L
        logger_instance.info("===== SESSION PROFIT/LOSS =====")
        for asset, abs_change in metrics['session_pl']['absolute'].items():
            pct = metrics['session_pl']['percentage'].get(asset, 0)
            if abs_change != 0:
                direction = "PROFIT" if abs_change > 0 else "LOSS"
                logger_instance.info(f"Session {direction}: {abs(abs_change):.8f} {asset} ({abs(pct):.2f}%)")
                
        logger_instance.info("=============================")


def format_currency(value: float, currency: str = "") -> str:
    """
    Format a currency value for display.
    
    Args:
        value: Numeric value to format
        currency: Currency symbol or code
        
    Returns:
        Formatted string
    """
    # For crypto assets, use 8 decimal places
    if currency.upper() in ["BTC", "ETH", "XBT", "XRP", "LTC"]:
        formatted = f"{value:.8f}"
    # For fiat currencies, use 2 decimal places
    else:
        formatted = f"{value:.2f}"
        
    # Add currency symbol/code if provided
    if currency:
        return f"{formatted} {currency}"
    return formatted


def calculate_trade_pnl(entry_price: float, exit_price: float, volume: float, 
                      is_long: bool = True) -> Dict[str, float]:
    """
    Calculate profit/loss for a single trade.
    
    Args:
        entry_price: Price at trade entry
        exit_price: Price at trade exit
        volume: Trade volume/amount
        is_long: Whether it was a long (buy) position
        
    Returns:
        Dictionary with absolute and percentage P/L
    """
    if is_long:
        # For long positions: profit = (exit - entry) * volume
        absolute_pnl = (exit_price - entry_price) * volume
        pct_change = ((exit_price / entry_price) - 1) * 100
    else:
        # For short positions: profit = (entry - exit) * volume
        absolute_pnl = (entry_price - exit_price) * volume
        pct_change = ((entry_price / exit_price) - 1) * 100
        
    return {
        'absolute': absolute_pnl,
        'percentage': pct_change
    }