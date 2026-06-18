import requests
import pandas as pd

def get_perpetual_symbols(min_volume_24h=1_000_000):
    """
    Ambil semua symbol linear (USDT perpetual) dari Bybit,
    dengan volume 24h minimal (default 1 juta USD).
    """
    url = "https://api.bybit.com/v5/market/instruments-info"
    params = {"category": "linear"}
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TradingBot/1.0)",
        "Accept": "application/json"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    
    # Cek status code
    if resp.status_code != 200:
        raise Exception(f"HTTP {resp.status_code}: {resp.text}")
    
    # Coba parsing JSON
    try:
        data = resp.json()
    except Exception as e:
        raise Exception(f"Invalid JSON: {resp.text}")
    
    # Cek retCode dari Bybit
    if data.get("retCode") != 0:
        raise Exception(f"Bybit API error: {data}")
    
    symbols = []
    for item in data["result"]["list"]:
        if item.get("quoteCoin") == "USDT" and item.get("status") == "Trading":
            try:
                vol = float(item["volume24h"])
                if vol >= min_volume_24h:
                    symbols.append(item["symbol"])
            except (ValueError, KeyError):
                continue
    return symbols

def get_klines(symbol, interval=15, limit=100):
    """
    Ambil candle Bybit perpetual (linear).
    interval dalam menit: 1,5,15,30,60,240,...
    """
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TradingBot/1.0)",
        "Accept": "application/json"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    
    if resp.status_code != 200:
        raise Exception(f"HTTP {resp.status_code}: {resp.text}")
    
    try:
        data = resp.json()
    except Exception as e:
        raise Exception(f"Invalid JSON: {resp.text}")
    
    if data.get("retCode") != 0:
        raise Exception(f"Bybit API error: {data}")
    
    candles = data["result"]["list"]
    df = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close", "volume", "turnover"])
    df = df.iloc[::-1].reset_index(drop=True)  # balik urutan ke ascending
    df["close"] = pd.to_numeric(df["close"])
    df["volume"] = pd.to_numeric(df["volume"])
    df["time"] = pd.to_datetime(pd.to_numeric(df["time"]), unit="ms")
    return df
