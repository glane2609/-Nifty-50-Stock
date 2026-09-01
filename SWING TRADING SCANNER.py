# ============================================================
# VERSION 1
# INDIAN MARKET SWING TRADING SCANNER
#
# Zerodha NSE Universe
# Moving Average Pullback Strategy
# RSI
# Volume
# ATR
# Risk / Reward
# Position Sizing
#
# OUTPUT:
# TOP 10 SWING STOCKS
#
# NO AUTOMATIC ORDER PLACEMENT
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from kiteconnect import KiteConnect

from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import time


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="India Swing Scanner V1",
    page_icon="📈",
    layout="wide"
)


st.title("📈 Indian Swing Trading Scanner — Version 1")

st.caption(
    "Moving Average Pullback Strategy | Zerodha NSE Universe"
)


# ============================================================
# SESSION STATE
# ============================================================

if "instruments" not in st.session_state:
    st.session_state.instruments = None

if "results" not in st.session_state:
    st.session_state.results = None


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔐 Zerodha")

api_key = st.sidebar.text_input(
    "Kite API Key",
    type="password"
)

access_token = st.sidebar.text_input(
    "Access Token",
    type="password"
)


# ============================================================
# ACCOUNT SETTINGS
# ============================================================

st.sidebar.header("💰 Account")

capital = st.sidebar.number_input(
    "Trading Capital ₹",
    min_value=1000.0,
    value=20000.0,
    step=1000.0
)

risk_percent = st.sidebar.number_input(
    "Risk per trade %",
    min_value=0.1,
    max_value=5.0,
    value=1.0,
    step=0.1
)

max_positions = st.sidebar.number_input(
    "Maximum positions",
    min_value=1,
    max_value=10,
    value=2
)


# ============================================================
# STRATEGY SETTINGS
# ============================================================

st.sidebar.header("📊 Strategy")


EMA_FAST = st.sidebar.number_input(
    "Fast EMA",
    min_value=5,
    max_value=50,
    value=20
)


EMA_MEDIUM = st.sidebar.number_input(
    "Medium EMA",
    min_value=20,
    max_value=100,
    value=50
)


EMA_SLOW = st.sidebar.number_input(
    "Slow EMA",
    min_value=100,
    max_value=300,
    value=200
)


RSI_PERIOD = st.sidebar.number_input(
    "RSI Period",
    min_value=5,
    max_value=30,
    value=14
)


ATR_PERIOD = st.sidebar.number_input(
    "ATR Period",
    min_value=5,
    max_value=30,
    value=14
)


# ============================================================
# PULLBACK SETTINGS
# ============================================================

st.sidebar.header(
    "🎯 Moving Average Pullback"
)


MAX_EMA_DISTANCE = st.sidebar.slider(
    "Maximum distance from EMA20 %",
    min_value=0.5,
    max_value=10.0,
    value=3.0,
    step=0.5
)


MIN_RSI = st.sidebar.slider(
    "Minimum RSI",
    min_value=30,
    max_value=70,
    value=50
)


MAX_RSI = st.sidebar.slider(
    "Maximum RSI",
    min_value=60,
    max_value=90,
    value=70
)


# ============================================================
# VOLUME
# ============================================================

st.sidebar.header("📊 Volume")


VOLUME_PERIOD = st.sidebar.number_input(
    "Volume average period",
    min_value=5,
    max_value=50,
    value=20
)


MIN_RELATIVE_VOLUME = st.sidebar.number_input(
    "Minimum relative volume",
    min_value=0.5,
    max_value=5.0,
    value=1.0,
    step=0.1
)


# ============================================================
# RISK MANAGEMENT
# ============================================================

st.sidebar.header("🛡 Risk Management")


ATR_MULTIPLIER = st.sidebar.number_input(
    "ATR Stop Multiplier",
    min_value=0.5,
    max_value=5.0,
    value=1.5,
    step=0.1
)


MIN_RR = st.sidebar.number_input(
    "Minimum Risk / Reward",
    min_value=1.0,
    max_value=5.0,
    value=2.0,
    step=0.25
)


# ============================================================
# LIQUIDITY
# ============================================================

st.sidebar.header("💧 Liquidity")


MIN_PRICE = st.sidebar.number_input(
    "Minimum Stock Price ₹",
    min_value=1.0,
    value=20.0
)


MIN_AVG_VOLUME = st.sidebar.number_input(
    "Minimum Average Volume",
    min_value=0,
    value=100000,
    step=50000
)


