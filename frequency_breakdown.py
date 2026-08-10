import sys
import os
import time
import pandas as pd
from binance.client import Client
import config

sys.stdout.reconfigure(encoding='utf-8')

SYMBOLS = ["SOLUSDT", "DOGEUSDT", "XRPUSDT", "ADAUSDT"]
TIMEFRAME = "15m"
client = Client(config.BINANCE_API_KEY, config.BINANCE_SECRET_KEY)

def analizar_frecuencia_modulos():
    print("=== CALCULANDO FRECUENCIA SEMANAL REAL DE OPERACIONES POR MÓDULO ===")
    datos = {}
    for s in SYMBOLS:
        all_klines = []
        end_time = None
        for _ in range(5): # 5,000 velas de 15m (~52 días = 7.4 semanas)
            params = {'symbol': s, 'interval': TIMEFRAME, 'limit': 1000}
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
    
    dias_totales = (full_df['timestamp'].iloc[-1] - full_df['timestamp'].iloc[0]).days
    semanas_totales = dias_totales / 7.0

    count_m8 = 0  # SFP Mecheros
    count_m9 = 0  # FVG Ineficiencias
    count_m10 = 0 # Liquidity Sweeps BSL/SSL

    for i in range(2, len(full_df)):
        row = full_df.iloc[i]
        open_p = row['open']
        high_p = row['high']
        low_p = row['low']
        close_p = row['close']

        swing_high = row['swing_high_24']
        swing_low = row['swing_low_24']

        # Módulo 8: SFP Mecheros (Fallo de impulso con mecha larga)
        sfp_b = (high_p > swing_high) and (close_p < swing_high) and ((high_p - max(open_p, close_p)) > abs(close_p - open_p) * 1.2)
        sfp_l = (low_p < swing_low) and (close_p > swing_low) and ((min(open_p, close_p) - low_p) > abs(close_p - open_p) * 1.2)
        if sfp_b or sfp_l:
            count_m8 += 1

        # Módulo 9: FVG (Gaps de Ineficiencia de precio)
        fvg_b = row['fvg_bearish']
        fvg_l = row['fvg_bullish']
        if fvg_b or fvg_l:
            count_m9 += 1

        # Módulo 10: Liquidity Sweeps (Barridos de Nivel Clave)
        sweep_b = (high_p > swing_high and close_p < swing_high)
        sweep_l = (low_p < swing_low and close_p > swing_low)
        if sweep_b or sweep_l:
            count_m10 += 1

    print("\n=======================================================")
    print(f"📊 FRECUENCIA DE SEÑALES EN {semanas_totales:.1f} SEMANAS ({dias_totales} DÍAS)")
    print("=======================================================")
    print("Módulos Evaluados para 4 activos (SOL, DOGE, XRP, ADA):\n")

    ops_sem_m8 = count_m8 / semanas_totales
    print(f"🔹 MÓDULO 8 (SFP / Barrido de Mecheros):")
    print(f"   • Total Oportunidades: {count_m8} gatillos")
    print(f"   • Promedio Semanal TOTAL (4 monedas): ~{ops_sem_m8:.1f} operaciones/semana")
    print(f"   • Promedio por Cripto: ~{ops_sem_m8/4:.1f} operaciones/semana por activo")
    print(f"   • Frecuencia: ~1 operación cada {168/ops_sem_m8:.1f} horas\n")

    ops_sem_m9 = count_m9 / semanas_totales
    print(f"🔹 MÓDULO 9 (FVG / Ineficiencias de Precio):")
    print(f"   • Total Oportunidades: {count_m9} gatillos")
    print(f"   • Promedio Semanal TOTAL (4 monedas): ~{ops_sem_m9:.1f} operaciones/semana")
    print(f"   • Promedio por Cripto: ~{ops_sem_m9/4:.1f} operaciones/semana por activo")
    print(f"   • Frecuencia: ~1 operación cada {168/ops_sem_m9:.1f} horas\n")

    ops_sem_m10 = count_m10 / semanas_totales
    print(f"🔹 MÓDULO 10 (Liquidity Sweeps de Nivel Clave):")
    print(f"   • Total Oportunidades: {count_m10} gatillos")
    print(f"   • Promedio Semanal TOTAL (4 monedas): ~{ops_sem_m10:.1f} operaciones/semana")
    print(f"   • Promedio por Cripto: ~{ops_sem_m10/4:.1f} operaciones/semana por activo")
    print(f"   • Frecuencia: ~1 operación cada {168/ops_sem_m10:.1f} horas\n")

    print("=======================================================\n")

if __name__ == "__main__":
    analizar_frecuencia_modulos()
