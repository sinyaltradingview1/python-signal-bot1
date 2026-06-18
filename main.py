import os
import requests
import pandas as pd
import ta
from datetime import datetime, timezone

# --- SECRETS ---
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# --- KONFIGURASI ---
PAIR = "XXBTZUSD"
INTERVAL = 15
LIMIT = 100

def get_klines(pair, interval, limit):
    url = "https://api.kraken.com/0/public/OHLC"
    params = {"pair": pair, "interval": interval}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    if data["error"]:
        raise Exception(f"Kraken API error: {data['error']}")
    result = data["result"]
    if not result:
        raise Exception(f"Tidak ada data untuk pasangan {pair}")
    ohlc_key = list(result.keys())[0]
    ohlc = result[ohlc_key]
    df = pd.DataFrame(ohlc, columns=[
        "time", "open", "high", "low", "close", "vwap", "volume", "count"
    ])
    df["close"] = pd.to_numeric(df["close"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.tail(limit).reset_index(drop=True)
    return df

def check_signal(df):
    # TEST MODE - selalu kirim sinyal BUY
    return "BUY", 99.9

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

def main():
    print(f"[{datetime.now(timezone.utc)}] Fetching {PAIR} {INTERVAL}min...")
    try:
        df = get_klines(PAIR, INTERVAL, LIMIT)
        action, rsi_val = check_signal(df)
        price = df["close"].iloc[-1]
        candle_time = df["time"].iloc[-1].strftime("%Y-%m-%d %H:%M UTC")
        msg = (
            f"🚨 *TEST SINYAL {action} {PAIR}*\n"
            f"Harga: {price:.2f} USD\n"
            f"RSI: {rsi_val:.1f}\n"
            f"TF: {INTERVAL}menit\n"
            f"Candle: {candle_time}"
        )
        send_telegram(msg)
        print(f"✅ Sinyal terkirim: {action}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
