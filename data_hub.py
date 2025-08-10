from __future__ import annotations
import os, hashlib
import pandas as pd
import yfinance as yf

CACHE_DIR = '.cache'
os.makedirs(CACHE_DIR, exist_ok=True)

def _cache_path(symbol: str, interval: str, years: int) -> str:
    key = f"{symbol}_{interval}_{years}".lower()
    return os.path.join(CACHE_DIR, hashlib.md5(key.encode()).hexdigest() + '.parquet')

def load_history_yf(symbol: str, period_years: int = 3, interval: str = '1d') -> pd.DataFrame:
    path = _cache_path(symbol, interval, period_years)
    if os.path.exists(path):
        try:
            df = pd.read_parquet(path)
            if isinstance(df, pd.DataFrame) and not df.empty:
                return df
        except Exception:
            pass
    period = f"{period_years}y" if interval in ('1d','1wk') else '60d'
    df = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise RuntimeError(f'No data returned for {symbol} ({interval=})')
    df = df.rename(columns=str.lower).rename(columns={'adj close':'adj_close'})
    df.index = pd.to_datetime(df.index, utc=True)
    df = df.sort_index()
    try:
        df.to_parquet(path)
    except Exception:
        pass
    return df
