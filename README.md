# Kraken Trading Bot

A Python-based cryptocurrency trading bot that automates trading strategies using the Kraken exchange API. This sophisticated bot implements customizable trading strategies with robust logging and multiple operating modes to suit both beginners and advanced traders.

![Trading Bot Status](https://img.shields.io/badge/status-active-green)
![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Paper Trading](#paper-trading-mode)
  - [Live Trading](#live-trading-mode)
  - [Backtesting](#backtesting)
  - [Command-Line Options](#command-line-options)
- [Logging System](#logging-system)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
  - [Trading Bot](#trading-bot)
  - [API Client](#api-client)
  - [Strategies](#strategies)
  - [Data Utilities](#data-utilities)
  - [Logging Utilities](#logging-utilities)
- [Extending the Bot](#extending-the-bot)
  - [Creating New Strategies](#creating-new-strategies)
  - [Supporting Additional Exchanges](#supporting-additional-exchanges)
  - [Adding Technical Indicators](#adding-technical-indicators)
- [Performance Monitoring](#performance-monitoring)
- [Safety Measures](#safety-measures)
- [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [License](#license)

## Overview

This trading bot automates cryptocurrency trading using algorithmic strategies. The modular design allows you to deploy various trading strategies while providing tools for historical backtesting and risk-free paper trading. Advanced logging ensures you can monitor all aspects of the bot's operation, and the customizable design lets you adapt the bot to your specific trading style.

## Key Features

- **Multiple Trading Modes**:
  - Live trading with real funds
  - Paper trading for risk-free testing
  - Backtesting against historical data to validate strategies

- **Strategy Implementation**:
  - Moving Average Crossover strategy (default)
  - Extensible framework for custom strategy development
  - Parameter optimization capabilities

- **Advanced Data Handling**:
  - Real-time market data fetching
  - Historical data storage and retrieval
  - Data visualization with buy/sell signals
  - Multi-timeframe analysis support

- **Comprehensive Logging**:
  - Multi-level logging (DEBUG to CRITICAL)
  - Rotating log files for long-term operation
  - Detailed trade logging with price and order information
  - Exception tracking with full stack traces

- **Reliability Features**: 
  - Exception handling throughout the application
  - Graceful error recovery
  - API rate limit management
  - Connection issue handling

- **Highly Configurable**:
  - Environment-based configuration
  - Command-line parameter support
  - Trading pair and volume customization
  - Strategy parameter adjustment

## System Architecture

The trading bot is designed with a modular, component-based architecture that separates concerns and promotes maintainability:

```
                    ┌───────────────────┐
                    │     Main Entry    │
                    │     (main.py)     │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │    Trading Bot    │
                    │  (trading_bot.py) │
                    └─────────┬─────────┘
                              │
           ┌─────────────┬────┴────┬─────────────┐
           │             │         │             │
┌──────────▼─────────┐   │   ┌─────▼──────┐ ┌────▼────────┐
│    API Client      │   │   │ Strategies │ │   Logging   │
│ (kraken_client.py) │   │   │(strategies)│ │ (logger.py) │
└────────────────────┘   │   └────────────┘ └─────────────┘
                         │
                    ┌────▼───────┐
                    │    Data    │
                    │ Utilities  │
                    └────────────┘
```

- **Main Entry**: Processes command-line arguments and launches the bot
- **Trading Bot**: Core component that orchestrates the trading process
- **API Client**: Handles communication with the Kraken exchange
- **Strategies**: Implements trading algorithms to generate signals
- **Logging**: Provides comprehensive activity tracking
- **Data Utilities**: Manages data storage, retrieval, and visualization

## Prerequisites

- Python 3.7 or higher
- Access to the internet (for API connections)
- Kraken account with API key and secret (for live trading)
- Basic understanding of cryptocurrency trading concepts

## Installation

1. **Clone the repository**:

```bash
git clone https://github.com/yourusername/tradingbot.git
cd tradingbot
```

2. **Create and activate a virtual environment** (recommended):

```bash
# On macOS/Linux
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. **Install required packages**:

```bash
pip install -r requirements.txt
```

4. **Create necessary directories** (if they don't exist):

```bash
mkdir -p config data logs
```

5. **Create a configuration file**:

```bash
cp config/.env.sample config/.env
```

6. **Edit the configuration file** with your Kraken API credentials and trading parameters (see Configuration section).

## Configuration

The bot is configured through environment variables, which can be set in the `.env` file or directly in your environment.

### Required Configuration

```ini
# API Authentication
KRAKEN_API_KEY=your_api_key_here
KRAKEN_API_SECRET=your_api_secret_here

# Trading Parameters
TRADING_PAIR=XXBTZUSD       # Kraken asset pair (BTC/USD)
TRADE_VOLUME=0.001          # Amount to trade (0.001 BTC)
STRATEGY=simple_ma          # Strategy to use (simple moving average)
```

### Strategy Parameters

```ini
# Moving Average Strategy Parameters
SHORT_WINDOW=20             # Short-term moving average period
LONG_WINDOW=50              # Long-term moving average period
```

### Logging Configuration

```ini
# Logging Configuration
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, or CRITICAL
LOG_TO_FILE=true            # Whether to write logs to files
LOG_DIR=logs                # Directory for log files
```

## Usage

### Paper Trading Mode

Paper trading lets you test the bot's strategy using real market data but without risking actual funds:

```bash
python main.py --paper --interval 60
```

This runs the bot in paper trading mode, checking the market every 60 minutes and logging what trades it would have executed.

For shorter testing sessions:

```bash
python main.py --paper --interval 5
```

For more detailed logging:

```bash
python main.py --paper --interval 60 --verbose
```

### Live Trading Mode

**⚠️ WARNING: Live trading uses real funds. Use with caution and start with small amounts.**

```bash
python main.py --live --interval 60
```

This runs the bot in live trading mode, making real trades on your behalf every 60 minutes based on the configured strategy.

For conservative live trading with detailed logs:

```bash
python main.py --live --interval 60 --verbose
```

### Backtesting

Backtesting allows you to test your strategy against historical data to see how it would have performed:

```bash
python main.py --backtest --start 2023-01-01 --end 2023-12-31
```

This evaluates the strategy using historical data from January 1st to December 31st, 2023.

For faster backtests with a different time interval:

```bash
python main.py --backtest --start 2023-01-01 --end 2023-01-31 --interval 15
```

To suppress the visualization plot:

```bash
python main.py --backtest --start 2023-01-01 --end 2023-12-31 --no-plot
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--paper` | Run in paper trading mode | (default if no mode specified) |
| `--live` | Run in live trading mode using real funds | - |
| `--backtest` | Run in backtesting mode with historical data | - |
| `-c, --config` | Path to configuration file | `config/.env` |
| `-i, --interval` | Trading interval in minutes | `60` |
| `-v, --verbose` | Enable verbose (DEBUG level) logging | `False` |
| `--start` | Start date for backtest (YYYY-MM-DD) | Earliest available |
| `--end` | End date for backtest (YYYY-MM-DD) | Latest available |
| `--no-plot` | Disable plotting in backtest mode | `False` |

## Logging System

The bot features a comprehensive logging system to provide visibility into all operations, trades, and potential issues.

### Log Levels

| Level | Description | Usage |
|-------|-------------|-------|
| DEBUG | Detailed information for troubleshooting | Development and detailed diagnosis |
| INFO | Confirmation of normal operation | General operational tracking |
| WARNING | Indication of potential issues | Situations requiring attention |
| ERROR | Serious problems affecting functionality | Failed operations that need intervention |
| CRITICAL | Critical failures requiring immediate action | System-threatening issues |

### Log Files

The bot generates several types of log files in the `logs/` directory:

| File Pattern | Description | Rotation |
|--------------|-------------|----------|
| `main.log` | General application logs | Daily |
| `trading_bot.log` | Trading-specific logs | Daily |
| `main_detailed_[timestamp].log` | Detailed debug logs for application | Size-based (10MB) |
| `trading_bot_detailed_[timestamp].log` | Detailed debug logs for trading | Size-based (10MB) |

### Log Message Types

The logs include specialized message formats for different events:

- **Trade Execution Logs**: Records all trade attempts, successes, and failures with price, volume, and order ID
- **Strategy Signal Logs**: Documents every buy/sell/hold decision with the indicator values that led to it
- **Exception Logs**: Captures all exceptions with stack traces for troubleshooting
- **API Communication Logs**: Tracks requests and responses when in debug mode

### Monitoring Logs

For real-time monitoring:

```bash
# Watch main application logs
tail -f logs/main.log

# Watch trading-specific logs
tail -f logs/trading_bot.log

# Search for all error messages
grep "ERROR" logs/trading_bot.log
```

## Project Structure

```
├── config/                  # Configuration files
│   ├── .env                 # Active configuration (create from .env.sample)
│   └── .env.sample          # Sample environment variables template
├── data/                    # Market data and backtest results
│   └── market_*.csv         # Historical market data files
├── examples/                # Example usage scripts
│   ├── paper_trading.py     # Example of paper trading implementation
│   └── simple_backtest.py   # Example of strategy backtesting
├── logs/                    # Log files directory
│   ├── main.log             # Application logs
│   └── trading_bot.log      # Trading-specific logs
├── src/                     # Source code
│   ├── api/                 # API clients
│   │   └── kraken_client.py # Kraken exchange API wrapper
│   ├── strategies/          # Trading strategies
│   │   ├── base_strategy.py # Abstract base strategy class
│   │   └── moving_average.py# Moving average crossover strategy
│   ├── utils/               # Utility functions
│   │   ├── data_utils.py    # Data handling and visualization
│   │   └── logger.py        # Logging configuration and utilities
│   ├── __init__.py          # Package initialization
│   └── trading_bot.py       # Main bot implementation
├── tests/                   # Test suite
│   ├── __init__.py          # Test package initialization
│   └── test_strategy.py     # Strategy tests
├── .gitignore               # Git ignore file
├── LICENSE                  # Project license
├── main.py                  # Entry point script
├── README.md                # Project documentation (this file)
└── requirements.txt         # Python dependencies
```

## Core Components

### Trading Bot

The `TradingBot` class in `src/trading_bot.py` is the central component that coordinates all trading activities. It:

- Integrates with the exchange API to access market data and execute trades
- Applies the configured trading strategy to generate buy/sell/hold signals
- Manages the trading lifecycle (fetch data → analyze → decide → execute)
- Handles different operating modes (live, paper, backtest)
- Logs all activities and maintains state

Key methods include:
- `fetch_market_data()`: Gets OHLC data from the exchange
- `analyze_market()`: Applies the strategy to generate signals
- `execute_trade()`: Places orders on the exchange (in live mode)
- `backtest()`: Simulates strategy performance on historical data
- `start()`: Begins the trading loop at specified intervals

### API Client

The `KrakenClient` class in `src/api/kraken_client.py` provides a simplified interface to the Kraken exchange API, handling:

- Authentication with API keys
- Market data retrieval
- Trade execution
- Account balance queries
- Error handling and rate limiting

Key methods include:
- `get_ohlc_data()`: Fetches candle (OHLC) data
- `create_order()`: Places market or limit orders
- `get_account_balance()`: Retrieves current asset balances
- `get_ticker()`: Gets current market pricing information

### Strategies

The strategies in `src/strategies/` implement trading algorithms that analyze market data to generate trading signals:

- **Base Strategy** (`base_strategy.py`): Abstract class defining the strategy interface
- **Moving Average Crossover** (`moving_average.py`): Implementation that generates signals based on MA crossovers

All strategies implement two key methods:
- `generate_signal()`: Produces a single buy/sell/hold decision for the current market state
- `calculate_indicators()`: Computes technical indicators and signals for the entire dataset

### Data Utilities

The `data_utils.py` module provides functions for data manipulation and visualization:

- `save_data()`: Persists market data to CSV or pickle files
- `load_data()`: Loads saved market data for analysis
- `plot_strategy()`: Visualizes price, indicators, and signals
- `resample_ohlc()`: Changes the timeframe of market data (e.g., 1m to 1h)

### Logging Utilities

The `logger.py` module implements a sophisticated logging system:

- `setup_logger()`: Configures loggers with console and file handlers
- `log_exception()`: Records exceptions with context and stack traces
- `log_trade_execution()`: Formats and logs trade operations
- `log_strategy_signal()`: Documents strategy decisions with indicators

## Extending the Bot

### Creating New Strategies

To add a new trading strategy:

1. Create a new Python file in `src/strategies/` (e.g., `rsi_strategy.py`)
2. Import and subclass the base `Strategy` class:

```python
from .base_strategy import Strategy
import pandas as pd

class RSIStrategy(Strategy):
    """
    RSI-based trading strategy.
    
    Generates buy signals when RSI is below the oversold threshold
    and sell signals when RSI is above the overbought threshold.
    """
    def __init__(self, params=None):
        default_params = {
            'period': 14,
            'oversold': 30,
            'overbought': 70
        }
        
        # Update defaults with any provided parameters
        if params:
            default_params.update(params)
            
        super().__init__(default_params)
    
    def generate_signal(self, data):
        """Generate buy/sell/hold signal based on RSI"""
        if len(data) < self.params['period']:
            return 'hold'  # Not enough data
            
        # Calculate RSI
        rsi = self._calculate_rsi(data['close'], self.params['period'])
        current_rsi = rsi.iloc[-1]
        
        # Generate signal based on RSI thresholds
        if current_rsi < self.params['oversold']:
            return 'buy'
        elif current_rsi > self.params['overbought']:
            return 'sell'
        else:
            return 'hold'
    
    def calculate_indicators(self, data):
        """Calculate RSI and signals for the entire dataset"""
        result = data.copy()
        
        # Add RSI column
        result['rsi'] = self._calculate_rsi(result['close'], self.params['period'])
        
        # Generate signals based on RSI thresholds
        result['signal'] = 'hold'
        result.loc[result['rsi'] < self.params['oversold'], 'signal'] = 'buy'
        result.loc[result['rsi'] > self.params['overbought'], 'signal'] = 'sell'
        
        return result
    
    def _calculate_rsi(self, prices, period):
        """Calculate the Relative Strength Index"""
        # Implementation of RSI calculation
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
```

3. Update the `TradingBot._init_strategy()` method to include your strategy:

```python
def _init_strategy(self, strategy_name: str):
    """Initialize the trading strategy"""
    self.logger.debug(f"Initializing strategy: {strategy_name}")
    
    if strategy_name == 'simple_ma':
        # Get parameters from environment variables
        short_window = int(os.getenv('SHORT_WINDOW', '20'))
        long_window = int(os.getenv('LONG_WINDOW', '50'))
        
        self.strategy = MovingAverageCrossover({
            'short_window': short_window,
            'long_window': long_window
        })
        
    elif strategy_name == 'rsi':
        # Get parameters from environment variables
        period = int(os.getenv('RSI_PERIOD', '14'))
        oversold = int(os.getenv('RSI_OVERSOLD', '30'))
        overbought = int(os.getenv('RSI_OVERBOUGHT', '70'))
        
        self.strategy = RSIStrategy({
            'period': period,
            'oversold': oversold,
            'overbought': overbought
        })
        
    else:
        self.logger.error(f"Unknown strategy: {strategy_name}")
        raise ValueError(f"Unknown strategy: {strategy_name}")
```

4. Update your `.env` file to use the new strategy:

```ini
STRATEGY=rsi
RSI_PERIOD=14
RSI_OVERSOLD=30
RSI_OVERBOUGHT=70
```

### Supporting Additional Exchanges

To add support for another exchange:

1. Create a new API client in `src/api/` (e.g., `binance_client.py`)
2. Implement the same interface as the `KrakenClient` class
3. Modify the `TradingBot` class to use the appropriate client based on configuration

### Adding Technical Indicators

To add new technical indicators for strategy development:

1. Create a utility module in `src/utils/` (e.g., `indicators.py`)
2. Implement indicator functions that operate on pandas DataFrames
3. Use these indicators in your strategy implementations

## Performance Monitoring

The bot records detailed information about its operation that can be used to evaluate performance:

- **Trade History**: All executed trades are logged with timestamp, price, and volume
- **Strategy Signals**: The signals generated by the strategy are logged with indicators
- **Backtest Results**: Performance metrics are calculated for backtests
- **Market Data**: Raw market data is saved for later analysis

To analyze performance:

1. Run a backtest to generate performance metrics:
   ```bash
   python main.py --backtest --start 2023-01-01 --end 2023-12-31
   ```

2. Check the logs for performance data:
   ```bash
   grep "Backtest completed" logs/main.log
   ```

3. Review the generated visualization (saved in the `data/` directory)

## Safety Measures

The bot implements several safety measures:

1. **Paper Trading Mode**: Test strategies without risking real funds
2. **Trade Validation**: Validates trades before execution
3. **Error Handling**: Gracefully handles API errors and network issues
4. **Parameter Validation**: Validates strategy parameters before use
5. **Default to Hold**: When in doubt, the bot defaults to 'hold'

## Common Issues and Troubleshooting

### API Connection Issues

**Problem**: The bot fails to connect to the Kraken API.

**Solution**:
1. Check your internet connection
2. Verify API key and secret in `.env` file
3. Ensure the API key has the necessary permissions
4. Check Kraken's API status at https://status.kraken.com/

### Strategy Not Generating Signals

**Problem**: The bot runs but doesn't generate buy/sell signals.

**Solution**:
1. Enable verbose logging to see the indicators: `python main.py --paper --verbose`
2. Adjust strategy parameters in the `.env` file
3. Ensure you have enough market data for your strategy (e.g., MovingAverage needs at least `long_window` periods)

### Out of Funds Error

**Problem**: Live trading fails with insufficient funds error.

**Solution**:
1. Check your Kraken account balance
2. Lower the `TRADE_VOLUME` in the `.env` file
3. Ensure you're not trying to trade below the minimum order size

### Incorrect Order Volume

**Problem**: Bot is buying/selling incorrect amounts.

**Solution**:
1. Verify `TRADE_VOLUME` in the `.env` file
2. Check that you're using the correct units (e.g., 0.001 BTC, not 1 BTC)
3. Review the trades in the logs to confirm what's being executed

## Contributing

Contributions to improve the trading bot are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Please ensure your code follows the existing style and includes appropriate tests.

## Disclaimer

**⚠️ IMPORTANT**: This trading bot is provided for educational and research purposes only. Cryptocurrency trading involves significant risk and may result in the loss of your investment. The authors and contributors of this project are not responsible for any financial losses incurred from using this software.

- Do not invest money you cannot afford to lose
- Always start with small amounts when testing
- Past performance does not guarantee future results
- The bot may contain bugs or behave unexpectedly

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.