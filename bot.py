import sys
import io
import os
import threading
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

# Estado global y logs para el Dashboard Web en vivo
bot_status = {
    "balance": "Conectando...",
    "estado": "Inicializando...",
    "activo_actual": "Ninguno",
    "posicion": "SIN POSICIÓN (Escaneando)",
    "precio_entrada": "0.0000",
    "servidor": "Render Cloud EU",
    "logs": []
}

def registrar_log(mensaje):
    timestamp = time.strftime('%H:%M:%S')
    linea = f"[{timestamp}] {mensaje}"
    print(linea)
    bot_status["logs"].insert(0, (timestamp, mensaje))
    if len(bot_status["logs"]) > 50:
        bot_status["logs"].pop()

# Contador global de rotación de fondos de pantalla cósmicos
bg_index = 0

# Dashboard HTML Ultra-Pro con Fondos Espaciales Rotativos
class DashboardWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global bg_index
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        # 4 Fondos Espaciales / Nebulosas de Alta Definición
        bg_images = [
            "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1920&q=80",
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80",
            "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1920&q=80",
            "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1920&q=80"
        ]
        
        current_bg = bg_images[bg_index % len(bg_images)]
        bg_index += 1
        
        # Formateo dinámico con colores según el tipo de log
        logs_rendered = []
        for ts, msg in bot_status["logs"]:
            color = "#00f2fe" # Azul cian por defecto
            if "ENTRADA" in msg or "🚀" in msg:
                color = "#0ecb81" # Verde esmeralda
            elif "CIERRE" in msg or "🏁" in msg:
                color = "#f0b90b" # Dorado
            elif "STOP LOSS" in msg or "❌" in msg:
                color = "#f6465d" # Rojo carmesí
            
            logs_rendered.append(f"""
            <div class="log-row">
                <span class="log-time">[{ts}]</span>
                <span class="log-msg" style="color: {color};">{msg}</span>
            </div>
            """)
        
        logs_html = "".join(logs_rendered) if logs_rendered else "<div class='log-row'><span class='log-msg'>Iniciando sistema de escaneo...</span></div>"
        
        pos_str = bot_status["posicion"]
        pos_badge_color = "#848e9c"
        if "LONG" in pos_str:
            pos_badge_color = "#0ecb81"
        elif "SHORT" in pos_str:
            pos_badge_color = "#f6465d"
        elif "Escaneando" in pos_str:
            pos_badge_color = "#f0b90b"

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
            <style>
                :root {{
                    --panel-bg: rgba(15, 18, 26, 0.78);
                    --panel-border: rgba(255, 255, 255, 0.12);
                    --accent-gold: #f0b90b;
                    --accent-green: #0ecb81;
                    --accent-red: #f6465d;
                    --accent-cyan: #00f2fe;
                    --text-main: #ffffff;
                    --text-muted: #a0aec0;
                }}
                
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                    background-color: #05070a;
                    background-image: url('{current_bg}');
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

                /* Capa de transparencia oscura del 75% sobre la imagen de fondo */
                body::before {{
                    content: '';
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(5, 7, 12, 0.75);
                    z-index: 0;
                    pointer-events: none;
                }}

                .dashboard {{
                    max-width: 1100px;
                    margin: 0 auto;
                    position: relative;
                    z-index: 1;
                }}

                /* Top Navigation & Status Bar */
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

                .brand {{
                    display: flex;
                    align-items: center;
                    gap: 14px;
                }}

                .brand-icon {{
                    width: 44px;
                    height: 44px;
                    background: linear-gradient(135deg, #f0b90b 0%, #ff8c00 100%);
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 800;
                    color: #000;
                    font-size: 24px;
                    box-shadow: 0 0 20px rgba(240, 185, 11, 0.4);
                }}

                .brand-text h1 {{
                    font-size: 20px;
                    font-weight: 800;
                    letter-spacing: -0.5px;
                    background: linear-gradient(90deg, #ffffff 0%, #f0b90b 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}

                .brand-text p {{
                    font-size: 11px;
                    color: var(--text-muted);
                    font-weight: 600;
                    letter-spacing: 0.5px;
                    text-transform: uppercase;
                }}

                .status-pill {{
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    background: rgba(14, 203, 129, 0.15);
                    border: 1px solid rgba(14, 203, 129, 0.4);
                    color: var(--accent-green);
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 700;
                }}

                .pulse-dot {{
                    width: 9px;
                    height: 9px;
                    background-color: var(--accent-green);
                    border-radius: 50%;
                    box-shadow: 0 0 10px var(--accent-green);
                    animation: pulse 1.8s infinite ease-in-out;
                }}

                @keyframes pulse {{
                    0% {{ transform: scale(0.95); opacity: 0.8; }}
                    50% {{ transform: scale(1.3); opacity: 1; }}
                    100% {{ transform: scale(0.95); opacity: 0.8; }}
                }}

                /* Grid Metrics Cards */
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
                    gap: 16px;
                    margin-bottom: 24px;
                }}

                .metric-card {{
                    background: var(--panel-bg);
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border: 1px solid var(--panel-border);
                    border-radius: 16px;
                    padding: 22px;
                    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
                    transition: transform 0.25s ease, box-shadow 0.25s ease;
                }}

                .metric-card:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 14px 35px rgba(0, 0, 0, 0.6);
                }}

                .metric-label {{
                    font-size: 12px;
                    color: var(--text-muted);
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 8px;
                }}

                .metric-val {{
                    font-size: 26px;
                    font-weight: 800;
                    letter-spacing: -0.5px;
                }}

                .metric-sub {{
                    font-size: 11px;
                    color: var(--text-muted);
                    margin-top: 6px;
                }}

                /* Asset Pool Chips */
                .assets-bar {{
                    background: var(--panel-bg);
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border: 1px solid var(--panel-border);
                    border-radius: 16px;
                    padding: 16px 22px;
                    margin-bottom: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    flex-wrap: wrap;
                    gap: 12px;
                    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
                }}

                .assets-title {{
                    font-size: 13px;
                    font-weight: 700;
                    color: var(--text-muted);
                    letter-spacing: 0.5px;
                }}

                .asset-chips {{
                    display: flex;
                    gap: 10px;
                }}

                .chip {{
                    background: rgba(240, 185, 11, 0.12);
                    border: 1px solid rgba(240, 185, 11, 0.3);
                    padding: 6px 14px;
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: 800;
                    letter-spacing: 0.5px;
                    color: var(--accent-gold);
                }}

                /* Terminal Window */
                .terminal-card {{
                    background: rgba(10, 13, 20, 0.92);
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border: 1px solid var(--panel-border);
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 16px 50px rgba(0, 0, 0, 0.7);
                }}

                .terminal-header {{
                    background: rgba(22, 27, 38, 0.9);
                    padding: 16px 22px;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}

                .terminal-title {{
                    font-size: 12px;
                    font-weight: 700;
                    color: var(--text-muted);
                    letter-spacing: 1px;
                    text-transform: uppercase;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}

                .terminal-dots {{
                    display: flex;
                    gap: 6px;
                }}

                .dot {{
                    width: 11px;
                    height: 11px;
                    border-radius: 50%;
                }}

                .dot-red {{ background: #ff5f56; }}
                .dot-yellow {{ background: #ffbd2e; }}
                .dot-green {{ background: #27c93f; }}

                .terminal-body {{
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 13px;
                    padding: 20px;
                    height: 390px;
                    overflow-y: auto;
                    line-height: 1.65;
                }}

                .log-row {{
                    display: flex;
                    gap: 14px;
                    padding: 5px 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.03);
                }}

                .log-time {{
                    color: #6e7681;
                    font-weight: 600;
                    user-select: none;
                }}

                .log-msg {{
                    flex: 1;
                    word-break: break-word;
                }}

                /* Scrollbar Customization */
                ::-webkit-scrollbar {{
                    width: 6px;
                }}
                ::-webkit-scrollbar-track {{
                    background: rgba(0, 0, 0, 0.2);
                }}
                ::-webkit-scrollbar-thumb {{
                    background: rgba(255, 255, 255, 0.15);
                    border-radius: 4px;
                }}
            </style>
            <script>
                // Rotación dinámica de fondo de pantalla cada 5 segundos
                const bgImages = [
                    "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1920&q=80",
                    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1920&q=80",
                    "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1920&q=80",
                    "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1920&q=80"
                ];
                let currentIdx = Math.floor(Math.random() * bgImages.length);
                
                setInterval(() => {{
                    currentIdx = (currentIdx + 1) % bgImages.length;
                    document.body.style.backgroundImage = `url('${{bgImages[currentIdx]}}')`;
                }}, 5000);
            </script>
        </head>
        <body>
            <div class="dashboard">
                <!-- Navigation Bar -->
                <div class="navbar">
                    <div class="brand">
                        <div class="brand-icon">🔥</div>
                        <div class="brand-text">
                            <h1>MARIO &amp; JOEL LIMPIAS BOT , MECHEROS like LUCAS</h1>
                            <p>Binance USDT-M Futures • 5x Leverage System</p>
                        </div>
                    </div>
                    <div class="status-pill">
                        <div class="pulse-dot"></div>
                        <span>SYSTEM ONLINE (24/7 CLOUD)</span>
                    </div>
                </div>

                <!-- Metrics Grid -->
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Account Balance</div>
                        <div class="metric-val" style="color: var(--accent-gold);">{bot_status["balance"]}</div>
                        <div class="metric-sub">Real-Time Wallet Balance</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">Engine Position Status</div>
                        <div class="metric-val" style="color: {pos_badge_color}; font-size: 19px; margin-top: 4px;">{bot_status["posicion"]}</div>
                        <div class="metric-sub">Strategy: EMA 9/21 + RSI 14</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">Active Target Asset</div>
                        <div class="metric-val" style="color: var(--accent-cyan);">{bot_status["activo_actual"]}</div>
                        <div class="metric-sub">Timeframe: 5m Candles</div>
                    </div>

                    <div class="metric-card">
                        <div class="metric-label">Risk Management</div>
                        <div class="metric-val" style="color: #ffffff; font-size: 19px;">SL -1.2% | TP +2.5%</div>
                        <div class="metric-sub">Margin: Isolated 5x • VIP 0 Fees Included</div>
                    </div>
                </div>

                <!-- Asset Pool Selector Bar -->
                <div class="assets-bar">
                    <div class="assets-title">📡 ACTIVE SCANNER POOL (TOP LIQUIDITY PAIRS)</div>
                    <div class="asset-chips">
                        <div class="chip">SOL/USDT</div>
                        <div class="chip">DOGE/USDT</div>
                        <div class="chip">XRP/USDT</div>
                        <div class="chip">ADA/USDT</div>
                    </div>
                </div>

                <!-- Live Terminal Feed -->
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

def iniciar_servidor_web():
    try:
        port = int(os.getenv("PORT", 10000))
        server = HTTPServer(('0.0.0.0', port), DashboardWebHandler)
        registrar_log(f"Servidor Web Pro activo en puerto {port}")
        server.serve_forever()
    except Exception as e:
        print(f"Aviso servidor web: {e}")

# Iniciar servidor web de monitoreo en un hilo secundario
threading.Thread(target=iniciar_servidor_web, daemon=True).start()

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
        self.precisions = {}
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
                    balances = self.client.futures_account_balance()
                    usdt_balance = next((float(b['balance']) for b in balances if b['asset'] == 'USDT'), 0.0)
                    
                    bot_status["balance"] = f"{usdt_balance:.2f} USDT"
                    bot_status["estado"] = "Conectado y Escaneando"
                    registrar_log(f"✅ Conexión exitosa con Binance. Balance: {usdt_balance:.2f} USDT")
                    
                    mode_info = self.client.futures_get_position_mode()
                    self.hedge_mode = mode_info.get('dualSidePosition', False)
                    modo_str = "Hedge Mode" if self.hedge_mode else "One-Way Mode"
                    registrar_log(f"Modo de Posición: {modo_str}")
                    
                    info = self.client.futures_exchange_info()
                    for s in info['symbols']:
                        if s['symbol'] in config.ASSET_POOL:
                            self.precisions[s['symbol']] = s['quantityPrecision']
                    
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
            self.precisions = {'SOLUSDT': 2, 'XRPUSDT': 1, 'DOGEUSDT': 0, 'ADAUSDT': 0}

    def ajustar_precision_cantidad(self, symbol, qty):
        precision = self.precisions.get(symbol, 2)
        if precision == 0:
            return math.floor(qty)
        factor = 10 ** precision
        return math.floor(qty * factor) / factor

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
                registrar_log(f"🚀 ¡ORDEN EJECUTADA EN BINANCE! {side} en {symbol} @ ${price:.4f}")
            except Exception as e:
                registrar_log(f"❌ Error orden Binance: {e}")
                return

        self.current_symbol = symbol
        self.position_qty = qty
        self.entry_price = price
        self.position = side
        
        comision_entrada = valor_nocional * self.fee_rate
        self.margin -= comision_entrada

        bot_status["activo_actual"] = symbol
        bot_status["posicion"] = f"POSICIÓN {side} @ ${price:.4f}"
        bot_status["precio_entrada"] = f"{price:.4f}"

        registrar_log(f"ENTRADA: {side} {symbol} | Cantidad: {qty} | Valor Nocional: ${valor_nocional:.2f} USDT | Comisión VIP0: -${comision_entrada:.4f} USDT")

    def cerrar_posicion(self, price, motivo="SEÑAL"):
        if not self.position:
            return

        if not self.paper:
            try:
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
                registrar_log(f"🏁 Orden de Cierre ejecutada en Binance por {motivo}")
            except Exception as e:
                registrar_log(f"❌ Error al cerrar posición en Binance: {e}")

        valor_nocional_salida = self.position_qty * price
        comision_salida = valor_nocional_salida * self.fee_rate

        if self.position == 'LONG':
            ganancia_bruta = (price - self.entry_price) * self.position_qty
        else: # SHORT
            ganancia_bruta = (self.entry_price - price) * self.position_qty

        ganancia_neta = ganancia_bruta - comision_salida
        self.margin += (self.entry_price * self.position_qty / self.leverage) + ganancia_neta

        bot_status["balance"] = f"{self.margin:.2f} USDT"
        bot_status["posicion"] = "SIN POSICIÓN (Escaneando)"
        bot_status["activo_actual"] = "Ninguno"

        registrar_log(f"CIERRE ({motivo}): {self.current_symbol} | Precio Cierre: ${price:.4f} | Resultado Neto: {ganancia_neta:+.4f} USDT | Nuevo Saldo: ${self.margin:.2f} USDT")

        self.position = None
        self.current_symbol = None
        self.entry_price = 0.0
        self.position_qty = 0.0

    def ejecutar(self):
        registrar_log("El bot ha comenzado a escanear el mercado...")
        while True:
            try:
                if self.position is None:
                    activo, direccion, precio = self.escanear_mercado()
                    if activo:
                        self.abrir_posicion(activo, direccion, precio)
                    else:
                        timestamp = time.strftime('%H:%M:%S')
                        bot_status["posicion"] = "SIN POSICIÓN (Escaneando)"
                        bot_status["activo_actual"] = f"Escaneando {len(config.ASSET_POOL)} activos"
                        if len(bot_status["logs"]) == 0 or "Escaneando" not in bot_status["logs"][0][1]:
                            registrar_log(f"Escaneando {config.ASSET_POOL}... Buscando oportunidad...")

                else:
                    df = self.obtener_datos(self.current_symbol)
                    precio_actual = df.iloc[-1]['close']
                    long_sig, short_sig, _, _, _ = self.evaluar_senales(df)

                    bot_status["posicion"] = f"POSICIÓN {self.position} ({self.current_symbol})"
                    bot_status["activo_actual"] = f"${precio_actual:.4f} (Entrada: ${self.entry_price:.4f})"

                    if self.position == 'LONG':
                        rendimiento = (precio_actual - self.entry_price) / self.entry_price
                        if rendimiento <= -config.STOP_LOSS_PCT:
                            self.cerrar_posicion(precio_actual, "STOP LOSS")
                        elif rendimiento >= config.TAKE_PROFIT_PCT:
                            self.cerrar_posicion(precio_actual, "TAKE PROFIT")
                        elif short_sig:
                            self.cerrar_posicion(precio_actual, "CAMBIO A SHORT")

                    elif self.position == 'SHORT':
                        rendimiento = (self.entry_price - precio_actual) / self.entry_price
                        if rendimiento <= -config.STOP_LOSS_PCT:
                            self.cerrar_posicion(precio_actual, "STOP LOSS")
                        elif rendimiento >= config.TAKE_PROFIT_PCT:
                            self.cerrar_posicion(precio_actual, "TAKE PROFIT")
                        elif long_sig:
                            self.cerrar_posicion(precio_actual, "CAMBIO A LONG")

                time.sleep(10)
            except Exception as e:
                registrar_log(f"Error en bucle principal: {e}")
                time.sleep(10)

if __name__ == "__main__":
    bot = BotFuturosBinance()
    bot.ejecutar()
