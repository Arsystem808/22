import os, sys, pathlib
import streamlit as st
import yfinance as yf

# Не требуем src/common/config.py — работаем напрямую с ENV
BASE_DIR = pathlib.Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

def get_config():
    tickers_env = os.getenv("TICKERS", "AAPL,MSFT,NVDA")
    tickers = [t.strip().upper() for t in tickers_env.split(",") if t.strip()]
    lookback = int(os.getenv("DATA_LOOKBACK_YEARS", "3"))
    return {"tickers": tickers, "lookback_years": lookback}

def quick_signal(symbol: str):
    df = yf.download(symbol, period="3mo", interval="1d", progress=False)
    if df.empty:
        return {"symbol": symbol, "error": "No data"}
    px = float(df["Close"].iloc[-1])
    prev = float(df["Close"].iloc[-2]) if len(df) > 1 else px
    score = 0.7 if px > prev else 0.3
    action = "BUY" if score >= 0.6 else ("SHORT" if score <= 0.4 else "WAIT")
    return {"symbol": symbol, "price": round(px, 2), "action": action, "confidence": round(score, 2)}

st.set_page_config(page_title="US Stocks — Minimal", layout="wide")
cfg = get_config()
st.title("US Stocks — Minimal (no config.py)")
st.caption("Минимальный запуск без src/common/config.py — чтобы проверить деплой.")

tickers = st.text_input("Tickers", value=",".join(cfg["tickers"])).upper()
tickers_list = [t.strip() for t in tickers.split(",") if t.strip()]

selected = st.selectbox("Тикер", tickers_list, index=0 if tickers_list else None)
if st.button("Сигнал"):
    sig = quick_signal(selected)
    if "error" in sig:
        st.error(sig["error"])
    else:
        st.success(sig)
