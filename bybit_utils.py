import requests
import pandas as pd

def get_perpetual_symbols(min_volume_24h=1_000_000):
    """
    Ambil semua symbol linear (USDT perpetual) dari Bybit,
    dengan volume 24h minimal (default 1 juta USD).
    """
    url = "https://api.bybit.com/v5/market/instruments-info"
    params = {"category": "linear"}
    resp = requests.get(url, params=params)
    data = resp.json()
    if data["retCode"] != 0:
        raise Exception(f"Gagal ambil daftar: {data}")
    symbols = []
    for item in data["result"]["list"]:
        # Hanya USDT perpetual, abaikan inverse atau QUANTO
        if item["quoteCoin"] == "USDT" and item["status"] == "Trading":
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
    resp = requests.get(url, params=params)
    data = resp.json()
    if data["retCode"] != 0:
        raise Exception(f"Gagal ambil kline {symbol}: {data}")
    candles = data["result"]["list"]
    # Bybit mengembalikan dari terbaru ke terlama, balik jadi asc
    df = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close", "volume", "turnover"])
    df = df.iloc[::-1].reset_index(drop=True)
    df["close"] = pd.to_numeric(df["close"])
    df["volume"] = pd.to_numeric(df["volume"])
    df["time"] = pd.to_datetime(pd.to_numeric(df["time"]), unit="ms")
    return df