# ============================================================
# SCAN SETTINGS
# ============================================================

st.sidebar.header("🔎 Scanner")


testing_mode = st.sidebar.checkbox(
    "Testing mode",
    value=True
)


if testing_mode:

    test_stocks = st.sidebar.number_input(
        "Stocks to scan",
        min_value=10,
        max_value=5000,
        value=100,
        step=10
    )

else:

    test_stocks = 5000


# ============================================================
# ZERODHA CONNECTION
# ============================================================

def connect_kite():

    kite = KiteConnect(
        api_key=api_key
    )

    kite.set_access_token(
        access_token
    )

    return kite


# ============================================================
# LOAD NSE INSTRUMENTS
# ============================================================

@st.cache_data(ttl=86400)
def load_nse_instruments(
    api_key,
    access_token
):

    kite = KiteConnect(
        api_key=api_key
    )

    kite.set_access_token(
        access_token
    )

    instruments = kite.instruments(
        "NSE"
    )

    df = pd.DataFrame(
        instruments
    )

    # CASH EQUITY ONLY

    df = df[
        (df["exchange"] == "NSE")
        &
        (df["segment"] == "NSE")
        &
        (df["instrument_type"] == "EQ")
    ].copy()

    df = df[
        [
            "instrument_token",
            "tradingsymbol",
            "name",
            "exchange",
            "segment"
        ]
    ]

    df = df.drop_duplicates(
        subset="tradingsymbol"
    )

    df = df.sort_values(
        "tradingsymbol"
    )

    return df


# ============================================================
# LOAD BUTTON
# ============================================================

if st.sidebar.button(
    "🔄 Load Zerodha NSE Stocks",
    type="primary"
):

    if not api_key:

        st.sidebar.error(
            "Enter Kite API Key."
        )

    elif not access_token:

        st.sidebar.error(
            "Enter Access Token."
        )

    else:

        try:

            with st.spinner(
                "Loading NSE equity universe..."
            ):

                instruments = load_nse_instruments(
                    api_key,
                    access_token
                )

            st.session_state.instruments = (
                instruments
            )

            st.sidebar.success(
                f"{len(instruments):,} NSE stocks loaded"
            )

        except Exception as e:

            st.sidebar.error(
                f"Zerodha error: {e}"
            )


# ============================================================
# CHECK INSTRUMENTS
# ============================================================

if st.session_state.instruments is None:

    st.info(
        "Enter your Zerodha API credentials and "
        "click 'Load Zerodha NSE Stocks'."
    )

    st.stop()


instruments = (
    st.session_state.instruments
)


st.success(
    f"Loaded {len(instruments):,} NSE equity stocks."
)


# ============================================================
# SELECT SCAN UNIVERSE
# ============================================================

if testing_mode:

    scan_df = instruments.head(
        int(test_stocks)
    ).copy()

else:

    scan_df = instruments.copy()


st.info(
    f"Stocks selected for scanning: "
    f"**{len(scan_df):,}**"
)


# ============================================================
# RSI
# ============================================================

def calculate_rsi(
    close,
    period=14
):

    delta = close.diff()

    gains = delta.clip(
        lower=0
    )

    losses = -delta.clip(
        upper=0
    )

    avg_gain = (
        gains
        .ewm(
            alpha=1 / period,
            adjust=False
        )
        .mean()
    )

    avg_loss = (
        losses
        .ewm(
            alpha=1 / period,
            adjust=False
        )
        .mean()
    )

    rs = (
        avg_gain
        /
        avg_loss.replace(
            0,
            np.nan
        )
    )

    rsi = (
        100
        -
        (
            100
            /
            (1 + rs)
        )
    )

    return rsi


# ============================================================
# ATR
# ============================================================

def calculate_atr(
    df,
    period=14
):

    high = df["high"]

    low = df["low"]

    close = df["close"]

    previous_close = (
        close.shift(1)
    )

    tr1 = (
        high - low
    )

    tr2 = (
        high - previous_close
    ).abs()

    tr3 = (
        low - previous_close
    ).abs()

    true_range = pd.concat(
        [
            tr1,
            tr2,
            tr3
        ],
        axis=1
    ).max(
        axis=1
    )

    atr = (
        true_range
        .rolling(
            period
        )
        .mean()
    )

    return atr


# ============================================================
# INDICATORS
# ============================================================

