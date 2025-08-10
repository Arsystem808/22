import os, sys, pathlib, importlib.util
import streamlit as st

BASE_DIR = pathlib.Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / 'src'
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

try:
    from src.common.config import get_config
except Exception:
    cfg_path = SRC_DIR / 'common' / 'config.py'
    if not cfg_path.exists():
        st.error(f'Не найден {cfg_path}. Проверь, что он в репозитории.')
        st.stop()
    spec = importlib.util.spec_from_file_location('capintel_config', str(cfg_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    get_config = mod.get_config  # type: ignore

from src.signals.signal_engine import build_signal

cfg = get_config()

st.set_page_config(page_title='US Stocks — AI Signals (Cloud)', layout='wide')
st.title('US Stocks — AI Signals')
st.caption('3 тикера • 3 года истории • кэш данных. BUY / SHORT / WAIT + уровни.')

tickers = st.text_input('Tickers (comma-separated)', value=','.join(cfg.tickers)).upper()
tickers_list = [t.strip() for t in tickers.split(',') if t.strip()]

colA, colB = st.columns([1,3])

with colA:
    selected = st.selectbox('Выберите тикер', tickers_list, index=0 if tickers_list else None)
    if st.button('Сгенерировать сигнал'):
        if selected:
            sig = build_signal(selected, interval='1d')
            st.session_state['latest_signal'] = sig

sig = st.session_state.get('latest_signal')
with colB:
    if sig:
        st.subheader(f"Сигнал для {sig['symbol']}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Действие', sig['action'])
        c2.metric('Entry', sig['entry'])
        c3.metric('TP1', sig['tp'][0])
        c4.metric('TP2', sig['tp'][1])
        st.metric('SL', sig['sl'])
        st.write(f"**Уверенность:** {sig['confidence']:.2f}")
        st.write(sig['rationale_text'])
    else:
        st.info('Выберите тикер и нажмите «Сгенерировать сигнал».')
