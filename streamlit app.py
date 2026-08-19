import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NIFTY 50 Stock Analyzer",
    page_icon="📈",
    layout="wide"
)

# ============================================================
# NIFTY 50 STOCK LIST
# ============================================================

NIFTY_50 = {
    "ADANI ENTERPRISES": "ADANIENT.NS",
    "ADANI PORTS": "ADANIPORTS.NS",
    "APOLLO HOSPITALS": "APOLLOHOSP.NS",
    "ASIAN PAINTS": "ASIANPAINT.NS",
    "AXIS BANK": "AXISBANK.NS",
    "BAJAJ AUTO": "BAJAJ-AUTO.NS",
    "BAJAJ FINANCE": "BAJFINANCE.NS",
    "BAJAJ FINSERV": "BAJAJFINSV.NS",
    "BEL": "BEL.NS",
    "BHARTI AIRTEL": "BHARTIARTL.NS",
    "CIPLA": "CIPLA.NS",
    "COAL INDIA": "COALINDIA.NS",
    "DR REDDYS": "DRREDDY.NS",
    "EICHER MOTORS": "EICHERMOT.NS",
    "ETERNAL": "ETERNAL.NS",
    "GRASIM": "GRASIM.NS",
    "HCL TECHNOLOGIES": "HCLTECH.NS",
    "HDFC BANK": "HDFCBANK.NS",
    "HDFC LIFE": "HDFCLIFE.NS",
    "HEROMOTOCO": "HEROMOTOCO.NS",
    "HINDALCO": "HINDALCO.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
    "ICICI BANK": "ICICIBANK.NS",
    "INDUSIND BANK": "INDUSINDBK.NS",
    "INFOSYS": "INFY.NS",
    "ITC": "ITC.NS",
    "JIO FINANCIAL": "JIOFIN.NS",
    "JSW STEEL": "JSWSTEEL.NS",
    "KOTAK MAHINDRA BANK": "KOTAKBANK.NS",
    "LT": "LT.NS",
    "M&M": "M&M.NS",
    "MARUTI": "MARUTI.NS",
    "MAX HEALTHCARE": "MAXHEALTH.NS",
    "NESTLE INDIA": "NESTLEIND.NS",
    "NTPC": "NTPC.NS",
    "ONGC": "ONGC.NS",
    "POWER GRID": "POWERGRID.NS",
    "RELIANCE": "RELIANCE.NS",
    "SBILIFE": "SBILIFE.NS",
    "SHRIRAM FINANCE": "SHRIRAMFIN.NS",
    "STATE BANK OF INDIA": "SBIN.NS",
    "SUN PHARMA": "SUNPHARMA.NS",
    "TATA CONSUMER": "TATACONSUM.NS",
    "TATA MOTORS": "TATAMOTORS.NS",
    "TATA STEEL": "TATASTEEL.NS",
    "TCS": "TCS.NS",
    "TECH MAHINDRA": "TECHM.NS",
    "TITAN": "TITAN.NS",
    "TRENT": "TRENT.NS",
    "ULTRATECH CEMENT": "ULTRACEMCO.NS",
    "WIPRO": "WIPRO.NS"
}

# ============================================================
# FUNCTIONS
# ============================================================

