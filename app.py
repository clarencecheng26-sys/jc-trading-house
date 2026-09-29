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
    initial_sidebar_state="expanded"
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

# Helper function: Sanitizes LaTeX and escapes currency symbols
def sanitize_financial_text(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'\\mathbf\{([^}]+)\}', r'**\1**', text)
    clean = re.sub(r'\\mathit\{([^}]+)\}', r'*\1*', clean)
    clean = re.sub(r'\\mathbf', '', clean)
    clean = re.sub(r'(?<!\\)\$(\d+)', r'\\$\1', clean)
    return clean

# 3. Safe API Key Retrieval
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

# Sidebar Controls & Watchlist Management
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
    st.subheader("📌 Watchlist Management")
    
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = ["BTC-USD", "NVDA", "TSLA", "ETH-USD", "S68.SG", "AAPL", "PLTR"]
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

    # Asset Addition & Deletion Controls
    with st.expander("➕ Add / Remove Asset"):
        new_asset = st.text_input("New Asset Ticker (e.g. MSFT, GC=F)").strip().upper()
        col_add, col_del = st.columns(2)
        with col_add:
            if st.button("Add Symbol", use_container_width=True):
                if new_asset and new_asset not in st.session_state.watchlist:
                    st.session_state.watchlist.append(new_asset)
                    st.session_state.current_ticker = new_asset
                    st.success(f"Added {new_asset}")
                    st.rerun()
                elif new_asset in st.session_state.watchlist:
                    st.warning("Already in Watchlist.")
        with col_del:
            if st.button("Delete Active", use_container_width=True):
                if len(st.session_state.watchlist) > 1:
                    removed = st.session_state.current_ticker
                    st.session_state.watchlist.remove(removed)
                    st.session_state.current_ticker = st.session_state.watchlist[0]
                    st.success(f"Removed {removed}")
                    st.rerun()
                else:
                    st.error("Min 1 asset required.")

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

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean()

    sma20 = float(close.rolling(window=min(20, len(df))).mean().iloc[-1])
    tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(min(14, len(df))).mean().iloc[-1]) if len(tr) > 0 else 0.0

    trend = "BULLISH" if latest_price > sma20 else "BEARISH" if latest_price < sma20 else "NEUTRAL"

    return {
        "price": round(latest_price, 2),
        "rsi": round(rsi, 2),
        "macd": round(float(macd.iloc[-1]), 3) if not macd.empty else 0.0,
        "macd_signal": round(float(macd_signal.iloc[-1]), 3) if not macd_signal.empty else 0.0,
        "atr": round(atr, 2),
        "trend": trend,
        "sma20": round(sma20, 2)
    }

# 5. Robust Multi-Model LLM Query Engine
def query_agent_llm(prompt: str, context: dict) -> str:
    if not GEMINI_API_KEY:
        return (f"📊 **System (Heuristic Mode)**: Asset `{context['ticker']}` | Price: `${context['price']}` | "
                f"RSI: `{context['rsi']}` | Trend: `{context['trend']}`. Provide a valid Gemini API Key in the sidebar.")

    candidate_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    system_instruction = (
        "You are an institutional multi-agent trading desk: "
        "1. Alex (Quant Agent - Technical momentum, RSI, MACD) "
        "2. Sarah (Risk Agent - ATR bounds, position limits) "
        "3. Marcus (CIO Agent - Consensus synthesis). "
        "Format dollar figures cleanly with numbers like $350.00 rather than raw LaTeX syntax."
    )
    full_prompt = f"Market Context for {context['ticker']}: {context}\n\nUser Question: {prompt}"

    last_error = ""

    # Strategy 1: google.genai Client
    if HAS_GENAI:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
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
                    if response and response.text:
                        return sanitize_financial_text(response.text)
                except Exception as e:
                    last_error = str(e)
                    continue
        except Exception as e:
            last_error = str(e)

    # Strategy 2: Legacy google.generativeai Fallback
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=GEMINI_API_KEY)
        for model_id in candidate_models:
            try:
                model = legacy_genai.GenerativeModel(
                    model_name=model_id,
                    system_instruction=system_instruction
                )
                response = model.generate_content(full_prompt)
                if response and response.text:
                    return sanitize_financial_text(response.text)
            except Exception as e:
                last_error = str(e)
                continue
    except Exception as e:
        if not last_error:
            last_error = str(e)

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

