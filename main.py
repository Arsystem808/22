
import os, sys, pathlib
import streamlit as st
import pandas as pd
import numpy as np

BASE_DIR = pathlib.Path(__file__).resolve().parent

@st.cache_data(ttl=3600)
def load_history(symbol: str) -> pd.DataFrame:
    # Try Yahoo; fallback to local CSV under data/demo/*.csv
    try:
        import yfinance as yf
        df = yf.Ticker(symbol).history(period="6mo", interval="1d", auto_adjust=False)
        if df is not None and not df.empty:
            df = df.reset_index().rename(columns=str.title)
            return df[["Date","Open","High","Low","Close","Volume"]]
    except Exception:
        pass
    csv_path = BASE_DIR / "data" / "demo" / f"{symbol.lower()}_demo.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        return df[["Date","Open","High","Low","Close","Volume"]]
    return pd.DataFrame()

def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    tr = np.maximum(high - low, np.maximum((high - prev_close).abs(), (low - prev_close).abs()))
    return tr.rolling(window).mean()

def pivots(df: pd.DataFrame) -> pd.DataFrame:
    h1, l1, c1 = df["High"].shift(1), df["Low"].shift(1), df["Close"].shift(1)
    P = (h1 + l1 + c1) / 3.0
    R1 = 2*P - l1
    S1 = 2*P - h1
    R2 = P + (h1 - l1)
    S2 = P - (h1 - l1)
    out = pd.DataFrame({"pivot":P, "r1":R1, "s1":S1, "r2":R2, "s2":S2})
    return out
def build_levels(df: pd.DataFrame) -> dict:
    if df.empty:
        raise RuntimeError("Нет данных")
    df = df.copy()

    # Динамическое окно ATR: берём то, что есть (не меньше 5)
    win = max(5, min(14, len(df) - 1))
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    tr = np.maximum(high - low, np.maximum((high - prev_close).abs(), (low - prev_close).abs()))
    df["ATR14"] = tr.rolling(win).mean().fillna(tr.ewm(span=win, adjust=False).mean())

    # Пивоты считаем из предыдущего бара; если ряд короткий — fallback на последние значения
    h1, l1, c1 = high.shift(1), low.shift(1), close.shift(1)
    P = ((h1 + l1 + c1) / 3.0).fillna(close.rolling(min_periods=1, window=win).mean())
    R1 = (2*P - l1).fillna(P + (high - low).rolling(win).mean())
    S1 = (2*P - h1).fillna(P - (high - low).rolling(win).mean())
    df["pivot"], df["r1"], df["s1"] = P, R1, S1

    latest = df.iloc[-1]
    px = float(latest["Close"])
    a  = float(latest["ATR14"])
    P  = float(latest["pivot"])
    R1 = float(latest["r1"])
    S1 = float(latest["s1"])

    score = 0.5 if a <= 0 else max(0.0, min(1.0, 0.5 + (px - P)/(2.5*a)))
    action = "BUY" if score >= 0.6 else ("SHORT" if score <= 0.4 else "WAIT")

    if action == "BUY":
        entry, tp1, tp2, sl = px, max(px+0.6*a, R1), max(px+1.2*a, P+(R1-P)*1.5), px-1.0*a
        rationale = "Цена ≥ pivot; волатильность достаточна — приоритет BUY к R1."
    elif action == "SHORT":
        entry, tp1, tp2, sl = px, min(px-0.6*a, S1), min(px-1.2*a, P-(P-S1)*1.5), px+1.0*a
        rationale = "Цена ≤ pivot; спрос слабее — приоритет SHORT к S1."
    else:
        entry, tp1, tp2, sl = px, px+0.8*a, px+1.6*a, px-0.8*a
        rationale = "Сигнал нейтральный — дождаться выхода из диапазона."

    return {
        "price": round(px,2), "atr": round(a,2), "pivot": round(P,2),
        "r1": round(R1,2), "s1": round(S1,2),
        "action": action, "entry": round(entry,2),
        "tp1": round(tp1,2), "tp2": round(tp2,2), "sl": round(sl,2),
        "confidence": round(float(score),2), "rationale": rationale
    }
def get_cfg():
    env = os.getenv("TICKERS", "AAPL,MSFT,NVDA")
    return [t.strip().upper() for t in env.split(",") if t.strip()]

st.set_page_config(page_title="US Stocks — Demo (Levels)", layout="wide")
st.title("US Stocks — Demo: Signals + Levels")
st.caption("Работает даже без Yahoo: если нет сети — CSV fallback (data/demo).")

tickers = st.text_input("Tickers", value=",".join(get_cfg())).upper()
tickers_list = [t.strip() for t in tickers.split(",") if t.strip()]
selected = st.selectbox("Тикер", tickers_list, index=0 if tickers_list else None)

colA, colB = st.columns([1,2])
with colA:
    if st.button("Сгенерировать сигнал"):
        try:
            levels = build_levels(load_history(selected))
            st.session_state["levels"] = levels
        except Exception as e:
            st.error(str(e))

with colB:
    levels = st.session_state.get("levels")
    if levels:
        st.subheader(f"Сигнал для {selected}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Action", levels["action"])
        c2.metric("Entry", levels["entry"])
        c3.metric("TP1", levels["tp1"])
        c4.metric("SL", levels["sl"])
        d1, d2, d3 = st.columns(3)
        d1.metric("Pivot", levels["pivot"])
        d2.metric("R1", levels["r1"])
        d3.metric("S1", levels["s1"])
        st.write(f"**Confidence:** {levels['confidence']:.2f}")
        st.write(levels["rationale"])
        with st.expander("Последние строки данных"):
            st.dataframe(load_history(selected).tail(12))
    else:
        st.info("Нажмите «Сгенерировать сигнал».")
