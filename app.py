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

# 2. Streamlit Page Configuration & Styling
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

# Helper function: Cleans raw LaTeX markup and escapes currency symbols to prevent rendering errors
def sanitize_financial_text(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'\\mathbf\{([^}]+)\}', r'**\1**', text)
    clean = re.sub(r'\\mathit\{([^}]+)\}', r'*\1*', clean)
    clean = re.sub(r'\\mathbf', '', clean)
    clean = re.sub(r'(?<!\\)\$(\d+)', r'\\$\1', clean)
    return clean

# 3. Safe API Key Retrieval (Works Locally & on Streamlit Cloud)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

with st.sidebar:
    st.header("⚙️ Desk Controls & API Status")
    
    manual_key = st.text_input("Gemini API Key (Override)", value=GEMINI_API_KEY, type="password")
    if manual_key:
        GEMINI_API_KEY = manual_key

    if not GEMINI_API_KEY:
        st.error("⚠️ GEMINI_API_KEY missing. Enter key above or add to Streamlit Secrets.")
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
        {"role": "assistant", "content": "🏛️ **JC Trading House Desk**: Operational. Select an asset and submit your prompt to evaluate trade structure or momentum risk."}
    ]

# 4. Data Engine & Indicators
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
        return (f"📊 **System (Heuristic Mode)**: Asset `{context['ticker']}` | Price: `${context['price']}` | "
                f"RSI: `{context['rsi']}` | Trend: `{context['trend']}`. Provide a valid Gemini API Key in the sidebar.")

    candidate_models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash"
    ]
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    system_instruction = (
        "You are an institutional multi-agent trading desk: "
        "1. Alex (Quant Agent - Technical momentum, RSI, MACD) "
        "2. Sarah (Risk Agent - ATR bounds, position limits) "
        "3. Marcus (CIO Agent - Consensus synthesis). "
        "Format dollar figures cleanly with numbers like $350.00 rather than raw LaTeX syntax."
    )
    full_prompt = f"Market Context for {context['ticker']}: {context}\n\nUser Question: {prompt}"

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

    return f"⚠️ **AI Agent Desk Error**: API query failed. Detail: `{last_error}`"

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

