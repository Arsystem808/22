import pandas as pd
import numpy as np

def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df['close'].shift(1)
    tr = np.maximum(df['high']-df['low'], np.maximum((df['high']-prev_close).abs(), (df['low']-prev_close).abs()))
    return tr

def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    tr = true_range(df)
    return tr.rolling(window).mean()

def momentum(df: pd.DataFrame, window: int = 10) -> pd.Series:
    return df['close'].pct_change(window)

def pivots_daily(df: pd.DataFrame) -> pd.DataFrame:
    piv = pd.DataFrame(index=df.index)
    h1 = df['high'].shift(1)
    l1 = df['low'].shift(1)
    c1 = df['close'].shift(1)
    P = (h1 + l1 + c1) / 3.0
    R1 = 2*P - l1
    S1 = 2*P - h1
    R2 = P + (h1 - l1)
    S2 = P - (h1 - l1)
    piv['pivot'] = P
    piv['r1'] = R1
    piv['s1'] = S1
    piv['r2'] = R2
    piv['s2'] = S2
    return piv

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out['ret1'] = out['close'].pct_change()
    out['atr14'] = atr(out, 14)
    out['mom10'] = momentum(out, 10)
    piv = pivots_daily(out)
    out = out.join(piv)
    out['dist_pivot'] = (out['close'] - out['pivot']) / out['close']
    out['dist_r1'] = (out['r1'] - out['close']) / out['close']
    out['dist_s1'] = (out['close'] - out['s1']) / out['close']
    out = out.dropna()
    return out

def make_labels(df: pd.DataFrame, horizon: int = 1) -> pd.Series:
    future = df['close'].shift(-horizon)
    label = (future > df['close']).astype(int)
    return label
