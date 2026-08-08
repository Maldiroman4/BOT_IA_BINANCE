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

# Estado global, estadísticas y métricas avanzadas para el Dashboard Web
bot_status = {
    "balance": "Conectando...",
    "balance_inicial": 2.60,
    "estado": "Inicializando...",
    "activo_actual": "Ninguno",
    "posicion": "SIN POSICIÓN (Escaneando)",
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

# Dashboard HTML Ultra-Pro con Gráficos Interactivos, Pie Chart y Flechas de Tendencia
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
            if "ENTRADA" in msg or "🚀" in msg or "NATIVA" in msg:
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
        
        logs_html = "".join(logs_rendered) if logs_rendered else "<div class='log-row'><span class='log-msg'>Iniciando sistema de escaneo...</span></div>"
        
        # Generar Filas del Historial de Operaciones
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
        
        trades_html = "".join(trades_rendered) if trades_rendered else "<tr><td colspan='7' style='text-align: center; color: #848e9c; padding: 20px;'>No hay operaciones cerradas aún. El bot está escaneando las mejores oportunidades.</td></tr>"

        # Cálculos de Métricas de Ganancia / Pérdida
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

        # Datos para el gráfico de torta (Pie Chart)
        sol_c = bot_status["asset_counts"].get("SOLUSDT", 0)
        doge_c = bot_status["asset_counts"].get("DOGEUSDT", 0)
        xrp_c = bot_status["asset_counts"].get("XRPUSDT", 0)
        ada_c = bot_status["asset_counts"].get("ADAUSDT", 0)

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <meta http-equiv="refresh" content="5">
            <title>MARIO &amp; JOEL LIMPIAS BOT , MECHEROS like LUCAS</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                :root {{
                    --panel-bg: rgba(15, 18, 26, 0.82);
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
                    padding: 24px 16px;
                    position: relative;
                    transition: background-image 1s ease-in-out;
                }}

                body::before {{
                    content: '';
                    position: fixed;
                    top: 0; left: 0; right: 0; bottom: 0;
                    background: rgba(5, 7, 12, 0.75);
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
                    padding: 18px 24px;
                    margin-bottom: 24px;
                    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6);
                }}

                .brand {{ display: flex; align-items: center; gap: 14px; }}

                .brand-icon {{
                    width: 44px; height: 44px;
                    background: linear-gradient(135deg, #f0b90b 0%, #ff8c00 100%);
                    border-radius: 12px;
                    display: flex; align-items: center; justify-content: center;
                    font-weight: 800; color: #000; font-size: 24px;
                    box-shadow: 0 0 20px rgba(240, 185, 11, 0.4);
                }}

                .brand-text h1 {{
                    font-size: 20px; font-weight: 800; letter-spacing: -0.5px;
                    background: linear-gradient(90deg, #ffffff 0%, #f0b90b 100%);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                }}

                .brand-text p {{
                    font-size: 11px; color: var(--text-muted); font-weight: 600;
                    letter-spacing: 0.5px; text-transform: uppercase;
                }}

                .status-pill {{
                    display: flex; align-items: center; gap: 8px;
                    background: rgba(14, 203, 129, 0.15);
                    border: 1px solid rgba(14, 203, 129, 0.4);
                    color: var(--accent-green);
                    padding: 8px 16px; border-radius: 20px;
                    font-size: 12px; font-weight: 700;
                }}

                .pulse-dot {{
                    width: 9px; height: 9px;
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
                    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                    gap: 16px; margin-bottom: 24px;
                }}

                .metric-card {{
                    background: var(--panel-bg);
                    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
                    border: 1px solid var(--panel-border);
                    border-radius: 16px; padding: 22px;
                    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
                    transition: transform 0.25s ease, box-shadow 0.25s ease;
                }}

                .metric-card:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 14px 35px rgba(0, 0, 0, 0.6);
                }}

                .metric-label {{
                    font-size: 12px; color: var(--text-muted); font-weight: 600;
                    text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;
                }}

                .metric-val {{ font-size: 26px; font-weight: 800; letter-spacing: -0.5px; }}
                .metric-sub {{ font-size: 11px; color: var(--text-muted); margin-top: 6px; }}

                /* Layout de 2 Columnas para Gráficos y Métricas */
                .two-col {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 24px;
                }}

                @media (max-width: 850px) {{
                    .two-col {{ grid-template-columns: 1fr; }}
                }}

                .chart-card {{
                    background: var(--panel-bg);
                    backdrop-filter: blur(20px);
                    border: 1px solid var(--panel-border);
                    border-radius: 16px;
                    padding: 20px;
                    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.5);
                }}

                .chart-header {{
                    font-size: 13px; font-weight: 700; color: var(--text-muted);
                    margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.5px;
                }}

                /* Barra de Progreso Win Rate */
                .progress-container {{
                    background: rgba(255, 255, 255, 0.08);
                    border-radius: 10px; height: 16px; overflow: hidden; margin: 12px 0;
                }}

                .progress-bar {{
                    background: linear-gradient(90deg, #0ecb81 0%, #00f2fe 100%);
                    height: 100%; border-radius: 10px; transition: width 0.5s ease;
                }}

                /* Acordeón Desplegable para Historial */
                details {{
                    background: var(--panel-bg);
                    backdrop-filter: blur(20px);
                    border: 1px solid var(--panel-border);
                    border-radius: 16px;
                    margin-bottom: 24px; overflow: hidden;
                    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.5);
                }}

                summary {{
                    padding: 18px 24px; font-weight: 700; font-size: 14px;
                    cursor: pointer; color: var(--accent-gold);
                    display: flex; justify-content: space-between; align-items: center;
                    user-select: none;
                }}

                summary:hover {{ background: rgba(255, 255, 255, 0.03); }}

                table {{
                    width: 100%; border-collapse: collapse; font-size: 12.5px;
                }}

                th, td {{
                    padding: 12px 16px; text-align: left; border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                }}

                th {{ background: rgba(0, 0, 0, 0.3); color: var(--text-muted); text-transform: uppercase; font-size: 11px; }}

                .badge-green {{ background: rgba(14, 203, 129, 0.2); color: #0ecb81; padding: 3px 8px; border-radius: 6px; font-weight: 700; }}
                .badge-red {{ background: rgba(246, 70, 93, 0.2); color: #f6465d; padding: 3px 8px; border-radius: 6px; font-weight: 700; }}

                .terminal-card {{
                    background: rgba(10, 13, 20, 0.92);
                    backdrop-filter: blur(20px);
                    border: 1px solid var(--panel-border);
                    border-radius: 16px; overflow: hidden;
                    box-shadow: 0 16px 50px rgba(0, 0, 0, 0.7);
                }}

                .terminal-header {{
                    background: rgba(22, 27, 38, 0.9); padding: 16px 22px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                    display: flex; justify-content: space-between; align-items: center;
                }}

                .terminal-title {{
                    font-size: 12px; font-weight: 700; color: var(--text-muted);
                    letter-spacing: 1px; text-transform: uppercase;
                }}

                .terminal-body {{
                    font-family: 'JetBrains Mono', monospace; font-size: 13px;
                    padding: 20px; height: 350px; overflow-y: auto; line-height: 1.65;
                }}

                .log-row {{ display: flex; gap: 14px; padding: 5px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.03); }}
                .log-time {{ color: #6e7681; font-weight: 600; }}
                .log-msg {{ flex: 1; word-break: break-word; }}
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

                    // Inicializar Gráfico de Torta (Pie Chart de Activos Usados)
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
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{
                                legend: {{ position: 'bottom', labels: {{ color: '#eaecef', font: {{ family: 'Inter' }} }} }}
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
                            <h1>MARIO &amp; JOEL LIMPIAS BOT , MECHEROS like LUCAS</h1>
                            <p>Binance USDT-M Futures • Exchange-Side Native Protection</p>
                        </div>
                    </div>
                    <div class="status-pill">
                        <div class="pulse-dot"></div>
                        <span>BINANCE NATIVE PROTECTED 24/7</span>
                    </div>
                </div>

                <!-- Métricas Principales -->
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Account Balance</div>
                        <div class="metric-val" style="color: var(--accent-gold);">{bot_status["balance"]}</div>
                        <div class="metric-sub">Binance Live Wallet Sync</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">Engine Position Status</div>
                        <div class="metric-val" style="color: {pos_badge_color}; font-size: 19px; margin-top: 4px;">{arrow_icon} {bot_status["posicion"]}</div>
                        <div class="metric-sub">Strategy: EMA 9/21 + RSI 14</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">Active Target Asset</div>
                        <div class="metric-val" style="color: var(--accent-cyan);">{bot_status["activo_actual"]}</div>
                        <div class="metric-sub">Timeframe: 5m Candles</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">Binance Native Orders</div>
                        <div class="metric-val" style="color: #ffffff; font-size: 16px; margin-top: 4px;">SL: {bot_status["stop_loss"]} | TP: {bot_status["take_profit"]}</div>
                        <div class="metric-sub">Exchange-Side STOP/TP • 5x Isolated</div>
                    </div>
                </div>

                <!-- Segunda Sección: Rendimiento y Gráfico de Torta -->
                <div class="two-col">
                    <!-- Rendimiento de Ganancias/Pérdidas -->
                    <div class="chart-card">
                        <div class="chart-header">📊 Rendimiento de Operaciones (Win Rate &amp; PnL)</div>
                        <div style="display: flex; justify-content: space-between; font-size: 14px; font-weight: bold;">
                            <span>Tasa de Acierto: {win_rate:.1f}%</span>
                            <span style="color: {'#0ecb81' if bot_status['pnl_total_usd']>=0 else '#f6465d'};">PnL Acumulado: {bot_status['pnl_total_usd']:+.4f} USDT</span>
                        </div>
                        <div class="progress-container">
                            <div class="progress-bar" style="width: {max(win_rate, 5)}%;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted);">
                            <span>🟢 Operaciones Ganadas: {bot_status['wins']}</span>
                            <span>🔴 Operaciones Perdedoras: {bot_status['losses']}</span>
                        </div>
                    </div>

                    <!-- Gráfico de Torta de Activos Usados -->
                    <div class="chart-card">
                        <div class="chart-header">🍕 Distribución de Criptomonedas Operadas</div>
                        <div style="height: 140px; position: relative;">
                            <canvas id="assetChart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Historial Desplegable de Operaciones -->
                <details open>
                    <summary>
                        <span>📜 HISTORIAL DE OPERACIONES REALIZADAS</span>
                        <span style="font-size: 12px; color: var(--text-muted);">▼ Haz clic para contraer/desplegar</span>
                    </summary>
                    <div style="overflow-x: auto;">
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

                <!-- Consola Terminal en Vivo -->
                <div class="terminal-card">
                    <div class="terminal-header">
                        <div class="terminal-title">
                            <span>📟 REAL-TIME EXECUTION LOG STREAM</span>
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
            print("[KEEP-ALIVE] Auto-ping enviado correctamente.")
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
        registrar_log("=== Inicializando Bot de Trading Binance Futuros ===")
        
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
            registrar_log(f"Conectando a {servidor} con API Keys...")
            
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
            bot_status["estado"] = "Paper Trading"
            registrar_log("Estado: MODO SIMULACIÓN (Paper Trading)")
            self.qty_precisions = {'SOLUSDT': 2, 'XRPUSDT': 1, 'DOGEUSDT': 0, 'ADAUSDT': 0}
            self.price_precisions = {'SOLUSDT': 2, 'XRPUSDT': 4, 'DOGEUSDT': 5, 'ADAUSDT': 4}

    def sincronizar_saldo_binance(self):
        if self.paper:
            return
        try:
            balances = self.client.futures_account_balance()
            usdt_bal = next((float(b['balance']) for b in balances if b['asset'] == 'USDT'), 0.0)
            self.margin = min(usdt_bal, 10.0)
            if self.margin <= 0:
                self.margin = config.MARGIN_USD
            bot_status["balance"] = f"{usdt_bal:.2f} USDT"
            registrar_log(f"✅ Sincronización Binance: Saldo Real Billetera = {usdt_bal:.2f} USDT")
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
                    registrar_log(f"🔄 POSICIÓN RECUPERADA EN REINICIO: {self.position} {self.current_symbol} @ ${self.entry_price:.4f}")
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

        long_sig = (prev['ema_fast'] <= prev['ema_slow']) and (last['ema_fast'] > last['ema_slow']) and (last['rsi'] < 65)
        short_sig = (prev['ema_fast'] >= prev['ema_slow']) and (last['ema_fast'] < last['ema_slow']) and (last['rsi'] > 35)

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
                registrar_log(f"🚀 ORDEN ENTRADA MARKET EJECUTADA EN BINANCE: {side} {symbol} @ ${price:.4f}")

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
                registrar_log(f"🛡️ ORDEN NATIVA BINANCE STOP LOSS COLOCADA: ${sl_price:.4f}")

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
                registrar_log(f"🎯 ORDEN NATIVA BINANCE TAKE PROFIT COLOCADA: ${tp_price:.4f}")

            except Exception as e:
                registrar_log(f"❌ Error al colocar órdenes en Binance: {e}")
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

        registrar_log(f"POSICIÓN {side} ACTIVA: {symbol} | Qty: {qty} | SL Nativo: ${sl_price:.4f} | TP Nativo: ${tp_price:.4f}")

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

        # Registrar estadísticas de la operación para el Historial y Gráficos del Dashboard
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
        bot_status["posicion"] = "🔍 SIN POSICIÓN (Escaneando)"
        bot_status["activo_actual"] = "Ninguno"
        bot_status["stop_loss"] = "N/A"
        bot_status["take_profit"] = "N/A"

        registrar_log(f"CIERRE ({motivo}): {self.current_symbol} | Precio: ${price:.4f} | Resultado Neto: {ganancia_neta:+.4f} USDT | Saldo: {bot_status['balance']}")

        self.position = None
        self.current_symbol = None
        self.entry_price = 0.0
        self.position_qty = 0.0

    def ejecutar(self):
        registrar_log("El bot ha comenzado a escanear el mercado con Protección Nativa Binance 24/7...")
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
                        bot_status["posicion"] = "🔍 SIN POSICIÓN (Escaneando)"
                        bot_status["activo_actual"] = f"Escaneando {len(config.ASSET_POOL)} activos"
                        if len(bot_status["logs"]) == 0 or "Escaneando" not in bot_status["logs"][0][1]:
                            registrar_log(f"Escaneando {config.ASSET_POOL}... Buscando oportunidad...")

                else:
                    df = self.obtener_datos(self.current_symbol)
                    precio_actual = df.iloc[-1]['close']
                    long_sig, short_sig, _, _, _ = self.evaluar_senales(df)

                    flecha = "⬆️" if self.position == 'LONG' else "⬇️"
                    bot_status["posicion"] = f"{flecha} POSICIÓN {self.position} ({self.current_symbol})"
                    bot_status["activo_actual"] = f"${precio_actual:.4f} (Entrada: ${self.entry_price:.4f})"

                    if self.position == 'LONG' and short_sig:
                        self.cerrar_posicion(precio_actual, "CAMBIO A SHORT")
                    elif self.position == 'SHORT' and long_sig:
                        self.cerrar_posicion(precio_actual, "CAMBIO A LONG")

                time.sleep(10)
            except Exception as e:
                registrar_log(f"Error en bucle principal: {e}")
                time.sleep(10)

if __name__ == "__main__":
    bot = BotFuturosBinance()
    bot.ejecutar()
