import sys
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime
from binance.client import Client
import config

sys.stdout.reconfigure(encoding='utf-8')

SYMBOLS = ["SOLUSDT", "DOGEUSDT", "XRPUSDT", "ADAUSDT"]
INITIAL_BALANCE = 2.60
LEVERAGE = 5
MARGIN_PER_TRADE = 2.0
TAKER_FEE = 0.0005

client = Client(config.BINANCE_API_KEY, config.BINANCE_SECRET_KEY)

def descargar_datos_tf(symbol, tf):
    all_klines = []
    end_time = None
    for _ in range(6):
        params = {'symbol': symbol, 'interval': tf, 'limit': 1000}
        if end_time:
            params['endTime'] = end_time
        try:
            klines = client.futures_klines(**params)
            if not klines:
                break
            all_klines = klines + all_klines
            end_time = klines[0][0] - 1
            time.sleep(0.05)
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
    
    # Normalizar ventana de 24 horas según la temporalidad
    window_24h = 288 if tf == "5m" else (96 if tf == "15m" else (24 if tf == "1h" else 6))
    
    df['swing_high_24'] = df['high'].rolling(window_24h).max().shift(1)
    df['swing_low_24'] = df['low'].rolling(window_24h).min().shift(1)
    df['fvg_bullish'] = df['low'] > df['high'].shift(2)
    df['fvg_bearish'] = df['high'] < df['low'].shift(2)

    df.dropna(inplace=True)
    return df

def ejecutar_simulacion_tf(tf):
    datos = {}
    for s in SYMBOLS:
        try:
            datos[s] = descargar_datos_tf(s, tf)
        except Exception:
            pass

    records = []
    for s, df in datos.items():
        df['symbol'] = s
        records.append(df)
    
    full_df = pd.concat(records).sort_values(by='timestamp').reset_index(drop=True)
    dias_totales = (full_df['timestamp'].iloc[-1] - full_df['timestamp'].iloc[0]).days
    semanas_totales = max(dias_totales / 7.0, 1.0)

    balance = INITIAL_BALANCE
    wins = 0
    losses = 0
    active_position = None
    trades = []

    for i in range(2, len(full_df)):
        row = full_df.iloc[i]
        symbol = row['symbol']
        open_p = row['open']
        high_p = row['high']
        low_p = row['low']
        close_p = row['close']
        timestamp = row['timestamp']

        if active_position and active_position['symbol'] == symbol:
            pos = active_position
            side = pos['side']
            entry = pos['entry_price']
            
            # Risk Reward 3:1 (TP +3.0% / SL -1.0%)
            if side == 'LONG':
                tp_price = entry * 1.030
                sl_price = entry * 0.990
                hit_tp = high_p >= tp_price
                hit_sl = low_p <= sl_price
            else:
                tp_price = entry * 0.970
                sl_price = entry * 1.010
                hit_tp = low_p <= tp_price
                hit_sl = high_p >= sl_price

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

                trades.append({
                    'entry_time': pos['entry_time'],
                    'exit_time': timestamp,
                    'symbol': symbol,
                    'side': side,
                    'entry_price': entry,
                    'exit_price': exit_price,
                    'pnl_usd': pnl_neto,
                    'reason': pos['setup']
                })
                active_position = None

        if active_position is None:
            swing_high = row['swing_high_24']
            swing_low = row['swing_low_24']

            sfp_b = (high_p > swing_high) and (close_p < swing_high) and ((high_p - max(open_p, close_p)) > abs(close_p - open_p) * 1.2)
            sfp_l = (low_p < swing_low) and (close_p > swing_low) and ((min(open_p, close_p) - low_p) > abs(close_p - open_p) * 1.2)
            
            fvg_b = row['fvg_bearish']
            fvg_l = row['fvg_bullish']

            setup_short = sfp_b or (high_p > swing_high and fvg_b)
            setup_long = sfp_l or (low_p < swing_low and fvg_l)

            if setup_short or setup_long:
                side = 'SHORT' if setup_short else 'LONG'
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
                    'entry_time': timestamp,
                    'setup': "COMBINADO V3.0 (SFP+FVG+SWEEP)"
                }

    total = wins + losses
    wr = (wins / total * 100) if total > 0 else 0.0
    return balance, total, wins, losses, wr, semanas_totales, pd.DataFrame(trades)

if __name__ == "__main__":
    print("=== COMPARATIVA DE EFICIENCIA MULTI-TEMPORALIDAD (MÓDULOS 8+9+10 COMBINADOS) ===")
    tfs = ["5m", "15m", "1h", "4h"]
    
    mejores_trades_15m = None

    for tf in tfs:
        bal, total, w, l, wr, sem, df_tr = ejecutar_simulacion_tf(tf)
        print(f"\n⏱️ TEMPORALIDAD {tf.upper()}:")
        print(f"   • Total Trades: {total} | Operaciones/Semana: {total/sem:.1f}")
        print(f"   • Win Rate: {wr:.2f}% ({w} Ganadas / {l} Perdedoras)")
        print(f"   • Saldo Final: ${bal:.2f} USDT (PnL Neto: {bal-INITIAL_BALANCE:+.4f} USDT)")
        
        if tf == "15m":
            mejores_trades_15m = df_tr

    print("\n=======================================================")
    print("📌 10 EJEMPLOS HISTÓRICOS EXACTOS VERIFICABLES (TEMPORALIDAD 15M):")
    print("=======================================================")
    if mejores_trades_15m is not None and not mejores_trades_15m.empty:
        for idx, t in mejores_trades_15m.head(10).iterrows():
            signo = "🟢 GANADA" if t['pnl_usd'] >= 0 else "🔴 PERDIDA"
            print(f"{idx+1}. [{t['entry_time'].strftime('%Y-%m-%d %H:%M UTC')}] {t['symbol']} | Tipo: {t['side']} | Entrada: ${t['entry_price']:.4f} | Salida: ${t['exit_price']:.4f} | PnL: {t['pnl_usd']:+.4f} USDT ({signo})")
    print("=======================================================\n")