@st.cache_data(ttl=300)
def get_stock_data(symbol, period="2y"):

    data = yf.download(
        symbol,
        period=period,
        interval="1d",
        auto_adjust=False,
        progress=False
    )

    if data.empty:
        return pd.DataFrame()

    # Handle MultiIndex columns from yfinance
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.copy()

    # ========================================================
    # MOVING AVERAGES
    # ========================================================

    data["EMA_9"] = data["Close"].ewm(
        span=9,
        adjust=False
    ).mean()

    data["EMA_20"] = data["Close"].ewm(
        span=20,
        adjust=False
    ).mean()

    data["EMA_100"] = data["Close"].ewm(
        span=100,
        adjust=False
    ).mean()

    data["SMA_200"] = data["Close"].rolling(
        window=200
    ).mean()

    # ========================================================
    # RSI
    # ========================================================

    delta = data["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / 14,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / 14,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss

    data["RSI"] = 100 - (100 / (1 + rs))

    # ========================================================
    # MACD
    # ========================================================

    ema_12 = data["Close"].ewm(
        span=12,
        adjust=False
    ).mean()

    ema_26 = data["Close"].ewm(
        span=26,
        adjust=False
    ).mean()

    data["MACD"] = ema_12 - ema_26

    data["MACD_SIGNAL"] = data["MACD"].ewm(
        span=9,
        adjust=False
    ).mean()

    data["MACD_HIST"] = (
        data["MACD"] - data["MACD_SIGNAL"]
    )

    # ========================================================
    # VOLUME AVERAGE
    # ========================================================

    data["Volume_Avg_20"] = data["Volume"].rolling(
        window=20
    ).mean()

    # ========================================================
    # DAILY RETURN
    # ========================================================

    data["Return_%"] = data["Close"].pct_change() * 100

    return data


def calculate_score(row):

    score = 0
    signals = []

    price = float(row["Close"])

    ema9 = float(row["EMA_9"])
    ema20 = float(row["EMA_20"])
    ema100 = float(row["EMA_100"])
    sma200 = float(row["SMA_200"])

    rsi = float(row["RSI"])

    macd = float(row["MACD"])
    macd_signal = float(row["MACD_SIGNAL"])

    volume = float(row["Volume"])
    volume_avg = float(row["Volume_Avg_20"])

    # ========================================================
    # EMA 9 vs EMA 20
    # ========================================================

    if ema9 > ema20:
        score += 1
        signals.append("EMA 9 > EMA 20")
    else:
        score -= 1
        signals.append("EMA 9 < EMA 20")

    # ========================================================
    # PRICE vs EMA 20
    # ========================================================

    if price > ema20:
        score += 1
        signals.append("Price above EMA 20")
    else:
        score -= 1
        signals.append("Price below EMA 20")

    # ========================================================
    # PRICE vs EMA 100
    # ========================================================

    if price > ema100:
        score += 1
        signals.append("Price above EMA 100")
    else:
        score -= 1
        signals.append("Price below EMA 100")

    # ========================================================
    # PRICE vs SMA 200
    # ========================================================

    if price > sma200:
        score += 2
        signals.append("Price above SMA 200")
    else:
        score -= 2
        signals.append("Price below SMA 200")

    # ========================================================
    # RSI
    # ========================================================

    if 50 <= rsi <= 70:
        score += 1
        signals.append("RSI bullish")
    elif rsi < 30:
        score += 1
        signals.append("RSI oversold")
    elif rsi > 70:
        score -= 1
        signals.append("RSI overbought")
    else:
        signals.append("RSI neutral")

    # ========================================================
    # MACD
    # ========================================================

    if macd > macd_signal:
        score += 1
        signals.append("MACD bullish")
    else:
        score -= 1
        signals.append("MACD bearish")

    # ========================================================
    # VOLUME
    # ========================================================

    if volume > volume_avg:
        score += 1
        signals.append("Volume above 20-day average")
    else:
        signals.append("Volume below 20-day average")

    # ========================================================
    # FINAL SIGNAL
    # ========================================================

    if score >= 6:
        recommendation = "🟢 STRONG BUY"

    elif score >= 3:
        recommendation = "🟢 BUY"

    elif score >= 1:
        recommendation = "🟡 HOLD / WATCH"

    elif score <= -5:
        recommendation = "🔴 STRONG SELL"

    elif score <= -2:
        recommendation = "🔴 SELL"

    else:
        recommendation = "🟡 HOLD"

    return score, recommendation, signals


def get_short_term_trend(row):

    price = row["Close"]

    if (
        price > row["EMA_9"]
        and row["EMA_9"] > row["EMA_20"]
    ):
        return "🟢 Bullish"

    elif (
        price < row["EMA_9"]
        and row["EMA_9"] < row["EMA_20"]
    ):
        return "🔴 Bearish"

    return "🟡 Neutral"


def get_long_term_trend(row):

    price = row["Close"]

    if (
        price > row["EMA_100"]
        and price > row["SMA_200"]
        and row["EMA_100"] > row["SMA_200"]
    ):
        return "🟢 Strong Bullish"

    elif (
        price > row["SMA_200"]
        and row["EMA_100"] > row["SMA_200"]
    ):
        return "🟢 Bullish"

    elif (
        price < row["SMA_200"]
        and row["EMA_100"] < row["SMA_200"]
    ):
        return "🔴 Bearish"

    return "🟡 Neutral"


# ============================================================
# HEADER
# ============================================================

st.title("📈 NIFTY 50 Stock Analyzer")

st.caption(
    "Technical + Long-Term Trend Analysis"
)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Settings")

stock_name = st.sidebar.selectbox(
    "Select NIFTY 50 Stock",
    list(NIFTY_50.keys())
)

symbol = NIFTY_50[stock_name]

period = st.sidebar.selectbox(
    "Historical Period",
    [
        "1y",
        "2y",
        "5y",
        "10y"
    ],
    index=1
)

if st.sidebar.button("🔄 Refresh Data"):

    st.cache_data.clear()

    st.rerun()

st.sidebar.markdown("---")

st.sidebar.info(
    """
    **Indicators used**

    • EMA 9  
    • EMA 20  
    • EMA 100  
    • SMA 200  
    • RSI  
    • MACD  
    • Volume  
    • Short-term trend  
    • Long-term trend  
    • Technical score

    Dhan Market Depth is not used.
    """
)

# ============================================================
# LOAD DATA
# ============================================================

with st.spinner("Loading stock data..."):

    data = get_stock_data(
        symbol,
        period
    )

if data.empty:

    st.error(
        "Unable to download stock data. "
        "Please try again."
    )

    st.stop()

# ============================================================
# REMOVE INITIAL NaN VALUES
# ============================================================

data = data.dropna(
    subset=[
        "EMA_9",
        "EMA_20",
        "EMA_100",
        "SMA_200",
        "RSI",
        "MACD",
        "MACD_SIGNAL",
        "Volume_Avg_20"
    ]
)

if data.empty:

    st.error(
        "Not enough historical data "
        "to calculate all indicators."
    )

    st.stop()

# ============================================================
# LATEST DATA
# ============================================================

latest = data.iloc[-1]

price = float(latest["Close"])

previous_close = float(
    data.iloc[-2]["Close"]
)

daily_change = (
    (price - previous_close)
    / previous_close
) * 100

score, recommendation, signals = calculate_score(
    latest
)

short_term = get_short_term_trend(
    latest
)

long_term = get_long_term_trend(
    latest
)

# ============================================================
# STOCK HEADER
# ============================================================

st.subheader(stock_name)

st.caption(
    f"Ticker: {symbol}"
)

# ============================================================
# TOP METRICS
# ============================================================

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Price",
    f"₹{price:,.2f}",
    f"{daily_change:+.2f}%"
)

