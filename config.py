from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class AppConfig(BaseModel):
    tickers: list[str]
    horizon: str = 'swing'
    data_lookback_years: int = 3

def get_config() -> AppConfig:
    tickers_env = os.getenv('TICKERS','AAPL,MSFT,NVDA')
    tickers = [t.strip().upper() for t in tickers_env.split(',') if t.strip()]
    horizon = os.getenv('HORIZON','swing').lower().strip()
    lookback = int(os.getenv('DATA_LOOKBACK_YEARS','3'))
    return AppConfig(tickers=tickers, horizon=horizon, data_lookback_years=lookback)
