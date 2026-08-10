import sys
import os
import time
import math
import pandas as pd
import numpy as np
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

client = Client(config.BINANCE_API_KEY, config.BINANCE_SECRET_KEY)

def descargar_todos_los_datos():
    print("📥 Descargando 12,000 velas históricas de 15m para los 4 activos...")
    datos = {}
    for s in SYMBOLS:
        all_klines = []
        end_time = None
        for _ in range(12):
            params = {'symbol': s, 'interval': TIMEFRAME, 'limit': 1000}
            if end_time:
                params['endTime'] = end_time
            try:
                klines = client.futures_klines(**params)
                if not klines:
                    break
                all_klines = klines + all_klines
                end_time = klines[0][0] - 1
                time.sleep(0.1)
            except Exception:
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
        
        df['ema_fast'] = ta.trend.ema_indicator(df['close'], window=9)
        df['ema_slow'] = ta.trend.ema_indicator(df['close'], window=21)
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        
        adx_ind = ta.trend.ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=14)
        df['adx'] = adx_ind.adx()
        
        df.dropna(inplace=True)
        datos[s] = df
        print(f"  ✅ {s}: {len(df)} velas cargadas.")

    records = []
    for s, df in datos.items():
        df['symbol'] = s
        records.append(df)
    
    full_df = pd.concat(records).sort_values(by='timestamp').reset_index(drop=True)
    return full_df

def probar_parametros(full_df, tp_pct, sl_pct, req_adx=False):
    balance = INITIAL_BALANCE
    wins = 0
    losses = 0
    active_position = None

    for i in range(1, len(full_df)):
        row = full_df.iloc[i]
        prev_row = full_df.iloc[i-1] if i > 0 and full_df.iloc[i-1]['symbol'] == row['symbol'] else None
        
        if prev_row is None:
            continue

        symbol = row['symbol']
        high = row['high']
        low = row['low']

        if active_position and active_position['symbol'] == symbol:
            pos = active_position
            side = pos['side']
            entry = pos['entry_price']
            
            if side == 'LONG':
                tp_price = entry * (1.0 + tp_pct)
                sl_price = entry * (1.0 - sl_pct)
                hit_tp = high >= tp_price
                hit_sl = low <= sl_price
            else:
                tp_price = entry * (1.0 - tp_pct)
                sl_price = entry * (1.0 + sl_pct)
                hit_tp = low <= tp_price
                hit_sl = high >= sl_price

            if hit_tp or hit_sl:
                exit_price = tp_price if hit_tp else sl_price
                valor_nocional_salida = pos['qty'] * exit_price
                comision_salida = valor_nocional_salida * TAKER_FEE

                if side == 'LONG':
                    pnl_bruto = (exit_price - entry) * pos['qty']
                else:
                    pnl_bruto = (entry - exit_price) * pos['qty']

                pnl_neto = pnl_bruto - comision_salida
                balance += pnl_neto
                if pnl_neto >= 0:
                    wins += 1
                else:
                    losses += 1
                active_position = None

        if active_position is None:
            ema_fast = row['ema_fast']
            ema_slow = row['ema_slow']
            prev_fast = prev_row['ema_fast']
            prev_slow = prev_row['ema_slow']
            rsi = row['rsi']
            adx = row['adx']

            filtro_adx = (adx > 20) if req_adx else True

            long_sig = (prev_fast <= prev_slow) and (ema_fast > ema_slow) and (rsi < 60) and filtro_adx
            short_sig = (prev_fast >= prev_slow) and (ema_fast < ema_slow) and (rsi > 40) and filtro_adx

            if long_sig or short_sig:
                side = 'LONG' if long_sig else 'SHORT'
                price = row['close']
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
                    'entry_time': row['timestamp']
                }

    total_trades = wins + losses
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    return balance, total_trades, wins, losses, win_rate

if __name__ == "__main__":
    df_historico = descargar_todos_los_datos()
    print("\n=== EVALUANDO MATRIZ DE CONFIGURACIONES ===")
    
    combinaciones = [
        (0.025, 0.012, False, "Original V2.7 (TP 2.5% / SL 1.2%)"),
        (0.015, 0.010, False, "Estrategia Moderada (TP 1.5% / SL 1.0%)"),
        (0.012, 0.008, False, "Scalping Rápido (TP 1.2% / SL 0.8%)"),
        (0.015, 0.010, True,  "Estrategia Moderada + Filtro ADX > 20"),
        (0.012, 0.008, True,  "Scalping Rápido + Filtro ADX > 20")
    ]

    for tp, sl, adx, desc in combinaciones:
        bal, total, w, l, wr = probar_parametros(df_historico, tp, sl, adx)
        print(f"\n• {desc}:")
        print(f"  Trades: {total} | Win Rate: {wr:.2f}% ({w} Ganadas / {l} Perdedoras) | Saldo Final: ${bal:.2f} USDT (PnL Neto: {bal-INITIAL_BALANCE:+.4f} USDT)")
