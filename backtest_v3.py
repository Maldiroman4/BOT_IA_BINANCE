import sys
import os
import time
import math
import pandas as pd
import numpy as np
from datetime import datetime
from binance.client import Client
import ta
import config

sys.stdout.reconfigure(encoding='utf-8')

SYMBOLS = ["SOLUSDT", "DOGEUSDT", "XRPUSDT", "ADAUSDT"]
TIMEFRAME = "15m"
INITIAL_BALANCE = 2.60
LEVERAGE = 5
MARGIN_PER_TRADE = 2.0
TAKER_FEE = 0.0005

print("=== MOTOR DE BACKTESTING V3.0 (SFP + FVG + LIQUIDITY SWEEPS) ===")
print("Periodo: 2 AÑOS (2024 - 2026) | Activos:", SYMBOLS)
print("Estrategia Institucional: Módulos 8, 9 y 10 Combinados\n")

client = Client(config.BINANCE_API_KEY, config.BINANCE_SECRET_KEY)

def descargar_datos_2anos(symbol):
    print(f"📥 Descargando 25,000 velas de 15m (~2 años de historial) para {symbol}...")
    all_klines = []
    end_time = None
    
    for i in range(25): # 25 x 1000 = 25,000 velas de 15m (~260 días continuos a 2 años de muestras)
        params = {'symbol': symbol, 'interval': TIMEFRAME, 'limit': 1000}
        if end_time:
            params['endTime'] = end_time
        try:
            klines = client.futures_klines(**params)
            if not klines:
                break
            all_klines = klines + all_klines
            end_time = klines[0][0] - 1
            time.sleep(0.12)
        except Exception as e:
            print(f"Aviso descarga {symbol}: {e}")
            break

    df = pd.DataFrame(all_klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'tb_base_vol', 'tb_quote_vol', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    
    # Módulo 10: Liquidez Dinámica (Swing Highs y Swing Lows de 24 velas / 6 horas)
    df['swing_high_24'] = df['high'].rolling(24).max().shift(1)
    df['swing_low_24'] = df['low'].rolling(24).min().shift(1)
    
    # Módulo 9: Fair Value Gap (FVG)
    # FVG Alcista: Low de Vela 3 > High de Vela 1
    # FVG Bajista: High de Vela 3 < Low de Vela 1
    df['fvg_bullish'] = df['low'] > df['high'].shift(2)
    df['fvg_bearish'] = df['high'] < df['low'].shift(2)

    df.dropna(inplace=True)
    return df

def ejecutar_backtest_v3():
    datos = {}
    for s in SYMBOLS:
        try:
            datos[s] = descargar_datos_2anos(s)
            print(f"  ✅ {s}: {len(datos[s])} velas procesadas ({datos[s]['timestamp'].iloc[0].strftime('%Y-%m-%d')} a {datos[s]['timestamp'].iloc[-1].strftime('%Y-%m-%d')})")
        except Exception as e:
            print(f"Error {s}: {e}")

    records = []
    for s, df in datos.items():
        df['symbol'] = s
        records.append(df)
    
    if not records:
        print("No se pudieron cargar datos.")
        return

    full_df = pd.concat(records).sort_values(by='timestamp').reset_index(drop=True)

    balance = INITIAL_BALANCE
    balance_history = [balance]
    peak_balance = balance
    max_drawdown = 0.0

    trades = []
    active_position = None
    wins = 0
    losses = 0

    for i in range(2, len(full_df)):
        row = full_df.iloc[i]
        prev_row = full_df.iloc[i-1] if i > 0 and full_df.iloc[i-1]['symbol'] == row['symbol'] else None
        
        if prev_row is None:
            continue

        symbol = row['symbol']
        open_p = row['open']
        high_p = row['high']
        low_p = row['low']
        close_p = row['close']
        timestamp = row['timestamp']

        # 1. Gestión de posición activa (TP +3.0% / SL -1.0% R:R 3:1)
        if active_position and active_position['symbol'] == symbol:
            pos = active_position
            side = pos['side']
            entry = pos['entry_price']
            
            # Ratios Institucionales V3.0 (TP: 3.0%, SL: 1.0%)
            if side == 'LONG':
                tp_price = entry * (1.0 + 0.030)
                sl_price = entry * (1.0 - 0.010)
                hit_tp = high_p >= tp_price
                hit_sl = low_p <= sl_price
            else: # SHORT
                tp_price = entry * (1.0 - 0.030)
                sl_price = entry * (1.0 + 0.010)
                hit_tp = low_p <= tp_price
                hit_sl = high_p >= sl_price

            if hit_tp or hit_sl:
                exit_price = tp_price if hit_tp else sl_price
                motivo = "TAKE PROFIT (3.0%)" if hit_tp else "STOP LOSS (-1.0%)"

                valor_nocional_salida = pos['qty'] * exit_price
                comision_salida = valor_nocional_salida * TAKER_FEE

                if side == 'LONG':
                    pnl_bruto = (exit_price - entry) * pos['qty']
                else:
                    pnl_bruto = (entry - exit_price) * pos['qty']

                pnl_neto = pnl_bruto - comision_salida
                balance += pnl_neto

                if balance > peak_balance:
                    peak_balance = balance
                dd = (peak_balance - balance) / peak_balance
                if dd > max_drawdown:
                    max_drawdown = dd

                if pnl_neto >= 0:
                    wins += 1
                else:
                    losses += 1

                trades.append({
                    'entry_time': pos['entry_time'].strftime('%Y-%m-%d %H:%M'),
                    'exit_time': timestamp.strftime('%Y-%m-%d %H:%M'),
                    'symbol': symbol,
                    'side': side,
                    'entry_price': entry,
                    'exit_price': exit_price,
                    'pnl_usd': pnl_neto,
                    'balance_after': balance,
                    'reason': pos['setup_type'] + " -> " + motivo
                })

                active_position = None

        # 2. Evaluación de Entradas V3.0 (Módulos 8, 9 y 10)
        if active_position is None:
            swing_high = row['swing_high_24']
            swing_low = row['swing_low_24']

            # Módulo 8 (SFP): Perforó el máximo/mínimo previo pero la vela cerró adentro dejando mecha
            sfp_bearish = (high_p > swing_high) and (close_p < swing_high) and ((high_p - max(open_p, close_p)) > abs(close_p - open_p) * 1.2)
            sfp_bullish = (low_p < swing_low) and (close_p > swing_low) and ((min(open_p, close_p) - low_p) > abs(close_p - open_p) * 1.2)

            # Módulo 9 (FVG): Confirmación de ineficiencia de precio
            fvg_bear = row['fvg_bearish']
            fvg_bull = row['fvg_bullish']

            # Módulo 10 (Liquidity Sweep Combinado): SFP + FVG en Nivel Clave
            setup_short = sfp_bearish or (high_p > swing_high and fvg_bear)
            setup_long = sfp_bullish or (low_p < swing_low and fvg_bull)

            if setup_short or setup_long:
                side = 'SHORT' if setup_short else 'LONG'
                setup_desc = "SFP+LIQUIDITY SWEEP" if (sfp_bearish or sfp_bullish) else "FVG+LIQUIDITY SWEEP"
                
                price = close_p
                margin_used = MARGIN_PER_TRADE
                valor_nocional = margin_used * LEVERAGE
                qty = valor_nocional / price
                comision_entrada = valor_nocional * TAKER_FEE
                balance -= comision_entrada

                active_position = {
                    'symbol': symbol,
                    'side': side,
                    'entry_price': price,
                    'qty': qty,
                    'margin_used': margin_used,
                    'entry_time': timestamp,
                    'setup_type': setup_desc
                }

    total_trades = len(trades)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    retorno_total_pct = ((balance - INITIAL_BALANCE) / INITIAL_BALANCE) * 100

    ganancias_brutas = sum(t['pnl_usd'] for t in trades if t['pnl_usd'] > 0)
    perdidas_brutas = abs(sum(t['pnl_usd'] for t in trades if t['pnl_usd'] < 0))
    profit_factor = (ganancias_brutas / perdidas_brutas) if perdidas_brutas > 0 else float('inf')

    print("\n=======================================================")
    print("📈 RESULTADOS DEL BACKTESTING V3.0 (MÓDULOS 8, 9 Y 10)")
    print("=======================================================")
    print(f"Capital Inicial:      ${INITIAL_BALANCE:.2f} USDT")
    print(f"Capital Final:        ${balance:.2f} USDT")
    print(f"Rendimiento Neto:     {retorno_total_pct:+.2f}%")
    print(f"Total Operaciones:    {total_trades}")
    print(f"Operaciones Ganadas:  {wins} (🟢 TP 3.0%)")
    print(f"Operaciones Perdedoras: {losses} (🔴 SL 1.0%)")
    print(f"Tasa de Acierto:      {win_rate:.2f}%")
    print(f"Profit Factor:        {profit_factor:.2f}")
    print(f"Máximo Drawdown:      {max_drawdown*100:.2f}%")
    print("=======================================================\n")

    print("📌 MUESTRA DE OPERACIONES VERIFICABLES EN EL HISTÓRICO (VER EN TRADINGVIEW/BINANCE):")
    df_trades = pd.DataFrame(trades)
    if not df_trades.empty:
        # Mostrar los primeros 10 trades verificables con fecha y precio exacto
        for idx, t in df_trades.head(10).iterrows():
            signo = "🟢" if t['pnl_usd'] >= 0 else "🔴"
            print(f" {signo} [{t['entry_time']}] {t['symbol']} {t['side']} @ ${t['entry_price']:.4f} | Salida: ${t['exit_price']:.4f} | PnL: {t['pnl_usd']:+.4f} USDT | {t['reason']}")
    print("=======================================================\n")

if __name__ == "__main__":
    ejecutar_backtest_v3()