def calculate_indicators(
    df
):

    df = df.copy()

    # --------------------------------------------------------
    # EMA
    # --------------------------------------------------------

    df["EMA20"] = (
        df["close"]
        .ewm(
            span=EMA_FAST,
            adjust=False
        )
        .mean()
    )

    df["EMA50"] = (
        df["close"]
        .ewm(
            span=EMA_MEDIUM,
            adjust=False
        )
        .mean()
    )

    df["EMA200"] = (
        df["close"]
        .ewm(
            span=EMA_SLOW,
            adjust=False
        )
        .mean()
    )

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    df["RSI"] = calculate_rsi(
        df["close"],
        RSI_PERIOD
    )

    # --------------------------------------------------------
    # ATR
    # --------------------------------------------------------

    df["ATR"] = calculate_atr(
        df,
        ATR_PERIOD
    )

    # --------------------------------------------------------
    # VOLUME
    # --------------------------------------------------------

    df["AverageVolume"] = (
        df["volume"]
        .rolling(
            VOLUME_PERIOD
        )
        .mean()
    )

    df["RelativeVolume"] = (
        df["volume"]
        /
        df["AverageVolume"]
    )

    return df


# ============================================================
# MOVING AVERAGE PULLBACK
# ============================================================

def check_ma_pullback(
    df
):

    if len(df) < EMA_SLOW + 30:

        return False, []


    last = df.iloc[-1]

    previous = df.iloc[-2]


    price = last["close"]

    ema20 = last["EMA20"]

    ema50 = last["EMA50"]

    ema200 = last["EMA200"]


    # ========================================================
    # CONDITION 1
    # BULLISH TREND
    # ========================================================

    bullish_trend = (

        price > ema20

        and

        ema20 > ema50

        and

        ema50 > ema200

    )


    # ========================================================
    # CONDITION 2
    # PRICE NEAR EMA20
    # ========================================================

    distance = (

        abs(
            price - ema20
        )
        /
        ema20
        *
        100

    )


    near_ema = (
        distance
        <= MAX_EMA_DISTANCE
    )


    # ========================================================
    # CONDITION 3
    # PREVIOUS CANDLE APPROACHED EMA
    # ========================================================

    previous_distance = (

        abs(
            previous["close"]
            -
            previous["EMA20"]
        )
        /
        previous["EMA20"]
        *
        100

    )


    previous_near_ema = (

        previous_distance
        <= MAX_EMA_DISTANCE

    )


    # ========================================================
    # CONDITION 4
    # RECOVERY
    # ========================================================

    recovery = (

        price
        >
        previous["close"]

    )


    # ========================================================
    # CONDITION 5
    # LOW TOUCHES EMA
    # ========================================================

    ema_touch = (

        previous["low"]
        <=
        previous["EMA20"] * 1.01

    )


    # ========================================================
    # CONDITION 6
    # RSI
    # ========================================================

    rsi_ok = (

        MIN_RSI
        <=
        last["RSI"]
        <=
        MAX_RSI

    )


    # ========================================================
    # CONDITION 7
    # VOLUME
    # ========================================================

    volume_ok = (

        last["RelativeVolume"]
        >=
        MIN_RELATIVE_VOLUME

    )


    # ========================================================
    # FINAL SETUP
    # ========================================================

    setup = (

        bullish_trend

        and

        (
            near_ema
            or
            previous_near_ema
            or
            ema_touch
        )

        and

        recovery

        and

        rsi_ok

    )


    reasons = []


    if bullish_trend:

        reasons.append(
            "Bullish EMA alignment"
        )


    if (
        near_ema
        or
        previous_near_ema
        or
        ema_touch
    ):

        reasons.append(
            "EMA20 pullback"
        )


    if recovery:

        reasons.append(
            "Recovery candle"
        )


    if rsi_ok:

        reasons.append(
            "RSI confirmation"
        )


    if volume_ok:

        reasons.append(
            "Volume confirmation"
        )


    return setup, reasons


# ============================================================
# CALCULATE SCORE
# ============================================================

