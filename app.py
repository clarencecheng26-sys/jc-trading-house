import os
import re
import streamlit as st
import streamlit.components.v1 as components
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

# 2. Streamlit Page Configuration & Custom CSS
st.set_page_config(
    page_title="JC Trading House",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 98% !important; }
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    .stMetric { background-color: #161a23; padding: 12px; border-radius: 8px; border: 1px solid #2d3139; }
    .stChatInput { border-color: #2d3139 !important; }
    </style>
""", unsafe_allow_html=True)

def sanitize_financial_text(text: str) -> str:
    if not text: return ""
    clean = re.sub(r'\\mathbf\{([^}]+)\}', r'**\1**', text)
    clean = re.sub(r'\\mathit\{([^}]+)\}', r'*\1*', clean)
    clean = re.sub(r'\\mathbf', '', clean)
    clean = re.sub(r'(?<!\\)\$(\d+)', r'\\$\1', clean)
    return clean

# 3. Session State Initialization
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["BTC-USD", "NVDA", "TSLA", "ETH-USD", "S68.SG", "AAPL"]
if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = "BTC-USD"
if "chart_timeframe" not in st.session_state:
    st.session_state.chart_timeframe = "1mo"
if "sprint_results" not in st.session_state:
    st.session_state.sprint_results = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "🏛️ **Desk**: Operational. Submit your prompt to evaluate momentum risk."}
    ]

# 4. API Key Management (Sidebar)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception: pass

with st.sidebar:
    st.header("⚙️ System Settings")
    manual_key = st.text_input("Gemini API Key", value=GEMINI_API_KEY, type="password")
    if manual_key: GEMINI_API_KEY = manual_key
    if not GEMINI_API_KEY:
        st.error("⚠️ API Key missing.")
    else:
        st.success("✅ API Key connected.")
    st.markdown("---")
    st.subheader("🛡️ Portfolio Risk Bounds")
    capital = st.number_input("Account Capital ($)", min_value=1000, value=50000, step=5000)
    max_alloc_pct = st.slider("Max Allocation (%)", min_value=1, max_value=100, value=15)

# 5. Data Engine & Indicators
@st.cache_data(ttl=60)
def fetch_asset_data(ticker_symbol: str, timeframe: str) -> pd.DataFrame:
    interval_map = {"1d": "5m", "5d": "15m", "1mo": "1d", "6mo": "1d"}
    interval = interval_map.get(timeframe, "1d")
    try:
        asset = yf.Ticker(ticker_symbol)
        df = asset.history(period=timeframe, interval=interval)
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def compute_indicators(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 5:
        return {"price": 0.0, "rsi": 50.0, "macd": 0.0, "macd_signal": 0.0, "atr": 0.0, "trend": "NEUTRAL", "sma20": 0.0}
    
    close = df['Close']
    latest_price = float(close.iloc[-1])
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=min(14, len(df))).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=min(14, len(df))).mean()
    rs = gain / (loss + 1e-9)
    rsi = float((100 - (100 / (1 + rs))).iloc[-1]) if not rs.empty else 50.0

    sma20 = float(close.rolling(window=min(20, len(df))).mean().iloc[-1])
    tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(min(14, len(df))).mean().iloc[-1]) if len(tr) > 0 else 0.0
    trend = "BULLISH" if latest_price > sma20 else "BEARISH" if latest_price < sma20 else "NEUTRAL"

    return {
        "price": round(latest_price, 2), "rsi": round(rsi, 2),
        "atr": round(atr, 2), "trend": trend, "sma20": round(sma20, 2)
    }

# 6. Robust Multi-Model LLM Engine (Fix for 404 Errors)
def query_agent_llm(prompt: str, context: dict) -> str:
    if not GEMINI_API_KEY:
        return f"⚠️ **System**: Missing Gemini API Key. Cannot process."

    # Expanded aliases to ensure compatibility with older/newer SDKs
    candidate_models = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-pro"]
    system_instruction = "You are an institutional multi-agent trading desk. Keep answers concise."
    full_prompt = f"Market Context for {context['ticker']}: {context}\n\nUser Question: {prompt}"
    last_error = ""

    if HAS_GENAI:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            for model_id in candidate_models:
                try:
                    response = client.models.generate_content(
                        model=model_id,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.3)
                    )
                    return sanitize_financial_text(response.text)
                except Exception as e:
                    last_error = str(e)
                    continue
        except Exception as e: last_error = str(e)

    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=GEMINI_API_KEY)
        for model_id in candidate_models:
            try:
                model = legacy_genai.GenerativeModel(model_name=model_id, system_instruction=system_instruction)
                response = model.generate_content(full_prompt)
                return sanitize_financial_text(response.text)
            except Exception as e:
                last_error = str(e)
                continue
    except Exception as e:
        if not last_error: last_error = str(e)

    return f"⚠️ **AI Desk Error**: Query failed. Details: `{last_error}`"

# 7. Main UI Header & Watchlist Manager (Moved from Sidebar)
st.title("🏛️ JC TRADING HOUSE")
st.caption("Institutional Multi-Agent Trading Desk & Real-time Market Analytics")

# --- NEW ASSET MANAGEMENT UI ---
col_sel, col_add, col_del = st.columns([2, 1, 1])
with col_sel:
    selected_symbol = st.selectbox(
        "Active Asset Watchlist", 
        options=st.session_state.watchlist, 
        index=st.session_state.watchlist.index(st.session_state.current_ticker) if st.session_state.current_ticker in st.session_state.watchlist else 0
    )
    if selected_symbol != st.session_state.current_ticker:
        st.session_state.current_ticker = selected_symbol
        st.rerun()
with col_add:
    new_asset = st.text_input("Add Ticker", placeholder="e.g., MSFT, GC=F", label_visibility="collapsed").strip().upper()
    if st.button("➕ Add Asset", use_container_width=True) and new_asset:
        if new_asset not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_asset)
            st.session_state.current_ticker = new_asset
            st.rerun()
with col_del:
    if st.button("🗑️ Remove Asset", use_container_width=True):
        if len(st.session_state.watchlist) > 1:
            st.session_state.watchlist.remove(st.session_state.current_ticker)
            st.session_state.current_ticker = st.session_state.watchlist[0]
            st.rerun()
        else:
            st.error("Min 1 asset.")

st.markdown("<br>", unsafe_allow_html=True)

# Fetch Data (Fixed to use dynamic timeframe)
df_current = fetch_asset_data(st.session_state.current_ticker, st.session_state.chart_timeframe)
indicators = compute_indicators(df_current)
indicators['ticker'] = st.session_state.current_ticker

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Active Asset", st.session_state.current_ticker)
kpi2.metric("Last Price", f"${indicators['price']}")
kpi3.metric("RSI (14)", indicators['rsi'])
kpi4.metric("20-SMA Trend", indicators['trend'])
kpi5.metric("ATR Volatility", f"${indicators['atr']}")

# 8. Animated HTML5 Pixel Floor (Fixed Canvas Cut-off)
pixel_floor_html = """
<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background-color: transparent; font-family: monospace; }
  .canvas-wrapper { width: 100%; height: 100%; display: flex; align-items: flex-start; justify-content: center; }
  canvas { display: block; width: 100%; max-height: 280px; border: 1px solid #2d3139; border-radius: 8px; background: #12151f; object-fit: contain; }
</style>
</head>
<body>
<div class="canvas-wrapper">
  <canvas id="floor" width="1400" height="280"></canvas>
</div>
<script>
const canvas = document.getElementById('floor');
const ctx = canvas.getContext('2d');
let frame = 0;

class StaffMember {
  constructor(name, deskX, deskY, color, hairColor) {
    this.name = name;
    this.deskX = deskX; this.deskY = deskY;
    this.x = deskX; this.y = deskY;
    this.color = color; this.hairColor = hairColor;
    this.state = 'DESK'; 
    this.timer = Math.floor(Math.random() * 150) + 100;
    this.targetX = deskX; this.targetY = deskY;
    this.destName = '';
  }

  update() {
    if (this.state === 'DESK') {
      this.timer--;
      if (this.timer <= 0) {
        if (Math.random() < 0.6) {
          this.targetX = 1200 + Math.random() * 50; this.destName = 'PANTRY';
        } else {
          this.targetX = 85 + Math.random() * 20; this.destName = 'SERVER';
        }
        this.targetY = 160; this.state = 'WALKING_OUT';
      }
    } else if (this.state === 'WALKING_OUT') {
      const dx = this.targetX - this.x, dy = this.targetY - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) {
        this.x = this.targetX; this.y = this.targetY;
        this.state = 'AT_DEST'; this.timer = Math.floor(Math.random() * 140) + 90;
      } else {
        this.x += (dx / dist) * 1.5; this.y += (dy / dist) * 1.5;
      }
    } else if (this.state === 'AT_DEST') {
      this.timer--;
      if (this.timer <= 0) {
        this.targetX = this.deskX; this.targetY = this.deskY;
        this.state = 'WALKING_BACK';
      }
    } else if (this.state === 'WALKING_BACK') {
      const dx = this.targetX - this.x, dy = this.targetY - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) {
        this.x = this.deskX; this.y = this.deskY;
        this.state = 'DESK'; this.timer = Math.floor(Math.random() * 220) + 140;
      } else {
        this.x += (dx / dist) * 1.5; this.y += (dy / dist) * 1.5;
      }
    }
  }

  draw() {
    const isWalking = (this.state === 'WALKING_OUT' || this.state === 'WALKING_BACK');
    const bob = (this.state === 'DESK') ? Math.sin(frame * 0.12) * 1.5 : 0;
    const legOffset = isWalking ? Math.sin(frame * 0.25) * 4 : 0;

    ctx.fillStyle = this.hairColor;
    ctx.fillRect(this.x - 6, this.y - 38 + bob, 12, 12);
    ctx.fillStyle = this.color;
    ctx.fillRect(this.x - 8, this.y - 26 + bob, 16, 14);

    ctx.fillStyle = '#2c3e50';
    if (isWalking) {
      ctx.fillRect(this.x - 6, this.y - 12, 5, 12 + legOffset);
      ctx.fillRect(this.x + 1, this.y - 12, 5, 12 - legOffset);
    } else {
      ctx.fillRect(this.x - 6, this.y - 12 + bob, 12, 12);
    }

    let label = this.name;
    if (this.state === 'AT_DEST') label = (this.destName === 'PANTRY') ? `${this.name} ☕` : `${this.name} ⚙️`;
    else if (isWalking) label = `${this.name} 🚶`;

    ctx.fillStyle = '#161a23';
    ctx.fillRect(this.x - 60, this.y - 62, 120, 18);
    ctx.strokeStyle = this.color;
    ctx.lineWidth = 1.2;
    ctx.strokeRect(this.x - 60, this.y - 62, 120, 18);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 11px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(label, this.x, this.y - 49);
  }
}

