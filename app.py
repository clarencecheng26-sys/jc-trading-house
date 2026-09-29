import os
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# Safe import for Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

# 1. Page Configuration & Layout
st.set_page_config(page_title="JC Trading House", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1a1d24; padding: 10px; border-radius: 8px; border: 1px solid #2d3139; }
    </style>
""", unsafe_allow_html=True)

st.title("🏛️ JC TRADING HOUSE")
st.caption("Institutional multi-agent trading floor powered by live telemetry & LLM market intelligence.")

# 2. API Setup & Session State
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.sidebar.text_input("Gemini API Key (Optional for AI Agents)", type="password")

if not HAS_GENAI:
    st.sidebar.warning("`google-genai` package not detected locally. Running in technical heuristic mode. Install via `pip install google-genai` for live AI agent synthesis.")

if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["NVDA", "TSLA", "BTC-USD", "ETH-USD", "S68.SG", "AAPL", "PLTR"]

if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = "BTC-USD"

if "chart_timeframe" not in st.session_state:
    st.session_state.chart_timeframe = "1mo"

if "sprint_results" not in st.session_state:
    st.session_state.sprint_results = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "🏛️ **JC Trading House Desk**: Operational. Enter an API key in the sidebar for live AI reasoning or use built-in technical indicators."}
    ]

# 3. Data & Indicator Engines
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

def query_agent_llm(prompt: str, context: dict) -> str:
    if not HAS_GENAI or not GEMINI_API_KEY:
        return f"📊 **System (Rule-Based Heuristic)**: Current price for `{context['ticker']}` is `${context['price']}` | RSI: `{context['rsi']}` | Trend: `{context['trend']}`. Install `google-genai` and add a Gemini API Key to enable multi-agent LLM analysis."

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        system_instruction = (
            "You are a multi-agent quantitative trading desk consisting of: "
            "1. Alex (Quant Agent - focuses on RSI, MACD, trends) "
            "2. Sarah (Risk Agent - focuses on ATR, capital preservation, position sizing) "
            "3. Marcus (CIO Agent - synthesizes final decisions). "
            "Respond directly as these agents with concise, professional institutional analysis."
        )
        
        full_prompt = f"Market Context for {context['ticker']}: {context}\n\nUser Question: {prompt}"
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
            )
        )
        return response.text
    except Exception as e:
        return f"⚠️ **AI Agent Desk Error**: {str(e)}"

# 4. Office Canvas Diagnostics
st.subheader("🏢 Desk Telemetry & Server Bay")

office_canvas_html = r"""
<canvas id='officeCanvas' width='880' height='260' style='border:2px solid #3a3f4d; border-radius:8px; background-color:#14161d;'></canvas>
<script>
const canvas = document.getElementById('officeCanvas');
const ctx = canvas.getContext('2d');
function drawFloor() {
    ctx.fillStyle = '#14161d'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#2ecc71'; ctx.font = 'bold 12px monospace';
    ctx.fillText("JC TRADING HOUSE — LIVE TELEMETRY NODE", 20, 30);
    ctx.fillStyle = '#85929e'; ctx.font = '11px monospace';
    ctx.fillText("Status: Operational | Feeds: Active | Latency: 1.2ms", 20, 50);
}
drawFloor();
</script>
"""
st.components.v1.html(office_canvas_html, height=270)

# 5. Middle Section: Price Chart & Strategy Intelligence
col_chart, col_board = st.columns([1.1, 0.9])

with col_chart:
    st.subheader(f"📊 {st.session_state.current_ticker} Price Chart")
    tf1, tf2, tf3, tf4 = st.columns(4)
    if tf1.button("1 Day", use_container_width=True): st.session_state.chart_timeframe = "1d"; st.rerun()
    if tf2.button("5 Days", use_container_width=True): st.session_state.chart_timeframe = "5d"; st.rerun()
    if tf3.button("1 Month", use_container_width=True): st.session_state.chart_timeframe = "1mo"; st.rerun()
    if tf4.button("6 Months", use_container_width=True): st.session_state.chart_timeframe = "6mo"; st.rerun()

    df_chart = fetch_asset_data(st.session_state.current_ticker, st.session_state.chart_timeframe)

    if not df_chart.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'],
            increasing_line_color='#2ecc71', decreasing_line_color='#e74c3c'
        )])
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10), height=230, xaxis_rangeslider_visible=False,
            paper_bgcolor='#0e1117', plot_bgcolor='#0e1117',
            xaxis=dict(gridcolor='#1e222a', tickfont=dict(color='#85929e')),
            yaxis=dict(gridcolor='#1e222a', tickfont=dict(color='#85929e'))
        )
        st.plotly_chart(fig, use_container_width=True)

with col_board:
    st.subheader("📋 Deep Strategy Intelligence Board")
    if st.session_state.sprint_results is None:
        st.info("🔴 Desk idle. Select an asset below and click **Run Strategy Sprint**.")
    else:
        res = st.session_state.sprint_results
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CIO Call Sign", res['signal'])
        c2.metric("Certainty Score", f"{res['score']}/100")
        c3.metric("RSI (14)", res['rsi'])
        c4.metric("Market Trend", res['trend'])

        st.success(res['summary'])

    st.subheader("💬 Live Desk Q&A Terminal")
    chat_box = st.container(height=140)
    with chat_box:
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

    if user_prompt := st.chat_input("Ask desk agents a question..."):
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        df_ask = fetch_asset_data(st.session_state.current_ticker, "1mo")
        ind = compute_indicators(df_ask)
        ind['ticker'] = st.session_state.current_ticker
        
        reply = query_agent_llm(user_prompt, ind)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

st.markdown("---")

# 6. Watchlist & Controls
col_watch, col_risk = st.columns([1.1, 0.9])

with col_watch:
    st.subheader("📌 Active Watchlist & Asset Selection")
    active_symbol = st.selectbox("Active Asset", options=st.session_state.watchlist, index=st.session_state.watchlist.index(st.session_state.current_ticker) if st.session_state.current_ticker in st.session_state.watchlist else 0)
    if active_symbol != st.session_state.current_ticker:
        st.session_state.current_ticker = active_symbol
        st.rerun()

with col_risk:
    st.subheader("🛡️ Desk Risk Parameters & Dispatch")
    capital = st.number_input("Account Capital ($)", min_value=1000, max_value=1000000, value=50000, step=5000)
    max_alloc_pct = st.slider("Max Allocation (%)", min_value=1, max_value=100, value=15)

    if st.button("🚀 Run Strategy Sprint", type="primary", use_container_width=True):
        with st.spinner("🏛️ Dispatching multi-agent evaluation..."):
            df_eval = fetch_asset_data(st.session_state.current_ticker, "1mo")
            ind = compute_indicators(df_eval)
            ind['ticker'] = st.session_state.current_ticker
            
            sprint_prompt = f"Run a complete multi-agent trade assessment for allocation of ${capital * (max_alloc_pct/100)}."
            agent_assessment = query_agent_llm(sprint_prompt, ind)

            score = 50 + (20 if ind['trend'] == "BULLISH" else -20) + (25 if ind['rsi'] < 30 else -25 if ind['rsi'] > 70 else 0)
            score = max(0, min(100, score))
            signal = "BUY" if score >= 60 else "SELL" if score <= 40 else "HOLD"

            st.session_state.sprint_results = {
                "signal": signal,
                "score": score,
                "rsi": ind['rsi'],
                "trend": ind['trend'],
                "summary": agent_assessment
            }
            st.rerun()