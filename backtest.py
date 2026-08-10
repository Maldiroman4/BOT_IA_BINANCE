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
MARGIN_PER_TRADE = 2.0  # $2.00 USD fijo por trade para evitar distorsiones
STOP_LOSS_PCT = 0.012   # -1.2% en precio (~ -6.1% neto en margen)
TAKE_PROFIT_PCT = 0.025 # +2.5% en precio (~ +12.4% neto en margen)
TAKER_FEE = 0.0005      # 0.05% por orden (VIP 0 Taker Binance)

print("=== MOTOR DE BACKTESTING REALISTA FUTUROS BINANCE V2.7 ===")
print(f"Activos: {SYMBOLS}")
print(f"Temporalidad: {TIMEFRAME} | Apalancamiento: {LEVERAGE}x")
print(f"Margen Fijo por Operación: ${MARGIN_PER_TRADE:.2f} USDT")
print(f"Objetivos: Stop Loss -{STOP_LOSS_PCT*100}% | Take Profit +{TAKE_PROFIT_PCT*100}%\n")

client = Client(config.BINANCE_API_KEY, config.BINANCE_SECRET_KEY)

def descargar_datos_rapidos(symbol):
    all_klines = []
    end_time = None
    
    for _ in range(12): # 12,000 velas (~4 meses)
        params = {'symbol': symbol, 'interval': TIMEFRAME, 'limit': 1000}
        if end_time:
            params['endTime'] = end_time
        try:
            klines = client.futures_klines(**params)
            if not klines:
                break
            all_klines = klines + all_klines
            end_time = klines[0][0] - 1
            time.sleep(0.15)
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
    
    df['ema_fast'] = ta.trend.ema_indicator(df['close'], window=config.EMA_FAST)
    df['ema_slow'] = ta.trend.ema_indicator(df['close'], window=config.EMA_SLOW)
    df['rsi'] = ta.momentum.rsi(df['close'], window=config.RSI_PERIOD)
    
    df.dropna(inplace=True)
    return df