const staffList = [
  new StaffMember('ALEX (QUANT)', 360, 140, '#2ecc71', '#f1c40f'),
  new StaffMember('MARCUS (CIO)', 680, 130, '#f39c12', '#e67e22'),
  new StaffMember('SARAH (RISK)', 1000, 140, '#e74c3c', '#9b59b6')
];

function drawGrid() {
  ctx.strokeStyle = '#1a1e2b'; ctx.lineWidth = 1;
  for (let x = 0; x < canvas.width; x += 35) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke(); }
  for (let y = 0; y < canvas.height; y += 35) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke(); }
}

function drawHUD() {
  ctx.fillStyle = '#161a23'; ctx.fillRect(0, 0, canvas.width, 36);
  ctx.strokeStyle = '#2d3345'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, 36); ctx.lineTo(canvas.width, 36); ctx.stroke();
  ctx.fillStyle = '#2ecc71'; ctx.font = 'bold 12px monospace'; ctx.textAlign = 'left';
  ctx.fillText("● JC TRADING HOUSE — FLOOR & PANTRY TELEMETRY", 18, 23);
  let alpha = (Math.sin(frame * 0.1) + 1) / 2;
  ctx.fillStyle = `rgba(46, 204, 113, ${alpha})`;
  ctx.beginPath(); ctx.arc(1335, 20, 5, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ffffff'; ctx.font = 'bold 11px monospace'; ctx.fillText("LIVE", 1348, 23);
}

