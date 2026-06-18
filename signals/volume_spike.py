def check_volume_spike(df, window=20, multiplier=2.0):
    if len(df) < window + 1:
        return []
    recent_vol = df["volume"].iloc[-1]
    avg_vol = df["volume"].iloc[-(window+1):-1].mean()
    if avg_vol == 0:
        return []
    ratio = recent_vol / avg_vol
    if ratio >= multiplier:
        return [{
            "type": "VOL SPIKE",
            "price": df["close"].iloc[-1],
            "volume": recent_vol,
            "ratio": ratio,
            "candle_time": df["time"].iloc[-1]
        }]
    return []