def calculate_score(
    df,
    pullback,
    reasons
):

    last = df.iloc[-1]

    price = last["close"]

    ema20 = last["EMA20"]

    ema50 = last["EMA50"]

    ema200 = last["EMA200"]

    rsi = last["RSI"]

    relative_volume = (
        last["RelativeVolume"]
    )


    score = 0


    # ========================================================
    # TREND — 30 POINTS
    # ========================================================

    if (

        price > ema20

        and

        ema20 > ema50

        and

        ema50 > ema200

    ):

        score += 30


    elif (

        price > ema20

        and

        ema20 > ema50

    ):

        score += 20


    # ========================================================
    # PULLBACK — 25 POINTS
    # ========================================================

    if pullback:

        score += 25


    # ========================================================
    # RSI — 15 POINTS
    # ========================================================

    if 55 <= rsi <= 65:

        score += 15

    elif 50 <= rsi <= 70:

        score += 10

    elif 45 <= rsi <= 75:

        score += 5


    # ========================================================
    # VOLUME — 15 POINTS
    # ========================================================

    if relative_volume >= 1.5:

        score += 15

    elif relative_volume >= 1.2:

        score += 10

    elif relative_volume >= 1.0:

        score += 5


    # ========================================================
    # PRICE EXTENSION — 15 POINTS
    # ========================================================

    ema_distance = (

        abs(
            price - ema20
        )
        /
        ema20
        *
        100

    )


    if ema_distance <= 1:

        score += 15

    elif ema_distance <= 2:

        score += 12

    elif ema_distance <= 3:

        score += 8

    elif ema_distance <= 5:

        score += 3


    return min(
        score,
        100
    )


# ============================================================
# ANALYZE ONE STOCK
# ============================================================

def analyze_stock(
    row
):

    symbol = row["tradingsymbol"]

    name = row["name"]

    token = int(
        row["instrument_token"]
    )


    # Each worker gets its own Kite client

    try:

        kite = KiteConnect(
            api_key=api_key
        )

        kite.set_access_token(
            access_token
        )


        # ----------------------------------------------------
        # HISTORICAL PERIOD
        # ----------------------------------------------------

        to_date = datetime.now()

        from_date = (
            to_date
            -
            timedelta(
                days=400
            )
        )


        # ----------------------------------------------------
        # FETCH DAILY DATA
        # ----------------------------------------------------

        candles = kite.historical_data(
            token,
            from_date,
            to_date,
            "day",
            continuous=False,
            oi=False
        )


        if not candles:

            return None


        df = pd.DataFrame(
            candles
        )


        if len(df) < (
            EMA_SLOW + 30
        ):

            return None


        # ----------------------------------------------------
        # INDICATORS
        # ----------------------------------------------------

        df = calculate_indicators(
            df
        )


        last = df.iloc[-1]


        price = float(
            last["close"]
        )

        avg_volume = float(
            last["AverageVolume"]
        )

        relative_volume = float(
            last["RelativeVolume"]
        )

        rsi = float(
            last["RSI"]
        )

        atr = float(
            last["ATR"]
        )


        # ----------------------------------------------------
        # BASIC FILTERS
        # ----------------------------------------------------

        if price < MIN_PRICE:

            return None


        if avg_volume < MIN_AVG_VOLUME:

            return None


        # ----------------------------------------------------
        # PULLBACK
        # ----------------------------------------------------

        pullback, reasons = (
            check_ma_pullback(
                df
            )
        )


        # Version 1 = pullback strategy only

        if not pullback:

            return None


        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        score = calculate_score(
            df,
            pullback,
            reasons
        )


        # ----------------------------------------------------
        # ATR STOP
        # ----------------------------------------------------

        entry = price


        stop_loss = (

            entry
            -
            (
                atr
                *
                ATR_MULTIPLIER
            )

        )


        # ----------------------------------------------------
        # INVALID STOP
        # ----------------------------------------------------

        if stop_loss <= 0:

            return None


        # ----------------------------------------------------
        # RISK
        # ----------------------------------------------------

        risk_per_share = (
            entry
            -
            stop_loss
        )


        if risk_per_share <= 0:

            return None


        # ----------------------------------------------------
        # TARGET
        # ----------------------------------------------------

        target = (

            entry
            +
            (
                risk_per_share
                *
                MIN_RR
            )

        )


        # ----------------------------------------------------
        # R:R
        # ----------------------------------------------------

        rr = (

            target - entry
        ) / (
            entry - stop_loss
        )


        if rr < MIN_RR:

            return None


        # ----------------------------------------------------
        # POSITION SIZE
        # ----------------------------------------------------

        maximum_loss = (

            capital
            *
            risk_percent
            /
            100

        )


        shares_by_risk = int(

            maximum_loss
            /
            risk_per_share

        )


        # ----------------------------------------------------
        # DO NOT USE MORE THAN 35% CAPITAL
        # ON ONE POSITION
        # ----------------------------------------------------

        max_capital_per_trade = (

            capital
            *
            0.35

        )


        shares_by_capital = int(

            max_capital_per_trade
            /
            entry

        )


        shares = min(

            shares_by_risk,
            shares_by_capital

        )


        if shares < 1:

            return None


        capital_required = (
            shares
            *
            entry
        )


        actual_max_loss = (
            shares
            *
            risk_per_share
        )


        expected_profit = (
            shares
            *
            (
                target - entry
            )
        )


        # ----------------------------------------------------
        # EMA DISTANCE
        # ----------------------------------------------------

        ema20_distance = (

            (
                price
                -
                last["EMA20"]
            )
            /
            last["EMA20"]
            *
            100

        )


        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        return {

            "Symbol":
                symbol,

            "Company":
                name,

            "Setup":
                "Moving Average Pullback",

            "Score":
                score,

            "Price":
                price,

            "Entry":
                entry,

            "Stop Loss":
                stop_loss,

            "Target":
                target,

            "Risk/Reward":
                rr,

            "Shares":
                shares,

            "Capital Required":
                capital_required,

            "Max Loss":
                actual_max_loss,

            "Expected Profit":
                expected_profit,

            "RSI":
                rsi,

            "Relative Volume":
                relative_volume,

            "ATR":
                atr,

            "EMA20":
                last["EMA20"],

            "EMA50":
                last["EMA50"],

            "EMA200":
                last["EMA200"],

            "EMA20 Distance %":
                ema20_distance,

            "Reasons":
                ", ".join(
                    reasons
                )

        }


    except Exception:

        return None


