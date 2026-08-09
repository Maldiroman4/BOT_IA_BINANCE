import sys
import io
import os
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

# Forzar codificación UTF-8
sys.stdout.reconfigure(encoding='utf-8')

import time
import math
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
import ta
import config

BOT_VERSION = "v2.0 - Ultra-Trend 15m (Interés Compuesto Puro 100%)"

# Estado global, estadísticas y métricas avanzadas para el Dashboard Web
bot_status = {
    "version": "v2.0 - 15m",
    "balance": "Conectando...",
    "balance_inicial": 2.60,
    "estado": "Inicializando V2.0...",
    "activo_actual": "Ninguno",
    "posicion": "SIN POSICIÓN (Escaneando 15m)",
    "precio_entrada": "0.0000",
    "precio_actual": "0.0000",
    "direccion_flecha": "➡️",
    "stop_loss": "N/A",
    "take_profit": "N/A",
    "servidor": "Render Cloud EU",
    "wins": 0,
    "losses": 0,
    "pnl_total_usd": 0.0,
    "asset_counts": {"SOLUSDT": 0, "DOGEUSDT": 0, "XRPUSDT": 0, "ADAUSDT": 0},
    "trades": [],
    "logs": []
}

def registrar_log(mensaje):
    timestamp = time.strftime('%H:%M:%S')
    linea = f"[{timestamp}] {mensaje}"
    print(linea)
    bot_status["logs"].insert(0, (timestamp, mensaje))
    if len(bot_status["logs"]) > 50:
        bot_status["logs"].pop()

