import os
from datetime import datetime, timezone
import time
from exchange_utils import get_perpetual_symbols, get_24hr_volumes, get_klines
from telegram_utils import send_telegram
from signals.rsi_signal import check_rsi
from signals.volume_spike import check_volume_spike

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

INTERVAL = "15m"       # format Binance: 1m,5m,15m,1h,4h,1d
LIMIT = 100
MAX_PAIRS = 30
MIN_VOLUME_24H = 2_000_000  # 2 juta USD

def main():
    print(f"[{datetime.now(timezone.utc)}] Autoscan Binance Futures mulai...")
    # Ambil semua symbol perpetual USDT
    all_symbols = get_perpetual_symbols()
    # Ambil volume 24h untuk filter
    volumes = get_24hr_volumes(all_symbols)
    # Filter berdasarkan volume dan urutkan terbesar
    filtered = [s for s in all_symbols if volumes.get(s, 0) >= MIN_VOLUME_24H]
    filtered.sort(key=lambda s: volumes.get(s, 0), reverse=True)
    symbols = filtered[:MAX_PAIRS]

    print(f"Scanning {len(symbols)} pasangan (vol > {MIN_VOLUME_24H/1e6:.1f}M USD): {', '.join(symbols[:5])}...")

    for symbol in symbols:
        try:
            df = get_klines(symbol, interval=INTERVAL, limit=LIMIT)
            all_signals = []
            all_signals.extend(check_rsi(df))
            all_signals.extend(check_volume_spike(df))

            for s in all_signals:
                if "rsi" in s:
                    msg = (
                        f"🚨 *{s['type']} {symbol}*\n"
                        f"Harga: {s['price']:.4f}\n"
                        f"RSI: {s['rsi']:.1f}\n"
                        f"TF: {INTERVAL}\n"
                        f"Candle: {s['candle_time'].strftime('%Y-%m-%d %H:%M UTC')}"
                    )
                elif "volume" in s:
                    msg = (
                        f"📊 *{s['type']} {symbol}*\n"
                        f"Harga: {s['price']:.4f}\n"
                        f"Volume: {s['volume']:.2f}\n"
                        f"Rasio vs Avg: {s['ratio']:.1f}x\n"
                        f"TF: {INTERVAL}\n"
                        f"Candle: {s['candle_time'].strftime('%Y-%m-%d %H:%M UTC')}"
                    )
                else:
                    msg = f"{s['type']} {symbol} @ {s['price']}"
                send_telegram(TELEGRAM_TOKEN, CHAT_ID, msg)
                print(f"✅ {symbol}: {s['type']}")
            time.sleep(0.2)
        except Exception as e:
            print(f"❌ Gagal proses {symbol}: {e}")
            continue

    print("Scan selesai.")

if __name__ == "__main__":
    main()
