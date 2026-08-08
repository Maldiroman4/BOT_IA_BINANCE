import sys
import io
# Forzar codificación UTF-8 en la consola de Windows
sys.stdout.reconfigure(encoding='utf-8')

import time
import math
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
import ta
import config

class BotFuturosBinance:
    def __init__(self):
        print("\n==================================================")
        print("    BOT DE TRADING BINANCE FUTUROS - 2 USD       ")
        print("    (INCLUYE COMISIONES DE CUENTA BÁSICA VIP 0)  ")
        print("==================================================")
        
        self.paper = config.PAPER_TRADING
        self.margin = config.MARGIN_USD
        self.leverage = config.LEVERAGE
        self.current_symbol = None
        self.position = None        # None, 'LONG' o 'SHORT'
        self.entry_price = 0.0
        self.position_qty = 0.0
        self.precisions = {}
        self.hedge_mode = False     # Modo cobertura (Hedge Mode) o Modo Unilateral
        
        # Tarifa Taker Estándar de Binance Futuros para Cuentas Básicas (VIP 0): 0.05%
        self.fee_rate = 0.0005 

        if not self.paper:
            servidor = "TESTNET (Pruebas)" if config.USE_TESTNET else "CUENTA REAL DE BINANCE"
            print(f"Conectando a {servidor} con tus API Keys...")
            try:
                self.client = Client(
                    config.BINANCE_API_KEY, 
                    config.BINANCE_SECRET_KEY, 
                    testnet=config.USE_TESTNET
                )
                balances = self.client.futures_account_balance()
                usdt_balance = next((float(b['balance']) for b in balances if b['asset'] == 'USDT'), 0.0)
                
                print(f"✅ CONEXIÓN EXITOSA CON BINANCE FUTUROS ({servidor})")
                print(f"💰 Balance disponible en Binance: {usdt_balance:.2f} USDT")
                
                # Detectar el modo de posición de la cuenta del usuario (Hedge Mode vs One-Way Mode)
                mode_info = self.client.futures_get_position_mode()
                self.hedge_mode = mode_info.get('dualSidePosition', False)
                print(f"⚙️ Modo de Posición detectado: {'Modo Cobertura (Hedge Mode)' if self.hedge_mode else 'Modo Unilateral (One-Way)'}")
                
                # Obtener la precisión exacta de decimales para cada activo del pool
                info = self.client.futures_exchange_info()
                for s in info['symbols']:
                    if s['symbol'] in config.ASSET_POOL:
                        self.precisions[s['symbol']] = s['quantityPrecision']
                
            except BinanceAPIException as e:
                print(f"\n❌ ERROR DE CONEXIÓN BINANCE (Código {e.code}): {e.message}")
                exit(1)
            except Exception as e:
                print(f"❌ Error de conexión: {e}")
                exit(1)
        else:
            self.client = Client()
            print(f"Estado: MODO SIMULACIÓN (PAPER TRADING)")
            print(f"Capital Virtual Inicial: {self.margin:.2f} USDT")
            print(f"Apalancamiento: {self.leverage}x (Posición Nocional: {self.margin * self.leverage:.2f} USDT)")
            self.precisions = {'SOLUSDT': 2, 'XRPUSDT': 1, 'DOGEUSDT': 0, 'ADAUSDT': 0}

    def ajustar_precision_cantidad(self, symbol, qty):
        """Ajusta la cantidad según los decimales exactos permitidos por Binance."""
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
            print(f"⚠️ Aviso al configurar apalancamiento: {e}")
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
                print(f"Error escaneando {symbol}: {e}")

        return mejor_activo, mejor_direccion, mejor_precio

    def abrir_posicion(self, symbol, side, price):
        valor_nocional = self.margin * self.leverage
        qty_bruta = valor_nocional / price
        qty = self.ajustar_precision_cantidad(symbol, qty_bruta)

        if qty <= 0:
            print(f"⚠️ Cantidad calculada demasiado pequeña para {symbol}")
            return
        
        if not self.paper:
            config_ok = self._configurar_cuenta_binance(symbol)
            try:
                # Construir los parámetros compatibles según el modo de posición de la cuenta
                order_params = {
                    'symbol': symbol,
                    'side': 'BUY' if side == 'LONG' else 'SELL',
                    'type': 'MARKET',
                    'quantity': qty
                }
                
                if self.hedge_mode:
                    order_params['positionSide'] = side # 'LONG' o 'SHORT'

                self.client.futures_create_order(**order_params)
                print("✅ ORDEN ENVIADA Y EJECUTADA EXITOSAMENTE EN BINANCE FUTUROS")
            except Exception as e:
                print(f"❌ Error al enviar orden a Binance: {e}")
                return

        self.current_symbol = symbol
        self.position_qty = qty
        self.entry_price = price
        self.position = side
        
        comision_entrada = valor_nocional * self.fee_rate
        self.margin -= comision_entrada

        print("\n--------------------------------------------------")
        print(f"🚀 ¡NUEVA OPERACIÓN ENTRADA!")
        print(f"Activo: {symbol} | Tipo: {side}")
        print(f"Precio Entrada: {price:.4f} USDT | Cantidad: {qty}")
        print(f"Valor Posición Nocional: {valor_nocional:.2f} USDT")
        print(f"Comisión Entrada Binance VIP 0 (0.05%): -{comision_entrada:.4f} USDT")
        print(f"Margen Neto Restante: {self.margin:.2f} USDT")
        print("--------------------------------------------------\n")

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
                print("✅ Orden de cierre ejecutada en Binance Futuros")
            except Exception as e:
                print(f"❌ Error al cerrar posición en Binance: {e}")

        valor_nocional_salida = self.position_qty * price
        comision_salida = valor_nocional_salida * self.fee_rate

        if self.position == 'LONG':
            ganancia_bruta = (price - self.entry_price) * self.position_qty
        else: # SHORT
            ganancia_bruta = (self.entry_price - price) * self.position_qty

        ganancia_neta = ganancia_bruta - comision_salida
        self.margin += (self.entry_price * self.position_qty / self.leverage) + ganancia_neta

        print("\n--------------------------------------------------")
        print(f"🏁 CIERRE DE POSICIÓN ({motivo})")
        print(f"Activo: {self.current_symbol} | Tipo: {self.position}")
        print(f"Precio Cierre: {price:.4f} USDT")
        print(f"Resultado Bruto: {ganancia_bruta:+.4f} USDT")
        print(f"Comisión Salida Binance VIP 0 (0.05%): -{comision_salida:.4f} USDT")
        print(f"BENEFICIO NETO FINAL: {ganancia_neta:+.4f} USDT")
        print(f"💰 Saldo Total de la Cuenta: {self.margin:.2f} USDT")
        print("--------------------------------------------------\n")

        self.position = None
        self.current_symbol = None
        self.entry_price = 0.0
        self.position_qty = 0.0

    def ejecutar(self):
        print("\nEl bot ha comenzado a escanear el mercado...\n")
        while True:
            try:
                if self.position is None:
                    activo, direccion, precio = self.escanear_mercado()
                    if activo:
                        self.abrir_posicion(activo, direccion, precio)
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] Escaneando {config.ASSET_POOL}... Buscando oportunidad...", end='\r')

                else:
                    df = self.obtener_datos(self.current_symbol)
                    precio_actual = df.iloc[-1]['close']
                    long_sig, short_sig, _, _, _ = self.evaluar_senales(df)

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

                    print(f"[{time.strftime('%H:%M:%S')}] Posición Activa: {self.current_symbol} ({self.position}) | Precio: {precio_actual:.4f} USDT", end='\r')

                time.sleep(10)
            except Exception as e:
                print(f"\nError en ejecución: {e}")
                time.sleep(10)

if __name__ == "__main__":
    bot = BotFuturosBinance()
    bot.ejecutar()
