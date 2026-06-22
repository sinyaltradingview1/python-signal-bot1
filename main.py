import os
import time
from datetime import datetime, timezone
from exchange_utils import get_perpetual_symbols, get_klines
from telegram_utils import send_telegram
from signals.rsi_signal import check_rsi
from signals.volume_spike import check_volume_spike

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

INTERVAL = 15          # Bybit pakai integer (menit)
LIMIT = 100
MAX_PAIRS = 20
MIN_VOLUME_24H = 2_000_000

def main():
    print(f"[{datetime.now(timezone.utc)}] Autoscan Bybit perpetual...")
    symbols = get_perpetual_symbols(min_volume_24h=MIN_VOLUME_24H)
    symbols = symbols[:MAX_PAIRS]

    for sym in symbols:
        try:
            df = get_klines(sym, interval=INTERVAL, limit=LIMIT)
            all_signals = []
            all_signals.extend(check_rsi(df))
            all_signals.extend(check_volume_spike(df))

            for s in all_signals:
                if "rsi" in s:
                    msg = (
                        f"🚨 *{s['type']} {sym}*\n"
                        f"Harga: {s['price']:.4f}\n"
                        f"RSI: {s['rsi']:.1f}\n"
                        f"TF: {INTERVAL}menit\n"
                        f"Candle: {s['candle_time'].strftime('%Y-%m-%d %H:%M UTC')}"
                    )
                else:
                    msg = (
                        f"📊 *{s['type']} {sym}*\n"
                        f"Harga: {s['price']:.4f}\n"
                        f"Volume: {s['volume']:.2f}\n"
                        f"Rasio vs Avg: {s['ratio']:.1f}x\n"
                        f"TF: {INTERVAL}menit\n"
                        f"Candle: {s['candle_time'].strftime('%Y-%m-%d %H:%M UTC')}"
                    )
                send_telegram(TELEGRAM_TOKEN, CHAT_ID, msg)
                print(f"✅ {sym}: {s['type']}")
            time.sleep(0.3)
        except Exception as e:
            print(f"❌ {sym}: {e}")

if __name__ == "__main__":
    main()
