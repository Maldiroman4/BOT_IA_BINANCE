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
    "servidor": "Render Cloud",
    "logs": []
}

def registrar_log(mensaje):
    timestamp = time.strftime('%H:%M:%S')
    linea = f"[{timestamp}] {mensaje}"
    print(linea)
    bot_status["logs"].insert(0, linea)
    if len(bot_status["logs"]) > 40:
        bot_status["logs"].pop()

# Dashboard HTML profesional con autorrefresco cada 5 segundos
class DashboardWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        logs_html = "".join([f"<div class='log-line'>{l}</div>" for l in bot_status["logs"]])
        
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="5">
            <title>Dashboard | Bot Binance Futuros</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background-color: #0b0e11;
                    color: #eaecef;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 900px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    padding: 20px 0;
                    border-bottom: 1px solid #1e2329;
                }}
                .header h1 {{
                    color: #f0b90b;
                    margin: 0 0 10px 0;
                    font-size: 26px;
                }}
                .grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 25px 0;
                }}
                .card {{
                    background: #181a20;
                    border: 1px solid #2b313a;
                    border-radius: 8px;
                    padding: 15px;
                    text-align: center;
                }}
                .card-title {{
                    font-size: 12px;
                    color: #848e9c;
                    text-transform: uppercase;
                    margin-bottom: 5px;
                }}
                .card-value {{
                    font-size: 20px;
                    font-weight: bold;
                    color: #0ecb81;
                }}
                .terminal {{
                    background: #121418;
                    border: 1px solid #2b313a;
                    border-radius: 8px;
                    padding: 15px;
                    font-family: 'Courier New', Courier, monospace;
                    font-size: 13px;
                    height: 350px;
                    overflow-y: auto;
                }}
                .terminal-header {{
                    color: #848e9c;
                    border-bottom: 1px solid #2b313a;
                    padding-bottom: 8px;
                    margin-bottom: 10px;
                    font-weight: bold;
                }}
                .log-line {{
                    padding: 3px 0;
                    color: #00ffcc;
                    border-bottom: 1px solid #181a20;
                }}
                .live-badge {{
                    display: inline-block;
                    background: #0ecb81;
                    color: #000;
                    font-weight: bold;
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 Bot de Trading Binance Futuros</h1>
                    <span class="live-badge">🟢 EN VIVO (24/7 NUBE)</span>
                </div>

                <div class="grid">
                    <div class="card">
                        <div class="card-title">Balance en Binance</div>
                        <div class="card-value">{bot_status["balance"]}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Estado Actual</div>
                        <div class="card-value" style="color: #f0b90b;">{bot_status["posicion"]}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Activo Monitoreado</div>
                        <div class="card-value" style="color: #479dff;">{bot_status["activo_actual"]}</div>
                    </div>
                    <div class="card">
                        <div class="card-title">Apalancamiento</div>
                        <div class="card-value">5x ISOLATED</div>
                    </div>
                </div>

                <div class="terminal">
                    <div class="terminal-header">📟 Registro de Eventos en Tiempo Real (Actualiza cada 5s)</div>
                    {logs_html}
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
        registrar_log(f"Servidor Web de Monitoreo activo en puerto {port}")
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
                        if len(bot_status["logs"]) == 0 or "Escaneando" not in bot_status["logs"][0]:
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