# Dashboard HTML Ultra-Pro V2.0 100% Adaptativo e Interés Compuesto
class DashboardWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        bg_images = [
            "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1920&q=80",
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80",
            "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1920&q=80",
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1920&q=80"
        ]
        
        logs_rendered = []
        for ts, msg in bot_status["logs"]:
            color = "#00f2fe"
            if "ENTRADA" in msg or "🚀" in msg or "NATIVA" in msg or "V2.0" in msg or "COMPUESTO" in msg:
                color = "#0ecb81"
            elif "CIERRE" in msg or "🏁" in msg:
                color = "#f0b90b"
            elif "STOP LOSS" in msg or "❌" in msg:
                color = "#f6465d"
            
            logs_rendered.append(f"""
            <div class="log-row">
                <span class="log-time">[{ts}]</span>
                <span class="log-msg" style="color: {color};">{msg}</span>
            </div>
            """)
        
        logs_html = "".join(logs_rendered) if logs_rendered else "<div class='log-row'><span class='log-msg'>Iniciando V2.0 15m Interés Compuesto...</span></div>"
        
        trades_rendered = []
        for t in bot_status["trades"]:
            badge_cls = "badge-green" if t["pnl_usd"] >= 0 else "badge-red"
            trades_rendered.append(f"""
            <tr>
                <td>{t["time"]}</td>
                <td><strong>{t["symbol"]}</strong></td>
                <td><span class="{badge_cls}">{t["side"]}</span></td>
                <td>${t["entry"]:.4f}</td>
                <td>${t["exit"]:.4f}</td>
                <td style="color: {'#0ecb81' if t['pnl_usd']>=0 else '#f6465d'}; font-weight: bold;">{t['pnl_usd']:+.4f} USDT</td>
                <td><small>{t["reason"]}</small></td>
            </tr>
            """)
        
        trades_html = "".join(trades_rendered) if trades_rendered else "<tr><td colspan='7' style='text-align: center; color: #848e9c; padding: 20px;'>No hay operaciones cerradas aún en V2.0 (15m). Buscando tendencias sólidas.</td></tr>"

        total_trades = bot_status["wins"] + bot_status["losses"]
        win_rate = (bot_status["wins"] / total_trades * 100) if total_trades > 0 else 0.0
        
        pos_str = bot_status["posicion"]
        pos_badge_color = "#848e9c"
        arrow_icon = "➡️"
        if "LONG" in pos_str:
            pos_badge_color = "#0ecb81"
            arrow_icon = "⬆️"
        elif "SHORT" in pos_str:
            pos_badge_color = "#f6465d"
            arrow_icon = "⬇️"
        elif "Escaneando" in pos_str:
            pos_badge_color = "#f0b90b"
            arrow_icon = "🔍"

        sol_c = bot_status["asset_counts"].get("SOLUSDT", 0)
        doge_c = bot_status["asset_counts"].get("DOGEUSDT", 0)
        xrp_c = bot_status["asset_counts"].get("XRPUSDT", 0)
        ada_c = bot_status["asset_counts"].get("ADAUSDT", 0)

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta http-equiv="refresh" content="5">
            <title>MARIO &amp; JOEL LIMPIAS BOT , MECHEROS like LUCAS - V2.0</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                :root {{
                    --panel-bg: rgba(15, 18, 26, 0.84);
                    --panel-border: rgba(255, 255, 255, 0.12);
                    --accent-gold: #f0b90b;
                    --accent-green: #0ecb81;
                    --accent-red: #f6465d;
                    --accent-cyan: #00f2fe;
                    --text-main: #ffffff;
                    --text-muted: #a0aec0;
                }}
                
                * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                    background-color: #05070a;
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                    color: var(--text-main);
                    min-height: 100vh;
                    padding: 16px 12px;
                    position: relative;
                    transition: background-image 1s ease-in-out;
                    -webkit-tap-highlight-color: transparent;
                }}

                body::before {{
                    content: '';
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(5, 7, 12, 0.78);
                    z-index: 0;
                    pointer-events: none;
                }}

                .dashboard {{
                    max-width: 1150px;
                    margin: 0 auto;
                    position: relative;
                    z-index: 1;
                }}

                .navbar {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: var(--panel-bg);
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border: 1px solid var(--panel-border);
                    border-radius: 16px;
                    padding: 16px 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6);
                    flex-wrap: wrap;
                    gap: 12px;
                }}

                .brand {{ display: flex; align-items: center; gap: 12px; flex: 1; min-width: 260px; }}

                .brand-icon {{
                    width: 42px; height: 42px;
                    background: linear-gradient(135deg, #f0b90b 0%, #ff8c00 100%);
                    border-radius: 12px;
                    display: flex; align-items: center; justify-content: center;
                    font-weight: 800; color: #000; font-size: 22px;
                    box-shadow: 0 0 20px rgba(240, 185, 11, 0.4);
                    flex-shrink: 0;
                }}

                .brand-text h1 {{
                    font-size: 18px; font-weight: 800; letter-spacing: -0.5px;
                    background: linear-gradient(90deg, #ffffff 0%, #f0b90b 100%);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    line-height: 1.25;
                }}

                .brand-text p {{
                    font-size: 10.5px; color: var(--text-muted); font-weight: 600;
                    letter-spacing: 0.5px; text-transform: uppercase; margin-top: 2px;
                }}

                .version-tag {{
                    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
                    color: #000; font-size: 10px; font-weight: 800;
                    padding: 3px 8px; border-radius: 6px; margin-left: 6px;
                    display: inline-block; letter-spacing: 0.5px; vertical-align: middle;
                }}

                .status-pill {{
                    display: flex; align-items: center; gap: 8px;
                    background: rgba(14, 203, 129, 0.15);
                    border: 1px solid rgba(14, 203, 129, 0.4);
                    color: var(--accent-green);
                    padding: 8px 14px; border-radius: 20px;
                    font-size: 11.5px; font-weight: 700;
                }}

                .pulse-dot {{
                    width: 8px; height: 8px;
                    background-color: var(--accent-green); border-radius: 50%;
                    box-shadow: 0 0 10px var(--accent-green);
                    animation: pulse 1.8s infinite ease-in-out;
                }}

                @keyframes pulse {{
                    0% {{ transform: scale(0.95); opacity: 0.8; }}
                    50% {{ transform: scale(1.3); opacity: 1; }}
                    100% {{ transform: scale(0.95); opacity: 0.8; }}
                }}

                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 12px; margin-bottom: 20px;
                }}

                .metric-card {{
                    background: var(--panel-bg);
                    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
                    border: 1px solid var(--panel-border);
                    border-radius: 14px; padding: 16px;
                    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
                    transition: transform 0.25s ease, box-shadow 0.25s ease;
                }}

                .metric-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.6);
                }}

                .metric-label {{
                    font-size: 10.5px; color: var(--text-muted); font-weight: 600;
                    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;
                }}

                .metric-val {{ font-size: 22px; font-weight: 800; letter-spacing: -0.5px; word-break: break-word; }}
                .metric-sub {{ font-size: 10px; color: var(--text-muted); margin-top: 4px; line-height: 1.3; }}

                .two-col {{
                    display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;
                }}

                .chart-card {{
                    background: var(--panel-bg); backdrop-filter: blur(20px);
                    border: 1px solid var(--panel-border); border-radius: 14px;
                    padding: 18px; box-shadow: 0 10px 35px rgba(0, 0, 0, 0.5);
                }}

                .chart-header {{
                    font-size: 12px; font-weight: 700; color: var(--text-muted);
                    margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;
                }}

                .progress-container {{
                    background: rgba(255, 255, 255, 0.08);
                    border-radius: 10px; height: 14px; overflow: hidden; margin: 10px 0;
                }}

                .progress-bar {{
                    background: linear-gradient(90deg, #0ecb81 0%, #00f2fe 100%);
                    height: 100%; border-radius: 10px; transition: width 0.5s ease;
                }}

                details {{
                    background: var(--panel-bg); backdrop-filter: blur(20px);
                    border: 1px solid var(--panel-border); border-radius: 14px;
                    margin-bottom: 20px; overflow: hidden; box-shadow: 0 10px 35px rgba(0, 0, 0, 0.5);
                }}

                summary {{
                    padding: 16px 20px; font-weight: 700; font-size: 13px;
                    cursor: pointer; color: var(--accent-gold);
                    display: flex; justify-content: space-between; align-items: center;
                    user-select: none; gap: 10px;
                }}

                summary:hover {{ background: rgba(255, 255, 255, 0.03); }}

                .table-wrapper {{
                    width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch;
                }}

                table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; white-space: nowrap; }}

                th, td {{
                    padding: 10px 14px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                }}

                th {{ background: rgba(0, 0, 0, 0.3); color: var(--text-muted); text-transform: uppercase; font-size: 10px; }}

                .badge-green {{ background: rgba(14, 203, 129, 0.2); color: #0ecb81; padding: 2px 7px; border-radius: 5px; font-weight: 700; font-size: 10.5px; }}
                .badge-red {{ background: rgba(246, 70, 93, 0.2); color: #f6465d; padding: 2px 7px; border-radius: 5px; font-weight: 700; font-size: 10.5px; }}

                .terminal-card {{
                    background: rgba(10, 13, 20, 0.92); backdrop-filter: blur(20px);
                    border: 1px solid var(--panel-border); border-radius: 14px; overflow: hidden;
                    box-shadow: 0 16px 50px rgba(0, 0, 0, 0.7);
                }}

                .terminal-header {{
                    background: rgba(22, 27, 38, 0.9); padding: 14px 18px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                    display: flex; justify-content: space-between; align-items: center;
                }}

                .terminal-title {{
                    font-size: 11px; font-weight: 700; color: var(--text-muted); letter-spacing: 0.5px; text-transform: uppercase;
                }}

                .terminal-dots {{ display: flex; gap: 5px; }}
                .dot {{ width: 9px; height: 9px; border-radius: 50%; }}
                .dot-red {{ background: #ff5f56; }}
                .dot-yellow {{ background: #ffbd2e; }}
                .dot-green {{ background: #27c93f; }}

                .terminal-body {{
                    font-family: 'JetBrains Mono', monospace; font-size: 11.5px;
                    padding: 16px; height: 280px; overflow-y: auto; line-height: 1.6;
                }}

                .log-row {{ display: flex; gap: 10px; padding: 4px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.03); }}
                .log-time {{ color: #6e7681; font-weight: 600; flex-shrink: 0; }}
                .log-msg {{ flex: 1; word-break: break-word; }}

                @media (max-width: 768px) {{
                    .two-col {{ grid-template-columns: 1fr; }}
                    .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }}
                }}

                @media (max-width: 480px) {{
                    body {{ padding: 12px 8px; }}
                    .navbar {{ padding: 14px; flex-direction: column; align-items: flex-start; }}
                    .status-pill {{ width: 100%; justify-content: center; margin-top: 4px; }}
                    .brand-text h1 {{ font-size: 15px; }}
                    .metric-val {{ font-size: 18px; }}
                    .metric-card {{ padding: 12px; }}
                    summary {{ padding: 14px; font-size: 12px; }}
                }}
            </style>
            <script>
                const bgImages = [
                    "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1920&q=80",
                    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80",
                    "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1920&q=80",
                    "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1920&q=80"
                ];
                let currentIdx = Math.floor(Math.random() * bgImages.length);
                document.addEventListener("DOMContentLoaded", () => {{
                    document.body.style.backgroundImage = `url('${{bgImages[currentIdx]}}')`;
                    setInterval(() => {{
                        currentIdx = (currentIdx + 1) % bgImages.length;
                        document.body.style.backgroundImage = `url('${{bgImages[currentIdx]}}')`;
                    }}, 5000);

                    const ctx = document.getElementById('assetChart').getContext('2d');
                    new Chart(ctx, {{
                        type: 'doughnut',
                        data: {{
                            labels: ['SOL/USDT', 'DOGE/USDT', 'XRP/USDT', 'ADA/USDT'],
                            datasets: [{{
                                data: [{sol_c}, {doge_c}, {xrp_c}, {ada_c}],
                                backgroundColor: ['#f0b90b', '#0ecb81', '#00f2fe', '#9b51e0'],
                                borderWidth: 0
                            }}]
                        }},
                        options: {{
                            responsive: true, maintainAspectRatio: false,
                            plugins: {{
                                legend: {{ position: 'bottom', labels: {{ color: '#eaecef', font: {{ family: 'Inter', size: 11 }} }} }}
                            }}
                        }}
                    }});
                }});
            </script>
        </head>
        <body>
            <div class="dashboard">
                <div class="navbar">
                    <div class="brand">
                        <div class="brand-icon">🔥</div>
                        <div class="brand-text">
                            <h1>MARIO &amp; JOEL LIMPIAS BOT , MECHEROS like LUCAS <span class="version-tag">V2.0 - 15M</span></h1>
                            <p>Binance USDT-M Futures • Interés Compuesto 100% Automático</p>
                        </div>
                    </div>
                    <div class="status-pill">
                        <div class="pulse-dot"></div>
                        <span>V2.0 COMPOUNDING ACTIVE</span>
                    </div>
                </div>

                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Account Balance</div>
                        <div class="metric-val" style="color: var(--accent-gold);">{bot_status["balance"]}</div>
                        <div class="metric-sub">Binance Live Wallet Sync</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">Engine Position Status</div>
                        <div class="metric-val" style="color: {pos_badge_color}; font-size: 16px; margin-top: 2px;">{arrow_icon} {bot_status["posicion"]}</div>
                        <div class="metric-sub">Strategy V2.0: 15m Trend Candles</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">Active Target Asset</div>
                        <div class="metric-val" style="color: var(--accent-cyan);">{bot_status["activo_actual"]}</div>
                        <div class="metric-sub">Timeframe: 15m Candles</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">Binance Native Orders</div>
                        <div class="metric-val" style="color: #ffffff; font-size: 14px; margin-top: 2px;">SL: {bot_status["stop_loss"]} | TP: {bot_status["take_profit"]}</div>
                        <div class="metric-sub">Exchange-Side Target Only • 5x Isolated</div>
                    </div>
                </div>

                <div class="two-col">
                    <div class="chart-card">
                        <div class="chart-header">📊 Rendimiento V2.0 (Win Rate &amp; PnL)</div>
                        <div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: bold; flex-wrap: wrap; gap: 6px;">
                            <span>Tasa Acierto: {win_rate:.1f}%</span>
                            <span style="color: {'#0ecb81' if bot_status['pnl_total_usd']>=0 else '#f6465d'};">PnL V2.0: {bot_status['pnl_total_usd']:+.4f} USDT</span>
                        </div>
                        <div class="progress-container">
                            <div class="progress-bar" style="width: {max(win_rate, 5)}%;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted);">
                            <span>🟢 Ganadas: {bot_status['wins']}</span>
                            <span>🔴 Perdedoras: {bot_status['losses']}</span>
                        </div>
                    </div>

                    <div class="chart-card">
                        <div class="chart-header">🍕 Distribución Criptomonedas V2.0</div>
                        <div style="height: 140px; position: relative;">
                            <canvas id="assetChart"></canvas>
                        </div>
                    </div>
                </div>

                <details open>
                    <summary>
                        <span>📜 HISTORIAL V2.0 DE OPERACIONES (15M)</span>
                        <span style="font-size: 11px; color: var(--text-muted);">▼ Desplegar/Contraer</span>
                    </summary>
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>Fecha / Hora</th>
                                    <th>Criptomoneda</th>
                                    <th>Tipo</th>
                                    <th>Entrada</th>
                                    <th>Salida</th>
                                    <th>Beneficio Neto</th>
                                    <th>Motivo Cierre</th>
                                </tr>
                            </thead>
                            <tbody>
                                {trades_html}
                            </tbody>
                        </table>
                    </div>
                </details>

                <div class="terminal-card">
                    <div class="terminal-header">
                        <div class="terminal-title">
                            <span>📟 EXECUTION LOG STREAM (V2.0 COMPOUNDING ACTIVE)</span>
                        </div>
                        <div class="terminal-dots">
                            <div class="dot dot-red"></div>
                            <div class="dot dot-yellow"></div>
                            <div class="dot dot-green"></div>
                        </div>
                    </div>
                    <div class="terminal-body">
                        {logs_html}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        return

def auto_keep_alive():
    time.sleep(10)
    app_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:10000")
    while True:
        try:
            req = urllib.request.Request(app_url, headers={'User-Agent': 'KeepAliveAutoPing/1.0'})
            urllib.request.urlopen(req, timeout=10)
            print("[KEEP-ALIVE] Auto-ping V2.0 enviado correctamente.")
        except Exception as e:
            pass
        time.sleep(240)

def iniciar_servidor_web():
    try:
        port = int(os.getenv("PORT", 10000))
        server = HTTPServer(('0.0.0.0', port), DashboardWebHandler)
        registrar_log(f"Servidor Web Pro activo en puerto {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Aviso servidor web: {e}")

threading.Thread(target=iniciar_servidor_web, daemon=True).start()
threading.Thread(target=auto_keep_alive, daemon=True).start()

class BotFuturosBinance:
    def __init__(self):
        registrar_log(f"=== Inicializando Bot de Trading Binance Futuros ({BOT_VERSION}) ===")
        
        self.paper = config.PAPER_TRADING
        self.margin = config.MARGIN_USD
        self.leverage = config.LEVERAGE
        self.current_symbol = None
        self.position = None        # None, 'LONG' o 'SHORT'
        self.entry_price = 0.0
        self.position_qty = 0.0
        self.qty_precisions = {}
        self.price_precisions = {}
        self.hedge_mode = False
        self.fee_rate = 0.0005 

        if not self.paper:
            servidor = "TESTNET" if config.USE_TESTNET else "CUENTA REAL BINANCE"
            registrar_log(f"Conectando a {servidor} con API Keys en MODO V2.0 INTERÉS COMPUESTO...")
            
            conectado = False
            while not conectado:
                try:
                    self.client = Client(
                        config.BINANCE_API_KEY, 
                        config.BINANCE_SECRET_KEY, 
                        testnet=config.USE_TESTNET
                    )
                    
                    self.sincronizar_saldo_binance()
                    
                    mode_info = self.client.futures_get_position_mode()
                    self.hedge_mode = mode_info.get('dualSidePosition', False)
                    modo_str = "Hedge Mode" if self.hedge_mode else "One-Way Mode"
                    registrar_log(f"Modo de Posición: {modo_str}")
                    
                    info = self.client.futures_exchange_info()
                    for s in info['symbols']:
                        if s['symbol'] in config.ASSET_POOL:
                            self.qty_precisions[s['symbol']] = s['quantityPrecision']
                            self.price_precisions[s['symbol']] = s['pricePrecision']
                    
                    self.restaurar_posiciones_activas()
                    conectado = True
                    
                except BinanceAPIException as e:
                    bot_status["estado"] = f"Error Binance: {e.code}"
                    registrar_log(f"❌ Error Binance ({e.code}): {e.message}")
                    if "restricted location" in str(e.message).lower():
                        registrar_log("👉 AVISO: Cambia la región de Render a Frankfurt (Germany) o Singapore para evitar bloqueo IP EE.UU.")
                    time.sleep(30)
                except Exception as e:
                    registrar_log(f"❌ Error conexión: {e}. Reintentando...")
                    time.sleep(30)
        else:
            bot_status["balance"] = f"{self.margin:.2f} USDT (Virtual)"
            bot_status["estado"] = "Paper Trading V2.0"
            registrar_log("Estado: MODO SIMULACIÓN (Paper Trading V2.0)")
            self.qty_precisions = {'SOLUSDT': 2, 'XRPUSDT': 1, 'DOGEUSDT': 0, 'ADAUSDT': 0}
            self.price_precisions = {'SOLUSDT': 2, 'XRPUSDT': 4, 'DOGEUSDT': 5, 'ADAUSDT': 4}

    def sincronizar_saldo_binance(self):
        """Sincroniza el saldo real de Binance y calcula el Interés Compuesto Puro 100% de la billetera."""
        if self.paper:
            return
        try:
            balances = self.client.futures_account_balance()
            usdt_bal = next((float(b['balance']) for b in balances if b['asset'] == 'USDT'), 0.0)
            
            # INTERÉS COMPUESTO PURO: Usa el 100% del saldo real disponible en la billetera
            if usdt_bal > 0:
                self.margin = usdt_bal
            else:
                self.margin = config.MARGIN_USD

            bot_status["balance"] = f"{usdt_bal:.2f} USDT"
            registrar_log(f"✅ Interés Compuesto Activo: Saldo Real Billetera = {usdt_bal:.2f} USDT (Margen Entrada 100%)")
        except Exception as e:
            registrar_log(f"Error sincronizando saldo: {e}")

    def restaurar_posiciones_activas(self):
        if self.paper:
            return
        try:
            positions = self.client.futures_position_information()
            for p in positions:
                amt = float(p['positionAmt'])
                if p['symbol'] in config.ASSET_POOL and amt != 0:
                    self.current_symbol = p['symbol']
                    self.position_qty = abs(amt)
                    self.entry_price = float(p['entryPrice'])
                    self.position = 'LONG' if amt > 0 else 'SHORT'
                    
                    sl_price, tp_price = self.calcular_precios_sl_tp(self.current_symbol, self.position, self.entry_price)
                    bot_status["activo_actual"] = self.current_symbol
                    bot_status["posicion"] = f"POSICIÓN {self.position} @ ${self.entry_price:.4f}"
                    bot_status["precio_entrada"] = f"{self.entry_price:.4f}"
                    bot_status["stop_loss"] = f"${sl_price:.4f}"
                    bot_status["take_profit"] = f"${tp_price:.4f}"
                    registrar_log(f"🔄 POSICIÓN RECUPERADA EN REINICIO (V2.0 15M): {self.position} {self.current_symbol} @ ${self.entry_price:.4f}")
                    return
            bot_status["stop_loss"] = "N/A"
            bot_status["take_profit"] = "N/A"
            registrar_log("Sin posiciones previas abiertas en Binance.")
        except Exception as e:
            registrar_log(f"Error al verificar posiciones en Binance: {e}")

    def ajustar_precision_cantidad(self, symbol, qty):
        precision = self.qty_precisions.get(symbol, 2)
        if precision == 0:
            return math.floor(qty)
        factor = 10 ** precision
        return math.floor(qty * factor) / factor

    def ajustar_precision_precio(self, symbol, price):
        precision = self.price_precisions.get(symbol, 4)
        return round(price, precision)

    def calcular_precios_sl_tp(self, symbol, side, entry):
        if side == 'LONG':
            sl = entry * (1.0 - config.STOP_LOSS_PCT)
            tp = entry * (1.0 + config.TAKE_PROFIT_PCT)
        else: # SHORT
            sl = entry * (1.0 + config.STOP_LOSS_PCT)
            tp = entry * (1.0 - config.TAKE_PROFIT_PCT)
        
        sl_rounded = self.ajustar_precision_precio(symbol, sl)
        tp_rounded = self.ajustar_precision_precio(symbol, tp)
        return sl_rounded, tp_rounded

    def _configurar_cuenta_binance(self, symbol):
        if self.paper:
            return True
        try:
            self.client.futures_change_margin_type(symbol=symbol, marginType=config.MARGIN_TYPE)
        except Exception:
            pass
        try:
            self.client.futures_change_leverage(symbol=symbol, leverage=self.leverage)
            return True
        except Exception as e:
            registrar_log(f"Aviso apalancamiento: {e}")
            return False

    def obtener_datos(self, symbol):
        klines = self.client.futures_klines(symbol=symbol, interval=config.TIMEFRAME, limit=100)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'tb_base_vol', 'tb_quote_vol', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['ema_fast'] = ta.trend.ema_indicator(df['close'], window=config.EMA_FAST)
        df['ema_slow'] = ta.trend.ema_indicator(df['close'], window=config.EMA_SLOW)
        df['rsi'] = ta.momentum.rsi(df['close'], window=config.RSI_PERIOD)
        return df

    def evaluar_senales(self, df):
        last = df.iloc[-1]
        prev = df.iloc[-2]
        ema_diff = last['ema_fast'] - last['ema_slow']

        long_sig = (prev['ema_fast'] <= prev['ema_slow']) and (last['ema_fast'] > last['ema_slow']) and (last['rsi'] < 60)
        short_sig = (prev['ema_fast'] >= prev['ema_slow']) and (last['ema_fast'] < last['ema_slow']) and (last['rsi'] > 40)

        return long_sig, short_sig, last['close'], last['rsi'], ema_diff

    def escanear_mercado(self):
        mejor_activo = None
        mejor_direccion = None
        mejor_precio = 0.0
        max_fuerza = -1.0

        for symbol in config.ASSET_POOL:
            try:
                df = self.obtener_datos(symbol)
                long_sig, short_sig, price, rsi, ema_diff = self.evaluar_senales(df)
                fuerza = abs(ema_diff)

                if long_sig and fuerza > max_fuerza:
                    max_fuerza = fuerza
                    mejor_activo = symbol
                    mejor_direccion = 'LONG'
                    mejor_precio = price
                elif short_sig and fuerza > max_fuerza:
                    max_fuerza = fuerza
                    mejor_activo = symbol
                    mejor_direccion = 'SHORT'
                    mejor_precio = price
            except Exception as e:
                registrar_log(f"Error escaneando {symbol}: {e}")

        return mejor_activo, mejor_direccion, mejor_precio

    def abrir_posicion(self, symbol, side, price):
        # 1. Recalcular Saldo Actual para Interés Compuesto Puro
        self.sincronizar_saldo_binance()
        
        valor_nocional = self.margin * self.leverage
        qty_bruta = valor_nocional / price
        qty = self.ajustar_precision_cantidad(symbol, qty_bruta)

        if qty <= 0:
            registrar_log(f"⚠️ Cantidad calculada demasiado pequeña para {symbol}")
            return

        sl_price, tp_price = self.calcular_precios_sl_tp(symbol, side, price)
        
        if not self.paper:
            config_ok = self._configurar_cuenta_binance(symbol)
            try:
                order_params = {
                    'symbol': symbol,
                    'side': 'BUY' if side == 'LONG' else 'SELL',
                    'type': 'MARKET',
                    'quantity': qty
                }
                if self.hedge_mode:
                    order_params['positionSide'] = side

                self.client.futures_create_order(**order_params)
                registrar_log(f"🚀 [INTERÉS COMPUESTO] ENTRADA MARKET {side} {symbol} @ ${price:.4f} (Nocional: ${valor_nocional:.2f} USDT)")

                side_opuesto = 'SELL' if side == 'LONG' else 'BUY'
                
                sl_params = {
                    'symbol': symbol,
                    'side': side_opuesto,
                    'type': 'STOP_MARKET',
                    'stopPrice': sl_price,
                    'closePosition': True
                }
                if self.hedge_mode:
                    sl_params['positionSide'] = side

                self.client.futures_create_order(**sl_params)
                registrar_log(f"🛡️ [V2.0] STOP LOSS NATIVO EN BINANCE: ${sl_price:.4f} (-1.2%)")

                tp_params = {
                    'symbol': symbol,
                    'side': side_opuesto,
                    'type': 'TAKE_PROFIT_MARKET',
                    'stopPrice': tp_price,
                    'closePosition': True
                }
                if self.hedge_mode:
                    tp_params['positionSide'] = side

                self.client.futures_create_order(**tp_params)
                registrar_log(f"🎯 [V2.0] TAKE PROFIT NATIVO EN BINANCE: ${tp_price:.4f} (+2.5%)")

            except Exception as e:
                registrar_log(f"❌ Error al colocar órdenes V2.0 en Binance: {e}")
                try:
                    self.client.futures_cancel_all_open_orders(symbol=symbol)
                except Exception:
                    pass
                return

        self.current_symbol = symbol
        self.position_qty = qty
        self.entry_price = price
        self.position = side
        
        comision_entrada = valor_nocional * self.fee_rate
        self.margin -= comision_entrada

        flecha = "⬆️" if side == 'LONG' else "⬇️"
        bot_status["activo_actual"] = symbol
        bot_status["posicion"] = f"{flecha} POSICIÓN {side} @ ${price:.4f}"
        bot_status["precio_entrada"] = f"{price:.4f}"
        bot_status["stop_loss"] = f"${sl_price:.4f}"
        bot_status["take_profit"] = f"${tp_price:.4f}"

        registrar_log(f"POSICIÓN V2.0 {side} ACTIVA: {symbol} | Qty: {qty} | SL: ${sl_price:.4f} | TP: ${tp_price:.4f}")

    def cerrar_posicion(self, price, motivo="SEÑAL"):
        if not self.position:
            return

        if not self.paper:
            try:
                self.client.futures_cancel_all_open_orders(symbol=self.current_symbol)
                registrar_log("🧹 Órdenes nativas pendientes canceladas en Binance.")
                
                order_params = {
                    'symbol': self.current_symbol,
                    'side': 'SELL' if self.position == 'LONG' else 'BUY',
                    'type': 'MARKET',
                    'quantity': self.position_qty
                }
                
                if self.hedge_mode:
                    order_params['positionSide'] = self.position
                else:
                    order_params['reduceOnly'] = True

                self.client.futures_create_order(**order_params)
                registrar_log(f"🏁 Cierre ejecutado en Binance por {motivo}")
            except Exception as e:
                registrar_log(f"Aviso/Ejecución de cierre Binance: {e}")

        valor_nocional_salida = self.position_qty * price
        comision_salida = valor_nocional_salida * self.fee_rate

        if self.position == 'LONG':
            ganancia_bruta = (price - self.entry_price) * self.position_qty
        else: # SHORT
            ganancia_bruta = (self.entry_price - price) * self.position_qty

        ganancia_neta = ganancia_bruta - comision_salida
        self.margin += (self.entry_price * self.position_qty / self.leverage) + ganancia_neta

        trade_record = {
            "time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "symbol": self.current_symbol,
            "side": self.position,
            "entry": self.entry_price,
            "exit": price,
            "pnl_usd": ganancia_neta,
            "reason": motivo
        }
        bot_status["trades"].insert(0, trade_record)
        bot_status["asset_counts"][self.current_symbol] = bot_status["asset_counts"].get(self.current_symbol, 0) + 1
        bot_status["pnl_total_usd"] += ganancia_neta
        if ganancia_neta >= 0:
            bot_status["wins"] += 1
        else:
            bot_status["losses"] += 1

        self.sincronizar_saldo_binance()
        bot_status["posicion"] = "🔍 SIN POSICIÓN (Escaneando 15m)"
        bot_status["activo_actual"] = "Ninguno"
        bot_status["stop_loss"] = "N/A"
        bot_status["take_profit"] = "N/A"

        registrar_log(f"CIERRE V2.0 ({motivo}): {self.current_symbol} | Precio: ${price:.4f} | Resultado Neto: {ganancia_neta:+.4f} USDT | Nuevo Saldo: {bot_status['balance']}")

        self.position = None
        self.current_symbol = None
        self.entry_price = 0.0
        self.position_qty = 0.0

    def ejecutar(self):
        registrar_log(f"🚀 MODO V2.0 ACTIVADO: Escaneando tendencias limpias en 15m con Interés Compuesto Puro...")
        while True:
            try:
                if not self.paper:
                    positions = self.client.futures_position_information()
                    pos_activa = False
                    for p in positions:
                        amt = float(p['positionAmt'])
                        if p['symbol'] in config.ASSET_POOL and amt != 0:
                            pos_activa = True
                            break
                    
                    if not pos_activa and self.position is not None:
                        df = self.obtener_datos(self.current_symbol)
                        precio_actual = df.iloc[-1]['close']
                        registrar_log("⚡ Binance ejecutó la Orden Nativa (Stop Loss o Take Profit) en su servidor.")
                        self.cerrar_posicion(precio_actual, "ORDEN NATIVA BINANCE EJECUTADA")

                if self.position is None:
                    activo, direccion, precio = self.escanear_mercado()
                    if activo:
                        self.abrir_posicion(activo, direccion, price=precio)
                    else:
                        bot_status["posicion"] = "🔍 SIN POSICIÓN (Escaneando 15m)"
                        bot_status["activo_actual"] = f"Escaneando 4 activos en 15m"
                        if len(bot_status["logs"]) == 0 or "Escaneando" not in bot_status["logs"][0][1]:
                            registrar_log(f"Escaneando {config.ASSET_POOL} en velas de 15m... Buscando tendencia sólida...")

                else:
                    df = self.obtener_datos(self.current_symbol)
                    precio_actual = df.iloc[-1]['close']
                    flecha = "⬆️" if self.position == 'LONG' else "⬇️"
                    bot_status["posicion"] = f"{flecha} POSICIÓN {self.position} ({self.current_symbol})"
                    bot_status["activo_actual"] = f"${precio_actual:.4f} (Entrada: ${self.entry_price:.4f})"

                time.sleep(10)
            except Exception as e:
                registrar_log(f"Error en bucle principal V2.0: {e}")
                time.sleep(10)

if __name__ == "__main__":
    bot = BotFuturosBinance()
    bot.ejecutar()
