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
    Wrapper for Kraken API to handle trading operations.
    
    This class provides a simplified interface to the Kraken cryptocurrency exchange API.
    It handles authentication, request formatting, error handling, and data conversion
    to make the Kraken API easier to use within the trading bot.
    
    The client supports both:
    1. Public endpoints - market data, ticker information, OHLC data
    2. Private endpoints - account balance, order creation, trade history
    
    This wrapper uses two libraries:
    - krakenex: Low-level connection to Kraken API endpoints
    - pykrakenapi: Higher-level wrapper with additional functionality
    
    Security note: API keys are loaded from environment variables and
    never hardcoded or exposed in the source code.
    """
    def __init__(self, config_path: str = None):
        """
        Initialize the Kraken API client with authentication credentials.
        
        Sets up the connection to Kraken API using credentials from environment variables.
        The client will work in read-only mode without API keys, but trading operations
        require valid authentication.
        
        Args:
            config_path: Path to .env configuration file containing API credentials
                         If not provided, looks for .env in the current directory
        
        Environment Variables Used:
            KRAKEN_API_KEY: Your Kraken API key
            KRAKEN_API_SECRET: Your Kraken API secret key
        """
        # Load environment variables from specified file or default location
        if config_path:
            load_dotenv(config_path)
        else:
            load_dotenv()
            
        # Get API credentials from environment variables
        self.api_key = os.getenv('KRAKEN_API_KEY')
        self.api_secret = os.getenv('KRAKEN_API_SECRET')
        
        # Check if credentials are available and warn if missing
        if not self.api_key or not self.api_secret:
            logger.warning("API credentials not found. Only public endpoints will be available.")
            
        # Initialize the actual API client
        self._init_client()
    
    def _init_client(self):
        """
        Initialize the underlying Kraken API client objects.
        
        This internal method creates the actual API connection objects using
        the krakenex and pykrakenapi libraries. It's separated from __init__
        to allow re-initialization if needed (e.g., after connection issues).
        
        krakenex handles the raw HTTP requests with authentication.
        pykrakenapi adds convenience methods and data conversion.
        """
        # Create the base krakenex API object with our credentials
        self.kraken = krakenex.API(key=self.api_key, secret=self.api_secret)
        
        # Create the higher-level pykrakenapi object which wraps krakenex
        # This provides more user-friendly methods and returns pandas DataFrames
        self.api = KrakenAPI(self.kraken)
    
    def get_account_balance(self) -> Dict:
        """
        Get the current account balance for all assets.
        
        This method fetches the current balance of all assets in the account.
        Requires valid API credentials with balance permission.
        
        Returns:
            Dictionary mapping asset names to their balances
            Empty dictionary if the request fails
            
        Example response:
            {'ZUSD': '1342.76', 'XXBT': '0.142', 'XETH': '2.0'}
        """
        try:
            # Call the Kraken API to get account balance
            balance = self.api.get_account_balance()
            return balance
        except Exception as e:
            # Log any errors but don't crash the application
            logger.error(f"Error getting account balance: {e}")
            return {}
    
    def get_ticker(self, pair: str) -> Dict:
        """
        Get current ticker information for a trading pair.
        
        This method fetches the latest price and trading information
        for the specified trading pair.
        
        Args:
            pair: Trading pair symbol (e.g., 'XXBTZUSD' for BTC/USD)
            
        Returns:
            Dictionary with ticker information including:
            - Current ask and bid prices
            - Today's open price
            - 24h volume
            - Today's high and low prices
            
        Example response:
            {
                'a': ['39485.90000', '1', '1.000'],  # Ask price, whole lot volume, lot volume
                'b': ['39485.80000', '1', '1.000'],  # Bid price, whole lot volume, lot volume
                'c': ['39485.90000', '0.00080000'],  # Last trade closed, volume
                'v': ['1494.94379499', '5422.13122911'],  # Volume today, 24h
                'p': ['39399.97149', '39252.73289'],  # VWAP today, 24h
                'h': ['39699.90000', '39798.60000'],  # High today, 24h
                'l': ['39153.60000', '38500.00000'],  # Low today, 24h
                'o': '39212.40000'  # Today's opening price
            }
        """
        try:
            # Call the Kraken API to get ticker information
            ticker = self.api.get_ticker_information(pair)
            return ticker
        except Exception as e:
            # Log any errors but don't crash the application
            logger.error(f"Error getting ticker info for {pair}: {e}")
            return {}
    
    def get_ohlc_data(self, pair: str, interval: int = 1, since: int = None) -> pd.DataFrame:
        """
        Get OHLC (Open-High-Low-Close) candlestick data for a trading pair.
        
        This method retrieves historical price data formatted as candlesticks,
        which is essential for technical analysis and backtesting.
        
        Args:
            pair: Trading pair symbol (e.g., 'XXBTZUSD' for BTC/USD)
            interval: Candle interval in minutes (default: 1)
                      Valid intervals: 1, 5, 15, 30, 60, 240, 1440, 10080, 21600
            since: Return data since given UNIX timestamp (optional)
                   If not provided, returns most recent data
            
        Returns:
            DataFrame with OHLC data containing columns:
            - open: Opening price for the interval
            - high: Highest price during the interval
            - low: Lowest price during the interval
            - close: Closing price for the interval
            - volume: Trading volume during the interval
            - time: Timestamp for the start of the interval
            
        Notes:
            The Kraken API limits the number of candles returned in a single request,
            typically around 720 candles. For more data, make multiple calls with
            the 'since' parameter.
        """
        try:
            # Call the Kraken API to get OHLC data
            # Returns both the data and the last timestamp
            ohlc, last = self.api.get_ohlc_data(pair, interval=interval, since=since)
            return ohlc
        except Exception as e:
            # Log any errors but don't crash the application
            logger.error(f"Error getting OHLC data for {pair}: {e}")
            return pd.DataFrame()  # Return empty DataFrame on error
    
    def create_order(self, pair: str, order_type: str, side: str, volume: float, price: float = None) -> Dict:
        """
        Create a new order on the Kraken exchange.
        
        This method submits a new order to buy or sell cryptocurrency.
        It supports both market orders (execute immediately at current price)
        and limit orders (execute only at specified price or better).
        
        Args:
            pair: Trading pair symbol (e.g., 'XXBTZUSD' for BTC/USD)
            order_type: Type of order - 'market' or 'limit'
                - market: Execute immediately at current market price
                - limit: Execute only at specified price or better
            side: Order direction - 'buy' or 'sell'
            volume: Order quantity in base currency units
                    Example: 0.1 for 0.1 BTC in BTCUSD pair
            price: Price per unit for limit orders
                   Not used for market orders
            
        Returns:
            Dictionary with order result information including:
            - txid: List of transaction IDs for the order
            - descr: Order description details
            
        Raises:
            ValueError: If order parameters are invalid
            
        Example Response:
            {
                'txid': ['OAVY7T-MV5VK-KHDF5X'],
                'descr': {
                    'order': 'buy 0.1000 XXBTZUSD @ market'
                }
            }
            
        Notes:
            Market orders are subject to slippage in volatile markets.
            Using limit orders provides price protection but may not execute immediately.
        """
        try:
            # Validate order parameters before sending to the exchange
            if order_type not in ['market', 'limit']:
                raise ValueError(f"Invalid order type: {order_type}")
            
            if side not in ['buy', 'sell']:
                raise ValueError(f"Invalid order side: {side}")
            
            # Create the appropriate order based on type
            if order_type == 'market':
                # Market order - execute immediately at current price
                result = self.api.add_standard_order(
                    pair=pair,
                    type=side,
                    ordertype=order_type,
                    volume=str(volume)  # API expects string values
                )
            else:  # limit order
                # Limit order - requires a price
                if not price:
                    raise ValueError("Price is required for limit orders")
                
                result = self.api.add_standard_order(
                    pair=pair,
                    type=side,
                    ordertype=order_type,
                    volume=str(volume),
                    price=str(price)  # API expects string values
                )
            
            return result
        except Exception as e:
            # Log the error and return it as part of the result
            logger.error(f"Error creating {side} {order_type} order for {pair}: {e}")
            return {"error": str(e)}
    
    def get_closed_orders(self) -> Dict:
        """
        Get all closed orders from the account history.
        
        This method retrieves information about orders that have been filled,
        canceled, or expired. Useful for tracking trading history and performance.
        
        Returns:
            Dictionary containing closed orders information with:
            - closed: Dict of order IDs to order details
            - count: Total number of closed orders
            
        Example Response:
            {
                'closed': {
                    'OAVY7T-MV5VK-KHDF5X': {
                        'status': 'closed',
                        'cost': '3945.90000',
                        'fee': '7.89',
                        'vol_exec': '0.1000',
                        'price': '39459.0',
                        ...
                    },
                    ...
                },
                'count': 24
            }
        """
        try:
            # Call the Kraken API to get closed orders
            closed_orders = self.api.get_closed_orders()
            return closed_orders
        except Exception as e:
            # Log any errors but don't crash the application
            logger.error(f"Error getting closed orders: {e}")
            return {}
            
    def get_order_info(self, txid: str) -> Dict:
        """
        Get detailed information about a specific order.
        
        This method retrieves the current status and details of an order
        using its transaction ID.
        
        Args:
            txid: Transaction ID of the order to query
            
        Returns:
            Dictionary containing order details including:
            - status: Order status (open, closed, canceled, etc.)
            - price: Order price
            - volume: Order volume
            - cost: Total cost of the order
            
        Example Response:
            {
                'OAVY7T-MV5VK-KHDF5X': {
                    'status': 'closed',
                    'opentm': 1617483982.5542,
                    'closetm': 1617483982.5853,
                    'price': '39459.0',
                    'vol': '0.1000',
                    'vol_exec': '0.1000',
                    'cost': '3945.90000',
                    'fee': '7.89',
                    'descr': {'order': 'buy 0.1000 XXBTZUSD @ market'}
                }
            }
        """
        try:
            # Call the Kraken API to get order information
            order_info = self.api.query_orders_info(txid)
            return order_info
        except Exception as e:
            # Log any errors but don't crash the application
            logger.error(f"Error getting info for order {txid}: {e}")
            return {}