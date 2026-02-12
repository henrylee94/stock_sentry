"""
Data Manager - Unified real-time and historical stock data
Primary: Finnhub (real-time quote). Fallback: Yahoo Finance.
"""

import os
import time
import warnings
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import json

# Reduce yfinance noise (Failed to get ticker / possibly delisted are Yahoo issues, not Finnhub)
logging.getLogger("yfinance").setLevel(logging.WARNING)

import yfinance as yf
import pandas as pd

try:
    import finnhub
    FINNHUB_AVAILABLE = True
except ImportError:
    FINNHUB_AVAILABLE = False

def _load_env():
    env_file = Path('.env')
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip()

_load_env()

try:
    from core.rate_limiter import get_finnhub_limiter
    rate_limiter = get_finnhub_limiter()
except ImportError:
    rate_limiter = None

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
CACHE_SECONDS = 10
_cache: Dict[str, Dict[str, Any]] = {}
_cache_time: Dict[str, float] = {}


def _get_cached(symbol: str) -> Optional[Dict]:
    symbol = symbol.upper()
    if symbol not in _cache or symbol not in _cache_time:
        return None
    if time.time() - _cache_time[symbol] > CACHE_SECONDS:
        return None
    return _cache[symbol]


def _set_cached(symbol: str, data: Dict):
    symbol = symbol.upper()
    _cache[symbol] = data
    _cache_time[symbol] = time.time()


def _finnhub_quote(symbol: str) -> Optional[Dict]:
    if not FINNHUB_AVAILABLE or not FINNHUB_API_KEY:
        return None
    if rate_limiter and not rate_limiter.can_call():
        return None
    try:
        rate_limiter and rate_limiter.wait_if_needed()
        client = finnhub.Client(api_key=FINNHUB_API_KEY)
        q = client.quote(symbol)
        if q.get('c') is None:
            return None
        return {
            'current_price': float(q.get('c', 0)),
            'change': float(q.get('d', 0)),
            'change_pct': float(q.get('dp', 0)),
            'high': float(q.get('h', 0)),
            'low': float(q.get('l', 0)),
            'open': float(q.get('o', 0)),
            'previous_close': float(q.get('pc', 0)),
            'source': 'Finnhub',
            'timestamp': int(q.get('t', 0)),
        }
    except Exception as e:
        print(f"Finnhub quote error for {symbol}: {e}")
        return None