c2.metric(
    "RSI",
    f"{latest['RSI']:.2f}"
)

c3.metric(
    "Technical Score",
    f"{score}/8"
)

c4.metric(
    "Short-Term",
    short_term
)

c5.metric(
    "Long-Term",
    long_term
)

st.markdown("---")

# ============================================================
# RECOMMENDATION
# ============================================================

if "STRONG BUY" in recommendation:

    st.success(
        f"### {recommendation}\n\n"
        f"Technical score: **{score}/8**"
    )

elif recommendation == "🟢 BUY":

    st.success(
        f"### {recommendation}\n\n"
        f"Technical score: **{score}/8**"
    )

elif "SELL" in recommendation:

    st.error(
        f"### {recommendation}\n\n"
        f"Technical score: **{score}/8**"
    )

else:

    st.warning(
        f"### {recommendation}\n\n"
        f"Technical score: **{score}/8**"
    )

# ============================================================
# PRICE CHART
# ============================================================

st.subheader("📊 Price & Moving Averages")

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["Close"],
        name="Price",
        mode="lines"
    )
)

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["EMA_9"],
        name="EMA 9",
        mode="lines"
    )
)

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["EMA_20"],
        name="EMA 20",
        mode="lines"
    )
)

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["EMA_100"],
        name="EMA 100",
        mode="lines"
    )
)

fig.add_trace(
    go.Scatter(
        x=data.index,
        y=data["SMA_200"],
        name="SMA 200",
        mode="lines"
    )
)

