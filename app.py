import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="JC Trading House",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Render HTML canvas inside Streamlit
html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JC Trading House - Animated Pixel Floor</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #080a0f;
    color: #e0e6ed;
    font-family: 'Courier New', monospace;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px;
    min-height: 100vh;
  }

  .container {
    width: 100%;
    max-width: 1240px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .toolbar {
    background: #111622;
    border: 1px solid #232c3d;
    border-radius: 8px;
    padding: 10px 16px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }

  .btn-group {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  button {
    background: #1a2233;
    color: #00f0ff;
    border: 1px solid #00f0ff;
    padding: 6px 14px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    font-weight: bold;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  button:hover {
    background: #00f0ff;
    color: #080a0f;
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
  }

  button.danger {
    color: #ff4757;
    border-color: #ff4757;
  }

  button.danger:hover {
    background: #ff4757;
    color: #fff;
    box-shadow: 0 0 10px rgba(255, 71, 87, 0.4);
  }

  .canvas-wrapper {
    position: relative;
    width: 100%;
    background: #0c0f17;
    border: 2px solid #222b3d;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
  }

  canvas {
    display: block;
    width: 100%;
    height: auto;
    aspect-ratio: 1200 / 500;
    image-rendering: pixelated;
    cursor: pointer;
  }

  .bottom-panel {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  @media (max-width: 800px) {
    .bottom-panel { grid-template-columns: 1fr; }
  }

  .panel-box {
    background: #111622;
    border: 1px solid #232c3d;
    border-radius: 8px;
    padding: 12px;
    font-size: 12px;
  }

  .panel-title {
    color: #f1c40f;
    font-weight: bold;
    margin-bottom: 8px;
    border-bottom: 1px dashed #232c3d;
    padding-bottom: 4px;
  }

  #consoleLog {
    height: 90px;
    overflow-y: auto;
    color: #2ecc71;
    font-size: 11px;
    line-height: 1.4;
  }

  .stat-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .stat-card {
    background: #161d2d;
    padding: 6px 10px;
    border-radius: 4px;
    border-left: 3px solid #00f0ff;
  }
</style>
</head>
<body>

<div class="container">
  <div class="toolbar">
    <div class="btn-group">
      <button onclick="dispatchAll('PANTRY')">☕ Coffee Break</button>
      <button onclick="dispatchAll('WHITEBOARD')">📋 Strategy Sync</button>
      <button onclick="dispatchAll('SERVERS')">🖥️ Server Check</button>
      <button onclick="returnToDesks()">🖥️ Back to Desks</button>
    </div>
    <div class="btn-group">
      <button class="danger" onclick="toggleCrisis()">🚨 Crisis Mode</button>
      <button onclick="toggleSpeed()">⏩ Speed: <span id="speedLabel">1x</span></button>
      <button onclick="toggleAudio()">🔊 Sound: <span id="audioLabel">OFF</span></button>
    </div>
  </div>

  <div class="canvas-wrapper">
    <canvas id="tradingFloor" width="1200" height="500"></canvas>
  </div>

  <div class="bottom-panel">
    <div class="panel-box">
      <div class="panel-title">💡 AGENT INSPECTOR (Click any staff member on canvas)</div>
      <div class="stat-grid" id="inspectorContent">
        <div class="stat-card"><b>Agent:</b> <span id="inspName">ALEX</span></div>
        <div class="stat-card"><b>Role:</b> <span id="inspRole">QUANT</span></div>
        <div class="stat-card"><b>Status:</b> <span id="inspStatus">TYPING</span></div>
        <div class="stat-card"><b>Task:</b> <span id="inspTask">RSI Alpha Signal</span></div>
      </div>
    </div>
    <div class="panel-box">
      <div class="panel-title">📜 EVENT LOG CONSOLE</div>
      <div id="consoleLog">>JC Trading Engine initialized.<br>>System online. Select agents to inspect status.</div>
    </div>
  </div>
</div>

<script>
const canvas = document.getElementById('tradingFloor');
const ctx = canvas.getContext('2d');

let frame = 0;
let simSpeed = 1;
let audioEnabled = false;
let crisisMode = false;
let tickerOffset = 0;
let newsOffset = 0;
let selectedAgentIndex = 0;

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
    gain.gain.setValueAtTime(0.05, audioCtx.currentTime);
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
  constructor(name, title, deskX, deskY, shirtColor, hairColor, roleBadge, thoughts, currentTask) {
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
    this.currentTask = currentTask;
    this.state = 'DESK';
    this.timer = Math.floor(Math.random() * 120) + 60;
    this.targetX = deskX; 
    this.targetY = deskY;
    this.destName = '';
  }

  update() {
    if (this.state === 'DESK') {
      this.timer -= simSpeed;
      if (this.timer <= 0) {
        const rand = Math.random();
        if (rand < 0.35) {
          this.walkTo(1080 + Math.random() * 30, 280, 'PANTRY');
        } else if (rand < 0.65) {
          this.walkTo(90 + Math.random() * 30, 280, 'SERVERS');
        } else {
          this.walkTo(350 + Math.random() * 40, 165, 'WHITEBOARD');
        }
      }
    } else if (this.state === 'WALKING_OUT') {
      const dx = this.targetX - this.x, dy = this.targetY - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) {
        this.x = this.targetX; this.y = this.targetY;
        this.state = 'AT_DEST'; 
        this.timer = Math.floor(Math.random() * 140) + 80;
        playBeep(600, 'triangle', 0.05);
      } else {
        this.x += (dx / dist) * 2.2 * simSpeed; 
        this.y += (dy / dist) * 2.2 * simSpeed;
      }
    } else if (this.state === 'AT_DEST') {
      this.timer -= simSpeed;
      if (this.timer <= 0) {
        this.walkBackToDesk();
      }
    } else if (this.state === 'WALKING_BACK') {
      const dx = this.targetX - this.x, dy = this.targetY - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) {
        this.x = this.deskX; this.y = this.deskY;
        this.state = 'DESK'; 
        this.timer = Math.floor(Math.random() * 180) + 100;
        playBeep(800, 'sine', 0.05);
      } else {
        this.x += (dx / dist) * 2.2 * simSpeed; 
        this.y += (dy / dist) * 2.2 * simSpeed;
      }
    }
  }

  walkTo(tx, ty, destName) {
    this.targetX = tx;
    this.targetY = ty;
    this.destName = destName;
    this.state = 'WALKING_OUT';
    this.currentThought = this.thoughts[Math.floor(Math.random() * this.thoughts.length)];
    logEvent(`${this.name} (${this.title}) left desk for ${destName}.`);
  }

  walkBackToDesk() {
    this.targetX = this.deskX;
    this.targetY = this.deskY;
    this.state = 'WALKING_BACK';
    logEvent(`${this.name} returning to workstation.`);
  }

  draw(isSelected) {
    const isWalking = (this.state === 'WALKING_OUT' || this.state === 'WALKING_BACK');
    const bob = (this.state === 'DESK') ? Math.sin(frame * 0.15) * 2 : 0;
    const typingHand = (this.state === 'DESK') ? Math.sin(frame * 0.4) * 3 : 0;
    const legOffset = isWalking ? Math.sin(frame * 0.28) * 6 : 0;

    if (isSelected) {
      ctx.strokeStyle = '#00f0ff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.ellipse(this.x, this.y + 12, 18, 8, 0, 0, Math.PI * 2);
      ctx.stroke();
    }

    ctx.fillStyle = this.hairColor;
    ctx.fillRect(this.x - 10, this.y - 42 + bob, 20, 14);
    ctx.fillStyle = '#f1c27d';
    ctx.fillRect(this.x - 8, this.y - 32 + bob, 16, 12);
    ctx.fillStyle = '#111';
    ctx.fillRect(this.x - 5, this.y - 28 + bob, 3, 3);
    ctx.fillRect(this.x + 2, this.y - 28 + bob, 3, 3);
    ctx.fillStyle = this.shirtColor;
    ctx.fillRect(this.x - 12, this.y - 20 + bob, 24, 18);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(this.x - 3, this.y - 20 + bob, 6, 8);

    if (this.state === 'DESK') {
      ctx.fillStyle = '#f1c27d';
      ctx.fillRect(this.x - 14, this.y - 10 + typingHand, 5, 8);
      ctx.fillRect(this.x + 9, this.y - 10 - typingHand, 5, 8);
    }

    ctx.fillStyle = '#1e2530';
    if (isWalking) {
      ctx.fillRect(this.x - 9, this.y - 2, 7, 16 + legOffset);
      ctx.fillRect(this.x + 2, this.y - 2, 7, 16 - legOffset);
    } else {
      ctx.fillRect(this.x - 9, this.y - 2 + bob, 18, 16);
    }

    let actionTag = "TYPING";
    if (this.state === 'AT_DEST') actionTag = this.destName;
    else if (isWalking) actionTag = "WALKING";

    const labelText = `${this.roleBadge} ${this.name} [${actionTag}]`;
    ctx.font = 'bold 11px monospace';
    const textWidth = ctx.measureText(labelText).width + 14;

    ctx.fillStyle = 'rgba(12, 16, 25, 0.95)';
    ctx.fillRect(this.x - textWidth/2, this.y - 68 + bob, textWidth, 20);
    ctx.strokeStyle = isSelected ? '#00f0ff' : this.shirtColor;
    ctx.lineWidth = isSelected ? 2 : 1.5;
    ctx.strokeRect(this.x - textWidth/2, this.y - 68 + bob, textWidth, 20);

    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.fillText(labelText, this.x, this.y - 54 + bob);

    if (Math.sin(frame * 0.04 + this.x) > 0.2) {
      const bubbleText = `"${this.currentThought}"`;
      ctx.font = '10px monospace';
      const bWidth = ctx.measureText(bubbleText).width + 16;
      const bX = this.x - bWidth / 2;
      const bY = this.y - 96 + bob;

      ctx.fillStyle = 'rgba(15, 20, 30, 0.95)';
      ctx.fillRect(bX, bY, bWidth, 20);
      ctx.strokeStyle = '#f1c40f';
      ctx.lineWidth = 1;
      ctx.strokeRect(bX, bY, bWidth, 20);

      ctx.fillStyle = '#f1c40f';
      ctx.textAlign = 'center';
      ctx.fillText(bubbleText, this.x, bY + 14);
    }
  }
}

