import os
import requests
import pandas as pd
import ta
from datetime import datetime, timezone

# --- SECRETS ---
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# --- KONFIGURASI SINYAL ---
PAIR = "XBTUSD"            # Kraken pair: XBTUSD (Bitcoin), ETHUSD, SOLUSD, dll.
INTERVAL = 15              # menit: 1, 5, 15, 30, 60, 240, 1440
LIMIT = 100                # jumlah candle
RSI_LENGTH = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

# =============== FUNGSI ===============

def get_klines(pair, interval, limit):
    url = "https://api.kraken.com/0/public/OHLC"
    params = {"pair": pair, "interval": interval}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    # Ambil data candle dari hasil
    ohlc = data["result"][pair]
    df = pd.DataFrame(ohlc, columns=[
        "time", "open", "high", "low", "close", "vwap", "volume", "count"
    ])
    df["close"] = pd.to_numeric(df["close"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    # Ambil LIMIT terakhir
    df = df.tail(limit).reset_index(drop=True)
    return df

def check_signal(df):
    rsi = ta.momentum.RSIIndicator(df["close"], window=RSI_LENGTH).rsi()
    prev_rsi = rsi.iloc[-2]
    last_rsi = rsi.iloc[-1]

    if pd.isna(prev_rsi) or pd.isna(last_rsi):
        return None, None

    # --- SINI KAMU BISA EDIT LOGIKA SINYAL SENDIRI ---
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
    print(f"[{datetime.now(timezone.utc)}] Fetching {PAIR} {INTERVAL}min...")
    try:
        df = get_klines(PAIR, INTERVAL, LIMIT)
        action, rsi_val = check_signal(df)
        if action:
            price = df["close"].iloc[-1]
            candle_time = df["time"].iloc[-1].strftime("%Y-%m-%d %H:%M UTC")
            msg = (
                f"🚨 *Sinyal {action} {PAIR}*\n"
                f"Harga: {price:.2f} USD\n"
                f"RSI: {rsi_val:.1f}\n"
                f"TF: {INTERVAL}menit\n"
                f"Candle: {candle_time}"
            )
            send_telegram(msg)
            print(f"✅ Sinyal terkirim: {action}")
        else:
            print(f"ℹ️ Tidak ada sinyal. RSI = {rsi_val:.1f}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
