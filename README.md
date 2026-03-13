ASX Momentum Scanner

A lightweight Python scanner that analyses ASX200 stocks daily and sends Telegram alerts when momentum signals appear.

The scanner runs automatically using GitHub Actions, so no computer needs to stay on.

Features

• Scans ASX200 stocks daily after market close
• Detects multiple technical signals
• Sends ranked alerts via Telegram
• Runs automatically using GitHub Actions
• Includes failure alerts and log uploads
• Uses free market data via Yahoo Finance

Signals Detected

The scanner ranks stocks by the number of bullish signals detected.

Signals include:

SMA20 Breakout

Price crosses above the 20-day moving average

SMA50 Breakout

Price crosses above the 50-day moving average

Golden Cross

The 50-day SMA crosses above the 200-day SMA

20-Day Breakout

Price closes at a 20-day high

Volume Expansion

Daily volume is 50% higher than the 20-day average

Trend Acceleration

The slope of the 20-day moving average is increasing

Stocks with multiple signals appear at the top of the report.

Example Alert

Telegram message example:

📊 ASX Momentum Scanner

🏆 Top Opportunities

1. XYZ.AX
Signals: SMA20, Breakout, Volume
Close: 12.43

2. ABC.AX
Signals: SMA50, TrendAccel
Close: 8.12
How It Works

GitHub Actions runs the scanner daily

The script downloads ASX200 data using yfinance

Technical signals are calculated

The top 10 stocks are ranked

Telegram sends the alert

If the script fails, a Telegram error notification is sent with a link to the run logs.

Project Structure
.
├── asx_scanner_fast.py
├── .github/workflows/asx.yml
└── README.md
asx_scanner_fast.py

Main scanner script.

Responsibilities:

• fetch ASX200 tickers
• download market data
• calculate indicators
• rank signals
• send Telegram alerts

asx.yml

GitHub Actions workflow that:

• runs the scanner daily
• installs dependencies
• captures logs
• sends Telegram failure alerts

Setup
1. Clone the repo
git clone https://github.com/yourusername/asx-scanner.git
cd asx-scanner
2. Create a Telegram bot

Open Telegram and message:

@BotFather

Create a new bot and copy the Bot Token.

3. Get your chat ID

Message your bot once, then visit:

https://api.telegram.org/botYOUR_TOKEN/getUpdates

Find the chat.id.

4. Add GitHub secrets

Go to:

Repository → Settings → Secrets → Actions

Add:

TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
5. Enable GitHub Actions

The workflow runs automatically.

Manual run:

Actions → ASX Scanner → Run workflow
Dependencies

Python packages used:

pandas
yfinance
requests
lxml

Installed automatically by GitHub Actions.

Scheduling

Current schedule:

20 8 * * 1-5

This runs at 08:20 UTC Monday–Friday.

You may want to adjust this to run after the ASX closes.

Example:

10 7 * * 1-5
Error Handling

The workflow includes robust error handling:

• full Python traceback logging
• log file artifacts uploaded to GitHub
• Telegram failure alerts
• fallback ticker list if Wikipedia fails

Logs can be downloaded from the GitHub Actions run page.

Limitations

• Uses free Yahoo Finance data
• Data may occasionally lag or fail
• Scanner does not consider fundamentals
• Not financial advice

Ideas for Future Improvements

Possible upgrades:

• RSI signals
• relative strength vs index
• trend scoring model
• backtesting engine
• portfolio tracking
• email alerts
• dashboard UI

License

MIT License
