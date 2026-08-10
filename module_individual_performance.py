import sys
import os
import time
import pandas as pd
from binance.client import Client
import config

sys.stdout.reconfigure(encoding='utf-8')

SYMBOLS = ["SOLUSDT", "DOGEUSDT", "XRPUSDT", "ADAUSDT"]
TIMEFRAME = "15m"
INITIAL_BALANCE = 2.60
LEVERAGE = 5
MARGIN_PER_TRADE = 2.0
TAKER_FEE = 0.0005

client = Client(config.BINANCE_API_KEY, config.BINANCE_SECRET_KEY)

def descargar_datos():
    print("📥 Descargando 12,000 velas de 15m para los 4 activos...")
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
        
        df['swing_high_24'] = df['high'].rolling(24).max().shift(1)
        df['swing_low_24'] = df['low'].rolling(24).min().shift(1)
        
        df['fvg_bullish'] = df['low'] > df['high'].shift(2)
        df['fvg_bearish'] = df['high'] < df['low'].shift(2)

        df.dropna(inplace=True)
        datos[s] = df

    records = []
    for s, df in datos.items():
        df['symbol'] = s
        records.append(df)
    
    full_df = pd.concat(records).sort_values(by='timestamp').reset_index(drop=True)
    return full_df

def evaluar_modulo_individual(full_df, modulo_tipo, tp_pct=0.025, sl_pct=0.012):
    balance = INITIAL_BALANCE
    wins = 0
    losses = 0
    active_position = None

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

        if active_position and active_position['symbol'] == symbol:
            pos = active_position
            side = pos['side']
            entry = pos['entry_price']
            
            if side == 'LONG':
                tp_price = entry * (1.0 + tp_pct)
                sl_price = entry * (1.0 - sl_pct)
                hit_tp = high_p >= tp_price
                hit_sl = low_p <= sl_price
            else:
                tp_price = entry * (1.0 - tp_pct)
                sl_price = entry * (1.0 + sl_pct)
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
                active_position = None

        if active_position is None:
            swing_high = row['swing_high_24']
            swing_low = row['swing_low_24']

            setup_long = False
            setup_short = False

            if modulo_tipo == 8: # SFP Mecheros
                sfp_bearish = (high_p > swing_high) and (close_p < swing_high) and ((high_p - max(open_p, close_p)) > abs(close_p - open_p) * 1.2)
                sfp_bullish = (low_p < swing_low) and (close_p > swing_low) and ((min(open_p, close_p) - low_p) > abs(close_p - open_p) * 1.2)
                setup_short = sfp_bearish
                setup_long = sfp_bullish

            elif modulo_tipo == 9: # FVG Gaps
                fvg_bear = row['fvg_bearish']
                fvg_bull = row['fvg_bullish']
                setup_short = fvg_bear
                setup_long = fvg_bull

            elif modulo_tipo == 10: # Liquidity Sweeps
                sweep_b = (high_p > swing_high and close_p < swing_high)
                sweep_l = (low_p < swing_low and close_p > swing_low)
                setup_short = sweep_b
                setup_long = sweep_l

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
                    'margin_used': margin_used
                }

    total_trades = wins + losses
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    return balance, total_trades, wins, losses, win_rate

if __name__ == "__main__":
    df_full = descargar_datos()
    dias_totales = (df_full['timestamp'].iloc[-1] - df_full['timestamp'].iloc[0]).days
    semanas_totales = dias_totales / 7.0

    print("\n=======================================================")
    print(f"📊 RENDIMIENTO INDIVIDUAL POR MÓDULO EN {semanas_totales:.1f} SEMANAS ({dias_totales} DÍAS)")
    print("=======================================================\n")

    modulos = [
        (8, "MÓDULO 8: SFP (Caza de Mecheros)"),
        (9, "MÓDULO 9: FVG (Ineficiencias de Precio)"),
        (10, "MÓDULO 10: Liquidity Sweeps (Barridos de Nivel Clave)")
    ]

    for m_num, m_name in modulos:
        bal, total, w, l, wr = evaluar_modulo_individual(df_full, m_num)
        ops_sem = total / semanas_totales
        ops_dia = total / dias_totales
        print(f"🔹 {m_name}:")
        print(f"   • Tasa de Acierto (Win Rate): {wr:.2f}% ({w} Ganadas / {l} Perdedoras)")
        print(f"   • Frecuencia Semanal Total (4 activos): ~{ops_sem:.1f} operaciones/semana")
        print(f"   • Frecuencia Diaria Total (4 activos): ~{ops_dia:.1f} operaciones/día")
        print(f"   • Saldo Final Acumulado: ${bal:.2f} USDT (PnL Neto: {bal-INITIAL_BALANCE:+.4f} USDT)\n")
