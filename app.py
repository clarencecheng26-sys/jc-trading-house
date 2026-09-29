<!DOCTYPE html>
<html lang="en" class="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JC Trading House & AI Strategy Engine</title>
<!-- Tailwind CSS CDN -->
<script src="https://cdn.tailwindcss.com"></script>
<!-- Google Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,300;0,400;0,600;0,800;1,400&family=Share+Tech+Mono&display=swap" rel="stylesheet">

<script>
  tailwind.config = {
    darkMode: 'class',
    theme: {
      extend: {
        colors: {
          darkBg: '#080a0f',
          panelBg: '#0f1420',
          panelBorder: '#1c2538',
          accentBlue: '#00f0ff',
          accentGold: '#f1c40f',
          accentGreen: '#2ecc71',
          accentRed: '#ff4757',
          accentPurple: '#9b59b6',
        },
        fontFamily: {
          mono: ['"JetBrains Mono"', '"Share Tech Mono"', 'monospace'],
        }
      }
    }
  }
</script>

<style>
  body {
    background-color: #080a0f;
    color: #e0e6ed;
    font-family: 'JetBrains Mono', monospace;
    overflow-x: hidden;
  }

  /* Custom Scrollbar */
  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  ::-webkit-scrollbar-track {
    background: #090c14;
  }
  ::-webkit-scrollbar-thumb {
    background: #1e283d;
    border-radius: 3px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: #00f0ff;
  }

  /* Neon Glowing Borders & Text */
  .glow-cyan {
    box-shadow: 0 0 12px rgba(0, 240, 255, 0.35);
  }
  .glow-red {
    box-shadow: 0 0 15px rgba(255, 71, 87, 0.5);
  }
  .glow-green {
    box-shadow: 0 0 12px rgba(46, 204, 113, 0.35);
  }
  .text-glow-cyan {
    text-shadow: 0 0 8px rgba(0, 240, 255, 0.6);
  }

  /* Ticker animation */
  @keyframes tickerMove {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
  }
  .animate-ticker {
    display: flex;
    width: max-content;
    animation: tickerMove 30s linear infinite;
  }
  .animate-ticker:hover {
    animation-play-state: paused;
  }

  /* Canvas styling */
  canvas {
    image-rendering: pixelated;
    image-rendering: crisp-edges;
  }

  /* Pulse overlay for crisis mode */
  .crisis-pulse {
    animation: crisisAlert 1s infinite alternate;
  }
  @keyframes crisisAlert {
    from { border-color: #ff4757; box-shadow: 0 0 10px rgba(255, 71, 87, 0.4); }
    to { border-color: #bd1c2b; box-shadow: 0 0 25px rgba(255, 71, 87, 0.8); }
  }
</style>
</head>

<body class="min-h-screen flex flex-col p-2 md:p-4 gap-3 bg-darkBg select-none">

<!-- TOP HEADER & LIVE TICKER BAR -->
<header class="w-full bg-panelBg border border-panelBorder rounded-lg p-2 md:p-3 flex flex-col gap-2 shadow-lg">
  <div class="flex flex-wrap justify-between items-center gap-2 border-b border-panelBorder/60 pb-2">
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-2">
        <span class="w-3 h-3 rounded-full bg-accentGreen animate-ping"></span>
        <h1 class="text-lg md:text-xl font-bold tracking-wider text-accentBlue text-glow-cyan">
          JC TRADING HOUSE <span class="text-xs text-accentGold border border-accentGold/40 px-1.5 py-0.5 rounded ml-1">AI ENGINE v4.2</span>
        </h1>
      </div>
    </div>

    <!-- SIMULATION CONTROLS -->
    <div class="flex flex-wrap items-center gap-1.5 text-xs">
      <!-- Floor Dispatch Buttons -->
      <div class="flex items-center bg-darkBg border border-panelBorder rounded p-1 gap-1">
        <button onclick="dispatchAll('PANTRY')" class="hover:bg-accentBlue/20 text-accentBlue px-2 py-1 rounded transition">☕ Pantry</button>
        <button onclick="dispatchAll('WHITEBOARD')" class="hover:bg-accentBlue/20 text-accentBlue px-2 py-1 rounded transition">📋 Sync</button>
        <button onclick="dispatchAll('SERVERS')" class="hover:bg-accentBlue/20 text-accentBlue px-2 py-1 rounded transition">🖥️️ Servers</button>
        <button onclick="returnToDesks()" class="hover:bg-accentGold/20 text-accentGold px-2 py-1 rounded transition">🪑 Desks</button>
        <button onclick="openAddAgentModal()" class="bg-accentGreen/20 hover:bg-accentGreen/30 text-accentGreen border border-accentGreen/40 px-2 py-1 rounded transition font-bold">+ Agent</button>
      </div>

      <!-- Execution Toggles -->
      <div class="flex items-center bg-darkBg border border-panelBorder rounded p-1 gap-1">
        <button id="pauseBtn" onclick="togglePause()" class="hover:bg-accentBlue/20 text-accentBlue px-2 py-1 rounded transition">⏸️ Pause</button>
        <button id="crisisBtn" onclick="toggleCrisisMode()" class="hover:bg-accentRed/30 text-accentRed border border-accentRed/40 px-2 py-1 rounded transition font-bold">🚨 Crisis Mode</button>
        <button onclick="toggleSpeed()" class="hover:bg-accentGold/20 text-accentGold px-2 py-1 rounded transition">⏩ <span id="speedDisplay">1x</span></button>
        <button onclick="toggleSound()" class="hover:bg-accentBlue/20 text-accentBlue px-2 py-1 rounded transition">🔊 Sound: <span id="soundDisplay">ON</span></button>
      </div>
    </div>
  </div>

  <!-- SCROLLING MARKET TICKER BANNER -->
  <div class="w-full overflow-hidden bg-darkBg border border-panelBorder/80 rounded py-1 relative">
    <div id="tickerContainer" class="animate-ticker text-xs flex gap-8 items-center whitespace-nowrap">
      <!-- Dynamic Ticker Items Injected via JS -->
    </div>
  </div>
</header>

<!-- MAIN FLOOR CANVAS & INSPECTOR SECTION -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-3">
  
  <!-- 2D TRADING FLOOR CANVAS CONTAINER (8 Cols) -->
  <div class="lg:col-span-8 flex flex-col gap-2">
    <div id="canvasWrapper" class="relative w-full bg-darkBg border-2 border-panelBorder rounded-lg overflow-hidden shadow-2xl">
      <canvas id="tradingFloor" width="1200" height="420" class="w-full h-auto block"></canvas>
      
      <!-- Canvas Overlay Indicators -->
      <div class="absolute top-2 left-2 pointer-events-none flex gap-2 text-[10px]">
        <span class="bg-darkBg/80 backdrop-blur border border-accentBlue/40 text-accentBlue px-2 py-0.5 rounded">FLOOR: 1200x420 MATRIX</span>
        <span id="canvasStatusBadge" class="bg-darkBg/80 backdrop-blur border border-accentGreen/40 text-accentGreen px-2 py-0.5 rounded">STATUS: OPTIMAL 60FPS</span>
      </div>
    </div>
  </div>

  <!-- AGENT INSPECTOR & QUICK CONTROLS (4 Cols) -->
  <div class="lg:col-span-4 flex flex-col gap-3">
    <!-- AGENT INSPECTOR CARD -->
    <div class="bg-panelBg border border-panelBorder rounded-lg p-3 flex flex-col gap-2.5 h-full justify-between shadow-lg">
      <div class="flex justify-between items-center border-b border-panelBorder/80 pb-1.5">
        <h2 class="text-xs font-bold text-accentGold flex items-center gap-1.5">
          <span>🔍</span> AI AGENT INSPECTOR
        </h2>
        <button onclick="openEditTaskModal()" class="text-[10px] bg-accentBlue/10 hover:bg-accentBlue/20 text-accentBlue border border-accentBlue/30 px-2 py-0.5 rounded transition">
          ✏️ Edit Task
        </button>
      </div>

      <!-- Agent Details Grid -->
      <div class="grid grid-cols-2 gap-2 text-xs">
        <div class="bg-darkBg/80 p-2 rounded border border-panelBorder/50">
          <span class="text-[10px] text-gray-400 block">SELECTED AGENT</span>
          <span id="inspName" class="font-bold text-accentBlue text-sm">ALEX</span>
        </div>
        <div class="bg-darkBg/80 p-2 rounded border border-panelBorder/50">
          <span class="text-[10px] text-gray-400 block">ROLE / BADGE</span>
          <span id="inspRole" class="font-bold text-accentGreen text-sm">QUANT ANALYST 📈</span>
        </div>
        <div class="bg-darkBg/80 p-2 rounded border border-panelBorder/50">
          <span class="text-[10px] text-gray-400 block">FLOOR LOCATION</span>
          <span id="inspState" class="font-bold text-gray-200">WORKSTATION</span>
        </div>
        <div class="bg-darkBg/80 p-2 rounded border border-panelBorder/50">
          <span class="text-[10px] text-gray-400 block">MODEL BIAS</span>
          <span id="inspBias" class="font-bold text-accentGold">BULLISH (+0.72)</span>
        </div>
      </div>

      <!-- Active Task & Thought Output -->
      <div class="bg-darkBg p-2.5 rounded border border-panelBorder/80 flex flex-col gap-1.5">
        <div class="flex justify-between items-center text-[10px]">
          <span class="text-gray-400">CURRENT SUB-TASK:</span>
          <span id="inspTaskBadge" class="text-accentBlue font-semibold">ACTIVE</span>
        </div>
        <p id="inspTask" class="text-xs text-gray-200 font-mono leading-relaxed">
          Running Monte Carlo volatility matrix across BTC-USD order book depth...
        </p>
      </div>

      <div class="bg-darkBg p-2 rounded border border-panelBorder/80 flex flex-col gap-1 text-[11px]">
        <div class="flex justify-between text-gray-400">
          <span>ACTIVE THOUGHT:</span>
          <span class="text-accentGold animate-pulse">● LIVE REASONING</span>
        </div>
        <div id="inspThought" class="text-accentGold italic font-mono text-xs">
          "Order book imbalanced towards bid side. Pre-executing buy scalps."
        </div>
      </div>

      <!-- Quick Action Buttons for Selected Agent -->
      <div class="grid grid-cols-3 gap-1.5 text-[11px]">
        <button onclick="dispatchSelectedAgent('PANTRY')" class="bg-darkBg hover:bg-panelBorder border border-panelBorder text-gray-300 py-1 rounded transition text-center">☕ Coffee</button>
        <button onclick="dispatchSelectedAgent('SERVERS')" class="bg-darkBg hover:bg-panelBorder border border-panelBorder text-gray-300 py-1 rounded transition text-center">🖥️ Server</button>
        <button onclick="dispatchSelectedAgent('DESK')" class="bg-darkBg hover:bg-panelBorder border border-panelBorder text-gray-300 py-1 rounded transition text-center">🪑 Desk</button>
      </div>
    </div>
  </div>
</div>

<!-- PORTFOLIO PERFORMANCE METRICS BAR -->
<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-xs">
  <div class="bg-panelBg border border-panelBorder p-2.5 rounded-lg flex flex-col gap-1 shadow">
    <span class="text-[10px] text-gray-400">PORTFOLIO EQUITY</span>
    <span id="metricEquity" class="text-base font-bold text-accentBlue text-glow-cyan">$1,254,820.50</span>
    <span class="text-[9px] text-accentGreen">▲ +25.48% Overall</span>
  </div>
  <div class="bg-panelBg border border-panelBorder p-2.5 rounded-lg flex flex-col gap-1 shadow">
    <span class="text-[10px] text-gray-400">REALIZED P&L (SESSION)</span>
    <span id="metricPnL" class="text-base font-bold text-accentGreen">+$14,350.20</span>
    <span id="metricPnLPct" class="text-[9px] text-accentGreen">+1.16% Today</span>
  </div>
  <div class="bg-panelBg border border-panelBorder p-2.5 rounded-lg flex flex-col gap-1 shadow">
    <span class="text-[10px] text-gray-400">WIN RATE %</span>
    <span id="metricWinRate" class="text-base font-bold text-accentGold">68.4%</span>
    <span class="text-[9px] text-gray-400"><span id="metricTradesCount">142</span> Total Executions</span>
  </div>
  <div class="bg-panelBg border border-panelBorder p-2.5 rounded-lg flex flex-col gap-1 shadow">
    <span class="text-[10px] text-gray-400">SHARPE RATIO</span>
    <span id="metricSharpe" class="text-base font-bold text-accentBlue">2.84</span>
    <span class="text-[9px] text-accentGreen">Institutional Grade</span>
  </div>
  <div class="bg-panelBg border border-panelBorder p-2.5 rounded-lg flex flex-col gap-1 shadow">
    <span class="text-[10px] text-gray-400">MAX DRAWDOWN</span>
    <span id="metricDrawdown" class="text-base font-bold text-accentRed">-1.82%</span>
    <span class="text-[9px] text-gray-400">Limit: -5.00%</span>
  </div>
  <div class="bg-panelBg border border-panelBorder p-2.5 rounded-lg flex flex-col gap-1 shadow">
    <span class="text-[10px] text-gray-400">VaR CIRCUIT BREAKER</span>
    <span id="metricVaR" class="text-base font-bold text-accentGreen">PASS (1.15%)</span>
    <span class="text-[9px] text-gray-400">95% Confidence Level</span>
  </div>
</div>

<!-- MARKET ANALYTICS: INTERACTIVE CHART & ORDER BOOK LADDER -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-3">

  <!-- PRICE CHART CANVAS & ASSET SELECTOR (8 Cols) -->
  <div class="lg:col-span-8 bg-panelBg border border-panelBorder rounded-lg p-3 flex flex-col gap-3 shadow-lg">
    <!-- Asset Selector & Market Header -->
    <div class="flex flex-wrap justify-between items-center gap-2 border-b border-panelBorder/80 pb-2">
      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-400">SELECT ASSET:</span>
        <div id="assetSelectorGroup" class="flex gap-1 text-xs">
          <!-- Asset Buttons JS Generated -->
        </div>
      </div>
      <div class="flex items-center gap-3 text-xs">
        <div><span class="text-gray-400">PRICE:</span> <span id="assetLivePrice" class="font-bold text-accentGreen">$92,450.10</span></div>
        <div><span class="text-gray-400">24H HIGH:</span> <span id="assetHigh" class="text-gray-200">$93,100.00</span></div>
        <div><span class="text-gray-400">24H LOW:</span> <span id="assetLow" class="text-gray-200">$90,850.00</span></div>
      </div>
    </div>

    <!-- Chart Canvas Area -->
    <div class="relative w-full h-[260px] bg-darkBg border border-panelBorder rounded overflow-hidden">
      <canvas id="marketChart" width="800" height="260" class="w-full h-full block cursor-crosshair"></canvas>
      
      <!-- Chart Indicator Legend -->
      <div class="absolute top-2 left-2 flex gap-3 text-[10px] bg-darkBg/90 p-1.5 rounded border border-panelBorder">
        <span class="text-accentBlue flex items-center gap-1"><span class="w-2 h-0.5 bg-accentBlue inline-block"></span> Price Line</span>
        <span class="text-accentGold flex items-center gap-1"><span class="w-2 h-0.5 bg-accentGold inline-block"></span> SMA 20</span>
        <span class="text-accentPurple flex items-center gap-1"><span class="w-2 h-0.5 bg-accentPurple inline-block"></span> SMA 50</span>
        <span class="text-accentGreen">▲ BUY</span>
        <span class="text-accentRed">▼ SELL</span>
      </div>

      <!-- Tooltip -->
      <div id="chartTooltip" class="hidden absolute pointer-events-none bg-panelBg/95 border border-accentBlue p-2 rounded text-[10px] shadow-lg flex flex-col gap-0.5 z-10"></div>
    </div>
  </div>

  <!-- ORDER BOOK DEPTH LADDER (4 Cols) -->
  <div class="lg:col-span-4 bg-panelBg border border-panelBorder rounded-lg p-3 flex flex-col gap-2 justify-between shadow-lg">
    <div class="flex justify-between items-center border-b border-panelBorder/80 pb-1.5">
      <h2 class="text-xs font-bold text-accentBlue flex items-center gap-1">
        <span>📊</span> ORDER BOOK DEPTH LADDER
      </h2>
      <span class="text-[10px] text-gray-400" id="obSpreadText">SPREAD: $0.50</span>
    </div>

    <!-- Order Book Table -->
    <div class="flex flex-col gap-1 text-[11px] font-mono">
      <!-- Asks (Red) Header -->
      <div class="grid grid-cols-3 text-gray-500 text-[9px] border-b border-panelBorder pb-1">
        <span>PRICE ($)</span>
        <span class="text-right">SIZE</span>
        <span class="text-right">TOTAL</span>
      </div>

      <!-- Asks Ladder Container -->
      <div id="asksLadder" class="flex flex-col gap-0.5">
        <!-- JS Injected Asks -->
      </div>

      <!-- Mid-Price Separator -->
      <div class="my-1 py-1 bg-darkBg border-y border-panelBorder text-center font-bold text-xs flex justify-between px-2">
        <span class="text-gray-400 text-[10px]">MID PRICE</span>
        <span id="obMidPrice" class="text-accentGold">$92,450.10</span>
      </div>

      <!-- Bids Ladder Container -->
      <div id="bidsLadder" class="flex flex-col gap-0.5">
        <!-- JS Injected Bids -->
      </div>
    </div>
  </div>
</div>

<!-- AI STRATEGY ENGINE CONTROL PANEL -->
<div class="bg-panelBg border border-panelBorder rounded-lg p-3 flex flex-col gap-3 shadow-lg">
  <div class="flex justify-between items-center border-b border-panelBorder/80 pb-2">
    <h2 class="text-xs font-bold text-accentGold flex items-center gap-2">
      <span>⚡</span> AI STRATEGY ENGINE CONTROL & EXECUTION
    </h2>
    <span class="text-[10px] text-accentGreen">4 STRATEGIES MONITORED</span>
  </div>

  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
    
    <!-- Strategy 1: Quant Volatility Arbitrage -->
    <div class="bg-darkBg border border-panelBorder p-2.5 rounded-lg flex flex-col gap-2 relative overflow-hidden">
      <div class="flex justify-between items-center">
        <span class="text-xs font-bold text-accentBlue">1. QUANT VOL ARBITRAGE</span>
        <input type="checkbox" id="stratQuantActive" checked class="w-4 h-4 accent-accentBlue cursor-pointer">
      </div>
      <p class="text-[10px] text-gray-400">Bollinger Band mean reversion & Z-score statistical arbitrage.</p>
      <div class="flex justify-between items-center text-[10px]">
        <span class="text-gray-400">SIGNAL STATUS:</span>
        <span id="sigQuant" class="text-accentGreen font-bold bg-accentGreen/10 border border-accentGreen/30 px-1.5 py-0.5 rounded">BUY SIGNAL</span>
      </div>
      <div class="flex flex-col gap-1">
        <div class="flex justify-between text-[9px] text-gray-400">
          <span>AGGRESSIVENESS</span>
          <span id="valQuantAgg">1.8x</span>
        </div>
        <input type="range" id="sliderQuantAgg" min="1" max="3" step="0.1" value="1.8" class="h-1 bg-panelBorder rounded accent-accentBlue cursor-pointer">
      </div>
    </div>

    <!-- Strategy 2: AI News Sentiment Momentum -->
    <div class="bg-darkBg border border-panelBorder p-2.5 rounded-lg flex flex-col gap-2 relative overflow-hidden">
      <div class="flex justify-between items-center">
        <span class="text-xs font-bold text-accentGold">2. NEWS SENTIMENT AI</span>
        <input type="checkbox" id="stratNewsActive" checked class="w-4 h-4 accent-accentGold cursor-pointer">
      </div>
      <p class="text-[10px] text-gray-400">NLP sentiment parsing on live institutional news headlines.</p>
      <div class="flex justify-between items-center text-[10px]">
        <span class="text-gray-400">SENTIMENT SCORE:</span>
        <span id="sigNewsScore" class="text-accentGreen font-bold">+0.78 (BULLISH)</span>
      </div>
      <div class="w-full bg-panelBorder h-1.5 rounded overflow-hidden relative">
        <div id="sentimentBar" class="bg-accentGreen h-full transition-all duration-300" style="width: 82%;"></div>
      </div>
    </div>

    <!-- Strategy 3: Adaptive Market Making -->
    <div class="bg-darkBg border border-panelBorder p-2.5 rounded-lg flex flex-col gap-2 relative overflow-hidden">
      <div class="flex justify-between items-center">
        <span class="text-xs font-bold text-accentGreen">3. ADAPTIVE MARKET MAKING</span>
        <input type="checkbox" id="stratMMActive" checked class="w-4 h-4 accent-accentGreen cursor-pointer">
      </div>
      <p class="text-[10px] text-gray-400">Continuous micro-spread quoting around order book depth.</p>
      <div class="flex justify-between items-center text-[10px]">
        <span class="text-gray-400">QUOTING SPREAD:</span>
        <span id="sigMMSpread" class="text-accentGold font-bold">12 BPS</span>
      </div>
      <div class="flex flex-col gap-1">
        <div class="flex justify-between text-[9px] text-gray-400">
          <span>SPREAD CAPTURE BPS</span>
          <span id="valMMBps">12 BPS</span>
        </div>
        <input type="range" id="sliderMMBps" min="5" max="30" step="1" value="12" class="h-1 bg-panelBorder rounded accent-accentGreen cursor-pointer">
      </div>
    </div>

    <!-- Strategy 4: Dynamic Risk Manager -->
    <div class="bg-darkBg border border-panelBorder p-2.5 rounded-lg flex flex-col gap-2 relative overflow-hidden">
      <div class="flex justify-between items-center">
        <span class="text-xs font-bold text-accentRed">4. DYNAMIC RISK MANAGER</span>
        <input type="checkbox" id="stratRiskActive" checked class="w-4 h-4 accent-accentRed cursor-pointer">
      </div>
      <p class="text-[10px] text-gray-400">Automated stop-loss, drawdown cap, & VaR circuit breaker.</p>
      <div class="flex justify-between items-center text-[10px]">
        <span class="text-gray-400">AUTO STOP-LOSS:</span>
        <span class="text-accentRed font-bold">-2.0% POSITION</span>
      </div>
      <button onclick="emergencyLiquidate()" class="w-full bg-accentRed/20 hover:bg-accentRed/30 text-accentRed border border-accentRed/50 text-[10px] py-1 rounded transition font-bold">
        💥 EMERGENCY LIQUIDATE POSITIONS
      </button>
    </div>

  </div>
</div>

<!-- TRADES TABLE & CONSOLE LOG SECTION -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-3">
  
  <!-- EXECUTED TRADES TABLE (7 Cols) -->
  <div class="lg:col-span-7 bg-panelBg border border-panelBorder rounded-lg p-3 flex flex-col gap-2 shadow-lg">
    <div class="flex justify-between items-center border-b border-panelBorder/80 pb-1.5">
      <h2 class="text-xs font-bold text-accentGreen flex items-center gap-1.5">
        <span>📜</span> RECENT EXECUTED TRADES
      </h2>
      <button onclick="exportTradesCSV()" class="text-[10px] bg-darkBg hover:bg-panelBorder border border-panelBorder text-gray-300 px-2 py-0.5 rounded transition">
        💾 Export CSV
      </button>
    </div>

    <div class="overflow-x-auto max-h-[180px] overflow-y-auto">
      <table class="w-full text-left text-[11px] font-mono">
        <thead class="bg-darkBg text-gray-400 sticky top-0 border-b border-panelBorder">
          <tr>
            <th class="p-1.5">TIME</th>
            <th class="p-1.5">ASSET</th>
            <th class="p-1.5">TYPE</th>
            <th class="p-1.5">PRICE</th>
            <th class="p-1.5">QTY</th>
            <th class="p-1.5">STRATEGY</th>
            <th class="p-1.5 text-right">PROFIT</th>
          </tr>
        </thead>
        <tbody id="tradesTableBody" class="divide-y divide-panelBorder/40 text-gray-200">
          <!-- Executed Trades Injected Here -->
        </tbody>
      </table>
    </div>
  </div>

  <!-- CONSOLE EVENT LOG (5 Cols) -->
  <div class="lg:col-span-5 bg-panelBg border border-panelBorder rounded-lg p-3 flex flex-col gap-2 shadow-lg">
    <div class="flex justify-between items-center border-b border-panelBorder/80 pb-1.5">
      <h2 class="text-xs font-bold text-accentGold flex items-center gap-1.5">
        <span>💻</span> FLOOR & ENGINE CONSOLE
      </h2>
      <div class="flex gap-1">
        <button onclick="clearConsoleLogs()" class="text-[10px] bg-darkBg hover:bg-panelBorder border border-panelBorder text-gray-300 px-2 py-0.5 rounded transition">🗑️ Clear</button>
        <button onclick="exportConsoleLogs()" class="text-[10px] bg-darkBg hover:bg-panelBorder border border-panelBorder text-gray-300 px-2 py-0.5 rounded transition">💾 Export JSON</button>
      </div>
    </div>

    <div id="consoleLogContainer" class="bg-darkBg p-2 rounded border border-panelBorder font-mono text-[10px] leading-relaxed h-[180px] overflow-y-auto flex flex-col gap-1 text-accentGreen">
      <!-- Logs injected dynamically -->
    </div>
  </div>
</div>

<!-- CUSTOM MODALS -->
<!-- ADD AGENT MODAL -->
<div id="modalAddAgent" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
  <div class="bg-panelBg border border-accentBlue rounded-lg p-4 w-full max-w-md flex flex-col gap-3 shadow-2xl">
    <h3 class="text-sm font-bold text-accentBlue flex items-center gap-2">
      <span>➕</span> RECRUIT NEW AI AGENT
    </h3>
    <div class="flex flex-col gap-2 text-xs">
      <div>
        <label class="text-gray-400 block mb-1">AGENT NAME:</label>
        <input type="text" id="newAgentName" value="KAI" class="w-full bg-darkBg border border-panelBorder p-1.5 rounded text-gray-200 focus:border-accentBlue outline-none">
      </div>
      <div>
        <label class="text-gray-400 block mb-1">ROLE / SPECIALIZATION:</label>
        <select id="newAgentRole" class="w-full bg-darkBg border border-panelBorder p-1.5 rounded text-gray-200 focus:border-accentBlue outline-none">
          <option value="HFT TRADER">HFT TRADER ⚡</option>
          <option value="MACRO STRATEGIST">MACRO STRATEGIST 🌐</option>
          <option value="NLP SENTIMENT AI">NLP SENTIMENT AI 📰</option>
          <option value="ARBITRAGE BOT">ARBITRAGE BOT 🔄</option>
        </select>
      </div>
      <div>
        <label class="text-gray-400 block mb-1">ASSIGNED TASK:</label>
        <input type="text" id="newAgentTask" value="Monitoring cross-exchange liquidity imbalances" class="w-full bg-darkBg border border-panelBorder p-1.5 rounded text-gray-200 focus:border-accentBlue outline-none">
      </div>
    </div>
    <div class="flex justify-end gap-2 mt-2 text-xs">
      <button onclick="closeAddAgentModal()" class="bg-darkBg hover:bg-panelBorder border border-panelBorder px-3 py-1 rounded text-gray-300">Cancel</button>
      <button onclick="submitAddAgent()" class="bg-accentGreen/20 hover:bg-accentGreen/30 text-accentGreen border border-accentGreen/50 px-3 py-1 rounded font-bold">Add to Floor</button>
    </div>
  </div>
</div>

<!-- EDIT TASK MODAL -->
<div id="modalEditTask" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
  <div class="bg-panelBg border border-accentGold rounded-lg p-4 w-full max-w-md flex flex-col gap-3 shadow-2xl">
    <h3 class="text-sm font-bold text-accentGold flex items-center gap-2">
      <span>✏️</span> RE-ASSIGN AGENT TASK
    </h3>
    <div class="flex flex-col gap-2 text-xs">
      <div>
        <label class="text-gray-400 block mb-1">AGENT:</label>
        <span id="modalEditAgentName" class="font-bold text-accentBlue">ALEX</span>
      </div>
      <div>
        <label class="text-gray-400 block mb-1">NEW SUB-TASK DESCRIPTION:</label>
        <input type="text" id="modalEditTaskInput" value="" class="w-full bg-darkBg border border-panelBorder p-1.5 rounded text-gray-200 focus:border-accentGold outline-none">
      </div>
    </div>
    <div class="flex justify-end gap-2 mt-2 text-xs">
      <button onclick="closeEditTaskModal()" class="bg-darkBg hover:bg-panelBorder border border-panelBorder px-3 py-1 rounded text-gray-300">Cancel</button>
      <button onclick="submitEditTask()" class="bg-accentGold/20 hover:bg-accentGold/30 text-accentGold border border-accentGold/50 px-3 py-1 rounded font-bold">Update Task</button>
    </div>
  </div>
</div>

<script>
/* GLOBAL STATE & ENGINE DATA STRUCTURES */
let frame = 0;
let simSpeed = 1;
let soundEnabled = true;
let crisisMode = false;
let isPaused = false;
let audioCtx = null;

// Selected Asset
let currentAssetKey = 'BTC-USD';

// Market Data Definition
const marketAssets = {
  'BTC-USD': { name: 'BITCOIN', price: 92450.10, basePrice: 92450.10, high: 93100.00, low: 90850.00, vol: 4.2, spread: 0.50, history: [], buys: [], sells: [] },
  'NVDA': { name: 'NVIDIA CORP', price: 138.20, basePrice: 138.20, high: 140.50, low: 135.80, vol: 0.8, spread: 0.05, history: [], buys: [], sells: [] },
  'TSLA': { name: 'TESLA INC', price: 248.50, basePrice: 248.50, high: 252.00, low: 242.10, vol: 1.2, spread: 0.10, history: [], buys: [], sells: [] },
  'ETH-USD': { name: 'ETHEREUM', price: 3450.80, basePrice: 3450.80, high: 3510.00, low: 3380.00, vol: 0.9, spread: 0.20, history: [], buys: [], sells: [] },
  'S68.SG': { name: 'SGX GROUP', price: 10.85, basePrice: 10.85, high: 11.00, low: 10.70, vol: 0.05, spread: 0.01, history: [], buys: [], sells: [] },
  'AAPL': { name: 'APPLE INC', price: 228.10, basePrice: 228.10, high: 231.20, low: 225.40, vol: 0.6, spread: 0.08, history: [], buys: [], sells: [] }
};

// Portfolio Metrics
let portfolio = {
  equity: 1254820.50,
  startingEquity: 1000000.00,
  pnlSession: 14350.20,
  winCount: 97,
  totalTrades: 142,
  sharpe: 2.84,
  maxDrawdown: -1.82,
  positions: {}
};

// Executed Trades History
const executedTrades = [];
const consoleLogs = [];

// WEB AUDIO SYNTHESIZER
function initAudio() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
}

function playSynthTone(freq = 440, type = 'sine', duration = 0.08, vol = 0.05) {
  if (!soundEnabled) return;
  initAudio();
  if (!audioCtx) return;
  try {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    gain.gain.setValueAtTime(vol, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + duration);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + duration);
  } catch (e) {}
}

