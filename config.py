import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# ==========================================
# CONFIGURACIÓN GENERAL DEL BOT DE FUTUROS
# ==========================================

# 1. Credenciales de la API de Binance
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")

# 2. Modo de Operación
# PAPER_TRADING = True (Simulación) / False (Operación Real con API Key)
paper_env = os.getenv("PAPER_TRADING", "True").lower()
PAPER_TRADING = paper_env in ['true', '1', 't']

# USE_TESTNET = True (Red de prueba Binance) / False (Cuenta Real)
testnet_env = os.getenv("USE_TESTNET", "True").lower()
USE_TESTNET = testnet_env in ['true', '1', 't']

# 3. Selección y Gestión de Activos (Recomendados para 2 USD)
ASSET_POOL = ['SOLUSDT', 'DOGEUSDT', 'XRPUSDT', 'ADAUSDT']

# 4. Parámetros de Capital y Apalancamiento
MARGIN_USD = 2.0         # Tu capital/margen inicial (2 USD)
LEVERAGE = 5             # Apalancamiento 5x (2 x 5 = 10 USD de posición)
MARGIN_TYPE = 'ISOLATED' # Margen Aislado para proteger tu cuenta

# 5. Configuración de la Estrategia Técnica
TIMEFRAME = '5m'         # Velas de 5 minutos
EMA_FAST = 9             # Media Móvil Exponencial Rápida
EMA_SLOW = 21            # Media Móvil Exponencial Lenta
RSI_PERIOD = 14          # Periodo del RSI

# 6. Gestión de Riesgo (Stop Loss y Take Profit)
STOP_LOSS_PCT = 0.012    # -1.2% en el precio (-6% real en tu margen de 2 USD con 5x)
TAKE_PROFIT_PCT = 0.025   # +2.5% en el precio (+12.5% real en tu margen de 2 USD con 5x)
