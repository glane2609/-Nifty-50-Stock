# 📈 NIFTY 50 Stock Analyzer

A Streamlit-based stock analysis dashboard for analyzing NIFTY 50 stocks using technical indicators, price trends, volume, and long-term trend analysis.

## 🚀 Features

- 📊 NIFTY 50 stock selection
- 📈 Historical stock price analysis
- EMA 9
- EMA 20
- EMA 100
- SMA 200
- RSI
- MACD
- Trading volume
- Short-term trend analysis
- Long-term trend analysis
- Technical indicator-based stock assessment
- Interactive charts
- Buy/Hold/Sell-style analytical signals
- No Dhan API required

## 🧮 Technical Indicators

The application uses multiple indicators to assess stock trends:

### Moving Averages

- EMA 9 — short-term momentum
- EMA 20 — short-term/intermediate trend
- EMA 100 — medium/long-term trend
- SMA 200 — long-term trend

### Momentum

- RSI
- MACD

### Volume

Volume is used to confirm whether price movements are supported by market activity.

## 📌 Analysis Approach

The application combines multiple indicators rather than relying on a single indicator.

### Short-Term Trend

The short-term assessment considers:

- Price vs EMA 9
- Price vs EMA 20
- EMA 9 vs EMA 20
- RSI
- MACD
- Volume

### Long-Term Trend

The long-term assessment considers:

- Price vs EMA 100
- Price vs SMA 200
- EMA 100 vs SMA 200
- Overall price trend

The objective is to identify whether a stock currently shows a bullish, bearish, or neutral technical structure.

## 🛠️ Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- yfinance
- Plotly
- Technical Analysis

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/glane2609/-Nifty-50-Stock.git