function animate() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawGrid();
  
  // Minimal Server Bay
  ctx.fillStyle = '#1c202c'; ctx.fillRect(25, 60, 80, 160);
  ctx.strokeStyle = '#3a4154'; ctx.strokeRect(25, 60, 80, 160);
  ctx.fillStyle = '#00f0ff'; ctx.font = 'bold 11px monospace'; ctx.textAlign = 'center'; ctx.fillText("SERVERS", 65, 236);

  // Minimal Pantry
  ctx.fillStyle = '#222736'; ctx.fillRect(1160, 140, 210, 42);
  ctx.strokeStyle = '#3a4154'; ctx.strokeRect(1160, 140, 210, 42);
  ctx.fillStyle = '#f39c12'; ctx.font = 'bold 11px monospace'; ctx.textAlign = 'center'; ctx.fillText("☕ PANTRY", 1265, 75);

  // Desks
  const deskLocations = [
    { x: 360, y: 140, color: '#2ecc71' },
    { x: 680, y: 130, color: '#f39c12' },
    { x: 1000, y: 140, color: '#e74c3c' }
  ];
  deskLocations.forEach(d => {
    ctx.fillStyle = '#252a38'; ctx.fillRect(d.x - 50, d.y, 100, 42);
    ctx.strokeStyle = '#3d455b'; ctx.strokeRect(d.x - 50, d.y, 100, 42);
    ctx.fillStyle = '#11131a'; ctx.fillRect(d.x - 38, d.y - 30, 76, 28);
    ctx.strokeStyle = d.color; ctx.strokeRect(d.x - 38, d.y - 30, 76, 28);
  });

  staffList.forEach(s => { s.update(); s.draw(); });
  drawHUD();
  frame++;
  requestAnimationFrame(animate);
}
animate();
</script>
</body>
</html>
"""

components.html(pixel_floor_html, height=310, scrolling=False)

st.markdown("---")

# 9. Main Dashboard Layout (Fixed Timeframe Buttons)
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
    else:
        st.warning("No price data found.")

    if st.button("🚀 Dispatch Strategy Sprint", type="primary", use_container_width=True):
        with st.spinner("🏛️ Evaluating orders..."):
            sprint_prompt = f"Run trade assessment for portfolio allocation of ${capital * (max_alloc_pct/100)}."
            assessment = query_agent_llm(sprint_prompt, indicators)
            score = 50 + (20 if indicators['trend'] == "BULLISH" else -20)
            score = max(0, min(100, score))
            st.session_state.sprint_results = {
                "signal": "BUY" if score >= 60 else "SELL" if score <= 40 else "HOLD",
                "score": score,
                "summary": assessment
            }
            st.rerun()

with col_right:
    st.subheader("📋 Strategy Execution Board")
    if st.session_state.sprint_results:
        res = st.session_state.sprint_results
        sc1, sc2 = st.columns(2)
        sc1.metric("CIO Signal", res['signal'])
        sc2.metric("Confidence Score", f"{res['score']}/100")
        st.info(res['summary'])
    else:
        st.info("🔴 Desk idle.")

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