# 7. Animated HTML5 Pixel Floor with Autonomous Walking Staff & Responsive Scaling
pixel_floor_html = """
<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background-color: #0e1117; font-family: monospace; }
  .canvas-wrapper { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }
  canvas { display: block; width: 100%; height: 100%; border: 1px solid #2d3139; border-radius: 8px; background: #12151f; }
</style>
</head>
<body>
<div class="canvas-wrapper">
  <canvas id="floor" width="1400" height="250"></canvas>
</div>
<script>
const canvas = document.getElementById('floor');
const ctx = canvas.getContext('2d');
let frame = 0;

// Autonomous Pixel Staff Class
class StaffMember {
  constructor(name, deskX, deskY, color, hairColor) {
    this.name = name;
    this.deskX = deskX;
    this.deskY = deskY;
    this.x = deskX;
    this.y = deskY;
    this.color = color;
    this.hairColor = hairColor;
    this.state = 'DESK'; // DESK, WALKING_OUT, AT_DEST, WALKING_BACK
    this.timer = Math.floor(Math.random() * 150) + 100;
    this.targetX = deskX;
    this.targetY = deskY;
    this.destName = '';
  }

  update() {
    if (this.state === 'DESK') {
      this.timer--;
      if (this.timer <= 0) {
        if (Math.random() < 0.6) {
          this.targetX = 1200 + Math.random() * 50; // Break room pantry
          this.destName = 'PANTRY';
        } else {
          this.targetX = 85 + Math.random() * 20;   // Server bay
          this.destName = 'SERVER';
        }
        this.targetY = 145;
        this.state = 'WALKING_OUT';
      }
    } else if (this.state === 'WALKING_OUT') {
      const dx = this.targetX - this.x;
      const dy = this.targetY - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) {
        this.x = this.targetX;
        this.y = this.targetY;
        this.state = 'AT_DEST';
        this.timer = Math.floor(Math.random() * 140) + 90;
      } else {
        const speed = 1.4;
        this.x += (dx / dist) * speed;
        this.y += (dy / dist) * speed;
      }
    } else if (this.state === 'AT_DEST') {
      this.timer--;
      if (this.timer <= 0) {
        this.targetX = this.deskX;
        this.targetY = this.deskY;
        this.state = 'WALKING_BACK';
      }
    } else if (this.state === 'WALKING_BACK') {
      const dx = this.targetX - this.x;
      const dy = this.targetY - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) {
        this.x = this.deskX;
        this.y = this.deskY;
        this.state = 'DESK';
        this.timer = Math.floor(Math.random() * 220) + 140;
      } else {
        const speed = 1.4;
        this.x += (dx / dist) * speed;
        this.y += (dy / dist) * speed;
      }
    }
  }

  draw() {
    const isWalking = (this.state === 'WALKING_OUT' || this.state === 'WALKING_BACK');
    const bob = (this.state === 'DESK') ? Math.sin(frame * 0.12) * 1.5 : 0;
    const legOffset = isWalking ? Math.sin(frame * 0.25) * 4 : 0;

    // Head
    ctx.fillStyle = this.hairColor;
    ctx.fillRect(this.x - 6, this.y - 38 + bob, 12, 12);

    // Shirt / Torso
    ctx.fillStyle = this.color;
    ctx.fillRect(this.x - 8, this.y - 26 + bob, 16, 14);

    // Legs
    ctx.fillStyle = '#2c3e50';
    if (isWalking) {
      ctx.fillRect(this.x - 6, this.y - 12, 5, 12 + legOffset);
      ctx.fillRect(this.x + 1, this.y - 12, 5, 12 - legOffset);
    } else {
      ctx.fillRect(this.x - 6, this.y - 12 + bob, 12, 12);
    }

    // Label Text
    let label = this.name;
    if (this.state === 'AT_DEST') {
      label = (this.destName === 'PANTRY') ? `${this.name} ☕` : `${this.name} ⚙️`;
    } else if (isWalking) {
      label = `${this.name} 🚶`;
    }

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

// Staff Instances
const staffList = [
  new StaffMember('ALEX (QUANT)', 360, 125, '#2ecc71', '#f1c40f'),
  new StaffMember('MARCUS (CIO)', 680, 115, '#f39c12', '#e67e22'),
  new StaffMember('SARAH (RISK)', 1000, 125, '#e74c3c', '#9b59b6')
];

function drawGrid() {
  ctx.strokeStyle = '#1a1e2b';
  ctx.lineWidth = 1;
  for (let x = 0; x < canvas.width; x += 35) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += 35) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
  }
}

function drawServerBay() {
  ctx.fillStyle = '#1c202c';
  ctx.fillRect(25, 48, 80, 160);
  ctx.strokeStyle = '#3a4154';
  ctx.lineWidth = 1.5;
  ctx.strokeRect(25, 48, 80, 160);

  for(let i = 0; i < 6; i++) {
    let ledColor = ((frame + i * 12) % 40 < 20) ? '#2ecc71' : '#3498db';
    if (i === 4 && frame % 25 < 6) ledColor = '#e74c3c';
    ctx.fillStyle = ledColor;
    ctx.fillRect(35, 62 + i * 24, 10, 8);
    ctx.fillRect(52, 62 + i * 24, 42, 6);
  }

  let packetX = (frame * 4) % 1100 + 120;
  ctx.fillStyle = '#00f0ff';
  ctx.fillRect(packetX, 40, 14, 3);

  ctx.fillStyle = '#12151f';
  ctx.fillRect(20, 212, 90, 16);
  ctx.fillStyle = '#00f0ff';
  ctx.font = 'bold 11px monospace';
  ctx.textAlign = 'center';
  ctx.fillText("SERVER BAY", 65, 224);
}

function drawDesks() {
  const deskLocations = [
    { name: 'QUANT DESK', x: 360, y: 125, color: '#2ecc71' },
    { name: 'CIO DESK', x: 680, y: 115, color: '#f39c12' },
    { name: 'RISK DESK', x: 1000, y: 125, color: '#e74c3c' }
  ];

  deskLocations.forEach(d => {
    // Floor Shadow
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.fillRect(d.x - 55, d.y + 36, 110, 12);

    // Desk Surface
    ctx.fillStyle = '#252a38';
    ctx.fillRect(d.x - 50, d.y, 100, 42);
    ctx.strokeStyle = '#3d455b';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(d.x - 50, d.y, 100, 42);

    // Dual Monitors
    ctx.fillStyle = '#11131a';
    ctx.fillRect(d.x - 38, d.y - 30, 76, 28);
    ctx.strokeStyle = d.color;
    ctx.lineWidth = 2;
    ctx.strokeRect(d.x - 38, d.y - 30, 76, 28);

    // Screen Graphics
    ctx.fillStyle = d.color;
    ctx.fillRect(d.x - 30, d.y - 22, 18, 4 + Math.sin(frame * 0.1) * 2);
    ctx.fillRect(d.x - 8, d.y - 18, 20, 5 + Math.cos(frame * 0.1) * 2);
    ctx.fillRect(d.x + 16, d.y - 23, 14, 4 + Math.sin(frame * 0.15) * 2);
  });
}

function drawPantry() {
  ctx.strokeStyle = '#2d3345';
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(1140, 40); ctx.lineTo(1140, 215); ctx.stroke();

  // Table
  ctx.fillStyle = '#222736';
  ctx.fillRect(1160, 125, 210, 42);
  ctx.strokeStyle = '#3a4154';
  ctx.lineWidth = 1.5;
  ctx.strokeRect(1160, 125, 210, 42);

  // Espresso Machine
  ctx.fillStyle = '#e74c3c';
  ctx.fillRect(1170, 83, 42, 42);
  ctx.fillStyle = '#11131a';
  ctx.fillRect(1178, 100, 26, 18);

  // Steam Animation
  let steamY = 76 - (frame % 30) * 0.6;
  let steamAlpha = 1 - ((frame % 30) / 30);
  ctx.fillStyle = `rgba(255, 255, 255, ${steamAlpha})`;
  ctx.beginPath(); ctx.arc(1191, steamY, 3.5, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.arc(1198, steamY - 6, 2.5, 0, Math.PI * 2); ctx.fill();

  // Water Dispenser
  ctx.fillStyle = '#3498db';
  ctx.beginPath(); ctx.arc(1250, 88, 14, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ecf0f1';
  ctx.fillRect(1240, 101, 20, 24);

  // Header Sign
  ctx.fillStyle = '#161a23';
  ctx.fillRect(1160, 48, 210, 22);
  ctx.strokeStyle = '#f39c12';
  ctx.lineWidth = 1;
  ctx.strokeRect(1160, 48, 210, 22);

  ctx.fillStyle = '#f39c12';
  ctx.font = 'bold 11px monospace';
  ctx.textAlign = 'center';
  ctx.fillText("☕ BREAK ROOM & PANTRY", 1265, 63);
}

function drawHUD() {
  ctx.fillStyle = '#161a23';
  ctx.fillRect(0, 0, canvas.width, 36);
  ctx.strokeStyle = '#2d3345';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, 36); ctx.lineTo(canvas.width, 36); ctx.stroke();

  ctx.fillStyle = '#2ecc71';
  ctx.font = 'bold 12px monospace';
  ctx.textAlign = 'left';
  ctx.fillText("● JC TRADING HOUSE — FLOOR & PANTRY TELEMETRY", 18, 23);

  let alpha = (Math.sin(frame * 0.1) + 1) / 2;
  ctx.fillStyle = `rgba(46, 204, 113, ${alpha})`;
  ctx.beginPath(); ctx.arc(1335, 20, 5, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 11px monospace';
  ctx.fillText("LIVE", 1348, 23);
}

function animate() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawGrid();
  drawServerBay();
  drawDesks();
  drawPantry();
  
  // Update and draw walking staff
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

components.html(pixel_floor_html, height=270, scrolling=False)

st.markdown("---")

# 8. Main Dashboard Layout (2-Column Grid)
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
        st.warning(f"Unable to fetch price data for symbol `{st.session_state.current_ticker}`. Verify ticker symbol in sidebar.")

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