function playTradeSound(isBuy) {
  if (isBuy) {
    playSynthTone(587.33, 'triangle', 0.08, 0.06); // D5
    setTimeout(() => playSynthTone(880, 'sine', 0.12, 0.08), 50); // A5
  } else {
    playSynthTone(783.99, 'sawtooth', 0.08, 0.06); // G5
    setTimeout(() => playSynthTone(523.25, 'sine', 0.12, 0.08), 50); // C5
  }
}

function playAlertSound() {
  playSynthTone(300, 'sawtooth', 0.2, 0.1);
  setTimeout(() => playSynthTone(200, 'sawtooth', 0.3, 0.12), 150);
}

/* CONSOLE LOGGER */
function logConsole(msg, level = 'INFO') {
  const timestamp = new Date().toLocaleTimeString();
  const entry = { time: timestamp, msg: msg, level: level };
  consoleLogs.unshift(entry);

  const container = document.getElementById('consoleLogContainer');
  if (!container) return;

  let colorClass = 'text-accentGreen';
  if (level === 'ALERT') colorClass = 'text-accentRed font-bold';
  else if (level === 'TRADE') colorClass = 'text-accentBlue';
  else if (level === 'STRATEGY') colorClass = 'text-accentGold';

  const row = document.createElement('div');
  row.className = `${colorClass} flex gap-1.5`;
  row.innerHTML = `<span class="text-gray-500">[${timestamp}]</span> <span>[${level}]</span> <span>${msg}</span>`;
  
  container.insertBefore(row, container.firstChild);
  if (container.children.length > 80) container.removeChild(container.lastChild);
}

