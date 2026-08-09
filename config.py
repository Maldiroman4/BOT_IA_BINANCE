import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Credenciales de API de Binance
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")

# Configuración de Entorno
USE_TESTNET = os.getenv("USE_TESTNET", "False").lower() in ("true", "1", "t")
PAPER_TRADING = os.getenv("PAPER_TRADING", "False").lower() in ("true", "1", "t")

# Grupo de Activos a Escanear (Monedas Top Liquidez Binance)
ASSET_POOL = ["SOLUSDT", "DOGEUSDT", "XRPUSDT", "ADAUSDT"]

# Parámetros de Estrategia V2.0 (Ultra-Trend 15m)
TIMEFRAME = "15m"       # Velas de 15 minutos para eliminar ruido lateral
EMA_FAST = 9            # Media Móvil Exponencial Rápida
EMA_SLOW = 21           # Media Móvil Exponencial Lenta
RSI_PERIOD = 14         # Periodo RSI

# Gestión de Riesgo y Posición ($2.00 USD Margin @ 5x Leverage)
LEVERAGE = 5
MARGIN_USD = 2.0
MARGIN_TYPE = "ISOLATED" # Margen Aislado para cero riesgo cruzado

# Objetivos de Ganancia y Pérdida Nativos Binance (Take Profit & Stop Loss)
STOP_LOSS_PCT = 0.012   # -1.2% en precio (~ -6.0% ROI en margen a 5x)
TAKE_PROFIT_PCT = 0.025 # +2.5% en precio (~ +12.5% ROI en margen a 5x)
