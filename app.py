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
    .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 98% !important; }
    .main { background-color: #0b0e14; }
    div[data-testid="stMetricValue"] { font-size: 1.25rem !important; font-weight: bold; }
    .stMetric { background-color: #141824; padding: 12px; border-radius: 8px; border: 1px solid #232a3b; }
    .stChatInput { border-color: #2a344a !important; }
    .stButton>button { border-radius: 6px; }
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
        {"role": "assistant", "content": "🏛️ **Desk**: Operational. Quantitative & Risk agents standing by for prompt orders."}
    ]
if "quick_prompt" not in st.session_state:
    st.session_state.quick_prompt = None

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

# 6. Dynamic Model Discovery LLM Engine
def query_agent_llm(prompt: str, context: dict) -> str:
    if not GEMINI_API_KEY:
        return "⚠️ **System**: Missing Gemini API Key. Cannot process."

    system_instruction = "You are an institutional multi-agent trading desk. Keep answers concise, direct, and highly actionable."
    full_prompt = f"Market Context for {context['ticker']}: {context}\n\nUser Question: {prompt}"
    last_error = ""

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

# 7. Main UI Header & Watchlist Selector
st.title("🏛️ JC TRADING HOUSE")
st.caption("Institutional Multi-Agent Trading Desk & Real-time Telemetry Operations")

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
    new_asset = st.text_input("Add Ticker", placeholder="e.g., MSFT", label_visibility="collapsed").strip().upper()
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

df_current = fetch_asset_data(st.session_state.current_ticker, st.session_state.chart_timeframe)
indicators = compute_indicators(df_current)
indicators['ticker'] = st.session_state.current_ticker

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Active Asset", st.session_state.current_ticker)
kpi2.metric("Last Price", f"${indicators['price']}")
kpi3.metric("RSI (14)", indicators['rsi'])
kpi4.metric("20-SMA Trend", indicators['trend'])
kpi5.metric("ATR Volatility", f"${indicators['atr']}")

st.markdown("<br>", unsafe_allow_html=True)

# 8. High-Detail Animated Pixel Floor Engine
pixel_floor_html = """
<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #0b0e14; font-family: 'Courier New', monospace; }
  .canvas-container { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
  canvas { display: block; width: 100%; height: 100%; max-height: 520px; border: 2px solid #232838; border-radius: 10px; background: #0c0f17; image-rendering: pixelated; }
</style>
</head>
<body>
<div class="canvas-container">
  <canvas id="tradingFloor" width="1200" height="500"></canvas>
</div>
<script>
const canvas = document.getElementById('tradingFloor');
const ctx = canvas.getContext('2d');
let frame = 0;

let tickerOffset = 0;
let newsOffset = 0;

const stockTickerItems = [
  { symbol: "BTC-USD", price: "92,450.10", change: "+2.4%", up: true },
  { symbol: "NVDA", price: "138.20", change: "+1.8%", up: true },
  { symbol: "TSLA", price: "248.50", change: "-0.9%", up: false },
  { symbol: "ETH-USD", price: "3,450.80", change: "+3.1%", up: true },
  { symbol: "S68.SG", price: "10.85", change: "+0.4%", up: true },
  { symbol: "AAPL", price: "228.10", change: "-0.3%", up: false }
];

const newsHeadlines = [
  "⚡ [QUANT ENGINE]: REAL-TIME MOMENTUM MATRIX ONLINE",
  "📈 [MARKET BREAKING]: US FED PREPARES LIQUIDITY INJECTION",
  "🛡️ [RISK MONITOR]: VaR MAINTAINED WITHIN 95% PARAMETERS",
  "🏛️ [CIO DESK]: MARCUS DISPATCHING Q4 STRATEGY ALLOCATION",
  "☕ [PANTRY]: ESPRESSO BARISTA STATION OPERATIONAL"
];

class StaffMember {
  constructor(name, title, deskX, deskY, shirtColor, hairColor, roleBadge, thoughts) {
    this.name = name;
    this.title = title;
    this.deskX = deskX; 
    this.deskY = deskY;
    this.x = deskX; 
    this.y = deskY;
    this.shirtColor = shirtColor;
    this.hairColor = hairColor;
    this.roleBadge = roleBadge;
    this.thoughts = thoughts;
    this.currentThought = thoughts[0];
    this.state = 'DESK';
    this.timer = Math.floor(Math.random() * 120) + 80;
    this.targetX = deskX; 
    this.targetY = deskY;
    this.destName = '';
  }

  update() {
    if (this.state === 'DESK') {
      this.timer--;
      if (this.timer <= 0) {
        const rand = Math.random();
        if (rand < 0.3) {
          this.targetX = 1080 + Math.random() * 30; 
          this.targetY = 280;
          this.destName = 'PANTRY';
        } else if (rand < 0.6) {
          this.targetX = 90 + Math.random() * 30; 
          this.targetY = 280;
          this.destName = 'SERVERS';
        } else {
          this.targetX = 580 + Math.random() * 40; 
          this.targetY = 165;
          this.destName = 'WHITEBOARD';
        }
        this.state = 'WALKING_OUT';
        this.currentThought = this.thoughts[Math.floor(Math.random() * this.thoughts.length)];
      }
    } else if (this.state === 'WALKING_OUT') {
      const dx = this.targetX - this.x, dy = this.targetY - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) {
        this.x = this.targetX; this.y = this.targetY;
        this.state = 'AT_DEST'; 
        this.timer = Math.floor(Math.random() * 160) + 100;
      } else {
        this.x += (dx / dist) * 2.2; 
        this.y += (dy / dist) * 2.2;
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
        this.timer = Math.floor(Math.random() * 200) + 120;
      } else {
        this.x += (dx / dist) * 2.2; 
        this.y += (dy / dist) * 2.2;
      }
    }
  }

  draw() {
    const isWalking = (this.state === 'WALKING_OUT' || this.state === 'WALKING_BACK');
    const bob = (this.state === 'DESK') ? Math.sin(frame * 0.15) * 2 : 0;
    const typingHand = (this.state === 'DESK') ? Math.sin(frame * 0.4) * 3 : 0;
    const legOffset = isWalking ? Math.sin(frame * 0.28) * 6 : 0;

    // Head / Hair
    ctx.fillStyle = this.hairColor;
    ctx.fillRect(this.x - 10, this.y - 42 + bob, 20, 14);
    // Face
    ctx.fillStyle = '#f1c27d';
    ctx.fillRect(this.x - 8, this.y - 32 + bob, 16, 12);
    // Eyes
    ctx.fillStyle = '#111';
    ctx.fillRect(this.x - 5, this.y - 28 + bob, 3, 3);
    ctx.fillRect(this.x + 2, this.y - 28 + bob, 3, 3);
    // Body / Suit
    ctx.fillStyle = this.shirtColor;
    ctx.fillRect(this.x - 12, this.y - 20 + bob, 24, 18);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(this.x - 3, this.y - 20 + bob, 6, 8);

    // Arms / Typing
    if (this.state === 'DESK') {
      ctx.fillStyle = '#f1c27d';
      ctx.fillRect(this.x - 14, this.y - 10 + typingHand, 5, 8);
      ctx.fillRect(this.x + 9, this.y - 10 - typingHand, 5, 8);
    }

    // Legs
    ctx.fillStyle = '#1e2530';
    if (isWalking) {
      ctx.fillRect(this.x - 9, this.y - 2, 7, 16 + legOffset);
      ctx.fillRect(this.x + 2, this.y - 2, 7, 16 - legOffset);
    } else {
      ctx.fillRect(this.x - 9, this.y - 2 + bob, 18, 16);
    }

    // Floating Badge & Speech Bubble
    let actionTag = "💻 TYPING";
    if (this.state === 'AT_DEST') {
      if (this.destName === 'PANTRY') actionTag = "☕ PANTRY";
      else if (this.destName === 'SERVERS') actionTag = "⚙️ SERVERS";
      else actionTag = "📊 WHITEBOARD";
    } else if (isWalking) {
      actionTag = "🚶 MOVING";
    }

    const labelText = `${this.roleBadge} ${this.name} [${actionTag}]`;
    ctx.font = 'bold 11px monospace';
    const textWidth = ctx.measureText(labelText).width + 14;

    ctx.fillStyle = 'rgba(12, 16, 25, 0.95)';
    ctx.fillRect(this.x - textWidth/2, this.y - 68 + bob, textWidth, 20);
    ctx.strokeStyle = this.shirtColor;
    ctx.lineWidth = 1.5;
    ctx.strokeRect(this.x - textWidth/2, this.y - 68 + bob, textWidth, 20);

    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.fillText(labelText, this.x, this.y - 54 + bob);

    // Thought Bubble
    if (Math.sin(frame * 0.05 + this.x) > 0.3) {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.fillRect(this.x + 20, this.y - 85 + bob, 110, 22);
      ctx.strokeStyle = '#333'; ctx.lineWidth = 1;
      ctx.strokeRect(this.x + 20, this.y - 85 + bob, 110, 22);
      ctx.fillStyle = '#111'; ctx.font = '10px monospace'; ctx.textAlign = 'left';
      ctx.fillText(`💬 "${this.currentThought}"`, this.x + 24, y = this.y - 70 + bob);
    }
  }
}

const staffMembers = [
  new StaffMember('ALEX', 'QUANT', 270, 280, '#2ecc71', '#f39c12', '📈', ['Checking RSI', 'Backtesting...', 'Alpha Found!']),
  new StaffMember('MARCUS', 'CIO', 500, 280, '#3498db', '#e67e22', '🏛️', ['Rebalancing', 'Check Volatility', 'Macro Shift']),
  new StaffMember('SARAH', 'RISK', 730, 280, '#e74c3c', '#9b59b6', '🛡️', ['VaR Safe', 'Check Exposure', 'Stress Test']),
  new StaffMember('ELENA', 'DEV', 950, 280, '#9b59b6', '#34495e', '⚡', ['HFT Low Latency', 'Fixing API', 'Server Green'])
];

function drawEnvironment() {
  // Tile Flooring
  for (let x = 0; x < canvas.width; x += 40) {
    for (let y = 40; y < canvas.height - 30; y += 40) {
      ctx.fillStyle = ((x + y) % 80 === 0) ? '#101420' : '#131826';
      ctx.fillRect(x, y, 40, 40);
      ctx.strokeStyle = '#1a2133';
      ctx.lineWidth = 0.5;
      ctx.strokeRect(x, y, 40, 40);
    }
  }

  // Top Telemetry Header
  ctx.fillStyle = '#141824';
  ctx.fillRect(0, 0, canvas.width, 40);
  ctx.strokeStyle = '#283144';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, 40); ctx.lineTo(canvas.width, 40); ctx.stroke();

  ctx.fillStyle = '#2ecc71'; ctx.font = 'bold 13px monospace'; ctx.textAlign = 'left';
  ctx.fillText("● JC TRADING HOUSE — MAIN FLOOR & TELEMETRY DESK", 15, 25);

  // Top Moving Stock Ticker
  tickerOffset = (tickerOffset + 1.2) % 1200;
  ctx.fillStyle = '#0d111a'; ctx.fillRect(480, 6, 600, 28);
  ctx.strokeStyle = '#2d374d'; ctx.strokeRect(480, 6, 600, 28);
  
  ctx.save();
  ctx.beginPath(); ctx.rect(482, 8, 596, 24); ctx.clip();
  let tickerX = 1080 - tickerOffset;
  ctx.font = 'bold 12px monospace'; ctx.textAlign = 'left';
  stockTickerItems.forEach(item => {
    ctx.fillStyle = '#00f0ff'; ctx.fillText(item.symbol, tickerX, 24);
    ctx.fillStyle = '#ffffff'; ctx.fillText(`$${item.price}`, tickerX + 65, 24);
    ctx.fillStyle = item.up ? '#2ecc71' : '#e74c3c'; ctx.fillText(item.change, tickerX + 135, 24);
    tickerX += 200;
  });
  ctx.restore();

  let pulse = (Math.sin(frame * 0.1) + 1) / 2;
  ctx.fillStyle = `rgba(46, 204, 113, ${pulse})`;
  ctx.beginPath(); ctx.arc(1115, 20, 5, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ffffff'; ctx.font = 'bold 11px monospace'; ctx.fillText("LIVE", 1125, 24);

  // Wall-Mounted Bloomberg TV (Top Center)
  ctx.fillStyle = '#090c12'; ctx.fillRect(480, 55, 240, 85);
  ctx.strokeStyle = '#3a4763'; ctx.lineWidth = 2; ctx.strokeRect(480, 55, 240, 85);
  ctx.fillStyle = '#f39c12'; ctx.font = 'bold 11px monospace'; ctx.textAlign = 'center';
  ctx.fillText("📺 BLOOMBERG TERMINAL FEED", 600, 70);
  
  // Sine chart on Bloomberg TV
  ctx.strokeStyle = '#00f0ff'; ctx.lineWidth = 1.5; ctx.beginPath();
  for (let px = 0; px < 210; px += 5) {
    let py = 105 + Math.sin((frame + px) * 0.08) * 15;
    if (px === 0) ctx.moveTo(495 + px, py); else ctx.lineTo(495 + px, py);
  }
  ctx.stroke();

  // Whiteboard Strategy Board (Top Middle-Left)
  ctx.fillStyle = '#e8ecef'; ctx.fillRect(260, 55, 190, 85);
  ctx.strokeStyle = '#b0b7c0'; ctx.lineWidth = 3; ctx.strokeRect(260, 55, 190, 85);
  ctx.fillStyle = '#2c3e50'; ctx.font = 'bold 11px monospace'; ctx.textAlign = 'center';
  ctx.fillText("📋 STRATEGY BOARD", 355, 72);
  ctx.fillStyle = '#e74c3c'; ctx.font = '10px monospace'; ctx.fillText("VAR LIMIT: < 2.5%", 355, 88);
  ctx.fillStyle = '#27ae60'; ctx.fillText("MOMENTUM: BULL RUN", 355, 102);
  ctx.fillStyle = '#2980b9'; ctx.fillText("TARGET: +15% ALLOC", 355, 116);

  // Server Array (Left)
  ctx.fillStyle = '#141824'; ctx.fillRect(20, 55, 150, 400);
  ctx.strokeStyle = '#2a3448'; ctx.lineWidth = 2; ctx.strokeRect(20, 55, 150, 400);
  ctx.fillStyle = '#00f0ff'; ctx.font = 'bold 11px monospace'; ctx.textAlign = 'center';
  ctx.fillText("🖥️ HIGH-SPEED SERVERS", 95, 75);

  for (let r = 0; r < 4; r++) {
    let ry = 90 + r * 88;
    ctx.fillStyle = '#0c0f17'; ctx.fillRect(32, ry, 126, 75);
    ctx.strokeStyle = '#323f57'; ctx.strokeRect(32, ry, 126, 75);
    for (let slot = 0; slot < 4; slot++) {
      ctx.fillStyle = '#182030'; ctx.fillRect(38, ry + 6 + slot * 16, 114, 11);
      let ledOn = (Math.sin(frame * 0.2 + r + slot) > 0);
      ctx.fillStyle = ledOn ? (slot % 2 === 0 ? '#2ecc71' : '#00f0ff') : '#444';
      ctx.fillRect(138, ry + 10 + slot * 16, 8, 4);
    }
  }

  // Pantry & Coffee Lounge (Right)
  ctx.fillStyle = '#141824'; ctx.fillRect(1030, 55, 150, 400);
  ctx.strokeStyle = '#2a3448'; ctx.lineWidth = 2; ctx.strokeRect(1030, 55, 150, 400);
  ctx.fillStyle = '#f39c12'; ctx.font = 'bold 11px monospace'; ctx.textAlign = 'center';
  ctx.fillText("☕ BARISTA LOUNGE", 1105, 75);

  // Coffee Machine & Water Cooler
  ctx.fillStyle = '#2c3e50'; ctx.fillRect(1050, 110, 110, 65);
  ctx.fillStyle = '#e67e22'; ctx.fillRect(1065, 130, 25, 35);
  let steamY = (frame * 1.5) % 25;
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.beginPath(); ctx.arc(1077, 125 - steamY, 3, 0, Math.PI * 2); ctx.fill();

  // Water Cooler Bubbles
  ctx.fillStyle = '#3498db'; ctx.beginPath(); ctx.arc(1135, 230, 14, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ecf0f1'; ctx.fillRect(1125, 244, 20, 35);
  if (frame % 20 < 10) {
    ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(1135, 232, 3, 0, Math.PI * 2); ctx.fill();
  }

  // Potted Monstera Plants
  ctx.fillStyle = '#7f8c8d'; ctx.fillRect(190, 400, 25, 30);
  ctx.fillStyle = '#27ae60';
  ctx.beginPath(); ctx.arc(195, 390, 12, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.arc(210, 392, 10, 0, Math.PI * 2); ctx.fill();

  // Workstations
  const workstations = [
    { name: "QUANT (ALEX)", x: 270, y: 280, accent: "#2ecc71" },
    { name: "CIO (MARCUS)", x: 500, y: 280, accent: "#3498db" },
    { name: "RISK (SARAH)", x: 730, y: 280, accent: "#e74c3c" },
    { name: "DEV (ELENA)", x: 950, y: 280, accent: "#9b59b6" }
  ];

  workstations.forEach(ws => {
    // Desk Surface
    ctx.fillStyle = '#1e2433'; ctx.fillRect(ws.x - 70, ws.y + 10, 140, 50);
    ctx.strokeStyle = '#35425e'; ctx.lineWidth = 1.5; ctx.strokeRect(ws.x - 70, ws.y + 10, 140, 50);
    
    // Desk Banner Tag
    ctx.fillStyle = '#0f131c'; ctx.fillRect(ws.x - 70, ws.y - 92, 140, 22);
    ctx.strokeStyle = ws.accent; ctx.lineWidth = 1.5; ctx.strokeRect(ws.x - 70, ws.y - 92, 140, 22);
    ctx.fillStyle = '#ffffff'; ctx.font = 'bold 10px monospace'; ctx.textAlign = 'center';
    ctx.fillText(ws.name, ws.x, ws.y - 77);

    // Center Candlestick Monitor
    ctx.fillStyle = '#080b12'; ctx.fillRect(ws.x - 30, ws.y - 60, 60, 42);
    ctx.strokeStyle = ws.accent; ctx.lineWidth = 1.5; ctx.strokeRect(ws.x - 30, ws.y - 60, 60, 42);
    
    let chartShift = Math.sin(frame * 0.12 + ws.x) * 3;
    ctx.fillStyle = '#2ecc71'; ctx.fillRect(ws.x - 20, ws.y - 48 + chartShift, 5, 18);
    ctx.fillStyle = '#e74c3c'; ctx.fillRect(ws.x - 10, ws.y - 52 - chartShift, 5, 22);
    ctx.fillStyle = '#2ecc71'; ctx.fillRect(ws.x + 2, ws.y - 40 + chartShift, 5, 16);
    ctx.fillStyle = '#2ecc71'; ctx.fillRect(ws.x + 12, ws.y - 54 - chartShift, 5, 26);

    // Side Monitors
    ctx.fillStyle = '#080b12'; ctx.fillRect(ws.x - 65, ws.y - 52, 32, 32);
    ctx.strokeStyle = '#273147'; ctx.strokeRect(ws.x - 65, ws.y - 52, 32, 32);
    ctx.fillStyle = '#00f0ff'; ctx.fillRect(ws.x - 60, ws.y - 45, 22, 2);
    ctx.fillRect(ws.x - 60, ws.y - 38, 16, 2);

    ctx.fillStyle = '#080b12'; ctx.fillRect(ws.x + 33, ws.y - 52, 32, 32);
    ctx.strokeStyle = '#273147'; ctx.strokeRect(ws.x + 33, ws.y - 52, 32, 32);
    ctx.fillStyle = '#f1c40f'; ctx.fillRect(ws.x + 38, ws.y - 44, 22, 16);

    // Keyboard & Coffee Mug
    ctx.fillStyle = '#10141f'; ctx.fillRect(ws.x - 18, ws.y + 14, 36, 10);
    ctx.fillStyle = ws.accent; ctx.fillRect(ws.x + 24, ws.y + 16, 6, 8);
  });

  // Bottom Live News Ticker Bar
  ctx.fillStyle = '#080b12'; ctx.fillRect(0, 470, canvas.width, 30);
  ctx.strokeStyle = '#f1c40f'; ctx.lineWidth = 1; ctx.strokeRect(0, 470, canvas.width, 30);
  
  newsOffset = (newsOffset + 1.5) % 2400;
  ctx.save();
  ctx.beginPath(); ctx.rect(0, 470, canvas.width, 30); ctx.clip();
  ctx.fillStyle = '#f1c40f'; ctx.font = 'bold 12px monospace'; ctx.textAlign = 'left';
  let fullNewsText = newsHeadlines.join("  ---  ");
  ctx.fillText(fullNewsText, 1200 - newsOffset, 490);
  ctx.restore();
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

components.html(pixel_floor_html, height=520, scrolling=False)

st.markdown("---")

# 9. Main Dashboard & Expanded Live Terminal
col_left, col_right = st.columns([5, 6], gap="large")

with col_left:
    st.subheader(f"📊 {st.session_state.current_ticker} Market Analytics")
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
            margin=dict(l=10, r=10, t=10, b=10), height=380, xaxis_rangeslider_visible=False,
            paper_bgcolor='#0b0e14', plot_bgcolor='#0b0e14',
            xaxis=dict(gridcolor='#1e2433', tickfont=dict(color='#85929e')),
            yaxis=dict(gridcolor='#1e2433', tickfont=dict(color='#85929e'))
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No price data found.")

    if st.button("🚀 Dispatch Strategy Sprint", type="primary", use_container_width=True):
        with st.spinner("🏛️ Multi-agent desk evaluating strategy parameters..."):
            sprint_prompt = f"Run institutional trade assessment for portfolio allocation of ${capital * (max_alloc_pct/100)}."
            assessment = query_agent_llm(sprint_prompt, indicators)
            score = 50 + (20 if indicators['trend'] == "BULLISH" else -20)
            score = max(0, min(100, score))
            st.session_state.sprint_results = {
                "signal": "BUY" if score >= 60 else "SELL" if score <= 40 else "HOLD",
                "score": score,
                "summary": assessment
            }
            st.rerun()

    if st.session_state.sprint_results:
        st.markdown("##### 📋 CIO Strategy Dispatch Results")
        res = st.session_state.sprint_results
        sc1, sc2 = st.columns(2)
        sc1.metric("CIO Signal", res['signal'])
        sc2.metric("Confidence Score", f"{res['score']}/100")
        st.info(res['summary'])

with col_right:
    st.subheader("💬 Live Desk Q&A Terminal")
    st.caption("Direct telemetry line to Quant, Risk, CIO, and Execution agents")

    # Quick Execution Prompt Chips
    q1, q2, q3 = st.columns(3)
    if q1.button("⚡ Volatility Check", use_container_width=True):
        st.session_state.quick_prompt = "Evaluate current ATR volatility and risk bounds for this asset."
    if q2.button("🛡️ VaR Analysis", use_container_width=True):
        st.session_state.quick_prompt = "Calculate potential drawdown risk under extreme tail-risk scenarios."
    if q3.button("📈 Momentum Signals", use_container_width=True):
        st.session_state.quick_prompt = "Provide momentum trend analysis based on RSI and Moving Average crossovers."

    # Expanded 520px Terminal Container
    chat_box = st.container(height=520)
    with chat_box:
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(sanitize_financial_text(msg["content"]))

    # Input execution logic
    user_prompt = st.chat_input("Submit query to desk agents...")
    if st.session_state.quick_prompt:
        user_prompt = st.session_state.quick_prompt
        st.session_state.quick_prompt = None

    if user_prompt:
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        reply = query_agent_llm(user_prompt, indicators)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()