fig.update_layout(
    height=600,
    xaxis_title="Date",
    yaxis_title="Price (₹)",
    hovermode="x unified"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ============================================================
# INDICATOR VALUES
# ============================================================

st.subheader("📌 Current Indicator Values")

indicator_df = pd.DataFrame({
    "Indicator": [
        "Current Price",
        "EMA 9",
        "EMA 20",
        "EMA 100",
        "SMA 200",
        "RSI",
        "MACD",
        "MACD Signal",
        "MACD Histogram",
        "Volume",
        "20-Day Avg Volume"
    ],

    "Value": [
        price,
        latest["EMA_9"],
        latest["EMA_20"],
        latest["EMA_100"],
        latest["SMA_200"],
        latest["RSI"],
        latest["MACD"],
        latest["MACD_SIGNAL"],
        latest["MACD_HIST"],
        latest["Volume"],
        latest["Volume_Avg_20"]
    ]
})

indicator_df["Value"] = indicator_df["Value"].apply(
    lambda x: f"{x:,.2f}"
)

st.dataframe(
    indicator_df,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# TECHNICAL SIGNALS
# ============================================================

st.subheader("🔎 Technical Signals")

signal_df = pd.DataFrame({
    "Signal": signals
})

st.dataframe(
    signal_df,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# TREND ANALYSIS
# ============================================================

st.subheader("📈 Trend Analysis")

trend_col1, trend_col2 = st.columns(2)

with trend_col1:

    st.markdown("### Short-Term")

    st.write(
        """
        **Primary indicators:**

        EMA 9  
        EMA 20  
        RSI  
        MACD

        The short-term trend becomes more bullish
        when price > EMA 9 > EMA 20.
        """
    )

    st.info(
        f"Current Short-Term Trend: **{short_term}**"
    )

with trend_col2:

    st.markdown("### Long-Term")

    st.write(
        """
        **Primary indicators:**

        EMA 100  
        SMA 200  
        Current Price

        The long-term trend is stronger when
        price remains above the 200-day SMA and
        EMA 100 remains above SMA 200.
        """
    )

    st.info(
        f"Current Long-Term Trend: **{long_term}**"
    )

# ============================================================
# RSI
# ============================================================

st.subheader("📉 RSI")

fig_rsi = go.Figure()

fig_rsi.add_trace(
    go.Scatter(
        x=data.index,
        y=data["RSI"],
        name="RSI",
        mode="lines"
    )
)

fig_rsi.add_hline(
    y=70,
    line_dash="dash"
)

fig_rsi.add_hline(
    y=30,
    line_dash="dash"
)

fig_rsi.add_hline(
    y=50,
    line_dash="dot"
)

fig_rsi.update_layout(
    height=350,
    yaxis_title="RSI",
    xaxis_title="Date"
)

st.plotly_chart(
    fig_rsi,
    use_container_width=True
)

# ============================================================
# MACD
# ============================================================

st.subheader("📊 MACD")

fig_macd = go.Figure()

fig_macd.add_trace(
    go.Scatter(
        x=data.index,
        y=data["MACD"],
        name="MACD",
        mode="lines"
    )
)

fig_macd.add_trace(
    go.Scatter(
        x=data.index,
        y=data["MACD_SIGNAL"],
        name="Signal",
        mode="lines"
    )
)

fig_macd.add_bar(
    x=data.index,
    y=data["MACD_HIST"],
    name="Histogram"
)

fig_macd.update_layout(
    height=400,
    xaxis_title="Date",
    yaxis_title="MACD"
)

st.plotly_chart(
    fig_macd,
    use_container_width=True
)

# ============================================================
# VOLUME
# ============================================================

st.subheader("📦 Volume")

fig_volume = go.Figure()

fig_volume.add_trace(
    go.Bar(
        x=data.index,
        y=data["Volume"],
        name="Volume"
    )
)

fig_volume.add_trace(
    go.Scatter(
        x=data.index,
        y=data["Volume_Avg_20"],
        name="20-Day Average Volume",
        mode="lines"
    )
)

fig_volume.update_layout(
    height=400,
    xaxis_title="Date",
    yaxis_title="Volume"
)

st.plotly_chart(
    fig_volume,
    use_container_width=True
)

# ============================================================
# RECENT DATA
# ============================================================

st.subheader("📋 Recent Trading Data")

display_columns = [
    "Close",
    "EMA_9",
    "EMA_20",
    "EMA_100",
    "SMA_200",
    "RSI",
    "MACD",
    "MACD_SIGNAL",
    "Volume"
]

recent = data[display_columns].tail(20).copy()

recent = recent.round(2)

st.dataframe(
    recent,
    use_container_width=True
)

# ============================================================
# DISCLAIMER
# ============================================================

st.markdown("---")

st.caption(
    """
    ⚠️ This application is an analytical tool and not financial advice.
    Technical indicators can produce false signals. Always consider
    valuation, financial statements, sector conditions, market conditions,
    risk tolerance and your investment horizon before making an investment.
    """
)