const staffMembers = [
  new StaffMember('ALEX', 'QUANT', 270, 280, '#2ecc71', '#f39c12', '📈', ['Checking RSI', 'Backtesting...', 'Alpha Found!'], 'Vol Arbitrage Pipeline'),
  new StaffMember('MARCUS', 'CIO', 500, 280, '#3498db', '#e67e22', '🏛️', ['Rebalancing', 'Check Volatility', 'Macro Shift'], 'Portfolio Asset Allocation'),
  new StaffMember('SARAH', 'RISK', 730, 280, '#e74c3c', '#9b59b6', '🛡️', ['VaR Safe', 'Check Exposure', 'Stress Test'], '95% VaR Margin Monitoring'),
  new StaffMember('ELENA', 'DEV', 950, 280, '#9b59b6', '#34495e', '⚡', ['HFT Low Latency', 'Fixing API', 'Server Green'], 'Fixing WebSocket Feed')
];

function drawEnvironment() {
  for (let x = 0; x < canvas.width; x += 40) {
    for (let y = 40; y < canvas.height - 30; y += 40) {
      ctx.fillStyle = crisisMode 
        ? ((x + y) % 80 === 0 ? '#2a0c10' : '#1d080b')
        : ((x + y) % 80 === 0 ? '#101420' : '#131826');
      ctx.fillRect(x, y, 40, 40);
      ctx.strokeStyle = crisisMode ? '#3d1217' : '#1a2133';
      ctx.lineWidth = 0.5;
      ctx.strokeRect(x, y, 40, 40);
    }
  }

  ctx.fillStyle = '#141824';
  ctx.fillRect(0, 0, canvas.width, 40);
  ctx.strokeStyle = '#283144';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, 40); ctx.lineTo(canvas.width, 40); ctx.stroke();

  ctx.fillStyle = crisisMode ? '#ff4757' : '#2ecc71'; 
  ctx.font = 'bold 12px monospace'; ctx.textAlign = 'left';
  ctx.fillText(crisisMode ? "🚨 JC TRADING HOUSE - CRISIS ALERT ACTIVE" : "● JC TRADING HOUSE - MAIN FLOOR", 15, 25);

  tickerOffset = (tickerOffset + 1.2 * simSpeed) % 1200;
  ctx.fillStyle = '#0d111a'; ctx.fillRect(420, 6, 640, 28);
  ctx.strokeStyle = '#2d374d'; ctx.strokeRect(420, 6, 640, 28);
  
  ctx.save();
  ctx.beginPath(); ctx.rect(422, 8, 636, 24); ctx.clip();
  let tickerX = 1060 - tickerOffset;
  ctx.font = 'bold 12px monospace'; ctx.textAlign = 'left';
  stockTickerItems.forEach(item => {
    ctx.fillStyle = '#00f0ff'; ctx.fillText(item.symbol, tickerX, 24);
    ctx.fillStyle = '#ffffff'; ctx.fillText(`$${item.price}`, tickerX + 65, 24);
    ctx.fillStyle = item.up ? '#2ecc71' : '#e74c3c'; ctx.fillText(item.change, tickerX + 135, 24);
    tickerX += 200;
  });
  ctx.restore();

  let pulse = (Math.sin(frame * 0.1) + 1) / 2;
  ctx.fillStyle = crisisMode ? `rgba(255, 71, 87, ${pulse})` : `rgba(46, 204, 113, ${pulse})`;
  ctx.beginPath(); ctx.arc(1085, 20, 5, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ffffff'; ctx.font = 'bold 11px monospace'; ctx.fillText("LIVE", 1095, 24);

  ctx.fillStyle = '#090c12'; ctx.fillRect(480, 55, 240, 85);
  ctx.strokeStyle = '#3a4763'; ctx.lineWidth = 2; ctx.strokeRect(480, 55, 240, 85);
  ctx.fillStyle = '#f39c12'; ctx.font = 'bold 11px monospace'; ctx.textAlign = 'center';
  ctx.fillText("📺 BLOOMBERG TERMINAL FEED", 600, 70);
  
  ctx.strokeStyle = crisisMode ? '#ff4757' : '#00f0ff'; 
  ctx.lineWidth = 1.5; ctx.beginPath();
  for (let px = 0; px < 210; px += 5) {
    let py = 105 + Math.sin((frame * simSpeed + px) * 0.08) * (crisisMode ? 25 : 15);
    if (px === 0) ctx.moveTo(495 + px, py); else ctx.lineTo(495 + px, py);
  }
  ctx.stroke();

  ctx.fillStyle = '#e8ecef'; ctx.fillRect(260, 55, 190, 85);
  ctx.strokeStyle = '#b0b7c0'; ctx.lineWidth = 3; ctx.strokeRect(260, 55, 190, 85);
  ctx.fillStyle = '#2c3e50'; ctx.font = 'bold 11px monospace'; ctx.textAlign = 'center';
  ctx.fillText("📋 STRATEGY BOARD", 355, 72);
  ctx.fillStyle = '#e74c3c'; ctx.font = '10px monospace'; ctx.fillText("VAR LIMIT: < 2.5%", 355, 88);
  ctx.fillStyle = '#27ae60'; ctx.fillText("MOMENTUM: BULL RUN", 355, 102);
  ctx.fillStyle = '#2980b9'; ctx.fillText("TARGET: +15% ALLOC", 355, 116);

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
      ctx.fillStyle = crisisMode ? '#ff4757' : (ledOn ? (slot % 2 === 0 ? '#2ecc71' : '#00f0ff') : '#444');
      ctx.fillRect(138, ry + 10 + slot * 16, 8, 4);
    }
  }

  ctx.fillStyle = '#141824'; ctx.fillRect(1030, 55, 150, 400);
  ctx.strokeStyle = '#2a3448'; ctx.lineWidth = 2; ctx.strokeRect(1030, 55, 150, 400);
  ctx.fillStyle = '#f39c12'; ctx.font = 'bold 11px monospace'; ctx.textAlign = 'center';
  ctx.fillText("☕ BARISTA LOUNGE", 1105, 75);

  ctx.fillStyle = '#2c3e50'; ctx.fillRect(1050, 110, 110, 65);
  ctx.fillStyle = '#e67e22'; ctx.fillRect(1065, 130, 25, 35);
  let steamY = (frame * 1.5) % 25;
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.beginPath(); ctx.arc(1077, 125 - steamY, 3, 0, Math.PI * 2); ctx.fill();

  ctx.fillStyle = '#3498db'; ctx.beginPath(); ctx.arc(1135, 230, 14, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ecf0f1'; ctx.fillRect(1125, 244, 20, 35);
  if (frame % 20 < 10) {
    ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(1135, 232, 3, 0, Math.PI * 2); ctx.fill();
  }

  const workstations = [
    { name: "QUANT (ALEX)", x: 270, y: 280, accent: "#2ecc71" },
    { name: "CIO (MARCUS)", x: 500, y: 280, accent: "#3498db" },
    { name: "RISK (SARAH)", x: 730, y: 280, accent: "#e74c3c" },
    { name: "DEV (ELENA)", x: 950, y: 280, accent: "#9b59b6" }
  ];

  workstations.forEach(ws => {
    ctx.fillStyle = '#1e2433'; ctx.fillRect(ws.x - 70, ws.y + 10, 140, 50);
    ctx.strokeStyle = '#35425e'; ctx.lineWidth = 1.5; ctx.strokeRect(ws.x - 70, ws.y + 10, 140, 50);
    
    ctx.fillStyle = '#0f131c'; ctx.fillRect(ws.x - 70, ws.y - 92, 140, 22);
    ctx.strokeStyle = ws.accent; ctx.lineWidth = 1.5; ctx.strokeRect(ws.x - 70, ws.y - 92, 140, 22);
    ctx.fillStyle = '#ffffff'; ctx.font = 'bold 10px monospace'; ctx.textAlign = 'center';
    ctx.fillText(ws.name, ws.x, ws.y - 77);

    ctx.fillStyle = '#080b12'; ctx.fillRect(ws.x - 30, ws.y - 60, 60, 42);
    ctx.strokeStyle = ws.accent; ctx.lineWidth = 1.5; ctx.strokeRect(ws.x - 30, ws.y - 60, 60, 42);
    
    let chartShift = Math.sin(frame * 0.12 + ws.x) * 3;
    ctx.fillStyle = crisisMode ? '#e74c3c' : '#2ecc71'; 
    ctx.fillRect(ws.x - 20, ws.y - 48 + chartShift, 5, 18);
    ctx.fillStyle = '#e74c3c'; ctx.fillRect(ws.x - 10, ws.y - 52 - chartShift, 5, 22);
    ctx.fillStyle = crisisMode ? '#e74c3c' : '#2ecc71'; 
    ctx.fillRect(ws.x + 2, ws.y - 40 + chartShift, 5, 16);
    ctx.fillRect(ws.x + 12, ws.y - 54 - chartShift, 5, 26);
  });

  ctx.fillStyle = '#080b12'; ctx.fillRect(0, 470, canvas.width, 30);
  ctx.strokeStyle = '#f1c40f'; ctx.lineWidth = 1; ctx.strokeRect(0, 470, canvas.width, 30);
  
  newsOffset = (newsOffset + 1.5 * simSpeed) % 2400;
  ctx.save();
  ctx.beginPath(); ctx.rect(0, 470, canvas.width, 30); ctx.clip();
  ctx.fillStyle = '#f1c40f'; ctx.font = 'bold 12px monospace'; ctx.textAlign = 'left';
  let fullNewsText = newsHeadlines.join("  ---  ");
  ctx.fillText(fullNewsText, 1200 - newsOffset, 490);
  ctx.restore();
}

