import os
import requests
import pandas as pd
import ta
from datetime import datetime, timezone
import time

# --- KONFIGURASI SECRETS ---
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# --- KONFIGURASI SINYAL ---
COIN_ID = "bitcoin"              # ID CoinGecko: bitcoin, ethereum, solana, dll.
VS_CURRENCY = "usd"
INTERVAL_MINUTES = 15            # Interval candle dalam menit (15m)
LIMIT = 100                      # Jumlah candle
RSI_LENGTH = 14
RSI_OVERSOLD = 99
RSI_OVERBOUGHT = 70

# ================== FUNGSI ==================

def get_klines(coin_id, vs_currency, minutes, limit):
    # CoinGecko public API untuk OHLC
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
    params = {
        "vs_currency": vs_currency,
        "days": "1" if minutes <= 30 else "7",  # penyesuaian otomatis
    }
    # Karena CoinGecko tidak punya parameter interval selain daily,
    # kita ambil data 1 hari penuh lalu resample sendiri.
    # Alternatif: gunakan CoinGecko market_chart untuk granularity.
    # Lebih mudah pakai fungsi market_chart.
    
    # Kita pakai endpoint market_chart dengan granularity dalam detik
    granularity = minutes * 60
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": "7",  # ambil 7 hari terakhir
        "interval": "daily" if minutes > 120 else "hourly" if minutes > 15 else "15m"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    prices = data["prices"]
    df = pd.DataFrame(prices, columns=["timestamp", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    # CoinGecko hanya memberikan harga close, jadi kita hanya bisa RSI dari close
    df.set_index("timestamp", inplace=True)
    # Resample ke interval yang diinginkan (jika diperlukan)
    df = df.resample(f"{minutes}min").last().dropna()
    df.reset_index(inplace=True)
    # Ambil sebanyak LIMIT
    df = df.tail(LIMIT)
    return df

def check_signal(df):
    # Hitung RSI dari close
    rsi = ta.momentum.RSIIndicator(df["close"], window=RSI_LENGTH).rsi()
    prev_rsi = rsi.iloc[-2]
    last_rsi = rsi.iloc[-1]

    if pd.isna(prev_rsi) or pd.isna(last_rsi):
        return None, None

    # --- SINI KAMU BISA EDIT LOGIKA SINYAL SESUAI KEINGINAN ---
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
    print(f"[{datetime.now(timezone.utc)}] Mengambil data {COIN_ID}...")
    try:
        df = get_klines(COIN_ID, VS_CURRENCY, INTERVAL_MINUTES, LIMIT)
        action, rsi_val = check_signal(df)
        if action:
            price = df["close"].iloc[-1]
            candle_time = df["timestamp"].iloc[-1].strftime("%Y-%m-%d %H:%M UTC")
            msg = (
                f"🚨 *Sinyal {action} {COIN_ID.upper()}*\n"
                f"Harga: {price:.2f} USD\n"
                f"RSI: {rsi_val:.1f}\n"
                f"TF: {INTERVAL_MINUTES}menit\n"
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
