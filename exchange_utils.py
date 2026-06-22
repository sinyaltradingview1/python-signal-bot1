import requests
import pandas as pd

def get_perpetual_symbols(min_volume_24h=1_000_000):
    url = "https://api.bybit.com/v5/market/instruments-info"
    params = {"category": "linear"}
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data["retCode"] != 0:
        raise Exception(f"Bybit API error: {data}")
    symbols = []
    for item in data["result"]["list"]:
        if item.get("quoteCoin") == "USDT" and item.get("status") == "Trading":
            try:
                vol = float(item.get("volume24h", 0))
                if vol >= min_volume_24h:
                    symbols.append(item["symbol"])
            except (ValueError, KeyError):
                continue
    return symbols

def get_klines(symbol, interval=15, limit=100):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data["retCode"] != 0:
        raise Exception(f"Bybit Kline error: {data}")
    candles = data["result"]["list"]
    df = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close", "volume", "turnover"])
    df = df.iloc[::-1].reset_index(drop=True)
    df["close"] = pd.to_numeric(df["close"])
    df["volume"] = pd.to_numeric(df["volume"])
    df["time"] = pd.to_datetime(pd.to_numeric(df["time"]), unit="ms")
    return df