function updateInspector() {
  const agent = staffMembers[selectedAgentIndex];
  if (!agent) return;
  document.getElementById('inspName').innerText = agent.name;
  document.getElementById('inspRole').innerText = agent.title;
  document.getElementById('inspStatus').innerText = agent.state;
  document.getElementById('inspTask').innerText = agent.currentTask;
}

function animate() {
  try {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawEnvironment();
    staffMembers.forEach((s, idx) => {
      s.update();
      s.draw(idx === selectedAgentIndex);
    });
    updateInspector();
    frame++;
  } catch (err) {
    console.error("Frame Execution Error:", err);
  }
  requestAnimationFrame(animate);
}

function dispatchAll(destination) {
  initAudio();
  staffMembers.forEach(s => {
    if (destination === 'PANTRY') s.walkTo(1080 + Math.random() * 20, 280, 'PANTRY');
    else if (destination === 'SERVERS') s.walkTo(90 + Math.random() * 20, 280, 'SERVERS');
    else if (destination === 'WHITEBOARD') s.walkTo(330 + Math.random() * 40, 165, 'WHITEBOARD');
  });
}

function returnToDesks() {
  initAudio();
  staffMembers.forEach(s => s.walkBackToDesk());
}

function toggleCrisis() {
  initAudio();
  crisisMode = !crisisMode;
  logEvent(crisisMode ? "🚨 EMERGENCY CRISIS MODE ACTIVATED!" : "✅ Crisis mode cleared. Operations normal.");
  if (crisisMode) playBeep(250, 'sawtooth', 0.3);
}

function toggleSpeed() {
  simSpeed = simSpeed === 1 ? 2 : (simSpeed === 2 ? 4 : 1);
  document.getElementById('speedLabel').innerText = simSpeed + 'x';
  logEvent(`Simulation speed set to ${simSpeed}x.`);
}

function toggleAudio() {
  initAudio();
  audioEnabled = !audioEnabled;
  document.getElementById('audioLabel').innerText = audioEnabled ? 'ON' : 'OFF';
  if (audioEnabled) playBeep(523.25, 'sine', 0.1);
}

canvas.addEventListener('click', (e) => {
  initAudio();
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const clickX = (e.clientX - rect.left) * scaleX;
  const clickY = (e.clientY - rect.top) * scaleY;

  staffMembers.forEach((s, idx) => {
    const dist = Math.sqrt((clickX - s.x) ** 2 + (clickY - s.y) ** 2);
    if (dist < 40) {
      selectedAgentIndex = idx;
      playBeep(440, 'sine', 0.08);
      logEvent(`Inspecting Agent: ${s.name} (${s.title})`);
    }
  });
});

animate();
</script>
</body>
</html>
"""

components.html(html_code, height=750, scrolling=True)