# ============================================================
# SCAN BUTTON
# ============================================================

st.markdown("---")

st.subheader(
    "🔎 Find Top 10 Swing Stocks"
)


if st.button(
    "🚀 Scan & Rank Top 10",
    type="primary",
    use_container_width=True
):

    rows = [
        row
        for _, row
        in scan_df.iterrows()
    ]


    results = []


    progress = st.progress(
        0
    )


    status = st.empty()


    total = len(rows)

    completed = 0


    # --------------------------------------------------------
    # THREADS
    # --------------------------------------------------------

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

        futures = [

            executor.submit(
                analyze_stock,
                row
            )

            for row in rows

        ]


        for future in as_completed(
            futures
        ):

            try:

                result = future.result()

                if result is not None:

                    results.append(
                        result
                    )

            except Exception:

                pass


            completed += 1


            progress.progress(
                completed / total
            )


            status.write(
                f"Scanning "
                f"{completed:,} / "
                f"{total:,} stocks..."
            )


    progress.empty()


    status.empty()


    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    if len(results) == 0:

        st.warning(
            "No qualifying Moving Average Pullback "
            "stocks were found."
        )

        st.session_state.results = None

    else:

        result_df = pd.DataFrame(
            results
        )


        # ----------------------------------------------------
        # SORT BY SCORE
        # ----------------------------------------------------

        result_df = (
            result_df
            .sort_values(
                [
                    "Score",
                    "Risk/Reward",
                    "Relative Volume"
                ],
                ascending=[
                    False,
                    False,
                    False
                ]
            )
            .reset_index(
                drop=True
            )
        )


        # ----------------------------------------------------
        # TOP 10
        # ----------------------------------------------------

        result_df = (
            result_df
            .head(10)
            .copy()
        )


        result_df[
            "Rank"
        ] = (
            np.arange(
                1,
                len(result_df) + 1
            )
        )


        # Put Rank first

        cols = [
            "Rank"
        ] + [
            c
            for c
            in result_df.columns
            if c != "Rank"
        ]


        result_df = (
            result_df[cols]
        )


        st.session_state.results = (
            result_df
        )


# ============================================================
# DISPLAY RESULTS
# ============================================================

if st.session_state.results is None:

    st.stop()


results = (
    st.session_state.results
    .copy()
)


# ============================================================
# TOP 10
# ============================================================

st.markdown("---")

st.header(
    "🏆 TOP 10 SWING STOCKS"
)


st.success(
    "These are the highest-scoring stocks "
    "currently matching the Moving Average "
    "Pullback strategy."
)


# ============================================================
# MAIN TABLE
# ============================================================