def _yahoo_extended(symbol: str) -> Optional[Dict]:
    try:
        warnings.filterwarnings('ignore')
        ticker = yf.Ticker(symbol)
        hist_data = ticker.history(period="1mo", interval="1d")
        # prepost=True: include pre-market and after-hours so data works 24/7
        today_data = ticker.history(period="1d", interval="5m", prepost=True)
        if hist_data.empty or len(hist_data) < 2:
            return None
        # Use latest from intraday (pre/post) if available, else last day close
        if not today_data.empty and len(today_data) >= 1:
            current_price = float(today_data['Close'].iloc[-1])
            last_update = today_data.index[-1]
            session_note = "extended"  # pre-market or after-hours
        else:
            current_price = float(hist_data['Close'].iloc[-1])
            last_update = hist_data.index[-1]
            session_note = "regular"
        prev_close = float(hist_data['Close'].iloc[-2])
        price_change_pct = ((current_price - prev_close) / prev_close) * 100
        # EMAs
        ema_5 = float(hist_data['Close'].ewm(span=5, adjust=False).mean().iloc[-1])
        ema_9 = float(hist_data['Close'].ewm(span=9, adjust=False).mean().iloc[-1])
        ema_21 = float(hist_data['Close'].ewm(span=21, adjust=False).mean().iloc[-1])
        ema_50 = float(hist_data['Close'].ewm(span=min(50, len(hist_data)), adjust=False).mean().iloc[-1]) if len(hist_data) >= 21 else None
        
        # RSI
        delta = hist_data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs)).iloc[-1]) if not rs.empty and not pd.isna(rs.iloc[-1]) else 50.0
        
        # Support/Resistance (20-day)
        recent_high = float(hist_data['High'].tail(20).max())
        recent_low = float(hist_data['Low'].tail(20).min())
        
        # Bollinger Bands (20-period SMA ± 2 std dev)
        sma_20 = hist_data['Close'].rolling(20).mean()
        std_20 = hist_data['Close'].rolling(20).std()
        bb_upper = float((sma_20 + (2 * std_20)).iloc[-1]) if not sma_20.empty and not pd.isna(sma_20.iloc[-1]) else 0
        bb_middle = float(sma_20.iloc[-1]) if not sma_20.empty and not pd.isna(sma_20.iloc[-1]) else 0
        bb_lower = float((sma_20 - (2 * std_20)).iloc[-1]) if not sma_20.empty and not pd.isna(sma_20.iloc[-1]) else 0
        
        # Donchian Channels
        donchian_upper_20 = float(hist_data['High'].rolling(20).max().iloc[-1])
        donchian_lower_20 = float(hist_data['Low'].rolling(20).min().iloc[-1])
        donchian_upper_40 = float(hist_data['High'].rolling(40).max().iloc[-1]) if len(hist_data) >= 40 else donchian_upper_20
        donchian_lower_40 = float(hist_data['Low'].rolling(40).min().iloc[-1]) if len(hist_data) >= 40 else donchian_lower_20
        
        # ATR (Average True Range, 14-period)
        high_low = hist_data['High'] - hist_data['Low']
        high_close = (hist_data['High'] - hist_data['Close'].shift()).abs()
        low_close = (hist_data['Low'] - hist_data['Close'].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = float(true_range.rolling(14).mean().iloc[-1]) if not true_range.empty and not pd.isna(true_range.rolling(14).mean().iloc[-1]) else 0
        
        # 52-week high/low (252 trading days, or use available data)
        if len(hist_data) >= 252:
            week_52_high = float(hist_data['High'].rolling(252).max().iloc[-1])
            week_52_low = float(hist_data['Low'].rolling(252).min().iloc[-1])
        else:
            week_52_high = float(hist_data['High'].max())
            week_52_low = float(hist_data['Low'].min())
        week_high = float(hist_data['High'].tail(5).max())
        week_low = float(hist_data['Low'].tail(5).min())
        day_high = float(today_data['High'].max()) if not today_data.empty else recent_high
        day_low = float(today_data['Low'].min()) if not today_data.empty else recent_low
        avg_volume = float(hist_data['Volume'].tail(20).mean()) if hist_data['Volume'].tail(20).mean() > 0 else 1.0
        current_volume = int(today_data['Volume'].iloc[-1]) if not today_data.empty else int(hist_data['Volume'].iloc[-1])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        if current_price > ema_9 > ema_21:
            trend, trend_en = "强势看涨", "bullish"
        elif current_price < ema_9 < ema_21:
            trend, trend_en = "强势看跌", "bearish"
        elif current_price > ema_9:
            trend, trend_en = "弱势看涨", "bullish"
        else:
            trend, trend_en = "弱势看跌", "bearish"
        last_update_str = last_update.strftime('%m/%d %H:%M') if hasattr(last_update, 'strftime') else str(last_update)
        return {
            'symbol': symbol.upper(),
            'session': session_note,
            'current_price': current_price,
            'ema_5': ema_5,
            'ema_9': ema_9,
            'ema_21': ema_21,
            'ema_50': ema_50,
            'rsi': rsi,
            'resistance': recent_high,
            'support': recent_low,
            'week_high': week_high,
            'week_low': week_low,
            'day_high': day_high,
            'day_low': day_low,
            'avg_volume': int(avg_volume),
            'current_volume': current_volume,
            'volume_ratio': volume_ratio,
            'trend': trend,
            'trend_en': trend_en,
            'price_change_pct': price_change_pct,
            'last_update': last_update_str,
            'data_source': 'Yahoo Finance (incl. pre/post)' if session_note == 'extended' else 'Yahoo Finance',
            # New indicators
            'bb_upper': bb_upper,
            'bb_middle': bb_middle,
            'bb_lower': bb_lower,
            'donchian_upper_20': donchian_upper_20,
            'donchian_lower_20': donchian_lower_20,
            'donchian_upper_40': donchian_upper_40,
            'donchian_lower_40': donchian_lower_40,
            'atr': atr,
            'week_52_high': week_52_high,
            'week_52_low': week_52_low,
        }
    except Exception as e:
        print(f"Yahoo extended error for {symbol}: {e}")
        return None


def get_extended_stock_data(symbol: str, use_cache: bool = True) -> Optional[Dict]:
    """Finnhub first; only call Yahoo if Finnhub fails (or not configured)."""
    symbol = symbol.upper()
    if use_cache:
        cached = _get_cached(symbol)
        if cached is not None:
            print(f"[DATA] {symbol} ← cache ({cached.get('data_source', '?')})")
            return cached

    # 1st: Try Finnhub only. If we get a quote, return it and do not call Yahoo.
    fq = _finnhub_quote(symbol) if FINNHUB_AVAILABLE and FINNHUB_API_KEY else None
    if fq:
        print(f"[DATA] {symbol} ← Finnhub only | ${fq['current_price']:.2f}")
        out = {
            'symbol': symbol,
            'session': 'regular',
            'current_price': fq['current_price'],
            'ema_9': fq['current_price'],
            'ema_21': fq['current_price'],
            'ema_50': None,
            'rsi': 50.0,
            'resistance': fq['high'],
            'support': fq['low'],
            'week_high': fq['high'],
            'week_low': fq['low'],
            'day_high': fq['high'],
            'day_low': fq['low'],
            'avg_volume': 0,
            'current_volume': 0,
            'volume_ratio': 1.0,
            'trend': 'neutral',
            'trend_en': 'neutral',
            'price_change_pct': fq['change_pct'],
            'last_update': str(fq.get('timestamp', '')),
            'data_source': 'Finnhub',
        }
        _set_cached(symbol, out)
        return out

    # 2nd: Finnhub failed or not configured → use Yahoo only
    yahoo_data = _yahoo_extended(symbol)
    if yahoo_data is not None:
        print(f"[DATA] {symbol} ← Yahoo only | ${yahoo_data['current_price']:.2f}")
        _set_cached(symbol, yahoo_data)
        return yahoo_data
    return None


class DataManager:
    @staticmethod
    def get_extended_stock_data(symbol: str, use_cache: bool = True) -> Optional[Dict]:
        return get_extended_stock_data(symbol, use_cache=use_cache)

    @staticmethod
    def get_realtime_quote(symbol: str) -> Optional[Dict]:
        return get_extended_stock_data(symbol, use_cache=True)


__all__ = ['get_extended_stock_data', 'DataManager']
