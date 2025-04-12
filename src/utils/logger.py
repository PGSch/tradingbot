import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import time
from pathlib import Path
import sys
import socket
import traceback

def setup_logger(name=None, log_level=None, log_dir=None):
    """
    Configure logging with console and file handlers.
    
    This is the main logging setup function that creates a feature-rich logging system.
    It includes both console output and file-based logging with different levels of detail.
    The logger is configurable via environment variables and/or direct parameters.
    
    Logging features:
    - Console output with simplified formatting
    - Daily rotating log files for regular logs
    - Size-based rotating log files for detailed debug logs
    - Hostname tracking for multi-instance deployments
    - Comprehensive formatting with file/line/function information
    
    Args:
        name: Logger name (default: root logger)
              Used to identify the source of logs, especially in multi-module applications
        log_level: Logging level (default: from env or INFO)
                  Controls verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: from env or project logs/)
                Storage location for log files
    
    Returns:
        Configured logger instance ready for use
    
    Environment Variables:
        LOG_LEVEL: Logging level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        LOG_DIR: Directory to store log files
        LOG_TO_FILE: Whether to write logs to files (true/false)
    """
    # Get logger configuration from environment variables with sensible defaults
    # This allows configuration without code changes via env vars
    env_log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    env_log_dir = os.getenv('LOG_DIR', 'logs')
    env_log_to_file = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
    
    # Use provided values or fall back to environment variables
    # Parameters take precedence over environment variables
    log_level = log_level or getattr(logging, env_log_level, logging.INFO)
    log_dir = log_dir or env_log_dir
    
    # Get or create logger - if the logger already exists with the same name,
    # we'll get the existing instance
    logger = logging.getLogger(name)
    
    # Return logger if already configured to avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Configure the logger's base properties
    logger.setLevel(log_level)  # Base level - handlers might filter further
    logger.propagate = False    # Prevent duplicate logs in parent loggers
    
    # Create formatters with different levels of detail
    # Console format is simpler for readability
    # File format includes detailed context for troubleshooting
    hostname = socket.gethostname()  # Include hostname for multi-server setups
    
    # Basic format for console - optimized for readability
    console_format = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s: %(message)s')
    
    # Detailed format for files - includes context for debugging
    file_format = logging.Formatter('%(asctime)s [%(levelname)s] [%(name)s] [%(threadName)s] %(filename)s:%(lineno)d - %(funcName)s() - %(message)s')
    
    # Add console handler for terminal output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_format)
    console_handler.setLevel(log_level)  # Use the same level as the logger
    logger.addHandler(console_handler)
    
    # Add file handlers if enabled and a directory is provided
    # This creates persistent logs that can be reviewed later
    if log_dir and env_log_to_file:
        # Create the log directory if it doesn't exist
        log_dir_path = Path(log_dir)
        os.makedirs(log_dir_path, exist_ok=True)
        
        # Generate a timestamp for unique log filenames
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_name = name if name else 'main'
        
        # Daily rotating file handler for regular logs
        # Creates a new file each day and keeps logs for 30 days
        daily_log_filename = f"{log_name}.log"
        daily_file_handler = TimedRotatingFileHandler(
            log_dir_path / daily_log_filename,
            when='midnight',           # Rotate at midnight
            backupCount=30             # Keep 30 days of logs
        )
        daily_file_handler.setFormatter(file_format)
        daily_file_handler.setLevel(log_level)
        logger.addHandler(daily_file_handler)
        
        # Size-based rotating handler for detailed logs
        # Creates a new file when the current one reaches 10MB
        # Keeps 10 backup files before deleting the oldest
        detailed_log_filename = f"{log_name}_detailed_{timestamp}.log"
        detailed_file_handler = RotatingFileHandler(
            log_dir_path / detailed_log_filename,
            maxBytes=10*1024*1024,     # 10 MB per file
            backupCount=10             # Keep 10 backup files
        )
        detailed_file_handler.setFormatter(file_format)
        # Always include DEBUG and higher for detailed logs, regardless of main level
        detailed_file_handler.setLevel(min(log_level, logging.DEBUG))
        logger.addHandler(detailed_file_handler)
    
    # Log the logger creation for tracking
    logger.info(f"Logger '{name}' initialized with level {logging.getLevelName(log_level)} on {hostname}")
    
    return logger

def log_exception(logger, e, message="An exception occurred"):
    """
    Log an exception with traceback information.
    
    This helper function provides standardized exception logging with both:
    - A user-friendly error message at ERROR level
    - Full traceback information at DEBUG level for troubleshooting
    
    Args:
        logger: Logger instance to use
        e: Exception object to log
        message: Custom message to provide context about what operation failed
    """
    # Log basic error message at ERROR level for immediate visibility
    logger.error(f"{message}: {str(e)}")
    
    # Log detailed traceback at DEBUG level for troubleshooting
    # This provides full context but won't clutter logs unless DEBUG is enabled
    logger.debug(f"Exception details: {traceback.format_exc()}")

def log_trade_execution(logger, action, pair, volume, price=None, order_id=None, status="initiated"):
    """
    Log trade execution details in a standardized format.
    
    This function creates consistent, informative log entries for all trade activities,
    making it easy to track trades throughout their lifecycle (initiated -> completed/failed).
    
    Args:
        logger: Logger instance to use
        action: Trade action (buy/sell)
        pair: Trading pair (e.g., BTCUSD)
        volume: Trade volume (quantity being traded)
        price: Trade price (optional) - the price at which the trade executed
        order_id: Order ID (optional) - exchange-assigned or internal ID
        status: Trade status (initiated/completed/failed)
    """
    # Format optional fields if present
    price_str = f" at {price}" if price else ""
    order_str = f" (Order ID: {order_id})" if order_id else ""
    
    # Build the log message with all available information
    log_message = f"Trade {status}: {action.upper()} {volume} {pair}{price_str}{order_str}"
    
    # Use appropriate log level based on status
    if status == "failed":
        # Failed trades are logged as errors for visibility
        logger.error(log_message)
    else:
        # Normal trade operations are logged as info
        logger.info(log_message)

def log_strategy_signal(logger, strategy_name, signal, indicators=None):
    """
    Log strategy signal with optional indicator values.
    
    This function creates standardized logs for strategy signals,
    including technical indicator values for context and troubleshooting.
    The indicators help understand why a particular signal was generated.
    
    Args:
        logger: Logger instance to use
        strategy_name: Name of the strategy that generated the signal
        signal: Generated signal (buy/sell/hold)
        indicators: Dictionary of indicator values (optional)
                  e.g., {'short_ma': 10542.3, 'long_ma': 10425.7}
    """
    # Build the base log message with strategy and signal
    log_message = f"Strategy '{strategy_name}' generated signal: {signal.upper()}"
    
    # Add indicator values if provided
    if indicators:
        # Format each indicator, handling float values with 4 decimal precision
        indicator_str = ", ".join([f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" 
                                 for k, v in indicators.items()])
        log_message += f" | Indicators: {indicator_str}"
        
    # Log the strategy signal at INFO level
    logger.info(log_message)