# Kraken Trading Bot

A Python-based cryptocurrency trading bot using the Kraken exchange API. This bot implements automated trading strategies with customizable parameters and supports both live and paper trading modes.

## Features

- **Multiple Trading Modes**: Live trading, paper trading, and backtesting
- **Strategy Implementation**: Moving Average Crossover strategy (extensible for more)
- **Data Visualization**: Visualize trading performance and signals
- **Configurable**: Easily adjust parameters via environment variables
- **Logging**: Comprehensive logging system for tracking bot activities

## Prerequisites

- Python 3.7+
- Kraken account with API key (for live trading)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/tradingbot.git
cd tradingbot
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the `config` directory (use the sample as a template):

```bash
cp config/.env.sample config/.env
```

4. Edit the `.env` file with your Kraken API credentials and trading parameters:

```
KRAKEN_API_KEY=your_api_key_here
KRAKEN_API_SECRET=your_api_secret_here

# Trading parameters
TRADING_PAIR=XXBTZUSD
TRADE_VOLUME=0.001  # BTC
STRATEGY=simple_ma  # simple moving average strategy

# Moving Average parameters
SHORT_WINDOW=20
LONG_WINDOW=50
```

## Usage

### Paper Trading Mode

Paper trading allows you to test the bot's strategy without risking real funds:

```bash
python main.py --paper --interval 60
```

This will run the bot in paper trading mode with a 60-minute trading interval.

### Live Trading Mode

**WARNING**: Live trading uses real funds. Use with caution.

```bash
python main.py --live --interval 60
```

### Backtesting

Test your strategy against historical data:

```bash
python main.py --backtest --start 2023-01-01 --end 2023-12-31
```

### Command-Line Options

- `--paper`: Run in paper trading mode (default)
- `--live`: Run in live trading mode
- `--backtest`: Run in backtesting mode
- `-c, --config`: Path to configuration file
- `-i, --interval`: Trading interval in minutes (default: 60)
- `-v, --verbose`: Enable verbose logging
- `--start`: Start date for backtest (format: YYYY-MM-DD)
- `--end`: End date for backtest (format: YYYY-MM-DD)
- `--no-plot`: Disable plotting in backtest mode

## Project Structure

```
├── config/              # Configuration files
│   └── .env.sample      # Sample environment variables
├── data/                # Market data and backtest results
├── logs/                # Log files
├── src/                 # Source code
│   ├── api/             # API clients
│   │   └── kraken_client.py
│   ├── strategies/      # Trading strategies
│   │   ├── base_strategy.py
│   │   └── moving_average.py
│   ├── utils/           # Utility functions
│   │   ├── data_utils.py
│   │   └── logger.py
│   └── trading_bot.py   # Main bot implementation
├── tests/               # Test suite
├── main.py              # Entry point
└── requirements.txt     # Dependencies
```

## Extending the Bot

### Adding New Strategies

1. Create a new strategy file in `src/strategies/`
2. Extend the `Strategy` base class in `src/strategies/base_strategy.py`
3. Implement the `generate_signal()` method
4. Update `TradingBot._init_strategy()` to include your new strategy

## Disclaimer

This trading bot is for educational and research purposes only. Use at your own risk. The authors are not responsible for any financial losses incurred from using this software.

## License

This project is licensed under the terms of the included LICENSE file.