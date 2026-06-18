import os
import requests
import pandas as pd
from datetime import datetime, timezone
from signals.rsi_signal import check_rsi
from signals.volume_spike import check_volume_spike

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
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
    df["volume"] = pd.to_numeric(df["volume"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.tail(limit).reset_index(drop=True)
    return df

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
        all_signals = []
        all_signals.extend(check_rsi(df))
        all_signals.extend(check_volume_spike(df))
        # nanti tinggal tambah all_signals.extend(check_ema(df)) dll.

        for s in all_signals:
            if "rsi" in s:
                msg = (
                    f"🚨 *{s['type']} {PAIR}*\n"
                    f"Harga: {s['price']:.2f} USD\n"
                    f"RSI: {s['rsi']:.1f}\n"
                    f"TF: {INTERVAL}menit\n"
                    f"Candle: {s['candle_time'].strftime('%Y-%m-%d %H:%M UTC')}"
                )
            else:
                msg = (
                    f"📊 *{s['type']} {PAIR}*\n"
                    f"Harga: {s['price']:.2f} USD\n"
                    f"Volume: {s['volume']:.2f}\n"
                    f"Rasio vs Avg: {s['ratio']:.1f}x\n"
                    f"TF: {INTERVAL}menit\n"
                    f"Candle: {s['candle_time'].strftime('%Y-%m-%d %H:%M UTC')}"
                )
            send_telegram(msg)
            print(f"✅ Terkirim: {s['type']}")

        if not all_signals:
            print("ℹ️ Tidak ada sinyal terpicu.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
