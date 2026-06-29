"""Trading strategies.

Each strategy takes a price DataFrame (indexed by date, with a `close` column)
plus params, and returns a position Series: 1.0 = hold long, 0.0 = flat.
Signals are shifted by one bar in the engine, so a signal on day T is acted on
at day T+1's open — no look-ahead bias.
"""
import pandas as pd


def ma_cross(df: pd.DataFrame, fast: int = 5, slow: int = 20) -> pd.Series:
    """Dual moving average: long while fast MA is above slow MA."""
    fast_ma = df["close"].rolling(fast).mean()
    slow_ma = df["close"].rolling(slow).mean()
    return (fast_ma > slow_ma).astype(float)


def rsi(df: pd.DataFrame, period: int = 14, low: int = 30, high: int = 70) -> pd.Series:
    """RSI mean-reversion: buy when oversold, sell when overbought, else hold."""
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, 1e-9)
    rsi_val = 100 - 100 / (1 + rs)

    pos = pd.Series(index=df.index, dtype=float)
    pos[rsi_val < low] = 1.0   # oversold -> enter
    pos[rsi_val > high] = 0.0  # overbought -> exit
    return pos.ffill().fillna(0.0)


def bollinger(df: pd.DataFrame, period: int = 20, k: float = 2.0) -> pd.Series:
    """Bollinger bands: buy on lower-band touch, exit on middle-band return."""
    mid = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std()
    lower = mid - k * std

    pos = pd.Series(index=df.index, dtype=float)
    pos[df["close"] < lower] = 1.0  # touch lower band -> enter
    pos[df["close"] > mid] = 0.0    # back above mid -> exit
    return pos.ffill().fillna(0.0)


REGISTRY = {
    "ma_cross": ma_cross,
    "rsi": rsi,
    "bollinger": bollinger,
}
