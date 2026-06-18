import requests
import pandas as pd

def get_perpetual_symbols(min_volume_24h=1_000_000):
    """
    Ambil semua symbol USDT perpetual dari Binance Futures,
    dengan volume 24h minimal (default 1 juta USD).
    """
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    symbols = []
    for item in data["symbols"]:
        if item["contractType"] == "PERPETUAL" and item["quoteAsset"] == "USDT" and item["status"] == "TRADING":
            # Ambil volume 24h dari ticker 24hr (perlu request lagi)
            # Untuk efisiensi, kita ambil dulu semua symbol, lalu filter nanti
            symbols.append(item["symbol"])
    return symbols  # Kita filter volume nanti di main()

def get_24hr_volumes(symbols):
    """
    Ambil volume 24h untuk banyak symbol (batch).
    """
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    vol = {}
    for ticker in data:
        if ticker["symbol"] in symbols:
            vol[ticker["symbol"]] = float(ticker["quoteVolume"])  # volume dalam USDT
    return vol

def get_klines(symbol, interval=15, limit=100):
    """
    Ambil candle Binance Futures.
    interval: '1m','5m','15m','30m','1h','4h','1d', dll.
    """
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["close"] = pd.to_numeric(df["close"])
    df["volume"] = pd.to_numeric(df["volume"])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    return df
