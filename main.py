import os
import requests
import pandas as pd
import ta
from datetime import datetime, timezone

# Token & Chat ID dari GitHub Secrets (aman)
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SYMBOL = "BTCUSDT"       # Ganti dengan pair crypto yang kamu mau
INTERVAL = "15m"         # Timeframe: 1m, 5m, 15m, 1h, 4h, 1d
LIMIT = 100              # Jumlah candle untuk hitung indikator
RSI_LENGTH = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

def get_klines(symbol, interval, limit):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["close"] = pd.to_numeric(df["close"])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    return df

def check_signal(df):
    rsi = ta.rsi(df["close"], length=RSI_LENGTH)
    prev_rsi = rsi.iloc[-2]
    last_rsi = rsi.iloc[-1]

    if pd.isna(prev_rsi) or pd.isna(last_rsi):
        return None, None

    # Sinyal BUY: RSI naik dari bawah 30 ke atas 30
    if prev_rsi < RSI_OVERSOLD and last_rsi >= RSI_OVERSOLD:
        return "BUY", last_rsi
    # Sinyal SELL: RSI turun dari atas 70 ke bawah 70
    elif prev_rsi > RSI_OVERBOUGHT and last_rsi <= RSI_OVERBOUGHT:
        return "SELL", last_rsi
    return None, last_rsi

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

def main():
    print(f"[{datetime.now(timezone.utc)}] Fetching {SYMBOL} {INTERVAL} ...")
    df = get_klines(SYMBOL, INTERVAL, LIMIT)
    action, rsi_val = check_signal(df)

    if action:
        price = df["close"].iloc[-1]
        candle_time = df["open_time"].iloc[-1].strftime("%Y-%m-%d %H:%M UTC")
        msg = (
            f"🚨 *Sinyal {action} {SYMBOL}*\n"
            f"Harga: {price:.2f} USD\n"
            f"RSI: {rsi_val:.1f}\n"
            f"TF: {INTERVAL}\n"
            f"Candle: {candle_time}"
        )
        send_telegram(msg)
        print(f"✅ Sinyal terkirim: {action}")
    else:
        print(f"ℹ️ Tidak ada sinyal. RSI = {rsi_val:.1f}")

if __name__ == "__main__":
    main()
