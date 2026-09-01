import io
import re
import concurrent.futures

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NIFTY Stock Analyzer",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.6rem; }
    div[data-testid="stMetricValue"] { font-size: 1.35rem; }
    .app-title { display:flex; align-items:center; gap:0.6rem; margin-bottom:0; }
    .app-subtitle { color: #6b7280; margin-top:0.1rem; margin-bottom:1.2rem; }
    .rec-badge {
        display:inline-block;
        padding: 0.55rem 1.1rem;
        border-radius: 10px;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0.3rem 0 1.1rem 0;
    }
    .rec-strongbuy, .rec-buy { background-color:#e3f6e8; color:#177a3a; border:1px solid #177a3a33; }
    .rec-strongsell, .rec-sell { background-color:#fbe7e7; color:#b3261e; border:1px solid #b3261e33; }
    .rec-hold { background-color:#fff6dd; color:#8a6a00; border:1px solid #8a6a0033; }
    .section-caption { color:#6b7280; margin-top:-0.4rem; margin-bottom:1rem; }
    hr { margin: 1.1rem 0; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# NIFTY 50 STOCK LIST (fast default universe + offline fallback)
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

NSE_500_CSV_URL = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"

CAP_CATEGORIES = ["Large Cap", "Medium Cap", "Small Cap", "Micro Cap", "Nano Cap"]

# Sectoral indices on niftyindices.com — each page exposes a "Downloads >
# Index Constituent" CSV link that we scrape for live sector membership.
SECTOR_INDICES = {
    "NIFTY AUTO": "nifty-auto",
    "NIFTY BANK": "nifty-bank",
    "NIFTY CAPITAL GOODS": "nifty-capital-goods",
    "NIFTY CEMENT": "nifty-cement",
    "NIFTY CHEMICALS": "nifty-chemicals",
    "NIFTY COMMERCIAL & TRANSPORT SERVICES": "nifty-commercial---transport-services",
    "NIFTY CONSTRUCTION": "nifty-construction",
    "NIFTY CONSUMER DURABLES": "nifty-consumer-durables-index",
    "NIFTY CONSUMER SERVICES": "nifty-consumer-services",
    "NIFTY FINANCIAL SERVICES": "nifty-financial-services",
    "NIFTY FINANCIAL SERVICES 25/50": "nifty-financial-services-25-50-index",
    "NIFTY FINANCIAL SERVICES EX BANK": "nifty-financial--services-ex-bank",
    "NIFTY FMCG": "nifty-fmcg",
    "NIFTY HEALTHCARE": "nifty-healthcare-index",
    "NIFTY HOSPITALS": "nifty-hospitals",
    "NIFTY HOUSING FINANCE": "nifty-housing-finance",
    "NIFTY INSURANCE": "nifty-insurance",
    "NIFTY IT": "nifty-it",
    "NIFTY MEDIA": "nifty-media",
    "NIFTY METAL": "nifty-metal",
    "NIFTY NBFC": "nifty-nbfc",
    "NIFTY OIL AND GAS": "nifty-oil-and-gas-index",
    "NIFTY PHARMA": "nifty-pharma",
    "NIFTY POWER": "nifty-power",
    "NIFTY PRIVATE BANK": "nifty-private-bank",
    "NIFTY PSU BANK": "nifty-psu-bank",
    "NIFTY REALTY": "nifty-realty",
    "NIFTY REITS & REALTY": "nifty-reits---realty",
    "NIFTY RETAIL": "nifty-retail",
    "NIFTY TELECOMMUNICATIONS": "nifty-telecommunications",
    "NIFTY500 HEALTHCARE": "nifty500-healthcare",
    "NIFTY MIDSMALL FINANCIAL SERVICES": "nifty-midsmall--financial-services",
    "NIFTY MIDSMALL HEALTHCARE": "nifty-midsmallhealthcare",
    "NIFTY MIDSMALL IT & TELECOM": "nifty-midsmall--it-telecom",
}

# Broad-based indices on niftyindices.com, ordered roughly small -> large
# universe. Each maps to (category_path, url_slug) used to build
# https://niftyindices.com/indices/equity/{category_path}/{slug}
# "NIFTY TOTAL MARKET" is the broadest — NSE's closest equivalent to
# "all tradeable stocks" (750+ names spanning large/mid/small/micro cap).
BROAD_INDICES = {
    "NIFTY 50": ("broad-based-indices", "nifty--50"),
    "NIFTY NEXT 50": ("broad-based-indices", "nifty-next-50"),
    "NIFTY 100": ("broad-based-indices", "nifty-100"),
    "NIFTY NEXT 100": ("broad-based-indices", "nifty-next-100"),
    "NIFTY 200": ("broad-based-indices", "nifty-200"),
    "NIFTY 500": ("broad-based-indices", "nifty-500"),
    "NIFTY LARGEMIDCAP 250": ("broad-based-indices", "nifty-largemidcap-250"),
    "NIFTY MIDCAP 50": ("broad-based-indices", "nifty-midcap-50"),
    "NIFTY MIDCAP 100": ("broad-based-indices", "nifty-midcap-100"),
    "NIFTY MIDCAP 150": ("broad-based-indices", "nifty-midcap-150"),
    "NIFTY MIDSMALLCAP 400": ("broad-based-indices", "nifty-midsmallcap-400"),
    "NIFTY SMALLCAP 50": ("broad-based-indices", "niftysmallcap50"),
    "NIFTY SMALLCAP 100": ("broad-based-indices", "nifty-smallcap-100"),
    "NIFTY SMALLCAP 250": ("broad-based-indices", "niftysmallcap250"),
    "NIFTY SMALLCAP 500": ("broad-based-indices", "nifty-smallcap-500"),
    "NIFTY MICROCAP 250": ("broad-based-indices", "nifty-microcap-250"),
    "NIFTY TOTAL MARKET (ALL STOCKS)": ("broad-based-indices", "nifty-total-market"),
}

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0 Safari/537.36"
    )
}

# ============================================================
# SHARED INDICATOR / SCORING FUNCTIONS
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

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.copy()

    data["EMA_9"] = data["Close"].ewm(span=9, adjust=False).mean()
    data["EMA_20"] = data["Close"].ewm(span=20, adjust=False).mean()
    data["EMA_100"] = data["Close"].ewm(span=100, adjust=False).mean()
    data["SMA_200"] = data["Close"].rolling(window=200).mean()

    delta = data["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))

    ema_12 = data["Close"].ewm(span=12, adjust=False).mean()
    ema_26 = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = ema_12 - ema_26
    data["MACD_SIGNAL"] = data["MACD"].ewm(span=9, adjust=False).mean()
    data["MACD_HIST"] = data["MACD"] - data["MACD_SIGNAL"]

    data["Volume_Avg_20"] = data["Volume"].rolling(window=20).mean()
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

    if ema9 > ema20:
        score += 1; signals.append("EMA 9 > EMA 20")
    else:
        score -= 1; signals.append("EMA 9 < EMA 20")

    if price > ema20:
        score += 1; signals.append("Price above EMA 20")
    else:
        score -= 1; signals.append("Price below EMA 20")

    if price > ema100:
        score += 1; signals.append("Price above EMA 100")
    else:
        score -= 1; signals.append("Price below EMA 100")

    if price > sma200:
        score += 2; signals.append("Price above SMA 200")
    else:
        score -= 2; signals.append("Price below SMA 200")

    if 50 <= rsi <= 70:
        score += 1; signals.append("RSI bullish")
    elif rsi < 30:
        score += 1; signals.append("RSI oversold")
    elif rsi > 70:
        score -= 1; signals.append("RSI overbought")
    else:
        signals.append("RSI neutral")

    if macd > macd_signal:
        score += 1; signals.append("MACD bullish")
    else:
        score -= 1; signals.append("MACD bearish")

    if volume > volume_avg:
        score += 1; signals.append("Volume above 20-day average")
    else:
        signals.append("Volume below 20-day average")

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


def rec_css_class(recommendation):
    if "STRONG BUY" in recommendation or recommendation.endswith("BUY"):
        return "rec-buy"
    if "SELL" in recommendation:
        return "rec-sell"
    return "rec-hold"


def get_short_term_trend(row):
    price = row["Close"]
    if price > row["EMA_9"] and row["EMA_9"] > row["EMA_20"]:
        return "🟢 Bullish"
    elif price < row["EMA_9"] and row["EMA_9"] < row["EMA_20"]:
        return "🔴 Bearish"
    return "🟡 Neutral"


def get_long_term_trend(row):
    price = row["Close"]
    if price > row["EMA_100"] and price > row["SMA_200"] and row["EMA_100"] > row["SMA_200"]:
        return "🟢 Strong Bullish"
    elif price > row["SMA_200"] and row["EMA_100"] > row["SMA_200"]:
        return "🟢 Bullish"
    elif price < row["SMA_200"] and row["EMA_100"] < row["SMA_200"]:
        return "🔴 Bearish"
    return "🟡 Neutral"


# ============================================================
# FUNDAMENTALS (quarterly revenue, profit/loss, debt)
# ============================================================

def _find_row(df, candidates):
    """Finds a row in a yfinance financial statement DataFrame by trying
    exact matches first, then partial (case-insensitive) matches."""
    if df is None or df.empty:
        return None
    index_str = {str(idx).strip().lower(): idx for idx in df.index}
    for cand in candidates:
        key = cand.strip().lower()
        if key in index_str:
            return df.loc[index_str[key]]
    for cand in candidates:
        key = cand.strip().lower()
        for idx_lower, idx_orig in index_str.items():
            if key in idx_lower:
                return df.loc[idx_orig]
    return None


@st.cache_data(ttl=21600, show_spinner=False)
def get_fundamentals(symbol):
    """
    Pulls quarterly financial statements from yfinance and returns a tidy
    quarter-by-quarter DataFrame (oldest -> newest) plus a dict of
    trailing ratios from ticker.info. Returns (df, info, error_message).
    """
    ticker = yf.Ticker(symbol)

    qtr_income = pd.DataFrame()
    qtr_balance = pd.DataFrame()
    info = {}

    try:
        qtr_income = ticker.quarterly_income_stmt
        if qtr_income is None or qtr_income.empty:
            qtr_income = ticker.quarterly_financials
    except Exception:
        try:
            qtr_income = ticker.quarterly_financials
        except Exception:
            qtr_income = pd.DataFrame()

    try:
        qtr_balance = ticker.quarterly_balance_sheet
    except Exception:
        qtr_balance = pd.DataFrame()

    try:
        info = ticker.info or {}
    except Exception:
        info = {}

    if (qtr_income is None or qtr_income.empty) and (qtr_balance is None or qtr_balance.empty):
        return None, info, "No quarterly financial statements are available for this stock on Yahoo Finance."

    revenue = _find_row(qtr_income, ["Total Revenue", "Operating Revenue"])
    net_income = _find_row(qtr_income, [
        "Net Income", "Net Income Common Stockholders",
        "Net Income Applicable To Common Shares", "Net Income Continuous Operations"
    ])
    total_debt = _find_row(qtr_balance, ["Total Debt"])
    if total_debt is None:
        long_debt = _find_row(qtr_balance, ["Long Term Debt"])
        short_debt = _find_row(qtr_balance, ["Current Debt", "Short Long Term Debt"])
        if long_debt is not None:
            total_debt = long_debt.add(short_debt, fill_value=0) if short_debt is not None else long_debt
    equity = _find_row(qtr_balance, [
        "Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"
    ])

    series_map = {
        "Revenue": revenue,
        "Net Profit/Loss": net_income,
        "Total Debt": total_debt,
        "Equity": equity,
    }

    available = {k: v for k, v in series_map.items() if v is not None and not v.empty}
    if not available:
        return None, info, "Could not find Revenue, Net Income, Debt or Equity line items for this stock."

    combined = pd.DataFrame(available)
    combined.index = pd.to_datetime(combined.index)
    combined = combined.sort_index()  # oldest -> newest
    combined = combined.dropna(how="all")

    if "Revenue" in combined.columns:
        combined["Revenue QoQ %"] = combined["Revenue"].pct_change() * 100
        combined["Revenue YoY %"] = combined["Revenue"].pct_change(periods=4) * 100
    if "Net Profit/Loss" in combined.columns:
        combined["Net Profit QoQ %"] = combined["Net Profit/Loss"].pct_change() * 100
        combined["Net Profit YoY %"] = combined["Net Profit/Loss"].pct_change(periods=4) * 100
    if "Total Debt" in combined.columns and "Equity" in combined.columns:
        combined["Debt to Equity"] = combined["Total Debt"] / combined["Equity"].replace(0, np.nan)

    return combined, info, None


def format_inr_crore(value):
    if pd.isna(value):
        return "N/A"
    crores = value / 1e7
    if abs(crores) >= 1e5:
        return f"₹{crores / 1e5:,.2f} Lakh Cr"
    return f"₹{crores:,.1f} Cr"


def format_pct(value):
    if pd.isna(value):
        return "—"
    return f"{value:+.1f}%"


# ============================================================
# UNIVERSE / CONSTITUENT LOOKUPS
# ============================================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_nifty500_list():
    """Live NIFTY 500 constituents from NSE archives; falls back to NIFTY 50."""
    try:
        resp = requests.get(NSE_500_CSV_URL, headers=REQUEST_HEADERS, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        df.columns = [c.strip() for c in df.columns]
        df["Symbol"] = df["Symbol"].astype(str).str.strip()
        df["YF_SYMBOL"] = df["Symbol"] + ".NS"
        df["Source"] = "NIFTY 500 (live)"
        return df[["Company Name", "Symbol", "YF_SYMBOL", "Source"]]
    except Exception as e:
        st.warning(
            f"Could not fetch the live NIFTY 500 list from NSE ({e}). "
            "Falling back to the NIFTY 50 list."
        )
        fallback = pd.DataFrame({
            "Company Name": list(NIFTY_50.keys()),
            "Symbol": [v.replace(".NS", "") for v in NIFTY_50.values()],
            "YF_SYMBOL": list(NIFTY_50.values()),
            "Source": "NIFTY 50 (fallback)"
        })
        return fallback


@st.cache_data(ttl=86400, show_spinner=False)
def _scrape_index_constituents(category_path, slug):
    """
    Scrapes a niftyindices.com index page (sectoral or broad-based) for the
    'Downloads > Index Constituent' CSV link and returns its stock list.
    This is the generic engine behind get_sector_constituents() and
    get_index_constituents().
    """
    page_url = f"https://niftyindices.com/indices/equity/{category_path}/{slug}"
    resp = requests.get(page_url, headers=REQUEST_HEADERS, timeout=15)
    resp.raise_for_status()

    match = re.search(r'href="([^"]*IndexConstituent/ind_[^"]+?\.csv)"', resp.text, re.IGNORECASE)
    if not match:
        raise ValueError("Could not locate the Index Constituent CSV link on the index page.")

    csv_url = match.group(1)
    if csv_url.startswith("//"):
        csv_url = "https:" + csv_url
    elif csv_url.startswith("/"):
        csv_url = "https://niftyindices.com" + csv_url

    csv_resp = requests.get(csv_url, headers=REQUEST_HEADERS, timeout=15)
    csv_resp.raise_for_status()

    df = pd.read_csv(io.StringIO(csv_resp.text))
    df.columns = [c.strip() for c in df.columns]
    df["Symbol"] = df["Symbol"].astype(str).str.strip()
    df["YF_SYMBOL"] = df["Symbol"] + ".NS"
    return df[["Company Name", "Symbol", "YF_SYMBOL"]]


def get_sector_constituents(sector_slug):
    return _scrape_index_constituents("sectoral-indices", sector_slug)


@st.cache_data(ttl=86400, show_spinner=False)
def get_index_constituents(index_name):
    """
    Returns constituents for any registered broad-based index. NIFTY 500
    uses the fast, well-tested NSE archives CSV; every other index
    (NIFTY 50, 100, 200, Next 50, midcap/smallcap/microcap tiers, and
    Total Market) is scraped live from its niftyindices.com page.
    Falls back to the static NIFTY 50 list if a fetch fails.
    """
    if index_name == "NIFTY 500":
        df = get_nifty500_list()
        return df[["Company Name", "Symbol", "YF_SYMBOL"]], df["Source"].iloc[0] if not df.empty else "Unknown"

    if index_name not in BROAD_INDICES:
        raise ValueError(f"Unknown index: {index_name}")

    category_path, slug = BROAD_INDICES[index_name]
    try:
        df = _scrape_index_constituents(category_path, slug)
        return df, f"{index_name} (live)"
    except Exception as e:
        st.warning(f"Could not fetch {index_name} from niftyindices.com ({e}). Falling back to NIFTY 50.")
        fallback = pd.DataFrame({
            "Company Name": list(NIFTY_50.keys()),
            "Symbol": [v.replace(".NS", "") for v in NIFTY_50.values()],
            "YF_SYMBOL": list(NIFTY_50.values()),
        })
        return fallback, "NIFTY 50 (fallback)"


def _fetch_market_cap(symbol):
    try:
        ticker = yf.Ticker(symbol)
        mcap = None
        try:
            mcap = ticker.fast_info.get("market_cap")
        except Exception:
            mcap = None
        if not mcap:
            try:
                mcap = ticker.info.get("marketCap")
            except Exception:
                mcap = None
        return symbol, mcap
    except Exception:
        return symbol, None


@st.cache_data(ttl=43200, show_spinner=False)
def get_market_caps(symbols):
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(_fetch_market_cap, s): s for s in symbols}
        for future in concurrent.futures.as_completed(futures):
            symbol, mcap = future.result()
            results[symbol] = mcap
    return results


def categorize_by_market_cap(universe_df, market_caps):
    df = universe_df.copy()
    df["MarketCap"] = df["YF_SYMBOL"].map(market_caps)
    df = df.dropna(subset=["MarketCap"])
    df = df.sort_values("MarketCap", ascending=False).reset_index(drop=True)

    n = len(df)
    if n == 0:
        df["Category"] = []
        return df

    bucket_size = n / 5.0

    def bucket_label(rank):
        idx = min(int(rank // bucket_size), 4)
        return CAP_CATEGORIES[idx]

    df["Category"] = [bucket_label(i) for i in range(n)]
    return df


def _score_symbol(symbol, period="1y"):
    """Technical score using n-1: the previous COMPLETED trading day."""
    try:
        data = get_stock_data(symbol, period)
        if data.empty:
            return None

        data = data.dropna(subset=[
            "EMA_9", "EMA_20", "EMA_100", "SMA_200",
            "RSI", "MACD", "MACD_SIGNAL", "Volume_Avg_20"
        ])

        if len(data) < 2:
            return None

        ref_row = data.iloc[-2]
        score, recommendation, signals = calculate_score(ref_row)

        return {
            "Symbol": symbol,
            "Reference Date": ref_row.name.date(),
            "Close": float(ref_row["Close"]),
            "RSI": float(ref_row["RSI"]),
            "Score": score,
            "Recommendation": recommendation,
        }
    except Exception:
        return None


@st.cache_data(ttl=21600, show_spinner=False)
def build_screener_scores(symbols, period="1y"):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(_score_symbol, s, period): s for s in symbols}
        for future in concurrent.futures.as_completed(futures):
            r = future.result()
            if r:
                results.append(r)
    return pd.DataFrame(results)


def format_market_cap(value):
    if pd.isna(value):
        return "N/A"
    crores = value / 1e7
    if crores >= 1e5:
        return f"₹{crores / 1e5:,.2f} Lakh Cr"
    return f"₹{crores:,.0f} Cr"


def render_top10_table(df, top_n=10):
    if df.empty:
        st.info("No data available.")
        return

    display = df.sort_values("Score", ascending=False).head(top_n).reset_index(drop=True).copy()

    cols = ["Company Name", "Symbol", "Close", "RSI", "Score", "Recommendation", "Reference Date"]
    if "MarketCap" in display.columns:
        display["Market Cap"] = display["MarketCap"].apply(format_market_cap)
        cols = ["Company Name", "Symbol", "Market Cap", "Close", "RSI", "Score", "Recommendation", "Reference Date"]

    display["Close"] = display["Close"].apply(lambda x: f"₹{x:,.2f}")
    display["RSI"] = display["RSI"].apply(lambda x: f"{x:.1f}")
    display["Score"] = display["Score"].apply(lambda x: f"{x}/8")
    display = display.rename(columns={"Close": "Price (n-1)"})
    cols = [c if c != "Close" else "Price (n-1)" for c in cols]

    display.index = display.index + 1
    st.dataframe(display[cols], use_container_width=True)


# ============================================================
# HEADER (rendered once)
# ============================================================

st.markdown('<h1 class="app-title">📈 NIFTY Stock Analyzer</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="app-subtitle">Technical, trend and fundamentals analysis for any NIFTY 50/500 stock, '
    'plus a Market-Cap and Sector screener</p>',
    unsafe_allow_html=True
)

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.header("Navigate")
mode = st.sidebar.radio(
    "Choose a view",
    ["🔍 Single Stock Analyzer", "🏆 Screener (Top 10)"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# ============================================================
# MODE 1: SINGLE STOCK ANALYZER
# ============================================================

if mode == "🔍 Single Stock Analyzer":

    st.sidebar.subheader("Settings")

    universe_choice = st.sidebar.selectbox(
        "Universe",
        ["NIFTY 50"] + [k for k in BROAD_INDICES.keys() if k != "NIFTY 50"],
        help="NIFTY TOTAL MARKET is the broadest option — closest to 'all tradeable NSE stocks'."
    )

    if universe_choice == "NIFTY 50":
        stock_options = NIFTY_50
    else:
        with st.spinner(f"Loading {universe_choice} list..."):
            index_df, _source = get_index_constituents(universe_choice)
        stock_options = dict(zip(index_df["Company Name"], index_df["YF_SYMBOL"]))

    stock_name = st.sidebar.selectbox(f"Select {universe_choice} Stock", sorted(stock_options.keys()))
    symbol = stock_options[stock_name]

    period = st.sidebar.selectbox("Historical Period", ["1y", "2y", "5y", "10y"], index=1)

    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Indicators used**\n\n"
        "EMA 9 • EMA 20 • EMA 100 • SMA 200 • RSI • MACD • Volume • "
        "Short-term trend • Long-term trend • Technical score"
    )

    with st.spinner(f"Loading {stock_name} data..."):
        data = get_stock_data(symbol, period)

    if data.empty:
        st.error("Unable to download stock data. Please try again.")
        st.stop()

    data = data.dropna(subset=[
        "EMA_9", "EMA_20", "EMA_100", "SMA_200",
        "RSI", "MACD", "MACD_SIGNAL", "Volume_Avg_20"
    ])

    if data.empty:
        st.error("Not enough historical data to calculate all indicators.")
        st.stop()

    latest = data.iloc[-1]
    price = float(latest["Close"])
    previous_close = float(data.iloc[-2]["Close"])
    daily_change = ((price - previous_close) / previous_close) * 100

    score, recommendation, signals = calculate_score(latest)
    short_term = get_short_term_trend(latest)
    long_term = get_long_term_trend(latest)

    st.subheader(f"{stock_name}  ·  {symbol}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Price", f"₹{price:,.2f}", f"{daily_change:+.2f}%")
    c2.metric("RSI", f"{latest['RSI']:.2f}")
    c3.metric("Technical Score", f"{score}/8")
    c4.metric("Short-Term", short_term)
    c5.metric("Long-Term", long_term)

    st.markdown(
        f'<div class="rec-badge {rec_css_class(recommendation)}">{recommendation} '
        f'&nbsp;·&nbsp; Score {score}/8</div>',
        unsafe_allow_html=True
    )

    tab_chart, tab_indicators, tab_trend, tab_fundamentals, tab_data = st.tabs(
        ["📊 Charts", "📌 Indicators & Signals", "📈 Trend Analysis", "💰 Fundamentals", "📋 Recent Data"]
    )

    with tab_chart:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Price", mode="lines"))
        fig.add_trace(go.Scatter(x=data.index, y=data["EMA_9"], name="EMA 9", mode="lines"))
        fig.add_trace(go.Scatter(x=data.index, y=data["EMA_20"], name="EMA 20", mode="lines"))
        fig.add_trace(go.Scatter(x=data.index, y=data["EMA_100"], name="EMA 100", mode="lines"))
        fig.add_trace(go.Scatter(x=data.index, y=data["SMA_200"], name="SMA 200", mode="lines"))
        fig.update_layout(height=520, xaxis_title="Date", yaxis_title="Price (₹)", hovermode="x unified",
                           margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)

        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=data.index, y=data["RSI"], name="RSI", mode="lines"))
        fig_rsi.add_hline(y=70, line_dash="dash")
        fig_rsi.add_hline(y=30, line_dash="dash")
        fig_rsi.add_hline(y=50, line_dash="dot")
        fig_rsi.update_layout(height=280, yaxis_title="RSI", xaxis_title="Date", margin=dict(t=20))
        st.plotly_chart(fig_rsi, use_container_width=True)

        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=data.index, y=data["MACD"], name="MACD", mode="lines"))
        fig_macd.add_trace(go.Scatter(x=data.index, y=data["MACD_SIGNAL"], name="Signal", mode="lines"))
        fig_macd.add_bar(x=data.index, y=data["MACD_HIST"], name="Histogram")
        fig_macd.update_layout(height=320, xaxis_title="Date", yaxis_title="MACD", margin=dict(t=20))
        st.plotly_chart(fig_macd, use_container_width=True)

        fig_volume = go.Figure()
        fig_volume.add_trace(go.Bar(x=data.index, y=data["Volume"], name="Volume"))
        fig_volume.add_trace(go.Scatter(x=data.index, y=data["Volume_Avg_20"], name="20-Day Avg Volume", mode="lines"))
        fig_volume.update_layout(height=320, xaxis_title="Date", yaxis_title="Volume", margin=dict(t=20))
        st.plotly_chart(fig_volume, use_container_width=True)

    with tab_indicators:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Current Indicator Values**")
            indicator_df = pd.DataFrame({
                "Indicator": [
                    "Current Price", "EMA 9", "EMA 20", "EMA 100", "SMA 200",
                    "RSI", "MACD", "MACD Signal", "MACD Histogram",
                    "Volume", "20-Day Avg Volume"
                ],
                "Value": [
                    price, latest["EMA_9"], latest["EMA_20"], latest["EMA_100"], latest["SMA_200"],
                    latest["RSI"], latest["MACD"], latest["MACD_SIGNAL"], latest["MACD_HIST"],
                    latest["Volume"], latest["Volume_Avg_20"]
                ]
            })
            indicator_df["Value"] = indicator_df["Value"].apply(lambda x: f"{x:,.2f}")
            st.dataframe(indicator_df, use_container_width=True, hide_index=True)

        with col_b:
            st.markdown("**Technical Signals**")
            st.dataframe(pd.DataFrame({"Signal": signals}), use_container_width=True, hide_index=True)

    with tab_trend:
        trend_col1, trend_col2 = st.columns(2)
        with trend_col1:
            st.markdown("**Short-Term** — EMA 9, EMA 20, RSI, MACD")
            st.caption("Turns more bullish when price > EMA 9 > EMA 20.")
            st.info(f"Current Short-Term Trend: **{short_term}**")
        with trend_col2:
            st.markdown("**Long-Term** — EMA 100, SMA 200, Price")
            st.caption("Stronger when price stays above the 200-day SMA and EMA 100 > SMA 200.")
            st.info(f"Current Long-Term Trend: **{long_term}**")

    with tab_fundamentals:
        with st.spinner("Loading quarterly financials..."):
            fundamentals, fin_info, fund_error = get_fundamentals(symbol)

        if fund_error:
            st.warning(fund_error)
        else:
            latest_q = fundamentals.iloc[-1]
            quarter_label = fundamentals.index[-1].strftime("%b %Y")

            fcol1, fcol2, fcol3, fcol4 = st.columns(4)

            if "Revenue" in fundamentals.columns:
                fcol1.metric(
                    f"Revenue ({quarter_label})",
                    format_inr_crore(latest_q.get("Revenue")),
                    format_pct(latest_q.get("Revenue QoQ %"))
                )
            if "Net Profit/Loss" in fundamentals.columns:
                net_val = latest_q.get("Net Profit/Loss")
                label = "Net Profit" if pd.notna(net_val) and net_val >= 0 else "Net Loss"
                fcol2.metric(
                    f"{label} ({quarter_label})",
                    format_inr_crore(net_val),
                    format_pct(latest_q.get("Net Profit QoQ %"))
                )
            if "Total Debt" in fundamentals.columns:
                fcol3.metric(f"Total Debt ({quarter_label})", format_inr_crore(latest_q.get("Total Debt")))
            if "Debt to Equity" in fundamentals.columns:
                dte = latest_q.get("Debt to Equity")
                fcol4.metric("Debt to Equity", f"{dte:.2f}" if pd.notna(dte) else "N/A")

            st.caption(
                "QoQ = change vs. the previous quarter · YoY = change vs. the same quarter last year. "
                "Figures are as reported to exchanges via Yahoo Finance and may lag the latest results."
            )

            if "Revenue" in fundamentals.columns:
                st.markdown("**Quarterly Revenue (Sales)**")
                fig_rev = go.Figure()
                fig_rev.add_bar(
                    x=fundamentals.index, y=fundamentals["Revenue"] / 1e7, name="Revenue (₹ Cr)"
                )
                if "Revenue QoQ %" in fundamentals.columns:
                    fig_rev.add_trace(go.Scatter(
                        x=fundamentals.index, y=fundamentals["Revenue QoQ %"],
                        name="QoQ Growth %", mode="lines+markers", yaxis="y2"
                    ))
                fig_rev.update_layout(
                    height=340, margin=dict(t=20),
                    yaxis=dict(title="₹ Crore"),
                    yaxis2=dict(title="QoQ %", overlaying="y", side="right"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02)
                )
                st.plotly_chart(fig_rev, use_container_width=True)

            if "Net Profit/Loss" in fundamentals.columns:
                st.markdown("**Quarterly Net Profit / Loss**")
                colors = ["#177a3a" if v >= 0 else "#b3261e" for v in fundamentals["Net Profit/Loss"].fillna(0)]
                fig_np = go.Figure()
                fig_np.add_bar(
                    x=fundamentals.index, y=fundamentals["Net Profit/Loss"] / 1e7,
                    name="Net Profit/Loss (₹ Cr)", marker_color=colors
                )
                fig_np.update_layout(height=340, margin=dict(t=20), yaxis_title="₹ Crore")
                st.plotly_chart(fig_np, use_container_width=True)

            if "Total Debt" in fundamentals.columns:
                st.markdown("**Total Debt Trend**")
                fig_debt = go.Figure()
                fig_debt.add_trace(go.Scatter(
                    x=fundamentals.index, y=fundamentals["Total Debt"] / 1e7,
                    name="Total Debt (₹ Cr)", mode="lines+markers", fill="tozeroy"
                ))
                fig_debt.update_layout(height=300, margin=dict(t=20), yaxis_title="₹ Crore")
                st.plotly_chart(fig_debt, use_container_width=True)

            st.markdown("**Quarter-by-Quarter Summary**")
            summary = fundamentals.copy()
            summary.index = summary.index.strftime("%b %Y")

            for money_col in ["Revenue", "Net Profit/Loss", "Total Debt", "Equity"]:
                if money_col in summary.columns:
                    summary[money_col] = summary[money_col].apply(format_inr_crore)
            for pct_col in ["Revenue QoQ %", "Revenue YoY %", "Net Profit QoQ %", "Net Profit YoY %"]:
                if pct_col in summary.columns:
                    summary[pct_col] = summary[pct_col].apply(format_pct)
            if "Debt to Equity" in summary.columns:
                summary["Debt to Equity"] = summary["Debt to Equity"].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else "N/A"
                )

            st.dataframe(summary.iloc[::-1], use_container_width=True)

            with st.expander("📎 Trailing ratios (from Yahoo Finance)"):
                ratio_rows = {
                    "Trailing P/E": fin_info.get("trailingPE"),
                    "Price to Book": fin_info.get("priceToBook"),
                    "Return on Equity (ROE)": fin_info.get("returnOnEquity"),
                    "Profit Margin": fin_info.get("profitMargins"),
                    "Debt to Equity (trailing)": fin_info.get("debtToEquity"),
                    "Revenue Growth (YoY, trailing)": fin_info.get("revenueGrowth"),
                    "Earnings Growth (YoY, trailing)": fin_info.get("earningsGrowth"),
                }
                pct_metrics = {"Return on Equity (ROE)", "Profit Margin", "Revenue Growth (YoY, trailing)", "Earnings Growth (YoY, trailing)"}

                def _fmt_ratio(name, val):
                    if val is None or not isinstance(val, (int, float)):
                        return "N/A"
                    return f"{val:.2%}" if name in pct_metrics else f"{val:.2f}"

                ratio_df = pd.DataFrame({
                    "Metric": list(ratio_rows.keys()),
                    "Value": [_fmt_ratio(k, v) for k, v in ratio_rows.items()]
                })
                st.dataframe(ratio_df, use_container_width=True, hide_index=True)

    with tab_data:
        display_columns = ["Close", "EMA_9", "EMA_20", "EMA_100", "SMA_200", "RSI", "MACD", "MACD_SIGNAL", "Volume"]
        recent = data[display_columns].tail(20).copy().round(2)
        st.dataframe(recent, use_container_width=True)

    st.markdown("---")
    st.caption(
        "⚠️ This application is an analytical tool and not financial advice. "
        "Technical indicators can produce false signals. Always consider valuation, "
        "financial statements, sector conditions, market conditions, risk tolerance "
        "and your investment horizon before making an investment."
    )

# ============================================================
# MODE 2: SCREENER (Market Cap or Sector)
# ============================================================

else:

    st.sidebar.subheader("Settings")

    group_by = st.sidebar.radio("Group by", ["Market Cap", "Sector"])

    screener_period = st.sidebar.selectbox(
        "History window for indicators",
        ["6mo", "1y", "2y"],
        index=1,
        help="Needs ~200 trading days of history for the SMA 200 to be valid."
    )

    if group_by == "Sector":
        sector_name = st.sidebar.selectbox("Select Sector", sorted(SECTOR_INDICES.keys()))
    else:
        cap_universe_choice = st.sidebar.selectbox(
            "Universe to screen",
            ["NIFTY 500"] + [k for k in BROAD_INDICES.keys() if k != "NIFTY 500"],
            help="NIFTY TOTAL MARKET is the broadest option — closest to 'all tradeable NSE stocks', "
                 "but scoring 750+ stocks takes longer."
        )

    st.sidebar.markdown("---")

    st.subheader(f"🏆 Top 10 by {group_by}")
    st.markdown(
        '<p class="section-caption">Ranked by technical score computed from the previous '
        "completed trading day (n-1), so today's still-forming candle is never used.</p>",
        unsafe_allow_html=True
    )

    build_clicked = st.button("🔍 Build / Refresh Screener", type="primary")

    # ---------------- MARKET CAP MODE ----------------
    if group_by == "Market Cap":

        cap_state_key = f"cap_screener_df::{cap_universe_choice}"

        if cap_state_key not in st.session_state:
            st.session_state[cap_state_key] = None
            st.session_state[f"{cap_state_key}::source"] = None

        if build_clicked or st.session_state[cap_state_key] is None:
            with st.spinner(f"Fetching {cap_universe_choice} constituent list..."):
                universe, universe_source = get_index_constituents(cap_universe_choice)
            st.session_state[f"{cap_state_key}::source"] = universe_source

            with st.spinner(f"Fetching market caps for {len(universe)} stocks..."):
                market_caps = get_market_caps(tuple(universe["YF_SYMBOL"].tolist()))

            categorized = categorize_by_market_cap(universe, market_caps)

            if categorized.empty:
                st.error("Could not retrieve market cap data. Yahoo Finance may be unreachable from this network.")
                st.session_state[cap_state_key] = pd.DataFrame()
            else:
                with st.spinner(f"Scoring {len(categorized)} stocks using the previous trading day..."):
                    scores_df = build_screener_scores(tuple(categorized["YF_SYMBOL"].tolist()), period=screener_period)

                if scores_df.empty:
                    st.error("Could not compute technical scores for any stock.")
                    st.session_state[cap_state_key] = pd.DataFrame()
                else:
                    merged = categorized.merge(
                        scores_df, left_on="YF_SYMBOL", right_on="Symbol",
                        how="inner", suffixes=("", "_score")
                    )
                    st.session_state[cap_state_key] = merged

        merged = st.session_state[cap_state_key]

        if merged is not None and not merged.empty:
            st.caption(f"Universe: {st.session_state[f'{cap_state_key}::source']} • {len(merged)} stocks scored")

            cap_tabs = st.tabs(["🟦 Large", "🟩 Medium", "🟨 Small", "🟧 Micro", "🟥 Nano"])
            for tab, cap_name in zip(cap_tabs, CAP_CATEGORIES):
                with tab:
                    subset = merged[merged["Category"] == cap_name]
                    st.caption(f"{len(subset)} stocks in this bucket")
                    render_top10_table(subset)

        elif merged is not None and merged.empty:
            st.warning("No results yet — try 'Build / Refresh Screener' again.")
        else:
            st.info("Click **'Build / Refresh Screener'** to fetch NIFTY 500, pull market caps, and score every stock.")

        st.markdown("---")
        st.caption(
            "⚠️ Buckets are relative rank buckets across the NIFTY 500 (top 20% by market cap = "
            "Large Cap, next 20% = Medium Cap, and so on) — an informal 5-way split of SEBI's "
            "3-tier system, since NIFTY 500 alone doesn't contain enough distinct nano-cap names. "
            "Not financial advice."
        )

    # ---------------- SECTOR MODE ----------------
    else:

        sector_key = f"sector_screener_df::{sector_name}"

        if sector_key not in st.session_state:
            st.session_state[sector_key] = None

        if build_clicked or st.session_state[sector_key] is None:
            try:
                with st.spinner(f"Fetching {sector_name} constituents from niftyindices.com..."):
                    sector_df = get_sector_constituents(SECTOR_INDICES[sector_name])

                with st.spinner(f"Scoring {len(sector_df)} stocks using the previous trading day..."):
                    scores_df = build_screener_scores(tuple(sector_df["YF_SYMBOL"].tolist()), period=screener_period)

                if scores_df.empty:
                    st.error("Could not compute technical scores for this sector.")
                    st.session_state[sector_key] = pd.DataFrame()
                else:
                    merged = sector_df.merge(
                        scores_df, left_on="YF_SYMBOL", right_on="Symbol",
                        how="inner", suffixes=("", "_score")
                    )
                    st.session_state[sector_key] = merged

            except Exception as e:
                st.error(
                    f"Could not fetch {sector_name} constituents ({e}). "
                    "niftyindices.com may be unreachable from this network, or the page layout changed."
                )
                st.session_state[sector_key] = pd.DataFrame()

        sector_df_result = st.session_state[sector_key]

        if sector_df_result is not None and not sector_df_result.empty:
            st.caption(f"{sector_name} • {len(sector_df_result)} stocks scored")
            render_top10_table(sector_df_result)
        elif sector_df_result is not None and sector_df_result.empty:
            st.warning("No results yet — try 'Build / Refresh Screener' again.")
        else:
            st.info(f"Click **'Build / Refresh Screener'** to fetch and score {sector_name} constituents.")

        st.markdown("---")
        st.caption(
            "⚠️ Sector membership is pulled live from each index's 'Index Constituent' download "
            "on niftyindices.com. Not financial advice."
        )