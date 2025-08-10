from __future__ import annotations
from datetime import datetime, timezone
from src.data.data_hub import load_history_yf
from src.features.feature_engine import build_features

def soft_to_action(score: float) -> str:
    if score >= 0.6: return 'BUY'
    if score <= 0.4: return 'SHORT'
    return 'WAIT'

def rationale_text(action: str) -> str:
    if action == 'BUY':
        return 'Покупатели удержали цену у поддержки, спрос подбирает — ждём проталкивание выше к целям.'
    if action == 'SHORT':
        return 'Спрос выдыхается у сопротивления — ждём откат вниз к ближайшим уровням.'
    return 'Сигнал неочевиден: лучше дождаться ясного импульса.'

def build_signal(symbol: str, interval: str = '1d') -> dict:
    df = load_history_yf(symbol, period_years=3, interval=interval)
    feats = build_features(df)
    latest = feats.iloc[-1:]
    atr = float(latest['atr14'].iloc[-1])
    pivot = float(latest['pivot'].iloc[-1])
    px = float(df['close'].iloc[-1])
    score = 0.5
    if atr > 0:
        score = max(0.0, min(1.0, 0.5 + (px - pivot) / (2.5 * atr)))
    action = soft_to_action(score)
    r1 = float(latest['r1'].iloc[-1])
    s1 = float(latest['s1'].iloc[-1])
    if action == 'BUY':
        entry = px
        tp1 = max(px + 0.6*atr, r1)
        tp2 = max(px + 1.2*atr, pivot + (r1 - pivot)*1.5)
        sl = px - 1.0*atr
    elif action == 'SHORT':
        entry = px
        tp1 = min(px - 0.6*atr, s1)
        tp2 = min(px - 1.2*atr, pivot - (pivot - s1)*1.5)
        sl = px + 1.0*atr
    else:
        entry = px
        tp1 = px + 0.8*atr
        tp2 = px + 1.6*atr
        sl = px - 0.8*atr
    return {
        'symbol': symbol,
        'ts': datetime.now(timezone.utc).isoformat(),
        'horizon': 'swing',
        'action': action,
        'entry': round(entry, 2),
        'tp': [round(tp1, 2), round(tp2, 2)],
        'sl': round(sl, 2),
        'confidence': round(float(score), 3),
        'rationale_text': rationale_text(action),
        'expiry_ts': None
    }
