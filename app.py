import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
import requests

from main import buy_sell, detect_trend, moving_average, signal, signal_accuracy, trend_strength, volatility

CRYPTO_SYMBOLS = {
    "Bitcoin (BTC)": "BTCUSDT",
    "Ethereum (ETH)": "ETHUSDT",
    "Binance Coin (BNB)": "BNBUSDT",
    "Solana (SOL)": "SOLUSDT",
}

STOCK_SYMBOLS = [
    "TSLA",
    "AAPL",
    "MSFT",
    "GOOGL",
    "NVDA"
] 

PSX_SYMBOLS = [
    "PPL.KA",
    "HUBC.KA", 
    "HBL.KA",
    "UBL.KA",
    "ENGRO.KA"
]

# Make the dashboard use the full browser width
st.set_page_config(
    page_title="Market Analysis Dashboard",
    layout="wide",
)


def fetch_ohlc_data(market: str, symbol: str, interval: str = "1d") -> pd.DataFrame:
    """Fetch OHLC data for stocks/PSX (Yahoo Finance) and crypto (Binance)."""
    if market == "Stock" or market == "PSX":
        df = yf.download(symbol, period="max", interval=interval)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        df = df.dropna().reset_index()
        df = df.rename(columns={"Date": "time", "Datetime": "time"})
        return df[["time", "Open", "High", "Low", "Close"]]
    else:
        # Binance API
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": 1000}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data, columns=["time", "Open", "High", "Low", "Close", "Volume", "CloseTime", "QuoteVolume", "Trades", "TakerBase", "TakerQuote", "Ignore"])
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df = df[["time", "Open", "High", "Low", "Close"]].astype({"Open": float, "High": float, "Low": float, "Close": float})
        return df


st.title("Market Analysis Dashboard")

# Controls at the top in a horizontal layout
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.markdown("**Market**")
    market = st.selectbox(
        "Market",
        ["Crypto", "Stocks", "PSX"],
        label_visibility="collapsed"
    )

with col2:
    st.markdown("**Symbol**")

    if market == "Stock":
        stock_options = list(STOCK_SYMBOLS) + ["Other"]
        stock_choice = st.selectbox(
            "Stock Symbol",
            stock_options,
            index=0,
            label_visibility="collapsed"
        )
        if stock_choice == "Other":
            symbol = st.text_input(
                "Enter Stock Symbol",
                placeholder="e.g. NVDA, AMD",
                label_visibility="collapsed"
            ).upper()
        else:
            symbol = stock_choice
            
    elif market == "PSX":
        psx_options = PSX_SYMBOLS + ["Other"]
        psx_choice = st.selectbox(
            "PSX Symbol",
            psx_options,
            index=0,
            label_visibility="collapsed"
        )
        if psx_choice == "Other":
            symbol = st.text_input(
                "Enter PSX Symbol",
                placeholder="e.g. OGDC.KA, HBL.KA",
                label_visibility="collapsed"
            ).upper()
            if not symbol.endswith(".KA"):
                symbol = symbol + ".KA"
        else:
            symbol = psx_choice
            
    else:
        crypto_options = list(CRYPTO_SYMBOLS.keys()) + ["Other"]
        crypto_choice = st.selectbox(
            "Crypto",
            crypto_options,
            index=0,
            label_visibility="collapsed"
        )
        if crypto_choice == "Other":
            symbol = st.text_input(
                "Enter Crypto Symbol",
                placeholder="e.g. DOGEUSDT, XRPUSDT",
                label_visibility="collapsed"
            ).upper()
        else:
            symbol = CRYPTO_SYMBOLS[crypto_choice]

with col3:
    st.markdown("**Interval**")
    if market == "Crypto":
        interval_options = {
            "4 Hours": "4h",
            "1 Day": "1d",
            "1 Week": "1w",
            "1 Month": "1M"
        }
    else:
        interval_options = {
            "1 Day": "1d",
            "5 Days": "5d",
            "1 Week": "1wk",
            "1 Month": "1mo"
        }
    interval_choice = st.selectbox(
        "Interval",
        list(interval_options.keys()),
        index=0,
        label_visibility="collapsed"
    )
    interval = interval_options[interval_choice]

with col4:
    st.markdown("**Short MA**")
    short_window = st.slider(
        "Short MA",
        min_value=3,
        max_value=20,
        value=7,
        label_visibility="collapsed"
    )

with col5:
    st.markdown("**Long MA**")
    long_window = st.slider(
        "Long MA",
        min_value=10,
        max_value=50,
        value=14,
        label_visibility="collapsed"
    )

with col6:
    st.markdown("&nbsp;")  # Spacer for alignment
    analyze = st.button("Analyze", use_container_width=True)

vol_window = 5  # Default volatility window

st.markdown("---")
st.subheader(f"{symbol} Market Analysis")