# 7. Animated HTML5 Pixel Floor: Server Bay + Agent Desks + Pantry Nook
pixel_floor_html = """
<!DOCTYPE html>
<html>
<head>
<style>
  body { margin: 0; padding: 0; background-color: #0e1117; overflow: hidden; font-family: monospace; }
  canvas { display: block; margin: 0 auto; border: 1px solid #2d3139; border-radius: 8px; background: #12151f; }
</style>
</head>
<body>
<canvas id="floor" width="900" height="200"></canvas>
<script>
const canvas = document.getElementById('floor');
const ctx = canvas.getContext('2d');
let frame = 0;

const desks = [
  { name: 'ALEX (QUANT)', x: 220, y: 100, color: '#2ecc71' },
  { name: 'MARCUS (CIO)', x: 410, y: 88, color: '#f39c12' },
  { name: 'SARAH (RISK)', x: 600, y: 100, color: '#e74c3c' }
];

function drawGrid() {
  ctx.strokeStyle = '#1a1e2b';
  ctx.lineWidth = 1;
  for (let x = 0; x < canvas.width; x += 30) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += 30) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
  }
}

function drawServerBay() {
  // Server Cabinet
  ctx.fillStyle = '#1c202c';
  ctx.fillRect(15, 45, 50, 140);
  ctx.strokeStyle = '#3a4154';
  ctx.strokeRect(15, 45, 50, 140);

  // Blinking LEDs
  for(let i = 0; i < 6; i++) {
    let ledColor = ((frame + i * 12) % 40 < 20) ? '#2ecc71' : '#3498db';
    if (i === 4 && frame % 25 < 6) ledColor = '#e74c3c';
    ctx.fillStyle = ledColor;
    ctx.fillRect(22, 55 + i * 20, 6, 6);
    ctx.fillRect(34, 55 + i * 20, 24, 4);
  }

  // Network Packet Pulse
  let packetX = (frame * 3) % 700 + 70;
  ctx.fillStyle = '#00f0ff';
  ctx.fillRect(packetX, 35, 8, 2);
}

function drawDesk(d) {
  // Shadow
  ctx.fillStyle = 'rgba(0,0,0,0.3)';
  ctx.fillRect(d.x - 40, d.y + 32, 80, 10);

  # Desk Surface
  ctx.fillStyle = '#252a38';
  ctx.fillRect(d.x - 35, d.y, 70, 32);
  ctx.strokeStyle = '#3d455b';
  ctx.strokeRect(d.x - 35, d.y, 70, 32);

  // Monitor Display
  ctx.fillStyle = '#11131a';
  ctx.fillRect(d.x - 22, d.y - 24, 44, 20);
  ctx.strokeStyle = d.color;
  ctx.lineWidth = 1.5;
  ctx.strokeRect(d.x - 22, d.y - 24, 44, 20);

  // Animated Screen Data Lines
  ctx.fillStyle = d.color;
  ctx.fillRect(d.x - 18, d.y - 18, 10, 3 + Math.sin(frame * 0.1) * 2);
  ctx.fillRect(d.x - 6, d.y - 14, 12, 4 + Math.cos(frame * 0.1) * 2);
  ctx.fillRect(d.x + 8, d.y - 19, 8, 3 + Math.sin(frame * 0.15) * 2);

  // Pixel Staff Head & Body
  let bob = Math.sin(frame * 0.12) * 2;
  ctx.fillStyle = '#f1c40f';
  ctx.fillRect(d.x - 5, d.y - 38 + bob, 10, 10);
  ctx.fillStyle = d.color;
  ctx.fillRect(d.x - 8, d.y - 28 + bob, 16, 12);

  // Name Tag
  ctx.fillStyle = 'rgba(18, 21, 30, 0.9)';
  ctx.fillRect(d.x - 50, d.y - 58, 100, 14);
  ctx.strokeStyle = '#3a4154';
  ctx.lineWidth = 1;
  ctx.strokeRect(d.x - 50, d.y - 58, 100, 14);

  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 8.5px monospace';
  ctx.textAlign = 'center';
  ctx.fillText(d.name, d.x, d.y - 48);
}

function drawPantry() {
  // Pantry Area Divider
  ctx.strokeStyle = '#2d3345';
  ctx.beginPath(); ctx.moveTo(730, 40); ctx.lineTo(730, 185); ctx.stroke();

  // Coffee Machine Table
  ctx.fillStyle = '#222736';
  ctx.fillRect(750, 100, 125, 32);
  ctx.strokeStyle = '#3a4154';
  ctx.strokeRect(750, 100, 125, 32);

  // Espresso Machine
  ctx.fillStyle = '#e74c3c';
  ctx.fillRect(755, 68, 28, 32);
  ctx.fillStyle = '#11131a';
  ctx.fillRect(760, 80, 18, 14);

  // Steam Animation
  let steamY = 62 - (frame % 30) * 0.5;
  let steamAlpha = 1 - ((frame % 30) / 30);
  ctx.fillStyle = `rgba(255, 255, 255, ${steamAlpha})`;
  ctx.beginPath(); ctx.arc(768, steamY, 2.5, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.arc(772, steamY - 4, 1.5, 0, Math.PI * 2); ctx.fill();

  // Water Dispenser
  ctx.fillStyle = '#3498db';
  ctx.beginPath(); ctx.arc(810, 72, 9, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ecf0f1';
  ctx.fillRect(804, 80, 12, 20);

  // Coffee Mug
  ctx.fillStyle = '#f39c12';
  ctx.fillRect(790, 93, 6, 7);

  // Staff in Pantry
  let pantryBob = Math.cos(frame * 0.1) * 1.5;
  ctx.fillStyle = '#e67e22';
  ctx.fillRect(840, 68 + pantryBob, 10, 10); // Head
  ctx.fillStyle = '#9b59b6';
  ctx.fillRect(837, 78 + pantryBob, 16, 22); // Shirt/Body

  // Label
  ctx.fillStyle = '#85929e';
  ctx.font = 'bold 9px monospace';
  ctx.textAlign = 'center';
  ctx.fillText("☕ BREAK ROOM & PANTRY", 812, 52);
}

function drawHUD() {
  ctx.fillStyle = 'rgba(18, 21, 30, 0.95)';
  ctx.fillRect(0, 0, canvas.width, 28);
  ctx.strokeStyle = '#2d3345';
  ctx.beginPath(); ctx.moveTo(0, 28); ctx.lineTo(canvas.width, 28); ctx.stroke();

  ctx.fillStyle = '#2ecc71';
  ctx.font = 'bold 10px monospace';
  ctx.textAlign = 'left';
  ctx.fillText("● JC TRADING DESK FLOOR & PANTRY TELEMETRY", 12, 18);

  let alpha = (Math.sin(frame * 0.1) + 1) / 2;
  ctx.fillStyle = `rgba(46, 204, 113, ${alpha})`;
  ctx.beginPath(); ctx.arc(850, 15, 4, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ffffff';
  ctx.font = '9px monospace';
  ctx.fillText("LIVE", 860, 18);
}

function animate() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawGrid();
  drawServerBay();
  desks.forEach(drawDesk);
  drawPantry();
  drawHUD();
  frame++;
  requestAnimationFrame(animate);
}
animate();
</script>
</body>
</html>
"""

st.components.v1.html(pixel_floor_html, height=215, scrolling=False)

st.markdown("---")

# 8. Main Dashboard Layout (Balanced Columns)
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