function clearConsoleLogs() {
  consoleLogs.length = 0;
  document.getElementById('consoleLogContainer').innerHTML = '<div class="text-gray-500 font-italic">> Console logs cleared.</div>';
}

function exportConsoleLogs() {
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(consoleLogs, null, 2));
  const anchor = document.createElement('a');
  anchor.setAttribute("href", dataStr);
  anchor.setAttribute("download", `jc_trading_house_console_${Date.now()}.json`);
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}

function exportTradesCSV() {
  let csvContent = "data:text/csv;charset=utf-8,TIME,ASSET,TYPE,PRICE,QTY,STRATEGY,PROFIT\n";
  executedTrades.forEach(t => {
    csvContent += `${t.time},${t.asset},${t.type},${t.price},${t.qty},${t.strategy},${t.profit}\n`;
  });
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `jc_executed_trades_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
}

/* HISTORICAL MARKET DATA INITIALIZATION & SIMULATOR */
function initMarketHistory() {
  Object.keys(marketAssets).forEach(key => {
    const asset = marketAssets[key];
    let currentP = asset.basePrice;
    asset.history = [];
    for (let i = 0; i < 100; i++) {
      const change = (Math.random() - 0.49) * (asset.vol * 0.4);
      currentP += change;
      asset.history.push(currentP);
    }
    asset.price = currentP;
  });
}
initMarketHistory();

function updateMarketData() {
  if (isPaused) return;

  Object.keys(marketAssets).forEach(key => {
    const asset = marketAssets[key];
    
    // Crisis mode increases volatility & downward bias
    let bias = 0.495;
    let volMultiplier = 1.0;
    if (crisisMode) {
      bias = 0.62; // heavy selling bias
      volMultiplier = 3.5;
    }

    const delta = (Math.random() - bias) * (asset.vol * 0.25 * volMultiplier * simSpeed);
    asset.price = Math.max(0.1, asset.price + delta);
    
    if (asset.price > asset.high) asset.high = asset.price;
    if (asset.price < asset.low) asset.low = asset.price;

    asset.history.push(asset.price);
    if (asset.history.length > 120) asset.history.shift();
  });

  // Update asset UI elements
  const currentAsset = marketAssets[currentAssetKey];
  document.getElementById('assetLivePrice').innerText = `$${currentAsset.price.toFixed(2)}`;
  document.getElementById('assetLivePrice').className = (currentAsset.price >= currentAsset.basePrice) ? 'font-bold text-accentGreen' : 'font-bold text-accentRed';
  document.getElementById('assetHigh').innerText = `$${currentAsset.high.toFixed(2)}`;
  document.getElementById('assetLow').innerText = `$${currentAsset.low.toFixed(2)}`;
}

/* TECHNICAL INDICATORS CALCULATOR */
function calculateSMA(data, period) {
  if (data.length < period) return null;
  const slice = data.slice(data.length - period);
  const sum = slice.reduce((a, b) => a + b, 0);
  return sum / period;
}

function calculateBollingerBands(data, period = 20, stdDevMultiplier = 2) {
  if (data.length < period) return null;
  const sma = calculateSMA(data, period);
  const slice = data.slice(data.length - period);
  const variance = slice.reduce((sum, val) => sum + Math.pow(val - sma, 2), 0) / period;
  const stdDev = Math.sqrt(variance);
  return {
    sma: sma,
    upper: sma + stdDev * stdDevMultiplier,
    lower: sma - stdDev * stdDevMultiplier,
    stdDev: stdDev
  };
}

/* AI STRATEGY ENGINE & EXECUTION ROUTINNER */
function runAIStrategyEngine() {
  if (isPaused) return;

  const quantActive = document.getElementById('stratQuantActive').checked;
  const newsActive = document.getElementById('stratNewsActive').checked;
  const mmActive = document.getElementById('stratMMActive').checked;
  const riskActive = document.getElementById('stratRiskActive').checked;

  const currentAsset = marketAssets[currentAssetKey];
  const history = currentAsset.history;

  // 1. QUANT VOLATILITY ARBITRAGE
  if (quantActive && history.length >= 20) {
    const bb = calculateBollingerBands(history, 20, 2);
    if (bb) {
      const zScore = (currentAsset.price - bb.sma) / (bb.stdDev || 1);
      const sigElement = document.getElementById('sigQuant');
      
      if (zScore < -1.8) {
        sigElement.innerText = "BUY SIGNAL (OVERSOLD)";
        sigElement.className = "text-accentGreen font-bold bg-accentGreen/10 border border-accentGreen/30 px-1.5 py-0.5 rounded";
        if (Math.random() < 0.15 * simSpeed) executeTrade(currentAssetKey, 'BUY', 1.0, 'Quant Vol Arb');
      } else if (zScore > 1.8) {
        sigElement.innerText = "SELL SIGNAL (OVERBOUGHT)";
        sigElement.className = "text-accentRed font-bold bg-accentRed/10 border border-accentRed/30 px-1.5 py-0.5 rounded";
        if (Math.random() < 0.15 * simSpeed) executeTrade(currentAssetKey, 'SELL', 1.0, 'Quant Vol Arb');
      } else {
        sigElement.innerText = "HOLD (NEUTRAL)";
        sigElement.className = "text-gray-400 font-bold bg-darkBg border border-panelBorder px-1.5 py-0.5 rounded";
      }
    }
  }

  // 2. NEWS SENTIMENT MOMENTUM
  if (newsActive && frame % 180 === 0) {
    const sentimentScore = crisisMode ? -0.85 : (Math.random() * 1.6 - 0.7);
    const scoreElem = document.getElementById('sigNewsScore');
    const barElem = document.getElementById('sentimentBar');
    
    const fillPct = Math.max(0, Math.min(100, (sentimentScore + 1) * 50));
    barElem.style.width = `${fillPct}%`;

    if (sentimentScore > 0.4) {
      scoreElem.innerText = `+${sentimentScore.toFixed(2)} (BULLISH)`;
      scoreElem.className = "text-accentGreen font-bold";
      barElem.className = "bg-accentGreen h-full transition-all duration-300";
      if (Math.random() < 0.4) executeTrade(currentAssetKey, 'BUY', 0.5, 'News Sentiment');
    } else if (sentimentScore < -0.4) {
      scoreElem.innerText = `${sentimentScore.toFixed(2)} (BEARISH)`;
      scoreElem.className = "text-accentRed font-bold";
      barElem.className = "bg-accentRed h-full transition-all duration-300";
      if (Math.random() < 0.4) executeTrade(currentAssetKey, 'SELL', 0.5, 'News Sentiment');
    } else {
      scoreElem.innerText = `${sentimentScore.toFixed(2)} (NEUTRAL)`;
      scoreElem.className = "text-accentGold font-bold";
      barElem.className = "bg-accentGold h-full transition-all duration-300";
    }
  }

  // 3. ADAPTIVE MARKET MAKING
  if (mmActive && frame % 120 === 0) {
    if (Math.random() < 0.3 * simSpeed) {
      const isBuy = Math.random() > 0.5;
      executeTrade(currentAssetKey, isBuy ? 'BUY' : 'SELL', 0.25, 'Market Maker');
    }
  }

  // 4. DYNAMIC RISK MANAGER (CIRCUIT BREAKER)
  if (riskActive && crisisMode && frame % 60 === 0) {
    logConsole("CRISIS CIRCUIT BREAKER: Automated position hedge executed.", "ALERT");
    executeTrade(currentAssetKey, 'SELL', 2.0, 'Risk Manager');
  }
}

/* EXECUTE TRADE ENGINE */
function executeTrade(assetKey, type, qtyMultiplier, strategyName) {
  const asset = marketAssets[assetKey];
  const price = asset.price;
  const qty = parseFloat((qtyMultiplier * (assetKey.includes('BTC') ? 0.25 : 10)).toFixed(2));
  
  // Calculate simulated PnL profit
  const win = crisisMode ? (type === 'SELL') : (Math.random() < 0.68);
  const profit = win ? parseFloat((Math.random() * 450 + 50).toFixed(2)) : -parseFloat((Math.random() * 320 + 20).toFixed(2));

  // Update Portfolio
  portfolio.equity += profit;
  portfolio.pnlSession += profit;
  portfolio.totalTrades++;
  if (win) portfolio.winCount++;

  const timestamp = new Date().toLocaleTimeString();
  const tradeRecord = {
    time: timestamp,
    asset: assetKey,
    type: type,
    price: price.toFixed(2),
    qty: qty,
    strategy: strategyName,
    profit: profit
  };

  executedTrades.unshift(tradeRecord);
  if (executedTrades.length > 50) executedTrades.pop();

  // Attach execution marker to chart data
  if (type === 'BUY') {
    asset.buys.push({ x: asset.history.length - 1, price: price });
  } else {
    asset.sells.push({ x: asset.history.length - 1, price: price });
  }

  playTradeSound(type === 'BUY');
  logConsole(`EXECUTED ${type} ${qty} ${assetKey} @ $${price.toFixed(2)} [${strategyName}] (PnL: $${profit > 0 ? '+' : ''}${profit})`, "TRADE");

  renderTradesTable();
  updatePortfolioMetricsUI();
}

function emergencyLiquidate() {
  playAlertSound();
  logConsole("💥 EMERGENCY LIQUIDATION TRIGGERED BY USER. ALL OPEN ORDERS CANCELLED.", "ALERT");
  Object.keys(marketAssets).forEach(k => {
    executeTrade(k, 'SELL', 3.0, 'EMERGENCY LIQUIDATE');
  });
}

function updatePortfolioMetricsUI() {
  document.getElementById('metricEquity').innerText = `$${portfolio.equity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  
  const pnlElem = document.getElementById('metricPnL');
  pnlElem.innerText = `${portfolio.pnlSession >= 0 ? '+' : ''}$${portfolio.pnlSession.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  pnlElem.className = portfolio.pnlSession >= 0 ? 'text-base font-bold text-accentGreen' : 'text-base font-bold text-accentRed';

  const winRate = ((portfolio.winCount / Math.max(1, portfolio.totalTrades)) * 100).toFixed(1);
  document.getElementById('metricWinRate').innerText = `${winRate}%`;
  document.getElementById('metricTradesCount').innerText = portfolio.totalTrades;
}

function renderTradesTable() {
  const tbody = document.getElementById('tradesTableBody');
  if (!tbody) return;

  tbody.innerHTML = executedTrades.slice(0, 8).map(t => `
    <tr class="hover:bg-panelBorder/30 transition">
      <td class="p-1.5 text-gray-400">${t.time}</td>
      <td class="p-1.5 font-bold text-accentBlue">${t.asset}</td>
      <td class="p-1.5 font-bold ${t.type === 'BUY' ? 'text-accentGreen' : 'text-accentRed'}">${t.type}</td>
      <td class="p-1.5">$${t.price}</td>
      <td class="p-1.5">${t.qty}</td>
      <td class="p-1.5 text-gray-300">${t.strategy}</td>
      <td class="p-1.5 text-right font-bold ${t.profit >= 0 ? 'text-accentGreen' : 'text-accentRed'}">
        ${t.profit >= 0 ? '+' : ''}$${t.profit.toFixed(2)}
      </td>
    </tr>
  `).join('');
}

/* 2D TRADING FLOOR ANIMATED CANVAS ENGINE */
const floorCanvas = document.getElementById('tradingFloor');
const floorCtx = floorCanvas.getContext('2d');

class FloorAgent {
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
    this.currentThought = thoughts[0] || 'Analyzing...';
    this.currentTask = currentTask;
    this.state = 'DESK'; // DESK, WALKING_OUT, AT_DEST, WALKING_BACK
    this.timer = Math.floor(Math.random() * 120) + 60;
    this.targetX = deskX;
    this.targetY = deskY;
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
        else this.walkTo(350 + Math.random() * 40, 155, 'WHITEBOARD');
      }
    } else if (this.state === 'WALKING_OUT') {
      const dx = this.targetX - this.x, dy = this.targetY - this.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 4) {
        this.x = this.targetX; this.y = this.targetY;
        this.state = 'AT_DEST';
        this.timer = Math.floor(Math.random() * 140) + 80;
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
        this.state = 'DESK';
        this.timer = Math.floor(Math.random() * 180) + 100;
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
    if (this.thoughts.length > 0) {
      this.currentThought = this.thoughts[Math.floor(Math.random() * this.thoughts.length)];
    }
    logConsole(`${this.name} (${this.title}) dispatched to ${destName}.`, "INFO");
  }

  walkBackToDesk() {
    this.targetX = this.deskX;
    this.targetY = this.deskY;
    this.state = 'WALKING_BACK';
    logConsole(`${this.name} returning to workstation.`, "INFO");
  }

  draw(isSelected) {
    const isWalking = (this.state === 'WALKING_OUT' || this.state === 'WALKING_BACK');
    const bob = (this.state === 'DESK' && !isPaused) ? Math.sin(frame * 0.15) * 2 : 0;
    const typingHand = (this.state === 'DESK' && !isPaused) ? Math.sin(frame * 0.4) * 3 : 0;
    const legOffset = (isWalking && !isPaused) ? Math.sin(frame * 0.28) * 6 : 0;

    // Reticle highlight if selected
    if (isSelected) {
      floorCtx.strokeStyle = '#00f0ff';
      floorCtx.lineWidth = 2;
      floorCtx.beginPath();
      floorCtx.ellipse(this.x, this.y + 12, 18, 8, 0, 0, Math.PI * 2);
      floorCtx.stroke();
    }

    // Hair & Head
    floorCtx.fillStyle = this.hairColor;
    floorCtx.fillRect(this.x - 10, this.y - 42 + bob, 20, 14);
    floorCtx.fillStyle = '#f1c27d';
    floorCtx.fillRect(this.x - 8, this.y - 32 + bob, 16, 12);
    floorCtx.fillStyle = '#111';
    floorCtx.fillRect(this.x - 5, this.y - 28 + bob, 3, 3);
    floorCtx.fillRect(this.x + 2, this.y - 28 + bob, 3, 3);

    // Torso Shirt
    floorCtx.fillStyle = this.shirtColor;
    floorCtx.fillRect(this.x - 12, this.y - 20 + bob, 24, 18);
    floorCtx.fillStyle = '#ffffff';
    floorCtx.fillRect(this.x - 3, this.y - 20 + bob, 6, 8);

    // Typing Hands
    if (this.state === 'DESK') {
      floorCtx.fillStyle = '#f1c27d';
      floorCtx.fillRect(this.x - 14, this.y - 10 + typingHand, 5, 8);
      floorCtx.fillRect(this.x + 9, this.y - 10 - typingHand, 5, 8);
    }

    // Legs
    floorCtx.fillStyle = '#1e2530';
    if (isWalking) {
      floorCtx.fillRect(this.x - 9, this.y - 2, 7, 16 + legOffset);
      floorCtx.fillRect(this.x + 2, this.y - 2, 7, 16 - legOffset);
    } else {
      floorCtx.fillRect(this.x - 9, this.y - 2 + bob, 18, 16);
    }

    // Role Badge & Name Tag
    let actionTag = "DESK";
    if (this.state === 'AT_DEST') actionTag = this.destName;
    else if (isWalking) actionTag = "WALKING";

    const labelText = `${this.roleBadge} ${this.name} [${actionTag}]`;
    floorCtx.font = 'bold 11px monospace';
    const textWidth = floorCtx.measureText(labelText).width + 14;

    floorCtx.fillStyle = 'rgba(12, 16, 25, 0.95)';
    floorCtx.fillRect(this.x - textWidth / 2, this.y - 68 + bob, textWidth, 20);
    floorCtx.strokeStyle = isSelected ? '#00f0ff' : this.shirtColor;
    floorCtx.lineWidth = isSelected ? 2 : 1.5;
    floorCtx.strokeRect(this.x - textWidth / 2, this.y - 68 + bob, textWidth, 20);

    floorCtx.fillStyle = '#ffffff';
    floorCtx.textAlign = 'center';
    floorCtx.fillText(labelText, this.x, this.y - 54 + bob);

    // Thought Bubble
    if (Math.sin(frame * 0.04 + this.x) > 0.2) {
      const bubbleText = `"${this.currentThought}"`;
      floorCtx.font = '10px monospace';
      const bWidth = floorCtx.measureText(bubbleText).width + 16;
      const bX = this.x - bWidth / 2;
      const bY = this.y - 96 + bob;

      floorCtx.fillStyle = 'rgba(15, 20, 30, 0.95)';
      floorCtx.fillRect(bX, bY, bWidth, 20);
      floorCtx.strokeStyle = '#f1c40f';
      floorCtx.lineWidth = 1;
      floorCtx.strokeRect(bX, bY, bWidth, 20);

      floorCtx.fillStyle = '#f1c40f';
      floorCtx.textAlign = 'center';
      floorCtx.fillText(bubbleText, this.x, bY + 14);
    }
  }
}

// Staff Members List
const staffMembers = [
  new FloorAgent('ALEX', 'QUANT', 270, 280, '#2ecc71', '#f39c12', '📈', ['Checking RSI', 'Backtesting...', 'Alpha Found!'], 'Vol Arbitrage Pipeline'),
  new FloorAgent('MARCUS', 'CIO', 500, 280, '#3498db', '#e67e22', '🏛️', ['Rebalancing', 'Check Volatility', 'Macro Shift'], 'Portfolio Asset Allocation'),
  new FloorAgent('SARAH', 'RISK', 730, 280, '#e74c3c', '#9b59b6', '🛡️', ['VaR Safe', 'Check Exposure', 'Stress Test'], '95% VaR Margin Monitoring'),
  new FloorAgent('ELENA', 'DEV', 950, 280, '#9b59b6', '#34495e', '⚡', ['HFT Low Latency', 'Fixing API', 'Server Green'], 'Fixing WebSocket Feed')
];
let selectedAgentIndex = 0;

function drawFloorEnvironment() {
  // Tile floor grid
  for (let x = 0; x < floorCanvas.width; x += 40) {
    for (let y = 40; y < floorCanvas.height - 30; y += 40) {
      floorCtx.fillStyle = crisisMode
        ? ((x + y) % 80 === 0 ? '#2a0c10' : '#1d080b')
        : ((x + y) % 80 === 0 ? '#101420' : '#131826');
      floorCtx.fillRect(x, y, 40, 40);
      floorCtx.strokeStyle = crisisMode ? '#3d1217' : '#1a2133';
      floorCtx.lineWidth = 0.5;
      floorCtx.strokeRect(x, y, 40, 40);
    }
  }

  // Top Wall Header Banner
  floorCtx.fillStyle = '#141824';
  floorCtx.fillRect(0, 0, floorCanvas.width, 40);
  floorCtx.strokeStyle = '#283144';
  floorCtx.lineWidth = 1;
  floorCtx.beginPath(); floorCtx.moveTo(0, 40); floorCtx.lineTo(floorCanvas.width, 40); floorCtx.stroke();

  floorCtx.fillStyle = crisisMode ? '#ff4757' : '#2ecc71';
  floorCtx.font = 'bold 12px monospace'; floorCtx.textAlign = 'left';
  floorCtx.fillText(crisisMode ? "🚨 JC TRADING HOUSE - CRISIS ALERT ACTIVE" : "● JC TRADING HOUSE - MAIN TRADING FLOOR", 15, 25);

  // Bloomberg Terminal Wall Board (Center)
  floorCtx.fillStyle = '#090c12'; floorCtx.fillRect(480, 55, 240, 85);
  floorCtx.strokeStyle = '#3a4763'; floorCtx.lineWidth = 2; floorCtx.strokeRect(480, 55, 240, 85);
  floorCtx.fillStyle = '#f39c12'; floorCtx.font = 'bold 11px monospace'; floorCtx.textAlign = 'center';
  floorCtx.fillText("📺 BLOOMBERG TERMINAL FEED", 600, 70);

  floorCtx.strokeStyle = crisisMode ? '#ff4757' : '#00f0ff';
  floorCtx.lineWidth = 1.5; floorCtx.beginPath();
  for (let px = 0; px < 210; px += 5) {
    let py = 105 + Math.sin(((isPaused ? 0 : frame) * simSpeed + px) * 0.08) * (crisisMode ? 25 : 15);
    if (px === 0) floorCtx.moveTo(495 + px, py); else floorCtx.lineTo(495 + px, py);
  }
  floorCtx.stroke();

  // Strategy Board (Left)
  floorCtx.fillStyle = '#e8ecef'; floorCtx.fillRect(260, 55, 190, 85);
  floorCtx.strokeStyle = '#b0b7c0'; floorCtx.lineWidth = 3; floorCtx.strokeRect(260, 55, 190, 85);
  floorCtx.fillStyle = '#2c3e50'; floorCtx.font = 'bold 11px monospace'; floorCtx.textAlign = 'center';
  floorCtx.fillText("📋 STRATEGY SYNC", 355, 72);
  floorCtx.fillStyle = '#e74c3c'; floorCtx.font = '10px monospace'; floorCtx.fillText("VAR LIMIT: < 2.5%", 355, 88);
  floorCtx.fillStyle = '#27ae60'; floorCtx.fillText("MOMENTUM: BULL RUN", 355, 102);

  // Server Racks (Far Left)
  floorCtx.fillStyle = '#141824'; floorCtx.fillRect(20, 55, 150, 330);
  floorCtx.strokeStyle = '#2a3448'; floorCtx.lineWidth = 2; floorCtx.strokeRect(20, 55, 150, 330);
  floorCtx.fillStyle = '#00f0ff'; floorCtx.font = 'bold 11px monospace'; floorCtx.textAlign = 'center';
  floorCtx.fillText("🖥️ HIGH-SPEED SERVERS", 95, 75);

  for (let r = 0; r < 3; r++) {
    let ry = 90 + r * 95;
    floorCtx.fillStyle = '#0c0f17'; floorCtx.fillRect(32, ry, 126, 80);
    floorCtx.strokeStyle = '#323f57'; floorCtx.strokeRect(32, ry, 126, 80);
    for (let slot = 0; slot < 4; slot++) {
      floorCtx.fillStyle = '#182030'; floorCtx.fillRect(38, ry + 6 + slot * 17, 114, 12);
      let ledOn = (Math.sin(frame * 0.2 + r + slot) > 0);
      floorCtx.fillStyle = crisisMode ? '#ff4757' : (ledOn ? (slot % 2 === 0 ? '#2ecc71' : '#00f0ff') : '#444');
      floorCtx.fillRect(138, ry + 10 + slot * 17, 8, 4);
    }
  }

  // Barista Coffee Lounge (Far Right)
  floorCtx.fillStyle = '#141824'; floorCtx.fillRect(1030, 55, 150, 330);
  floorCtx.strokeStyle = '#2a3448'; floorCtx.lineWidth = 2; floorCtx.strokeRect(1030, 55, 150, 330);
  floorCtx.fillStyle = '#f39c12'; floorCtx.font = 'bold 11px monospace'; floorCtx.textAlign = 'center';
  floorCtx.fillText("☕ BARISTA LOUNGE", 1105, 75);

  floorCtx.fillStyle = '#2c3e50'; floorCtx.fillRect(1050, 110, 110, 65);
  floorCtx.fillStyle = '#e67e22'; floorCtx.fillRect(1065, 130, 25, 35);

  // Workstations for Agents
  staffMembers.forEach(ws => {
    floorCtx.fillStyle = '#1e2433'; floorCtx.fillRect(ws.deskX - 70, ws.deskY + 10, 140, 50);
    floorCtx.strokeStyle = '#35425e'; floorCtx.lineWidth = 1.5; floorCtx.strokeRect(ws.deskX - 70, ws.deskY + 10, 140, 50);

    floorCtx.fillStyle = '#0f131c'; floorCtx.fillRect(ws.deskX - 70, ws.deskY - 92, 140, 22);
    floorCtx.strokeStyle = ws.shirtColor; floorCtx.lineWidth = 1.5; floorCtx.strokeRect(ws.deskX - 70, ws.deskY - 92, 140, 22);
    floorCtx.fillStyle = '#ffffff'; floorCtx.font = 'bold 10px monospace'; floorCtx.textAlign = 'center';
    floorCtx.fillText(`${ws.title} (${ws.name})`, ws.deskX, ws.deskY - 77);

    floorCtx.fillStyle = '#080b12'; floorCtx.fillRect(ws.deskX - 30, ws.deskY - 60, 60, 42);
    floorCtx.strokeStyle = ws.shirtColor; floorCtx.lineWidth = 1.5; floorCtx.strokeRect(ws.deskX - 30, ws.deskY - 60, 60, 42);
  });
}

function updateAgentInspectorUI() {
  const agent = staffMembers[selectedAgentIndex];
  if (!agent) return;
  document.getElementById('inspName').innerText = agent.name;
  document.getElementById('inspRole').innerText = `${agent.title} ${agent.roleBadge}`;
  document.getElementById('inspState').innerText = agent.state;
  document.getElementById('inspTask').innerText = agent.currentTask;
  document.getElementById('inspThought').innerText = `"${agent.currentThought}"`;
}

// Floor Canvas Click Listener for Agent Selection
floorCanvas.addEventListener('click', (e) => {
  const rect = floorCanvas.getBoundingClientRect();
  const scaleX = floorCanvas.width / rect.width;
  const scaleY = floorCanvas.height / rect.height;
  const clickX = (e.clientX - rect.left) * scaleX;
  const clickY = (e.clientY - rect.top) * scaleY;

  staffMembers.forEach((s, idx) => {
    const dist = Math.sqrt((clickX - s.x) ** 2 + (clickY - s.y) ** 2);
    if (dist < 45) {
      selectedAgentIndex = idx;
      playSynthTone(523.25, 'sine', 0.08);
      logConsole(`Inspecting AI Agent: ${s.name} (${s.title})`, "INFO");
    }
  });
});

// Dispatch Actions
function dispatchAll(dest) {
  staffMembers.forEach(s => {
    if (dest === 'PANTRY') s.walkTo(1080 + Math.random() * 20, 260, 'PANTRY');
    else if (dest === 'SERVERS') s.walkTo(90 + Math.random() * 20, 260, 'SERVERS');
    else if (dest === 'WHITEBOARD') s.walkTo(330 + Math.random() * 40, 155, 'WHITEBOARD');
  });
}

function returnToDesks() {
  staffMembers.forEach(s => s.walkBackToDesk());
}

function dispatchSelectedAgent(dest) {
  const agent = staffMembers[selectedAgentIndex];
  if (!agent) return;
  if (dest === 'PANTRY') agent.walkTo(1080 + Math.random() * 20, 260, 'PANTRY');
  else if (dest === 'SERVERS') agent.walkTo(90 + Math.random() * 20, 260, 'SERVERS');
  else agent.walkBackToDesk();
}

/* INTERACTIVE MARKET PRICE CHART ENGINE */
const chartCanvas = document.getElementById('marketChart');
const chartCtx = chartCanvas.getContext('2d');

function renderMarketChart() {
  const width = chartCanvas.width;
  const height = chartCanvas.height;
  chartCtx.clearRect(0, 0, width, height);

  const asset = marketAssets[currentAssetKey];
  const history = asset.history;
  if (!history || history.length < 2) return;

  // Calculate scales
  const minP = Math.min(...history) * 0.998;
  const maxP = Math.max(...history) * 1.002;
  const rangeP = maxP - minP || 1;

  const getY = (price) => height - 25 - ((price - minP) / rangeP) * (height - 45);
  const getX = (idx) => (idx / (history.length - 1)) * (width - 60) + 10;

  // Background Grid Lines
  chartCtx.strokeStyle = '#182030';
  chartCtx.lineWidth = 1;
  for (let y = 30; y < height - 20; y += 40) {
    chartCtx.beginPath(); chartCtx.moveTo(0, y); chartCtx.lineTo(width - 50, y); chartCtx.stroke();
  }

  // Draw SMA 20 & SMA 50
  if (history.length >= 20) {
    chartCtx.strokeStyle = '#f1c40f'; // SMA 20 Gold
    chartCtx.lineWidth = 1.2;
    chartCtx.beginPath();
    for (let i = 19; i < history.length; i++) {
      const sma = calculateSMA(history.slice(0, i + 1), 20);
      if (i === 19) chartCtx.moveTo(getX(i), getY(sma));
      else chartCtx.lineTo(getX(i), getY(sma));
    }
    chartCtx.stroke();
  }

  if (history.length >= 50) {
    chartCtx.strokeStyle = '#9b59b6'; // SMA 50 Purple
    chartCtx.lineWidth = 1.2;
    chartCtx.beginPath();
    for (let i = 49; i < history.length; i++) {
      const sma = calculateSMA(history.slice(0, i + 1), 50);
      if (i === 49) chartCtx.moveTo(getX(i), getY(sma));
      else chartCtx.lineTo(getX(i), getY(sma));
    }
    chartCtx.stroke();
  }

  // Draw Price Line
  chartCtx.strokeStyle = '#00f0ff';
  chartCtx.lineWidth = 2;
  chartCtx.beginPath();
  for (let i = 0; i < history.length; i++) {
    if (i === 0) chartCtx.moveTo(getX(i), getY(history[i]));
    else chartCtx.lineTo(getX(i), getY(history[i]));
  }
  chartCtx.stroke();

  // Price Y-Axis Labels
  chartCtx.fillStyle = '#8a99ad';
  chartCtx.font = '10px monospace';
  chartCtx.textAlign = 'left';
  chartCtx.fillText(`$${maxP.toFixed(2)}`, width - 45, 35);
  chartCtx.fillText(`$${((maxP + minP) / 2).toFixed(2)}`, width - 45, height / 2);
  chartCtx.fillText(`$${minP.toFixed(2)}`, width - 45, height - 25);

  // Draw Trade Execution Markers
  asset.buys.forEach(b => {
    chartCtx.fillStyle = '#2ecc71';
    chartCtx.beginPath();
    chartCtx.arc(getX(b.x), getY(b.price), 5, 0, Math.PI * 2);
    chartCtx.fill();
  });

  asset.sells.forEach(s => {
    chartCtx.fillStyle = '#ff4757';
    chartCtx.beginPath();
    chartCtx.arc(getX(s.x), getY(s.price), 5, 0, Math.PI * 2);
    chartCtx.fill();
  });
}

/* ORDER BOOK DEPTH LADDER VISUALIZER */
function renderOrderBook() {
  const asset = marketAssets[currentAssetKey];
  const midPrice = asset.price;
  const spread = asset.spread;

  document.getElementById('obMidPrice').innerText = `$${midPrice.toFixed(2)}`;
  document.getElementById('obSpreadText').innerText = `SPREAD: $${spread.toFixed(2)}`;

  const asksContainer = document.getElementById('asksLadder');
  const bidsContainer = document.getElementById('bidsLadder');
  if (!asksContainer || !bidsContainer) return;

  let asksHTML = '';
  let bidsHTML = '';

  for (let i = 5; i >= 1; i--) {
    const p = midPrice + (spread / 2) + (i * 0.15);
    const sz = (Math.random() * 2.5 + 0.1).toFixed(2);
    const tot = (p * sz).toFixed(0);
    const depthPct = Math.min(100, sz * 30);
    asksHTML += `
      <div class="grid grid-cols-3 text-accentRed relative overflow-hidden py-0.5 px-1 rounded">
        <div class="absolute right-0 top-0 bottom-0 bg-accentRed/15" style="width: ${depthPct}%;"></div>
        <span class="z-10 font-bold">$${p.toFixed(2)}</span>
        <span class="z-10 text-right text-gray-200">${sz}</span>
        <span class="z-10 text-right text-gray-400">$${tot}</span>
      </div>`;
  }

  for (let i = 1; i <= 5; i++) {
    const p = midPrice - (spread / 2) - (i * 0.15);
    const sz = (Math.random() * 2.5 + 0.1).toFixed(2);
    const tot = (p * sz).toFixed(0);
    const depthPct = Math.min(100, sz * 30);
    bidsHTML += `
      <div class="grid grid-cols-3 text-accentGreen relative overflow-hidden py-0.5 px-1 rounded">
        <div class="absolute right-0 top-0 bottom-0 bg-accentGreen/15" style="width: ${depthPct}%;"></div>
        <span class="z-10 font-bold">$${p.toFixed(2)}</span>
        <span class="z-10 text-right text-gray-200">${sz}</span>
        <span class="z-10 text-right text-gray-400">$${tot}</span>
      </div>`;
  }

  asksContainer.innerHTML = asksHTML;
  bidsContainer.innerHTML = bidsHTML;
}

/* UI EVENT LISTENERS & MODAL CONTROLLERS */
function renderAssetSelectorButtons() {
  const group = document.getElementById('assetSelectorGroup');
  if (!group) return;

  group.innerHTML = Object.keys(marketAssets).map(k => `
    <button onclick="selectAsset('${k}')" class="px-2 py-1 rounded transition border ${k === currentAssetKey ? 'bg-accentBlue/20 text-accentBlue border-accentBlue font-bold' : 'bg-darkBg text-gray-400 border-panelBorder hover:text-gray-200'}">
      ${k}
    </button>
  `).join('');
}

function selectAsset(assetKey) {
  currentAssetKey = assetKey;
  renderAssetSelectorButtons();
  playSynthTone(600, 'sine', 0.05);
  logConsole(`Market Asset switched to ${assetKey}.`, "INFO");
}

function renderTickerBanner() {
  const ticker = document.getElementById('tickerContainer');
  if (!ticker) return;

  const items = Object.keys(marketAssets).map(k => {
    const a = marketAssets[k];
    const isUp = a.price >= a.basePrice;
    const pct = (((a.price - a.basePrice) / a.basePrice) * 100).toFixed(2);
    return `
      <div class="inline-flex items-center gap-2 px-3 border-r border-panelBorder/60 cursor-pointer" onclick="selectAsset('${k}')">
        <span class="font-bold text-accentBlue">${k}</span>
        <span class="text-gray-200">$${a.price.toFixed(2)}</span>
        <span class="${isUp ? 'text-accentGreen' : 'text-accentRed'} font-semibold">${isUp ? '▲ +' : '▼ '}${pct}%</span>
      </div>`;
  }).join('');

  ticker.innerHTML = items + items; // Duplicate for smooth continuous scrolling
}

// TOGGLE SIMULATION STATE
function togglePause() {
  isPaused = !isPaused;
  const btn = document.getElementById('pauseBtn');
  btn.innerText = isPaused ? "▶️ Resume" : "⏸️ Pause";
  logConsole(isPaused ? "Simulation Engine PAUSED." : "Simulation Engine RESUMED.", "INFO");
}

function toggleCrisisMode() {
  crisisMode = !crisisMode;
  const btn = document.getElementById('crisisBtn');
  const wrapper = document.getElementById('canvasWrapper');

  if (crisisMode) {
    btn.className = "bg-accentRed text-white px-2 py-1 rounded transition font-bold glow-red";
    wrapper.classList.add('crisis-pulse');
    playAlertSound();
    logConsole("🚨 CRISIS ALERT MODE ACTIVATED! HEAVY SELLING PRESSURE INDUCED.", "ALERT");
  } else {
    btn.className = "hover:bg-accentRed/30 text-accentRed border border-accentRed/40 px-2 py-1 rounded transition font-bold";
    wrapper.classList.remove('crisis-pulse');
    logConsole("✅ Crisis mode cleared. Normal market floor operations restored.", "INFO");
  }
}

function toggleSpeed() {
  simSpeed = simSpeed === 1 ? 2 : (simSpeed === 2 ? 4 : 1);
  document.getElementById('speedDisplay').innerText = `${simSpeed}x`;
  logConsole(`Simulation clock speed set to ${simSpeed}x.`, "INFO");
}

function toggleSound() {
  soundEnabled = !soundEnabled;
  document.getElementById('soundDisplay').innerText = soundEnabled ? 'ON' : 'OFF';
}

// MODAL HANDLERS
function openAddAgentModal() {
  document.getElementById('modalAddAgent').classList.remove('hidden');
}

function closeAddAgentModal() {
  document.getElementById('modalAddAgent').classList.add('hidden');
}

function submitAddAgent() {
  const name = document.getElementById('newAgentName').value.toUpperCase() || 'AGENT';
  const role = document.getElementById('newAgentRole').value || 'TRADER';
  const task = document.getElementById('newAgentTask').value || 'Executing strategy';

  const xPos = 250 + Math.random() * 600;
  const newStaff = new FloorAgent(name, role, xPos, 280, '#f1c40f', '#e74c3c', '💼', ['Scanning order books'], task);
  staffMembers.push(newStaff);
  selectedAgentIndex = staffMembers.length - 1;

  closeAddAgentModal();
  logConsole(`New AI Agent ${name} (${role}) added to floor.`, "INFO");
}

function openEditTaskModal() {
  const agent = staffMembers[selectedAgentIndex];
  if (!agent) return;
  document.getElementById('modalEditAgentName').innerText = agent.name;
  document.getElementById('modalEditTaskInput').value = agent.currentTask;
  document.getElementById('modalEditTask').classList.remove('hidden');
}

function closeEditTaskModal() {
  document.getElementById('modalEditTask').classList.add('hidden');
}

function submitEditTask() {
  const agent = staffMembers[selectedAgentIndex];
  if (!agent) return;
  const newTask = document.getElementById('modalEditTaskInput').value;
  if (newTask) {
    agent.currentTask = newTask;
    logConsole(`Updated task for ${agent.name}: "${newTask}"`, "INFO");
  }
  closeEditTaskModal();
}

/* MAIN 60FPS ENGINE ANIMATION LOOP */
function animateEngine() {
  try {
    frame++;

    // 1. Update Market Data & Runs Strategy
    if (frame % Math.max(1, Math.floor(15 / simSpeed)) === 0) {
      updateMarketData();
      renderTickerBanner();
    }

    runAIStrategyEngine();

    // 2. Render Floor Canvas & Update Agents
    floorCtx.clearRect(0, 0, floorCanvas.width, floorCanvas.height);
    drawFloorEnvironment();
    staffMembers.forEach((s, idx) => {
      s.update();
      s.draw(idx === selectedAgentIndex);
    });

    // 3. Render Chart & Order Book Depth
    if (frame % 5 === 0) {
      renderMarketChart();
      renderOrderBook();
      updateAgentInspectorUI();
    }

  } catch (e) {
    console.error("Engine Loop Exception:", e);
  }

  requestAnimationFrame(animateEngine);
}

// INITIALIZATION BOOTSTRAP
window.onload = () => {
  renderAssetSelectorButtons();
  renderTickerBanner();
  logConsole("JC Trading House & AI Strategy Engine Initialized.", "INFO");
  logConsole("System Online. All 4 AI Strategies operational.", "STRATEGY");
  
  // Start Main Loop
  requestAnimationFrame(animateEngine);
};
</script>
</body>
</html>