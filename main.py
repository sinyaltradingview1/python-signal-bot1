import os
from datetime import datetime, timezone
import time
from bybit_utils import get_perpetual_symbols, get_klines
from telegram_utils import send_telegram
from signals.rsi_signal import check_rsi
from signals.volume_spike import check_volume_spike

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

INTERVAL = 15
LIMIT = 100
MAX_PAIRS = 30  # batasi jumlah coin yang discan per run
# Konfigurasi filter volume (24h)
MIN_VOLUME_24H = 2_000_000  # 2 juta USD

def main():
    print(f"[{datetime.now(timezone.utc)}] Autoscan Bybit Perpetual mulai...")
    # Ambil daftar pasangan USDT dengan volume cukup
    symbols = get_perpetual_symbols(min_volume_24h=MIN_VOLUME_24H)
    # Potong maksimal MAX_PAIRS
    symbols = symbols[:MAX_PAIRS]
    print(f"Scanning {len(symbols)} pasangan (vol > {MIN_VOLUME_24H/1e6:.1f}M USD): {', '.join(symbols[:5])}...")

    for symbol in symbols:
        try:
            df = get_klines(symbol, interval=INTERVAL, limit=LIMIT)
            # Kumpulkan sinyal dari berbagai modul
            all_signals = []
            all_signals.extend(check_rsi(df))
            all_signals.extend(check_volume_spike(df))
            # Nanti tambah: all_signals.extend(check_macd(df)), dll.

            for s in all_signals:
                # Format pesan sesuai tipe
                if "rsi" in s:
                    msg = (
                        f"🚨 *{s['type']} {symbol}*\n"
                        f"Harga: {s['price']:.4f}\n"
                        f"RSI: {s['rsi']:.1f}\n"
                        f"TF: {INTERVAL}menit\n"
                        f"Candle: {s['candle_time'].strftime('%Y-%m-%d %H:%M UTC')}"
                    )
                elif "volume" in s:
                    msg = (
                        f"📊 *{s['type']} {symbol}*\n"
                        f"Harga: {s['price']:.4f}\n"
                        f"Volume: {s['volume']:.2f}\n"
                        f"Rasio vs Avg: {s['ratio']:.1f}x\n"
                        f"TF: {INTERVAL}menit\n"
                        f"Candle: {s['candle_time'].strftime('%Y-%m-%d %H:%M UTC')}"
                    )
                else:
                    # format fallback
                    msg = f"{s['type']} {symbol} @ {s['price']}"
                send_telegram(TELEGRAM_TOKEN, CHAT_ID, msg)
                print(f"✅ {symbol}: {s['type']}")
            # Jeda kecil biar sopan ke API
            time.sleep(0.2)
        except Exception as e:
            print(f"❌ Gagal proses {symbol}: {e}")
            continue

    print("Scan selesai.")

if __name__ == "__main__":
    main()
