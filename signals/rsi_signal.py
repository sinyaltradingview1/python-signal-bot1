import pandas as pd
import ta

def check_rsi(df, length=14, oversold=30, overbought=70):
    rsi = ta.momentum.RSIIndicator(df["close"], window=length).rsi()
    prev = rsi.iloc[-2]
    last = rsi.iloc[-1]
    if pd.isna(prev) or pd.isna(last):
        return []
    signals = []
    if prev < oversold and last >= oversold:
        signals.append({
            "type": "BUY (RSI)",
            "price": df["close"].iloc[-1],
            "rsi": last,
            "candle_time": df["time"].iloc[-1]
        })
    elif prev > overbought and last <= overbought:
        signals.append({
            "type": "SELL (RSI)",
            "price": df["close"].iloc[-1],
            "rsi": last,
            "candle_time": df["time"].iloc[-1]
        })
    return signals