def ejecutar_backtest():
    datos = {}
    for s in SYMBOLS:
        try:
            datos[s] = descargar_datos_rapidos(s)
        except Exception as e:
            print(f"Error {s}: {e}")

    records = []
    for s, df in datos.items():
        df['symbol'] = s
        records.append(df)
    
    full_df = pd.concat(records).sort_values(by='timestamp').reset_index(drop=True)
    
    balance_fijo = INITIAL_BALANCE
    balance_compuesto = INITIAL_BALANCE
    peak_balance = INITIAL_BALANCE
    max_drawdown = 0.0

    trades = []
    active_position = None
    wins = 0
    losses = 0

    for i in range(1, len(full_df)):
        row = full_df.iloc[i]
        prev_row = full_df.iloc[i-1] if i > 0 and full_df.iloc[i-1]['symbol'] == row['symbol'] else None
        
        if prev_row is None:
            continue

        symbol = row['symbol']
        price = row['close']
        high = row['high']
        low = row['low']

        if active_position and active_position['symbol'] == symbol:
            pos = active_position
            side = pos['side']
            entry = pos['entry_price']
            
            if side == 'LONG':
                tp_price = entry * (1.0 + TAKE_PROFIT_PCT)
                sl_price = entry * (1.0 - STOP_LOSS_PCT)
                hit_tp = high >= tp_price
                hit_sl = low <= sl_price
            else:
                tp_price = entry * (1.0 - TAKE_PROFIT_PCT)
                sl_price = entry * (1.0 + STOP_LOSS_PCT)
                hit_tp = low <= tp_price
                hit_sl = high >= sl_price

            if hit_tp or hit_sl:
                exit_price = tp_price if hit_tp else sl_price
                motivo = "TAKE PROFIT" if hit_tp else "STOP LOSS"

                valor_nocional_salida = pos['qty'] * exit_price
                comision_salida = valor_nocional_salida * TAKER_FEE

                if side == 'LONG':
                    pnl_bruto = (exit_price - entry) * pos['qty']
                else:
                    pnl_bruto = (entry - exit_price) * pos['qty']

                pnl_neto = pnl_bruto - comision_salida
                balance_fijo += pnl_neto

                if balance_fijo > peak_balance:
                    peak_balance = balance_fijo
                dd = (peak_balance - balance_fijo) / peak_balance
                if dd > max_drawdown:
                    max_drawdown = dd

                if pnl_neto >= 0:
                    wins += 1
                else:
                    losses += 1

                trades.append({
                    'entry_time': pos['entry_time'],
                    'exit_time': row['timestamp'],
                    'symbol': symbol,
                    'side': side,
                    'entry_price': entry,
                    'exit_price': exit_price,
                    'pnl_usd': pnl_neto,
                    'balance_after': balance_fijo,
                    'reason': motivo
                })

                active_position = None

        if active_position is None:
            ema_fast = row['ema_fast']
            ema_slow = row['ema_slow']
            prev_fast = prev_row['ema_fast']
            prev_slow = prev_row['ema_slow']
            rsi = row['rsi']

            long_sig = (prev_fast <= prev_slow) and (ema_fast > ema_slow) and (rsi < 60)
            short_sig = (prev_fast >= prev_slow) and (ema_fast < ema_slow) and (rsi > 40)

            if long_sig or short_sig:
                side = 'LONG' if long_sig else 'SHORT'
                margin_used = MARGIN_PER_TRADE
                valor_nocional = margin_used * LEVERAGE
                qty = valor_nocional / price
                comision_entrada = valor_nocional * TAKER_FEE
                balance_fijo -= comision_entrada

                active_position = {
                    'symbol': symbol,
                    'side': side,
                    'entry_price': price,
                    'qty': qty,
                    'margin_used': margin_used,
                    'entry_time': row['timestamp']
                }

    total_trades = len(trades)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    retorno_total_pct = ((balance_fijo - INITIAL_BALANCE) / INITIAL_BALANCE) * 100

    ganancias_brutas = sum(t['pnl_usd'] for t in trades if t['pnl_usd'] > 0)
    perdidas_brutas = abs(sum(t['pnl_usd'] for t in trades if t['pnl_usd'] < 0))
    profit_factor = (ganancias_brutas / perdidas_brutas) if perdidas_brutas > 0 else float('inf')

    print("=======================================================")
    print("RESULTADOS DEL BACKTESTING REALISTA (HISTÓRICO 15M)")
    print("=======================================================")
    print(f"Capital Inicial:      ${INITIAL_BALANCE:.2f} USDT")
    print(f"Capital Final:        ${balance_fijo:.2f} USDT")
    print(f"Rendimiento Neto:     {retorno_total_pct:+.2f}%")
    print(f"Total Operaciones:    {total_trades}")
    print(f"Operaciones Ganadas:  {wins} (🟢 TP +2.5%)")
    print(f"Operaciones Perdedoras: {losses} (🔴 SL -1.2%)")
    print(f"Tasa de Acierto:      {win_rate:.2f}%")
    print(f"Profit Factor:        {profit_factor:.2f}")
    print(f"Máximo Drawdown:      {max_drawdown*100:.2f}%")
    print("=======================================================\n")

    print("DESGLOSE POR CRIPTOMONEDA:")
    df_trades = pd.DataFrame(trades)
    if not df_trades.empty:
        for s in SYMBOLS:
            sub = df_trades[df_trades['symbol'] == s]
            if not sub.empty:
                s_wins = len(sub[sub['pnl_usd'] > 0])
                s_total = len(sub)
                s_wr = (s_wins / s_total) * 100
                s_pnl = sub['pnl_usd'].sum()
                print(f"  * {s}: {s_total} trades | WinRate: {s_wr:.1f}% | PnL Acumulado: {s_pnl:+.4f} USDT")
    print("=======================================================\n")

if __name__ == "__main__":
    ejecutar_backtest()
