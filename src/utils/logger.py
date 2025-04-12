import os
import logging
from logging.handlers import RotatingFileHandler
import time
from pathlib import Path

def setup_logger(name=None, log_level=logging.INFO, log_dir=None):
    """
    Configure logging with console and file handlers
    
    Args:
        name: Logger name (default: root logger)
        log_level: Logging level (default: INFO)
        log_dir: Directory for log files (default: project logs/)
    
    Returns:
        Configured logger instance
    """
    # Get or create logger
    logger = logging.getLogger(name)
    if logger.handlers:  # Return logger if already configured
        return logger
    
    logger.setLevel(log_level)
    logger.propagate = False  # Prevent duplicate logs
    
    # Create formatters
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_format)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    # Add file handler if log_dir is provided
    if log_dir:
        log_dir_path = Path(log_dir)
        os.makedirs(log_dir_path, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_filename = f"{timestamp}_{name if name else 'main'}.log"
        file_handler = RotatingFileHandler(
            log_dir_path / log_filename,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setFormatter(file_format)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    
    return logger