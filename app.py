import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="JC Trading House - Full Operations Floor & AI Engine",
    layout="wide",
    initial_sidebar_state="collapsed"
)

html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JC Trading House - Institutional AI Floor</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #080a0f;
    color: #e0e6ed;
    font-family: 'Courier New', monospace;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px;
    min-height: 100vh;
  }

  .container {
    width: 100%;
    max-width: 1280px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .toolbar {
    background: #111622;
    border: 1px solid #232c3d;
    border-radius: 6px;
    padding: 8px 12px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .btn-group {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }

  button {
    background: #1a2233;
    color: #00f0ff;
    border: 1px solid #00f0ff;
    padding: 5px 10px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    font-weight: bold;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  button:hover {
    background: #00f0ff;
    color: #080a0f;
    box-shadow: 0 0 8px rgba(0, 240, 255, 0.4);
  }

  button.danger { color: #ff4757; border-color: #ff4757; }
  button.danger:hover { background: #ff4757; color: #fff; box-shadow: 0 0 8px rgba(255, 71, 87, 0.4); }
  button.active { background: #00f0ff; color: #080a0f; }

  .canvas-wrapper {
    position: relative;
    width: 100%;
    background: #0c0f17;
    border: 2px solid #222b3d;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.8);
  }

  canvas {
    display: block;
    width: 100%;
    height: auto;
    aspect-ratio: 1200 / 420;
    image-rendering: pixelated;
    cursor: pointer;
  }

  .grid-2col {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 10px;
  }

  .grid-3col {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
  }

  @media (max-width: 900px) {
    .grid-2col, .grid-3col { grid-template-columns: 1fr; }
  }

  .panel-box {
    background: #111622;
    border: 1px solid #232c3d;
    border-radius: 6px;
    padding: 10px;
    font-size: 11px;
  }

  .panel-title {
    color: #f1c40f;
    font-weight: bold;
    margin-bottom: 6px;
    border-bottom: 1px dashed #232c3d;
    padding-bottom: 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .metric-value {
    font-size: 14px;
    font-weight: bold;
    color: #2ecc71;
  }
  .metric-value.negative { color: #ff4757; }

  #consoleLog {
    height: 90px;
    overflow-y: auto;
    color: #2ecc71;
    font-size: 10px;
    line-height: 1.3;
    background: #080a0f;
    padding: 6px;
    border-radius: 4px;
    border: 1px solid #1a2233;
  }

  .order-book-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 10px;
    text-align: right;
  }
  .order-book-table th { color: #888; border-bottom: 1px solid #222; padding: 2px; }
  .order-book-table td { padding: 2px; }
  .ask-row { color: #ff4757; }
  .bid-row { color: #2ecc71; }

  .strat-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 4px;
    background: #161d2d;
    padding: 4px 8px;
    border-radius: 4px;
  }
</style>
</head>
<body>

<div class="container">
  <!-- CONTROL TOOLBAR -->
  <div class="toolbar">
    <div class="btn-group">
      <button onclick="dispatchAll('PANTRY')">☕ Pantry</button>
      <button onclick="dispatchAll('WHITEBOARD')">📋 Sync</button>
      <button onclick="dispatchAll('SERVERS')">🖥️ Servers</button>
      <button onclick="returnToDesks()">🖥️ Desks</button>
      <button onclick="addAgentModal()">➕ Add Agent</button>
    </div>
    <div class="btn-group">
      <button id="asset-BTC-USD" class="active" onclick="selectAsset('BTC-USD')">BTC-USD</button>
      <button id="asset-NVDA" onclick="selectAsset('NVDA')">NVDA</button>
      <button id="asset-TSLA" onclick="selectAsset('TSLA')">TSLA</button>
      <button id="asset-ETH-USD" onclick="selectAsset('ETH-USD')">ETH-USD</button>
      <button id="asset-S68.SG" onclick="selectAsset('S68.SG')">S68.SG</button>
    </div>
    <div class="btn-group">
      <button onclick="togglePause()"><span id="pauseLabel">⏸️ Pause</span></button>
      <button class="danger" onclick="toggleCrisis()">🚨 Crisis</button>
      <button onclick="toggleSpeed()">⏩ <span id="speedLabel">1x</span></button>
      <button onclick="toggleAudio()">🔊 <span id="audioLabel">OFF</span></button>
    </div>
  </div>

  <!-- MAIN 2D PIXEL CANVAS -->
  <div class="canvas-wrapper">
    <canvas id="tradingFloor" width="1200" height="420"></canvas>
  </div>

  <!-- ANALYTICS & MARKET ENGINE PANEL -->
  <div class="grid-2col">
    <!-- CHART CANVAS & AI STRATEGY STATUS -->
    <div class="panel-box">
      <div class="panel-title">
        <span>📈 REAL-TIME MARKET DATA & SIGNALS (<span id="activeSymbolLabel">BTC-USD</span>)</span>
        <span>PRICE: $<span id="currentPriceLabel">92,450.10</span></span>
      </div>
      <div style="position: relative; width: 100%; height: 160px; background: #080a0f; border-radius: 4px; border: 1px solid #1a2233;">
        <canvas id="chartCanvas" width="800" height="160" style="width: 100%; height: 160px;"></canvas>
      </div>
    </div>

    <!-- ORDER BOOK DEPTH -->
    <div class="panel-box">
      <div class="panel-title">📖 ORDER BOOK DEPTH LADDER</div>
      <table class="order-book-table">
        <thead>
          <tr><th>TYPE</th><th>PRICE ($)</th><th>SIZE</th></tr>
        </thead>
        <tbody id="orderBookBody">
          <!-- Populated by JS -->
        </tbody>
      </table>
    </div>
  </div>

  <!-- AI STRATEGY & METRICS DASHBOARD -->
  <div class="grid-3col">
    <!-- STRATEGY CONTROLS -->
    <div class="panel-box">
      <div class="panel-title">🤖 AI STRATEGY ENGINE CONTROLS</div>
      <div class="strat-toggle">
        <span>Quant Volatility Arb (2σ)</span>
        <button id="btn-strat-quant" onclick="toggleStrategy('quant')">ON</button>
      </div>
      <div class="strat-toggle">
        <span>NLP News Sentiment</span>
        <button id="btn-strat-sentiment" onclick="toggleStrategy('sentiment')">ON</button>
      </div>
      <div class="strat-toggle">
        <span>Adaptive Market Maker</span>
        <button id="btn-strat-mm" onclick="toggleStrategy('mm')">ON</button>
      </div>
      <div class="strat-toggle">
        <span>Dynamic Risk Manager (VaR)</span>
        <button id="btn-strat-risk" onclick="toggleStrategy('risk')">ON</button>
      </div>
    </div>

    <!-- PERFORMANCE METRICS -->
    <div class="panel-box">
      <div class="panel-title">📊 PORTFOLIO & EXECUTION METRICS</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
        <div>Total Equity: <div id="metricEquity" class="metric-value">$1,000,000</div></div>
        <div>Realized PnL: <div id="metricPnL" class="metric-value">$0.00</div></div>
        <div>Win Rate: <div id="metricWinRate" class="metric-value">100%</div></div>
        <div>Sharpe Ratio: <div id="metricSharpe" class="metric-value">2.10</div></div>
      </div>
    </div>

    <!-- EVENT LOG & INSPECTOR -->
    <div class="panel-box">
      <div class="panel-title">
        <span>📜 SYSTEM EVENT LOG</span>
        <div>
          <button onclick="clearLogs()" style="padding: 1px 4px; font-size: 9px;">Clear</button>
          <button onclick="exportLogs()" style="padding: 1px 4px; font-size: 9px;">Export</button>
        </div>
      </div>
      <div id="consoleLog">> Initialization complete. Connected to Market Simulator.</div>
    </div>
  </div>
</div>

<script>
// --- CANVAS & SYSTEM STATE ---
const floorCanvas = document.getElementById('tradingFloor');
const floorCtx = floorCanvas.getContext('2d');
const chartCanvas = document.getElementById('chartCanvas');
const chartCtx = chartCanvas.getContext('2d');

let frame = 0;
let simSpeed = 1;
let audioEnabled = false;
let crisisMode = false;
let isPaused = false;
let tickerOffset = 0;
let newsOffset = 0;
let selectedAgentIndex = 0;
let selectedAsset = 'BTC-USD';

let audioCtx = null;
function initAudio() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
}

function playBeep(freq = 440, type = 'sine', duration = 0.08) {
  if (!audioEnabled || !audioCtx) return;
  try {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.04, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + duration);
  } catch (e) {}
}

function logEvent(msg) {
  const log = document.getElementById('consoleLog');
  const timestamp = new Date().toLocaleTimeString();
  log.innerHTML = `<div>[${timestamp}] ${msg}</div>` + log.innerHTML;
}

function clearLogs() {
  document.getElementById('consoleLog').innerHTML = '<div>> Console cleared.</div>';
}

function exportLogs() {
  const text = document.getElementById('consoleLog').innerText;
  const blob = new Blob([text], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `jc_trading_log_${Date.now()}.txt`;
  a.click();
}

// --- MARKET SIMULATION DATA ENGINE ---
const assetData = {
  'BTC-USD': { price: 92450.10, history: [], volatility: 45, mean: 92450 },
  'NVDA': { price: 138.20, history: [], volatility: 0.8, mean: 138 },
  'TSLA': { price: 248.50, history: [], volatility: 1.5, mean: 248 },
  'ETH-USD': { price: 3450.80, history: [], volatility: 18, mean: 3450 },
  'S68.SG': { price: 10.85, history: [], volatility: 0.05, mean: 10.85 }
};

// Seed initial chart history
Object.keys(assetData).forEach(sym => {
  let p = assetData[sym].price;
  for (let i = 0; i < 60; i++) {
    p += (Math.random() - 0.49) * assetData[sym].volatility;
    assetData[sym].history.push(p);
  }
});

let portfolio = {
  cash: 1000000,
  realizedPnL: 0,
  trades: 0,
  wins: 0,
  positions: { 'BTC-USD': 0, 'NVDA': 0, 'TSLA': 0, 'ETH-USD': 0, 'S68.SG': 0 }
};

const activeStrats = { quant: true, sentiment: true, mm: true, risk: true };

function toggleStrategy(stratKey) {
  activeStrats[stratKey] = !activeStrats[stratKey];
  const btn = document.getElementById(`btn-strat-${stratKey}`);
  btn.innerText = activeStrats[stratKey] ? 'ON' : 'OFF';
  btn.className = activeStrats[stratKey] ? 'active' : '';
  logEvent(`Strategy '${stratKey.toUpperCase()}' set to ${activeStrats[stratKey] ? 'ACTIVE' : 'DISABLED'}.`);
}

function selectAsset(sym) {
  selectedAsset = sym;
  Object.keys(assetData).forEach(s => {
    document.getElementById(`asset-${s}`).className = (s === sym) ? 'active' : '';
  });
  document.getElementById('activeSymbolLabel').innerText = sym;
  logEvent(`Switched primary monitoring chart to ${sym}.`);
}

// --- AI STAFF & AGENT SIMULATION ---
class StaffMember {
  constructor(name, title, deskX, deskY, shirtColor, hairColor, roleBadge, thoughts, currentTask) {
    this.name = name;
    this.title = title;
    this.deskX = deskX; this.deskY = deskY;
    this.x = deskX; this.y = deskY;
    this.shirtColor = shirtColor;
    this.hairColor = hairColor;
    this.roleBadge = roleBadge;
    this.thoughts = thoughts;
    this.currentThought = thoughts[0];
    this.currentTask = currentTask;
    this.state = 'DESK';
    this.timer = Math.floor(Math.random() * 120) + 60;
    this.targetX = deskX; this.targetY = deskY;
    this.destName = '';
  }

  update() {
    if (isPaused) return;
    if (this.state === 'DESK') {
      this.timer -= simSpeed;
      if (this.timer <= 0) {
        const rand = Math.random();
        if (rand < 0.35) this.walkTo(1080 + Math.random() * 30, 260, 'PANTRY');
        else if (rand < 0.65) this.walkTo(90 + Math.random() * 30, 260, 'SERVERS');
        else this.walkTo(350 + Math.random() * 40, 150, 'WHITEBOARD');
      }
    } else if (this.state === 'WALKING_OUT') {
      const dx = this.targetX - this.x, dy = this.targetY - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) {
        this.x = this.targetX; this.y = this.targetY;
        this.state = 'AT_DEST'; this.timer = Math.floor(Math.random() * 120) + 60;
      } else {
        this.x += (dx / dist) * 2.2 * simSpeed;
        this.y += (dy / dist) * 2.2 * simSpeed;
      }
    } else if (this.state === 'AT_DEST') {
      this.timer -= simSpeed;
      if (this.timer <= 0) this.walkBackToDesk();
    } else if (this.state === 'WALKING_BACK') {
      const dx = this.targetX - this.x, dy = this.targetY - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) {
        this.x = this.deskX; this.y = this.deskY;
        this.state = 'DESK'; this.timer = Math.floor(Math.random() * 180) + 100;
      } else {
        this.x += (dx / dist) * 2.2 * simSpeed;
        this.y += (dy / dist) * 2.2 * simSpeed;
      }
    }
  }

  walkTo(tx, ty, destName) {
    this.targetX = tx; this.targetY = ty; this.destName = destName;
    this.state = 'WALKING_OUT';
    this.currentThought = this.thoughts[Math.floor(Math.random() * this.thoughts.length)];
  }

  walkBackToDesk() {
    this.targetX = this.deskX; this.targetY = this.deskY;
    this.state = 'WALKING_BACK';
  }

  draw(isSelected) {
    const isWalking = (this.state === 'WALKING_OUT' || this.state === 'WALKING_BACK');
    const bob = (this.state === 'DESK') ? Math.sin(frame * 0.15) * 2 : 0;
    const legOffset = isWalking ? Math.sin(frame * 0.28) * 6 : 0;

    if (isSelected) {
      floorCtx.strokeStyle = '#00f0ff'; floorCtx.lineWidth = 2;
      floorCtx.beginPath(); floorCtx.ellipse(this.x, this.y + 12, 18, 8, 0, 0, Math.PI * 2); floorCtx.stroke();
    }

    // Body & Head
    floorCtx.fillStyle = this.hairColor; floorCtx.fillRect(this.x - 10, this.y - 42 + bob, 20, 14);
    floorCtx.fillStyle = '#f1c27d'; floorCtx.fillRect(this.x - 8, this.y - 32 + bob, 16, 12);
    floorCtx.fillStyle = this.shirtColor; floorCtx.fillRect(this.x - 12, this.y - 20 + bob, 24, 18);

    // Legs
    floorCtx.fillStyle = '#1e2530';
    if (isWalking) {
      floorCtx.fillRect(this.x - 9, this.y - 2, 7, 16 + legOffset);
      floorCtx.fillRect(this.x + 2, this.y - 2, 7, 16 - legOffset);
    } else {
      floorCtx.fillRect(this.x - 9, this.y - 2 + bob, 18, 16);
    }

    // Label
    const actionTag = (this.state === 'AT_DEST') ? this.destName : (isWalking ? 'WALKING' : 'DESK');
    const labelText = `${this.roleBadge} ${this.name} [${actionTag}]`;
    floorCtx.font = 'bold 10px monospace';
    const textWidth = floorCtx.measureText(labelText).width + 12;

    floorCtx.fillStyle = 'rgba(12, 16, 25, 0.9)';
    floorCtx.fillRect(this.x - textWidth/2, this.y - 64 + bob, textWidth, 18);
    floorCtx.strokeStyle = isSelected ? '#00f0ff' : this.shirtColor; floorCtx.lineWidth = 1;
    floorCtx.strokeRect(this.x - textWidth/2, this.y - 64 + bob, textWidth, 18);

    floorCtx.fillStyle = '#ffffff'; floorCtx.textAlign = 'center';
    floorCtx.fillText(labelText, this.x, this.y - 51 + bob);
  }
}

const staffMembers = [
  new StaffMember('ALEX', 'QUANT', 270, 260, '#2ecc71', '#f39c12', '📈', ['Evaluating 2σ band', 'Mean Reversion High', 'Executing Order'], 'Vol Arbitrage Pipeline'),
  new StaffMember('MARCUS', 'CIO', 500, 260, '#3498db', '#e67e22', '🏛️', ['Rebalancing Portfolio', 'Checking VaR Limit', 'Capital Allocated'], 'Portfolio Asset Allocation'),
  new StaffMember('SARAH', 'RISK', 730, 260, '#e74c3c', '#9b59b6', '🛡️', ['Exposure Safe', 'Drawdown Nominal', 'Stop Loss Standing'], '95% VaR Margin Monitoring'),
  new StaffMember('ELENA', 'DEV', 950, 260, '#9b59b6', '#34495e', '⚡', ['Low Latency API', 'Order Book Ingest', 'WebSocket 1ms'], 'Fixing High Frequency Engine')
];

function dispatchAll(dest) {
  staffMembers.forEach(s => s.walkTo(dest === 'PANTRY' ? 1080 : (dest === 'SERVERS' ? 90 : 350), 260, dest));
}
function returnToDesks() { staffMembers.forEach(s => s.walkBackToDesk()); }
function addAgentModal() {
  const name = prompt("New Agent Name:", "VIPER");
  if (name) {
    staffMembers.push(new StaffMember(name.toUpperCase(), 'TRADER', 300 + Math.random() * 400, 260, '#f1c40f', '#16a085', '💼', ['Analyzing Liquidity'], 'Order Flow Execution'));
    logEvent(`Agent '${name}' deployed to trading floor.`);
  }
}

// --- RENDER FLOORS & ENVIRONMENT ---
function drawFloor() {
  for (let x = 0; x < floorCanvas.width; x += 40) {
    for (let y = 40; y < floorCanvas.height - 30; y += 40) {
      floorCtx.fillStyle = crisisMode ? ((x + y) % 80 === 0 ? '#2a0c10' : '#1d080b') : ((x + y) % 80 === 0 ? '#101420' : '#131826');
      floorCtx.fillRect(x, y, 40, 40);
      floorCtx.strokeStyle = crisisMode ? '#3d1217' : '#1a2133'; floorCtx.lineWidth = 0.5;
      floorCtx.strokeRect(x, y, 40, 40);
    }
  }

  // Header Bar
  floorCtx.fillStyle = '#141824'; floorCtx.fillRect(0, 0, floorCanvas.width, 35);
  floorCtx.fillStyle = crisisMode ? '#ff4757' : '#2ecc71'; floorCtx.font = 'bold 12px monospace'; floorCtx.textAlign = 'left';
  floorCtx.fillText(crisisMode ? "🚨 CRISIS SYSTEM ACTIVE - DANGER" : "● JC TRADING HOUSE - INSTITUTIONAL FLOOR", 15, 22);

  // Workstations
  staffMembers.forEach(ws => {
    floorCtx.fillStyle = '#1e2433'; floorCtx.fillRect(ws.deskX - 60, ws.deskY + 10, 120, 45);
    floorCtx.strokeStyle = ws.shirtColor; floorCtx.lineWidth = 1.5; floorCtx.strokeRect(ws.deskX - 60, ws.deskY + 10, 120, 45);
    floorCtx.fillStyle = '#0f131c'; floorCtx.fillRect(ws.deskX - 30, ws.deskY - 45, 60, 35);
    floorCtx.strokeRect(ws.deskX - 30, ws.deskY - 45, 60, 35);
  });
}

// --- CHART & ORDER BOOK RENDERERS ---
function updateMarketAndCharts() {
  if (isPaused) return;

  // Tick prices
  Object.keys(assetData).forEach(sym => {
    const data = assetData[sym];
    const change = (Math.random() - 0.495) * data.volatility * simSpeed;
    data.price = Math.max(1, data.price + change);
    data.history.push(data.price);
    if (data.history.length > 80) data.history.shift();
  });

  const currData = assetData[selectedAsset];
  document.getElementById('currentPriceLabel').innerText = currData.price.toFixed(2);

  // Render Line Chart
  chartCtx.clearRect(0, 0, chartCanvas.width, chartCanvas.height);
  chartCtx.strokeStyle = '#00f0ff'; chartCtx.lineWidth = 1.5;
  chartCtx.beginPath();
  const hist = currData.history;
  const minP = Math.min(...hist), maxP = Math.max(...hist);
  const range = (maxP - minP) || 1;

  hist.forEach((p, idx) => {
    const x = (idx / (hist.length - 1)) * chartCanvas.width;
    const y = chartCanvas.height - ((p - minP) / range) * (chartCanvas.height - 20) - 10;
    if (idx === 0) chartCtx.moveTo(x, y); else chartCtx.lineTo(x, y);
  });
  chartCtx.stroke();

  // Render Order Book
  const obBody = document.getElementById('orderBookBody');
  let obHTML = '';
  for (let i = 3; i >= 1; i--) {
    obHTML += `<tr class="ask-row"><td>ASK</td><td>${(currData.price + i * 0.2).toFixed(2)}</td><td>${Math.floor(Math.random()*50 + 10)}</td></tr>`;
  }
  for (let i = 1; i <= 3; i++) {
    obHTML += `<tr class="bid-row"><td>BID</td><td>${(currData.price - i * 0.2).toFixed(2)}</td><td>${Math.floor(Math.random()*50 + 10)}</td></tr>`;
  }
  obBody.innerHTML = obHTML;
}

// --- AI STRATEGY AUTOMATION LOOP ---
function runAIStrategies() {
  if (isPaused || crisisMode) return;

  const curr = assetData[selectedAsset];
  const hist = curr.history;
  if (hist.length < 20) return;

  // 1. Quant Arbitrage (Bollinger Bands 2σ)
  if (activeStrats.quant && Math.random() < 0.05) {
    const mean = hist.reduce((a,b)=>a+b,0) / hist.length;
    const lastPrice = curr.price;
    if (lastPrice > mean + curr.volatility * 1.5) {
      executeTrade('SELL', selectedAsset, lastPrice, "Quant Arbitrage Upper Band Reversal");
    } else if (lastPrice < mean - curr.volatility * 1.5) {
      executeTrade('BUY', selectedAsset, lastPrice, "Quant Arbitrage Lower Band Dip");
    }
  }

  // 2. Risk Manager Check
  if (activeStrats.risk && portfolio.cash < 900000) {
    logEvent("🚨 RISK MANAGER: VaR Exceeded! Liquidating asset risk exposure.");
    portfolio.cash += 50000;
    document.getElementById('metricEquity').innerText = `$${portfolio.cash.toFixed(0)}`;
  }
}

function executeTrade(type, symbol, price, reason) {
  portfolio.trades++;
  const isWin = Math.random() > 0.35;
  if (isWin) portfolio.wins++;
  const pnl = (isWin ? 1 : -1) * (price * 0.02);
  portfolio.realizedPnL += pnl;
  portfolio.cash += pnl;

  playBeep(type === 'BUY' ? 800 : 400, 'sine', 0.05);
  logEvent(`[${type}] ${symbol} @ $${price.toFixed(2)} | PnL: $${pnl.toFixed(2)} | ${reason}`);

  document.getElementById('metricEquity').innerText = `$${portfolio.cash.toFixed(0)}`;
  const pnlElem = document.getElementById('metricPnL');
  pnlElem.innerText = `$${portfolio.realizedPnL.toFixed(2)}`;
  pnlElem.className = portfolio.realizedPnL >= 0 ? 'metric-value' : 'metric-value negative';
  document.getElementById('metricWinRate').innerText = `${((portfolio.wins / portfolio.trades) * 100).toFixed(0)}%`;
}

// --- MAIN LOOP & CONTROLS ---
function animate() {
  floorCtx.clearRect(0, 0, floorCanvas.width, floorCanvas.height);
  drawFloor();
  staffMembers.forEach((s, idx) => {
    s.update();
    s.draw(idx === selectedAgentIndex);
  });

  if (frame % 10 === 0) {
    updateMarketAndCharts();
    runAIStrategies();
  }

  if (!isPaused) frame++;
  requestAnimationFrame(animate);
}

function togglePause() {
  isPaused = !isPaused;
  document.getElementById('pauseLabel').innerText = isPaused ? '▶️ Resume' : '⏸️ Pause';
  logEvent(isPaused ? "Simulation Paused." : "Simulation Resumed.");
}

function toggleCrisis() {
  crisisMode = !crisisMode;
  logEvent(crisisMode ? "🚨 CRISIS MODE ACTIVATED!" : "✅ Operations Normalized.");
}

function toggleSpeed() {
  simSpeed = simSpeed === 1 ? 2 : (simSpeed === 2 ? 4 : 1);
  document.getElementById('speedLabel').innerText = `${simSpeed}x`;
}

function toggleAudio() {
  initAudio();
  audioEnabled = !audioEnabled;
  document.getElementById('audioLabel').innerText = audioEnabled ? 'ON' : 'OFF';
}

floorCanvas.addEventListener('click', (e) => {
  const rect = floorCanvas.getBoundingClientRect();
  const cx = (e.clientX - rect.left) * (floorCanvas.width / rect.width);
  const cy = (e.clientY - rect.top) * (floorCanvas.height / rect.height);

  staffMembers.forEach((s, idx) => {
    if (Math.sqrt((cx - s.x)**2 + (cy - s.y)**2) < 35) {
      selectedAgentIndex = idx;
      logEvent(`Inspecting Agent: ${s.name} (${s.title}) -> Task: ${s.currentTask}`);
    }
  });
});

animate();
</script>
</body>
</html>
"""

components.html(html_code, height=1150, scrolling=True)