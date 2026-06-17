import os
import requests
import pandas as pd
import ta
from datetime import datetime, timezone

# Token & Chat ID dari GitHub Secrets
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Konfigurasi sinyal
SYMBOL = "bitcoin"          # id CoinCap: bitcoin, ethereum, solana, dll.
QUOTE = "usdt"              # quote currency (tether)
INTERVAL = "m15"            # m1, m5, m15, m30, h1, h2, h4, d1
LIMIT = 100                 # jumlah candle
RSI_LENGTH = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

def get_klines(base, quote, interval, limit):
    url = "https://api.coincap.io/v2/candles"
    params = {
        "exchange": "binance",
        "interval": interval,
        "baseId": base,
        "quoteId": quote,
        "limit": limit
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()["data"]
    # Urutkan dari lama ke baru
    data = sorted(data, key=lambda x: x["period"])
    df = pd.DataFrame(data)
    df["close"] = pd.to_numeric(df["close"])
    df["period"] = pd.to_datetime(df["period"], unit="ms")
    return df

def check_signal(df):
    rsi = ta.momentum.RSIIndicator(df["close"], window=RSI_LENGTH).rsi()
    prev_rsi = rsi.iloc[-2]
    last_rsi = rsi.iloc[-1]

    if pd.isna(prev_rsi) or pd.isna(last_rsi):
        return None, None

    if prev_rsi < RSI_OVERSOLD and last_rsi >= RSI_OVERSOLD:
        return "BUY", last_rsi
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
    print(f"[{datetime.now(timezone.utc)}] Fetching {SYMBOL}/{QUOTE} {INTERVAL} ...")
    df = get_klines(SYMBOL, QUOTE, INTERVAL, LIMIT)
    action, rsi_val = check_signal(df)

    if action:
        price = df["close"].iloc[-1]
        candle_time = df["period"].iloc[-1].strftime("%Y-%m-%d %H:%M UTC")
        msg = (
            f"🚨 *Sinyal {action} {SYMBOL.upper()}*\n"
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