if analyze:
    # Fetch OHLC data for candlestick chart
    df = fetch_ohlc_data(market, symbol, interval)
    # Ensure we always get a 1D list of close prices
    close_col = df["Close"]
    if isinstance(close_col, pd.DataFrame):
        close_col = close_col.iloc[:, 0]
    close_prices = close_col.astype(float).tolist()

    # Core indicators using your existing logic
    short_ma = moving_average(close_prices, short_window)
    long_ma = moving_average(close_prices, long_window)

    vol_values = volatility(close_prices, vol_window)
    vol = vol_values[-1] if vol_values else 0
    trend = detect_trend(long_ma)
    strength = trend_strength(long_ma)

    signal_text = signal(
        short_ma, long_ma,
        trend, vol, strength
    )

    buy, sell = buy_sell(
        short_ma, long_ma,
        short_window, long_window
    )

    accuracy = signal_accuracy(close_prices, buy, sell)

    # Enhanced metrics area with custom styling
    st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #1e222d 0%, #2a2f3f 100%);
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 4px solid;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        margin-bottom: 1rem;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #a0a0a0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    }
    .trend-up { border-left-color: #00A78F; }
    .trend-down { border-left-color: #E53B51; }
    .signal-buy { border-left-color: #00E676; }
    .signal-sell { border-left-color: #FF5252; }
    .signal-hold { border-left-color: #FFA726; }
    </style>
    """, unsafe_allow_html=True)

    # Determine signal color class
    signal_class = "signal-hold"
    if "BUY" in signal_text.upper():
        signal_class = "signal-buy"
    elif "SELL" in signal_text.upper():
        signal_class = "signal-sell"
    
    trend_class = "trend-up" if "Upward" in trend else "trend-down"

    # First row of metrics
    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
    
    with row1_col1:
        st.markdown(f"""
        <div class="metric-card {trend_class}">
            <div class="metric-label">Trend</div>
            <div class="metric-value">{trend}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with row1_col2:
        st.markdown(f"""
        <div class="metric-card {trend_class}">
            <div class="metric-label">Trend Strength</div>
            <div class="metric-value">{strength}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with row1_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Volatility</div>
            <div class="metric-value">{round(vol, 2)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with row1_col4:
        current_price = close_prices[-1]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Current Price</div>
            <div class="metric-value">${current_price:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)    

    # Second row of metrics
    row2_col1, row2_col2 = st.columns(2)
    
    with row2_col1:
        st.markdown(f"""
        <div class="metric-card {signal_class}">
            <div class="metric-label">Signal</div>
            <div class="metric-value">{signal_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with row2_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Signal Accuracy</div>
            <div class="metric-value">{round(accuracy, 2)}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Candlestick + indicators
    fig = go.Figure()

    # Candlestick prices - solid filled bars
    fig.add_trace(go.Candlestick(
        x=df["time"],
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price",
        increasing_line_color="#00A78F",      # teal/green for bullish
        increasing_fillcolor="#00A78F",       # solid teal fill
        decreasing_line_color="#E53B51",     # red for bearish
        decreasing_fillcolor="#E53B51",       # solid red fill
        line=dict(width=1),                   # thin wicks
    ))

    # Align moving averages to dates (skip initial NaNs)
    fig.add_trace(go.Scatter(
        x=df["time"].iloc[short_window - 1:],
        y=short_ma,
        mode="lines",
        name=f"Short MA ({short_window})",
        line=dict(color="orange", width=1.5)
    ))

    fig.add_trace(go.Scatter(
        x=df["time"].iloc[long_window - 1:],
        y=long_ma,
        mode="lines",
        name=f"Long MA ({long_window})",
        line=dict(color="blue", width=1.5)
    ))

    # BUY / SELL labels styled similar to TradingView
    # Box with a small triangular pointer showing exactly where to buy/sell.
    if buy:
        for i in buy:
            if i < len(df):
                x = df["time"].iloc[i]
                y = float(df["Low"].iloc[i])
                fig.add_annotation(
                    x=x,
                    y=y,
                    text="BUY",
                    showarrow=True,
                    arrowhead=2,        # small triangle
                    arrowsize=1.2,
                    arrowwidth=1,
                    arrowcolor="#00E676",
                    ax=0,
                    ay=55,              # move box below candle
                    font=dict(size=12, color="white", family="Arial Black"),
                    bgcolor="#00E676",
                    bordercolor="#008F3A",
                    borderwidth=1,
                    borderpad=6,
                )

    if sell:
        for i in sell:
            if i < len(df):
                x = df["time"].iloc[i]
                y = float(df["High"].iloc[i])
                fig.add_annotation(
                    x=x,
                    y=y,
                    text="SELL",
                    showarrow=True,
                    arrowhead=2,        # small triangle
                    arrowsize=1.2,
                    arrowwidth=1,
                    arrowcolor="#FF5252",
                    ax=0,
                    ay=-55,             # move box above candle
                    font=dict(size=12, color="white", family="Arial Black"),
                    bgcolor="#FF5252",
                    bordercolor="#8E0000",
                    borderwidth=1,
                    borderpad=6,
                )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price",
        
        template="plotly_dark",
        height=600,
        margin=dict(l=40, r=20, t=40, b=40),
        dragmode="pan",  # Default to pan mode
        xaxis=dict(
            rangeslider=dict(visible=True, thickness=0.05),
            rangeselector=dict(
                bgcolor="#1e222d",
                activecolor="#2962ff",
                font=dict(color="white"),
                x=0,
                y=1.1
            ),
            type="date",
            fixedrange=False  # Enable horizontal zoom/pan
        ),
        yaxis=dict(
            fixedrange=False  # Enable vertical zoom/pan
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': True,
        'displayModeBar': True,
        'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
        'doubleClick': 'reset+autosize',
    })
else:
    st.info("Set your parameters above and click **Analyze** to see the candlestick chart.")