display_columns = [

    "Rank",

    "Symbol",

    "Company",

    "Score",

    "Price",

    "Entry",

    "Stop Loss",

    "Target",

    "Risk/Reward",

    "Shares",

    "Capital Required",

    "Max Loss",

    "Expected Profit",

    "RSI",

    "Relative Volume"

]


st.dataframe(

    results[
        display_columns
    ].round(2),

    use_container_width=True,

    hide_index=True

)


# ============================================================
# BEST STOCK
# ============================================================

best = results.iloc[0]


st.markdown("---")

st.header(
    "🥇 #1 Ranked Setup"
)


c1, c2, c3, c4, c5 = st.columns(5)


c1.metric(
    "Stock",
    best["Symbol"]
)


c2.metric(
    "Score",
    f'{best["Score"]:.0f}/100'
)


c3.metric(
    "Entry",
    f'₹{best["Entry"]:.2f}'
)


c4.metric(
    "Stop Loss",
    f'₹{best["Stop Loss"]:.2f}'
)


c5.metric(
    "Target",
    f'₹{best["Target"]:.2f}'
)


# ============================================================
# TRADE PLAN
# ============================================================

st.subheader(
    "🎯 Trade Plan"
)


trade_cols = st.columns(4)


trade_cols[0].metric(
    "Shares",
    int(best["Shares"])
)


trade_cols[1].metric(
    "Capital Required",
    f'₹{best["Capital Required"]:,.0f}'
)


trade_cols[2].metric(
    "Maximum Loss",
    f'₹{best["Max Loss"]:,.0f}'
)


trade_cols[3].metric(
    "Potential Profit",
    f'₹{best["Expected Profit"]:,.0f}'
)


st.write(
    "**Why this stock ranked #1:**"
)


st.write(
    best["Reasons"]
)


# ============================================================
# SCORE CHART
# ============================================================

st.markdown("---")

st.subheader(
    "📊 Top 10 Swing Scores"
)


chart_df = (
    results
    .sort_values(
        "Score"
    )
)


fig = px.bar(
    chart_df,
    x="Score",
    y="Symbol",
    orientation="h",
    title="Moving Average Pullback Score"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ============================================================
# RSI / VOLUME
# ============================================================

st.subheader(
    "📊 RSI vs Relative Volume"
)


fig2 = px.scatter(
    results,
    x="RSI",
    y="Relative Volume",
    size="Score",
    hover_name="Symbol",
    text="Symbol",
    title="Momentum vs Volume"
)


fig2.update_traces(
    textposition="top center"
)


st.plotly_chart(
    fig2,
    use_container_width=True
)


# ============================================================
# DOWNLOAD
# ============================================================

st.markdown("---")

csv = (
    results
    .to_csv(
        index=False
    )
    .encode(
        "utf-8"
    )
)


st.download_button(
    label="⬇️ Download Top 10",
    data=csv,
    file_name="top_10_swing_stocks.csv",
    mime="text/csv"
)


# ============================================================
# STRATEGY EXPLANATION
# ============================================================

with st.expander(
    "📚 Version 1 Strategy Rules"
):

    st.markdown(
        """
### 1. Bullish trend

The stock must generally satisfy:

**EMA20 > EMA50 > EMA200**

and price should be above the 20 EMA.

---

### 2. Moving Average Pullback

The stock should have pulled back toward the
20 EMA.

We don't want to chase a stock that is already
far above its moving average.

---

### 3. Recovery

The current price should show recovery compared
with the previous candle.

---

### 4. RSI

Preferred RSI range:

**50–70**

This attempts to avoid both weak momentum and
extremely overbought conditions.

---

### 5. Volume

Volume is compared with its recent average.

Higher relative volume gives the setup a higher score.

---

### 6. Stop Loss

Stop loss is calculated using ATR:

**Entry − (ATR × 1.5)**

---

### 7. Target

The default target is:

**2 × the amount risked**

Therefore:

**Risk : Reward = 1 : 2**

---

### 8. Position sizing

The scanner uses your account size and risk percentage.

For ₹20,000 capital and 1% risk:

**Maximum planned loss ≈ ₹200**

The number of shares is then calculated automatically.
"""
    )


# ============================================================
# IMPORTANT NOTICE
# ============================================================

st.markdown("---")

st.warning(
    """
The Top 10 list is a technical screening output,
not a guarantee that these stocks will rise.

The scanner does not place orders.

Before entering a trade, verify the chart,
liquidity, corporate announcements, market conditions,
and your own risk limits.
"""
)