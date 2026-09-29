import os
import re
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# 1. Safe Import for Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# 2. Streamlit Page Configuration & Dark Theme Styling
st.set_page_config(
    page_title="JC Trading House",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 98% !important; }
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    .stMetric { background-color: #161a23; padding: 12px; border-radius: 8px; border: 1px solid #2d3139; }
    .stChatInput { border-color: #2d3139 !important; }
    </style>
""", unsafe_allow_html=True)

# Helper function: Escapes currency symbols and cleans raw LaTeX markup to avoid rendering errors
def sanitize_financial_text(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'\\mathbf\{([^}]+)\}', r'**\1**', text)
    clean = re.sub(r'\\mathit\{([^}]+)\}', r'*\1*', clean)
    clean = re.sub(r'\\mathbf', '', clean)
    clean = re.sub(r'(?<!\\)\$(\d+)', r'\\$\1', clean)
    return clean

# 3. API Key Retrieval & Validation Integration
# Retrieve API Key safely inside app.py using Streamlit Secrets or Environment
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

with st.sidebar:
    st.header("⚙️ Desk Controls & API Status")
    
    # Optional manual override if st.secrets is not populated
    manual_key = st.text_input("Gemini API Key (Override)", value=GEMINI_API_KEY, type="password")
    if manual_key:
        GEMINI_API_KEY = manual_key

    # Display API Connection Status
    if not GEMINI_API_KEY:
        st.error("⚠️ GEMINI_API_KEY is missing from Streamlit Secrets.")
    else:
        st.success("✅ GEMINI_API_KEY connected.")

    st.markdown("---")
    st.subheader("📌 Asset Watchlist")
    
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = ["NVDA", "TSLA", "BTC-USD", "ETH-USD", "S68.SG", "AAPL", "PLTR"]
    if "current_ticker" not in st.session_state:
        st.session_state.current_ticker = "BTC-USD"

    selected_symbol = st.selectbox(
        "Active Asset", 
        options=st.session_state.watchlist, 
        index=st.session_state.watchlist.index(st.session_state.current_ticker) if st.session_state.current_ticker in st.session_state.watchlist else 0
    )
    if selected_symbol != st.session_state.current_ticker:
        st.session_state.current_ticker = selected_symbol
        st.rerun()

    st.markdown("---")
    st.subheader("🛡️ Portfolio Risk Bounds")
    capital = st.number_input("Account Capital ($)", min_value=1000, max_value=1000000, value=50000, step=5000)
    max_alloc_pct = st.slider("Max Allocation (%)", min_value=1, max_value=100, value=15)

# Session State Initialization
if "chart_timeframe" not in st.session_state:
    st.session_state.chart_timeframe = "1mo"
if "sprint_results" not in st.session_state:
    st.session_state.sprint_results = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "🏛️ **JC Trading House Desk**: Operational. Select an asset and enter your query to evaluate technical momentum or position risk."}
    ]

# 4. Data & Indicators Engine
@st.cache_data(ttl=60)
def fetch_asset_data(ticker_symbol: str, timeframe: str) -> pd.DataFrame:
    interval_map = {"1d": "5m", "5d": "15m", "1mo": "1d", "6mo": "1d"}
    interval = interval_map.get(timeframe, "1d")
    asset = yf.Ticker(ticker_symbol)
    return asset.history(period=timeframe, interval=interval)

def compute_indicators(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 20:
        return {"price": 0.0, "rsi": 50.0, "macd": 0.0, "macd_signal": 0.0, "atr": 0.0, "trend": "NEUTRAL", "sma20": 0.0}
    
    close = df['Close']
    latest_price = float(close.iloc[-1])

    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    rsi = float((100 - (100 / (1 + rs))).iloc[-1])

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean()

    sma20 = float(close.rolling(window=20).mean().iloc[-1])
    tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1]) if len(tr) >= 14 else float(tr.mean())

    trend = "BULLISH" if latest_price > sma20 else "BEARISH" if latest_price < sma20 else "NEUTRAL"

    return {
        "price": round(latest_price, 2),
        "rsi": round(rsi, 2),
        "macd": round(float(macd.iloc[-1]), 3),
        "macd_signal": round(float(macd_signal.iloc[-1]), 3),
        "atr": round(atr, 2),
        "trend": trend,
        "sma20": round(sma20, 2)
    }

# 5. LLM Query Engine
def query_agent_llm(prompt: str, context: dict) -> str:
    if not HAS_GENAI or not GEMINI_API_KEY:
        return (f"📊 **System (Heuristic)**: Asset `{context['ticker']}` | Price: `${context['price']}` | "
                f"RSI: `{context['rsi']}` | Trend: `{context['trend']}`. Add `GEMINI_API_KEY` to Streamlit Secrets to enable LLM agents.")

    candidate_models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    system_instruction = (
        "You are an institutional multi-agent trading desk consisting of: "
        "1. Alex (Quant Agent - Technical momentum, RSI, MACD) "
        "2. Sarah (Risk Agent - ATR bounds, capital allocation) "
        "3. Marcus (CIO Agent - Final decision synthesis). "
        "Format dollar numbers clearly without raw LaTeX math tags (e.g. use $350.00 instead of \\mathbf{350})."
    )
    full_prompt = f"Market Data for {context['ticker']}: {context}\n\nUser Question: {prompt}"

    last_error = ""
    for model_id in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                )
            )
            return sanitize_financial_text(response.text)
        except Exception as e:
            last_error = str(e)
            continue

    return f"⚠️ **AI Desk Error**: Unable to execute query. API error: `{last_error}`"

# 6. Header Telemetry Bar
st.title("🏛️ JC TRADING HOUSE")
st.caption("Institutional Multi-Agent Trading Desk & Real-time Market Analytics")

df_current = fetch_asset_data(st.session_state.current_ticker, "1mo")
indicators = compute_indicators(df_current)
indicators['ticker'] = st.session_state.current_ticker

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Active Asset", st.session_state.current_ticker)
kpi2.metric("Last Price", f"${indicators['price']}")
kpi3.metric("RSI (14)", indicators['rsi'])
kpi4.metric("20-SMA Trend", indicators['trend'])
kpi5.metric("ATR Volatility", f"${indicators['atr']}")

st.markdown("---")

# 7. Main Dashboard Layout (Balanced Columns)
col_left, col_right = st.columns([1, 1], gap="medium")

with col_left:
    st.subheader(f"📊 {st.session_state.current_ticker} Price Chart")
    t1, t2, t3, t4 = st.columns(4)
    if t1.button("1D", use_container_width=True): st.session_state.chart_timeframe = "1d"; st.rerun()
    if t2.button("5D", use_container_width=True): st.session_state.chart_timeframe = "5d"; st.rerun()
    if t3.button("1M", use_container_width=True): st.session_state.chart_timeframe = "1mo"; st.rerun()
    if t4.button("6M", use_container_width=True): st.session_state.chart_timeframe = "6mo"; st.rerun()

    if not df_current.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df_current.index, open=df_current['Open'], high=df_current['High'], low=df_current['Low'], close=df_current['Close'],
            increasing_line_color='#2ecc71', decreasing_line_color='#e74c3c'
        )])
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=340, xaxis_rangeslider_visible=False,
            paper_bgcolor='#0e1117', plot_bgcolor='#0e1117',
            xaxis=dict(gridcolor='#1e222a', tickfont=dict(color='#85929e')),
            yaxis=dict(gridcolor='#1e222a', tickfont=dict(color='#85929e'))
        )
        st.plotly_chart(fig, use_container_width=True)

    if st.button("🚀 Dispatch Strategy Sprint", type="primary", use_container_width=True):
        with st.spinner("🏛️ Multi-agent evaluation in progress..."):
            sprint_prompt = f"Run trade assessment for portfolio allocation of ${capital * (max_alloc_pct/100)}."
            assessment = query_agent_llm(sprint_prompt, indicators)

            score = 50 + (20 if indicators['trend'] == "BULLISH" else -20) + (25 if indicators['rsi'] < 30 else -25 if indicators['rsi'] > 70 else 0)
            score = max(0, min(100, score))
            signal = "BUY" if score >= 60 else "SELL" if score <= 40 else "HOLD"

            st.session_state.sprint_results = {
                "signal": signal,
                "score": score,
                "summary": assessment
            }
            st.rerun()

with col_right:
    st.subheader("📋 Strategy Execution Board & Terminal")
    
    if st.session_state.sprint_results:
        res = st.session_state.sprint_results
        sc1, sc2 = st.columns(2)
        sc1.metric("CIO Signal", res['signal'])
        sc2.metric("Confidence Score", f"{res['score']}/100")
        st.info(res['summary'])
    else:
        st.info("🔴 Desk idle. Click **Dispatch Strategy Sprint** on the left to evaluate orders.")

    st.markdown("##### 💬 Live Desk Q&A Terminal")
    chat_box = st.container(height=380)
    with chat_box:
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(sanitize_financial_text(msg["content"]))

    if user_prompt := st.chat_input("Ask desk agents a question..."):
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        reply = query_agent_llm(user_prompt, indicators)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()