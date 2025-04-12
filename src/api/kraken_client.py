import os
import time
from typing import Dict, List, Optional, Tuple, Union
import krakenex
from pykrakenapi import KrakenAPI
import pandas as pd
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class KrakenClient:
    """
    Wrapper for Kraken API to handle trading operations
    """
    def __init__(self, config_path: str = None):
        """
        Initialize the Kraken API client
        
        Args:
            config_path: Path to .env file with API credentials
        """
        # Load environment variables
        if config_path:
            load_dotenv(config_path)
        else:
            load_dotenv()
            
        # Initialize Kraken API
        self.api_key = os.getenv('KRAKEN_API_KEY')
        self.api_secret = os.getenv('KRAKEN_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            logger.warning("API credentials not found. Only public endpoints will be available.")
            
        self._init_client()
    
    def _init_client(self):
        """Initialize the Kraken API client"""
        self.kraken = krakenex.API(key=self.api_key, secret=self.api_secret)
        self.api = KrakenAPI(self.kraken)
    
    def get_account_balance(self) -> Dict:
        """Get account balance"""
        try:
            balance = self.api.get_account_balance()
            return balance
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return {}
    
    def get_ticker_info(self, pair: str) -> Dict:
        """Get ticker information for a pair"""
        try:
            ticker = self.api.get_ticker_information(pair)
            return ticker
        except Exception as e:
            logger.error(f"Error getting ticker info for {pair}: {e}")
            return {}
    
    def get_ohlc_data(self, pair: str, interval: int = 1, since: int = None) -> pd.DataFrame:
        """
        Get OHLC (candle) data for a pair
        
        Args:
            pair: Trading pair (e.g., 'XXBTZUSD')
            interval: Time frame interval in minutes (default: 1)
            since: Return data since given timestamp (optional)
            
        Returns:
            DataFrame with OHLC data
        """
        try:
            ohlc, last = self.api.get_ohlc_data(pair, interval=interval, since=since)
            return ohlc
        except Exception as e:
            logger.error(f"Error getting OHLC data for {pair}: {e}")
            return pd.DataFrame()
    
    def create_order(self, pair: str, order_type: str, side: str, volume: float, price: float = None) -> Dict:
        """
        Create a new order
        
        Args:
            pair: Trading pair (e.g., 'XXBTZUSD')
            order_type: Type of order (market, limit)
            side: buy or sell
            volume: Volume in base currency
            price: Price (for limit orders)
            
        Returns:
            Order result information
        """
        try:
            # Add validation
            if order_type not in ['market', 'limit']:
                raise ValueError(f"Invalid order type: {order_type}")
            
            if side not in ['buy', 'sell']:
                raise ValueError(f"Invalid order side: {side}")
            
            # Create order
            if order_type == 'market':
                result = self.api.add_standard_order(
                    pair=pair,
                    type=side,
                    ordertype=order_type,
                    volume=str(volume)
                )
            else:  # limit order
                if not price:
                    raise ValueError("Price is required for limit orders")
                
                result = self.api.add_standard_order(
                    pair=pair,
                    type=side,
                    ordertype=order_type,
                    volume=str(volume),
                    price=str(price)
                )
            
            return result
        except Exception as e:
            logger.error(f"Error creating {side} {order_type} order for {pair}: {e}")
            return {"error": str(e)}
    
    def get_closed_orders(self) -> Dict:
        """Get closed orders"""
        try:
            closed_orders = self.api.get_closed_orders()
            return closed_orders
        except Exception as e:
            logger.error(f"Error getting closed orders: {e}")
            return {}