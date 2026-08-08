# 🤖 Bot de Trading Algoritmico para Binance Futuros ($2 USD)

Bot de trading automatizado bidireccional (**LONG / SHORT**) desarrollado en Python para **Binance Futuros (USDT-M)**, optimizado para operar con presupuestos iniciales pequeños ($2 USDT) utilizando apalancamiento 5x Aislado e integración con la API oficial de Binance.

---

## 🎯 Características Principales

- **Estrategia Cuantitativa Tendencial:** Cruce de Medias Móviles Exponenciales (EMA 9/21) + Oscilador RSI (14).
- **Operación Bidireccional:** Opera a la ALZA (LONG) y a la BAJA (SHORT).
- **Escáner Dinámico Multi-Activo:** Monitorea en tiempo real un pool de activos altamente líquidos (`SOLUSDT`, `DOGEUSDT`, `XRPUSDT`, `ADAUSDT`) y selecciona automáticamente la mejor oportunidad del mercado.
- **Gestión de Riesgo Integrada:**
  - **Stop Loss:** -1.2% en precio (~ -6.5% neto sobre margen).
  - **Take Profit:** +2.5% en precio (~ +12.0% neto sobre margen).
- **Compatibilidad de Cuenta:**
  - Soporta **Hedge Mode** (Modo Cobertura) y **One-Way Mode** (Modo Unilateral).
  - Ajuste dinámico de decimales por activo (`quantityPrecision`) evitando errores de API.
  - Deducción e informe en tiempo real de comisiones Taker VIP 0 (0.05%).
- **Soporte para Paper Trading:** Modo de simulación local integrado sin riesgo para pruebas.

---

## 📂 Estructura del Proyecto

```text
├── bot.py           # Script principal del bot de trading y lógica de ejecución
├── config.py        # Carga de parámetros, variables de entorno e indicadores
├── .env.example     # Plantilla de variables de entorno para API Keys
├── .gitignore       # Protección de seguridad para excluir credenciales secretas
└── requirements.txt # Librerías requeridas (python-binance, pandas, ta, python-dotenv)
```

---

## ⚙️ Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Maldiroman4/BOT_IA_BINANCE.git
cd BOT_IA_BINANCE
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar Credenciales `.env`
Copia la plantilla `.env.example` a un archivo `.env`:
```bash
cp .env.example .env
```
Edita `.env` agregando tu `BINANCE_API_KEY` y `BINANCE_SECRET_KEY`:
```env
BINANCE_API_KEY=tu_api_key_aqui
BINANCE_SECRET_KEY=tu_secret_key_aqui
PAPER_TRADING=False
USE_TESTNET=False
```

---

## 🚀 Ejecución del Bot

Para iniciar el bot en producción o simulación:

```bash
python bot.py
```

---

## 🛡️ Seguridad
El archivo `.env` que contiene las llaves secretas de la API está incluido en `.gitignore` y **nunca debe ser subido a repositorios públicos**.
