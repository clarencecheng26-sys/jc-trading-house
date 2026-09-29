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

# 6. Dynamic Model Discovery LLM Engine (Fixes 404 for gen-lang-client Keys)
def query_agent_llm(prompt: str, context: dict) -> str:
    if not GEMINI_API_KEY:
        return f"⚠️ **System**: Missing Gemini API Key. Cannot process."

    system_instruction = "You are an institutional multi-agent trading desk. Keep answers concise, direct, and actionable."
    full_prompt = f"Market Context for {context['ticker']}: {context}\n\nUser Question: {prompt}"
    last_error = ""

    # Attempt 1: New Google GenAI SDK with Dynamic Model Resolution
    if HAS_GENAI:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            discovered = []
            try:
                for m in client.models.list():
                    name = getattr(m, "name", "")
                    if "gemini" in name.lower():
                        discovered.append(name.replace("models/", ""))
            except Exception: pass

            fallbacks = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
            model_queue = [m for m in (discovered + fallbacks) if m]

            for model_id in model_queue:
                try:
                    response = client.models.generate_content(
                        model=model_id,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.3)
                    )
                    if response and response.text:
                        return sanitize_financial_text(response.text)
                except Exception as e:
                    last_error = str(e)
                    continue
        except Exception as e: last_error = str(e)

    # Attempt 2: Legacy google.generativeai SDK
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=GEMINI_API_KEY)
        discovered = []
        try:
            for m in legacy_genai.list_models():
                if "generateContent" in getattr(m, "supported_generation_methods", []):
                    discovered.append(m.name)
        except Exception: pass

        fallbacks = ["models/gemini-1.5-flash", "models/gemini-2.0-flash", "models/gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
        model_queue = [m for m in (discovered + fallbacks) if m]

        for model_id in model_queue:
            try:
                model = legacy_genai.GenerativeModel(model_name=model_id, system_instruction=system_instruction)
                response = model.generate_content(full_prompt)
                if response and response.text:
                    return sanitize_financial_text(response.text)
            except Exception as e:
                last_error = str(e)
                continue
    except Exception as e:
        if not last_error: last_error = str(e)

    return f"⚠️ **AI Agent Desk Error**: Query failed. Details: `{last_error}`"

# 7. Main UI Header & Watchlist Manager
st.title("🏛️ JC TRADING HOUSE")
st.caption("Institutional Multi-Agent Trading Desk & Real-time Market Analytics")

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

df_current = fetch_asset_data(st.session_state.current_ticker, st.session_state.chart_timeframe)
indicators = compute_indicators(df_current)
indicators['ticker'] = st.session_state.current_ticker

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Active Asset", st.session_state.current_ticker)
kpi2.metric("Last Price", f"${indicators['price']}")
kpi3.metric("RSI (14)", indicators['rsi'])
kpi4.metric("20-SMA Trend", indicators['trend'])
kpi5.metric("ATR Volatility", f"${indicators['atr']}")

# 8. High-Detail Animated Pixel Floor Engine (HD Canvas)
pixel_floor_html = """
<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #0b0e14; font-family: 'Courier New', monospace; }
  .canvas-container { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
  canvas { display: block; width: 100%; height: 100%; max-height: 440px; border: 2px solid #232838; border-radius: 10px; background: #0e121b; image-rendering: pixelated; }
</style>
</head>
<body>
<div class="canvas-container">
  <canvas id="tradingFloor" width="1200" height="420"></canvas>
</div>
<script>
const canvas = document.getElementById('tradingFloor');
const ctx = canvas.getContext('2d');
let frame = 0;

class StaffMember {
  constructor(name, title, deskX, deskY, shirtColor, hairColor, roleBadge) {
    this.name = name;
    this.title = title;
    this.deskX = deskX; 
    this.deskY = deskY;
    this.x = deskX; 
    this.y = deskY;
    this.shirtColor = shirtColor;
    this.hairColor = hairColor;
    this.roleBadge = roleBadge;
    this.state = 'DESK';
    this.timer = Math.floor(Math.random() * 180) + 120;
    this.targetX = deskX; 
    this.targetY = deskY;
    this.destName = '';
  }

  update() {
    if (this.state === 'DESK') {
      this.timer--;
      if (this.timer <= 0) {
        if (Math.random() < 0.55) {
          this.targetX = 1080 + Math.random() * 40; 
          this.destName = 'PANTRY';
        } else {
          this.targetX = 110 + Math.random() * 30; 
          this.destName = 'SERVERS';
        }
        this.targetY = 240; 
        this.state = 'WALKING_OUT';
      }
    } else if (this.state === 'WALKING_OUT') {
      const dx = this.targetX - this.x, dy = this.targetY - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) {
        this.x = this.targetX; this.y = this.targetY;
        this.state = 'AT_DEST'; 
        this.timer = Math.floor(Math.random() * 160) + 100;
      } else {
        this.x += (dx / dist) * 1.8; 
        this.y += (dy / dist) * 1.8;
      }
    } else if (this.state === 'AT_DEST') {
      this.timer--;
      if (this.timer <= 0) {
        this.targetX = this.deskX; 
        this.targetY = this.deskY;
        this.state = 'WALKING_BACK';
      }
    } else if (this.state === 'WALKING_BACK') {
      const dx = this.targetX - this.x, dy = this.targetY - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) {
        this.x = this.deskX; this.y = this.deskY;
        this.state = 'DESK'; 
        this.timer = Math.floor(Math.random() * 240) + 160;
      } else {
        this.x += (dx / dist) * 1.8; 
        this.y += (dy / dist) * 1.8;
      }
    }
  }

  draw() {
    const isWalking = (this.state === 'WALKING_OUT' || this.state === 'WALKING_BACK');
    const bob = (this.state === 'DESK') ? Math.sin(frame * 0.1) * 2 : 0;
    const legOffset = isWalking ? Math.sin(frame * 0.22) * 6 : 0;

    // --- SPRITE RENDERING (32x45 px scale) ---
    // Hair / Head
    ctx.fillStyle = this.hairColor;
    ctx.fillRect(this.x - 10, this.y - 42 + bob, 20, 14);
    // Face
    ctx.fillStyle = '#f1c27d';
    ctx.fillRect(this.x - 8, this.y - 32 + bob, 16, 12);
    // Eyes
    ctx.fillStyle = '#111';
    ctx.fillRect(this.x - 5, this.y - 28 + bob, 3, 3);
    ctx.fillRect(this.x + 2, this.y - 28 + bob, 3, 3);
    // Shirt / Suit Body
    ctx.fillStyle = this.shirtColor;
    ctx.fillRect(this.x - 12, this.y - 20 + bob, 24, 18);
    // Collar / Tie Accent
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(this.x - 3,ヴェル = this.y - 20 + bob, 6, 8);

    // Pants & Legs
    ctx.fillStyle = '#1e2530';
    if (isWalking) {
      ctx.fillRect(this.x - 9, this.y - 2, 7, 16 + legOffset);
      ctx.fillRect(this.x + 2, this.y - 2, 7, 16 - legOffset);
    } else {
      ctx.fillRect(this.x - 9, this.y - 2 + bob, 18, 16);
    }

    // --- FLOATING HUD NAMEPLATE ---
    let actionTag = "📊 DESK";
    if (this.state === 'AT_DEST') actionTag = (this.destName === 'PANTRY') ? "☕ PANTRY" : "⚙️ SERVERS";
    else if (isWalking) actionTag = "🚶 MOVING";

    const labelText = `${this.roleBadge} ${this.name} [${actionTag}]`;
    ctx.font = 'bold 12px monospace';
    const textWidth = ctx.measureText(labelText).width + 16;

    // Badge Background
    ctx.fillStyle = 'rgba(15, 20, 30, 0.92)';
    ctx.fillRect(this.x - textWidth/2, this.y - 68 + bob, textWidth, 22);
    ctx.strokeStyle = this.shirtColor;
    ctx.lineWidth = 1.5;
    ctx.strokeRect(this.x - textWidth/2, this.y - 68 + bob, textWidth, 22);

    // Badge Text
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.fillText(labelText, this.x, this.y - 53 + bob);
  }
}

const staffMembers = [
  new StaffMember('ALEX', 'QUANT', 340, 230, '#2ecc71', '#f39c12', '📈'),
  new StaffMember('MARCUS', 'CIO', 600, 230, '#3498db', '#e67e22', '🏛️'),
  new StaffMember('SARAH', 'RISK', 860, 230, '#e74c3c', '#9b59b6', '🛡️')
];

function drawEnvironment() {
  // Tiled Slate Floor
  for (let x = 0; x < canvas.width; x += 40) {
    for (let y = 40; y < canvas.height; y += 40) {
      ctx.fillStyle = ((x + y) % 80 === 0) ? '#111520' : '#141926';
      ctx.fillRect(x, y, 40, 40);
      ctx.strokeStyle = '#1a2030';
      ctx.lineWidth = 0.5;
      ctx.strokeRect(x, y, 40, 40);
    }
  }

  // Top Telemetry Header Bar
  ctx.fillStyle = '#161b26';
  ctx.fillRect(0, 0, canvas.width, 40);
  ctx.strokeStyle = '#2d3548';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, 40); ctx.lineTo(canvas.width, 40); ctx.stroke();

  ctx.fillStyle = '#2ecc71'; ctx.font = 'bold 13px monospace'; ctx.textAlign = 'left';
  ctx.fillText("● JC TRADING HOUSE — MAIN TRADING FLOOR & TELEMETRY DESK", 20, 25);

  let pulse = (Math.sin(frame * 0.1) + 1) / 2;
  ctx.fillStyle = `rgba(46, 204, 113, ${pulse})`;
  ctx.beginPath(); ctx.arc(1130, 22, 6, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ffffff'; ctx.font = 'bold 12px monospace'; ctx.fillText("LIVE SYSTEM", 1145, 26);

  // --- ZONE 1: SERVER ARRAY (LEFT) ---
  ctx.fillStyle = '#181d2a'; ctx.fillRect(20, 60, 160, 330);
  ctx.strokeStyle = '#2a3347'; ctx.lineWidth = 2; ctx.strokeRect(20, 60, 160, 330);
  ctx.fillStyle = '#00f0ff'; ctx.font = 'bold 12px monospace'; ctx.textAlign = 'center';
  ctx.fillText("🖥️ SERVER ARRAY", 100, 82);

  // Server Racks with Blinking LEDs
  for (let r = 0; r < 3; r++) {
    let ry = 100 + r * 95;
    ctx.fillStyle = '#0f131d'; ctx.fillRect(35, ry, 130, 80);
    ctx.strokeStyle = '#3b4661'; ctx.strokeRect(35, ry, 130, 80);
    for (let slot = 0; slot < 4; slot++) {
      ctx.fillStyle = '#1a2233'; ctx.fillRect(42, ry + 8 + slot * 16, 116, 12);
      let ledOn = (Math.sin(frame * 0.2 + r + slot) > 0);
      ctx.fillStyle = ledOn ? (slot % 2 === 0 ? '#2ecc71' : '#00f0ff') : '#555';
      ctx.fillRect(142, ry + 12 + slot * 16, 10, 4);
    }
  }

  // --- ZONE 2: PANTRY & LOUNGE (RIGHT) ---
  ctx.fillStyle = '#181d2a'; ctx.fillRect(1020, 60, 160, 330);
  ctx.strokeStyle = '#2a3347'; ctx.lineWidth = 2; ctx.strokeRect(1020, 60, 160, 330);
  ctx.fillStyle = '#f39c12'; ctx.font = 'bold 12px monospace'; ctx.textAlign = 'center';
  ctx.fillText("☕ PANTRY & BREAKROOM", 1100, 82);

  // Espresso Machine
  ctx.fillStyle = '#2c3e50'; ctx.fillRect(1040, 120, 120, 70);
  ctx.fillStyle = '#e67e22'; ctx.fillRect(1055, 140, 30, 40);
  // Steam effect
  let steamY = (frame * 1.5) % 30;
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.beginPath(); ctx.arc(1070, 135 - steamY, 4, 0, Math.PI * 2); ctx.fill();

  // Water Cooler
  ctx.fillStyle = '#3498db'; ctx.beginPath(); ctx.arc(1135, 230, 14, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ecf0f1'; ctx.fillRect(1125, 244, 20, 40);

  // --- ZONE 3: TRADING WORKSTATIONS ---
  const workstations = [
    { name: "QUANT LAB (ALEX)", x: 340, y: 230, accent: "#2ecc71" },
    { name: "CIO DESK (MARCUS)", x: 600, y: 230, accent: "#3498db" },
    { name: "RISK DESK (SARAH)", x: 860, y: 230, accent: "#e74c3c" }
  ];

  workstations.forEach(ws => {
    // Desk Surface
    ctx.fillStyle = '#222838'; ctx.fillRect(ws.x - 85, ws.y + 10, 170, 55);
    ctx.strokeStyle = '#3d4863'; ctx.lineWidth = 2; ctx.strokeRect(ws.x - 85, ws.y + 10, 170, 55);
    
    // Station Overhead Title Banner
    ctx.fillStyle = '#121622'; ctx.fillRect(ws.x - 85, ws.y - 95, 170, 24);
    ctx.strokeStyle = ws.accent; ctx.lineWidth = 1.5; ctx.strokeRect(ws.x - 85, ws.y - 95, 170, 24);
    ctx.fillStyle = '#ffffff'; ctx.font = 'bold 11px monospace'; ctx.textAlign = 'center';
    ctx.fillText(ws.name, ws.x, ws.y - 79);

    // Center Main Monitor (Live Candlestick Graphic)
    ctx.fillStyle = '#0a0d14'; ctx.fillRect(ws.x - 35, ws.y - 60, 70, 48);
    ctx.strokeStyle = ws.accent; ctx.lineWidth = 1.5; ctx.strokeRect(ws.x - 35, ws.y - 60, 70, 48);
    // Simulated Candles
    ctx.fillStyle = '#2ecc71'; ctx.fillRect(ws.x - 25, ws.y - 45, 6, 20);
    ctx.fillStyle = '#e74c3c'; ctx.fillRect(ws.x - 12, ws.y - 50, 6, 25);
    ctx.fillStyle = '#2ecc71'; ctx.fillRect(ws.x + 2, ws.y - 38, 6, 18);
    ctx.fillStyle = '#2ecc71'; ctx.fillRect(ws.x + 15, ws.y - 52, 6, 30);

    // Left Side Monitor
    ctx.fillStyle = '#0a0d14'; ctx.fillRect(ws.x - 78, ws.y - 52, 38, 38);
    ctx.strokeStyle = '#2d364d'; ctx.strokeRect(ws.x - 78, ws.y - 52, 38, 38);
    ctx.fillStyle = '#00f0ff'; ctx.fillRect(ws.x - 72, ws.y - 44, 26, 3);
    ctx.fillRect(ws.x - 72, ws.y - 36, 20, 3);
    ctx.fillRect(ws.x - 72, ws.y - 28, 24, 3);

    // Right Side Monitor
    ctx.fillStyle = '#0a0d14'; ctx.fillRect(ws.x + 40, ws.y - 52, 38, 38);
    ctx.strokeStyle = '#2d364d'; ctx.strokeRect(ws.x + 40, ws.y - 52, 38, 38);
    ctx.fillStyle = '#f1c40f'; ctx.fillRect(ws.x + 46, ws.y - 42, 26, 18);

    // Keyboard & Ergonomic Chair Backing
    ctx.fillStyle = '#121622'; ctx.fillRect(ws.x - 22, ws.y + 16, 44, 12);
    ctx.fillStyle = ws.accent; ctx.fillRect(ws.x - 20, ws.y + 58, 40, 8);
  });
}

function animate() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawEnvironment();
  staffMembers.forEach(s => { s.update(); s.draw(); });
  frame++;
  requestAnimationFrame(animate);
}
animate();
</script>
</body>
</html>
"""

components.html(pixel_floor_html, height=460, scrolling=False)

st.markdown("---")

# 9. Main Dashboard Layout (Fixed Timeframe Buttons & Q&A)
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