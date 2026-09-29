# 8. High-Detail Animated Pixel Floor Engine (Fixed Animation Loop)
pixel_floor_html = """
<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; background: #0b0e14; font-family: 'Courier New', monospace; }
  .canvas-container { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; padding: 2px; }
  canvas { display: block; width: 100%; max-width: 1200px; height: auto; aspect-ratio: 1200 / 500; border: 2px solid #232838; border-radius: 10px; background: #0c0f17; image-rendering: pixelated; }
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
    this.timer = Math.floor(Math.random() * 100) + 50;
    this.targetX = deskX; 
    this.targetY = deskY;
    this.destName = '';
  }

  update() {
    if (this.state === 'DESK') {
      this.timer--;
      if (this.timer <= 0) {
        const rand = Math.random();
        if (rand < 0.35) {
          this.targetX = 1080 + Math.random() * 30; 
          this.targetY = 280;
          this.destName = 'PANTRY';
        } else if (rand < 0.65) {
          this.targetX = 90 + Math.random() * 30; 
          this.targetY = 280;
          this.destName = 'SERVERS';
        } else {
          this.targetX = 350 + Math.random() * 40; 
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
        this.timer = Math.floor(Math.random() * 140) + 80;
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
        this.timer = Math.floor(Math.random() * 180) + 100;
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

    // Floating Badge
    let actionTag = "TYPING";
    if (this.state === 'AT_DEST') {
      if (this.destName === 'PANTRY') actionTag = "PANTRY";
      else if (this.destName === 'SERVERS') actionTag = "SERVERS";
      else actionTag = "WHITEBOARD";
    } else if (isWalking) {
      actionTag = "WALKING";
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

    // Thought Bubble (Clean & Safe)
    if (Math.sin(frame * 0.04 + this.x) > 0.3) {
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

  ctx.fillStyle = '#2ecc71'; ctx.font = 'bold 12px monospace'; ctx.textAlign = 'left';
  ctx.fillText("● JC TRADING HOUSE — MAIN FLOOR", 15, 25);

  // Top Moving Stock Ticker
  tickerOffset = (tickerOffset + 1.2) % 1200;
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
  ctx.fillStyle = `rgba(46, 204, 113, ${pulse})`;
  ctx.beginPath(); ctx.arc(1085, 20, 5, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#ffffff'; ctx.font = 'bold 11px monospace'; ctx.fillText("LIVE", 1095, 24);

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
  try {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawEnvironment();
    staffMembers.forEach(s => { s.update(); s.draw(); });
    frame++;
  } catch (err) {
    console.error("Animation Error caught:", err);
  }
  requestAnimationFrame(animate);
}
animate();
</script>
</body>
</html>
"""