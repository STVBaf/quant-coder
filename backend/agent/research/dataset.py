"""Materialize price + indicator datasets for the sandbox.

The sandbox has no network and no DB access, so before running agent code we
pull OHLCV from the (cached) DB, compute a standard indicator set, and write one
parquet per stock into a temp directory that the runner mounts read-only.
"""
import tempfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from market.services import fetch_daily_bars


def _bars_to_df(bars: list) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "open": [b.open for b in bars],
            "high": [b.high for b in bars],
            "low": [b.low for b in bars],
            "close": [b.close for b in bars],
            "volume": [b.volume for b in bars],
        },
        index=pd.to_datetime([b.date for b in bars]),
    )
    return df.sort_index()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Attach a standard indicator set. Agent code may use these columns or roll
    its own from OHLCV."""
    c = df["close"]

    # Moving averages
    for n in (5, 10, 20, 60):
        df[f"ma{n}"] = c.rolling(n).mean()
    df["ema12"] = c.ewm(span=12, adjust=False).mean()
    df["ema26"] = c.ewm(span=26, adjust=False).mean()

    # MACD
    df["macd"] = df["ema12"] - df["ema26"]
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # RSI (14)
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, 1e-9)
    df["rsi14"] = 100 - 100 / (1 + rs)

    # Bollinger (20, 2)
    ma20, std20 = c.rolling(20).mean(), c.rolling(20).std()
    df["boll_mid"] = ma20
    df["boll_up"] = ma20 + 2 * std20
    df["boll_low"] = ma20 - 2 * std20

    # ATR (14)
    prev_close = c.shift(1)
    tr = pd.concat([df["high"] - df["low"],
                    (df["high"] - prev_close).abs(),
                    (df["low"] - prev_close).abs()], axis=1).max(axis=1)
    df["atr14"] = tr.rolling(14).mean()

    # Momentum & volatility
    df["mom10"] = c.pct_change(10)
    df["ret1"] = c.pct_change()
    df["vol20"] = df["ret1"].rolling(20).std()

    return df


INDICATOR_COLS = [
    "open", "high", "low", "close", "volume",
    "ma5", "ma10", "ma20", "ma60", "ema12", "ema26",
    "macd", "macd_signal", "macd_hist", "rsi14",
    "boll_mid", "boll_up", "boll_low", "atr14",
    "mom10", "ret1", "vol20",
]


def materialize(codes: list[str], start: str | None = None,
                end: str | None = None, out_dir: Path | None = None) -> Path:
    """Fetch, enrich, and write one parquet per code. Returns the data dir."""
    end = end or date.today().isoformat()
    start = start or (date.today() - timedelta(days=365 * 3)).isoformat()
    out_dir = out_dir or Path(tempfile.mkdtemp(prefix="qdata_"))

    for code in codes:
        bars = fetch_daily_bars(code, start, end)
        if not bars:
            continue
        df = add_indicators(_bars_to_df(bars))
        df.to_parquet(out_dir / f"{code}.parquet")
    return out_dir


def describe_columns() -> list[dict]:
    """Human-readable column catalog, for the agent's `list_data_columns` tool."""
    desc = {
        "open/high/low/close/volume": "日线量价",
        "ma5/ma10/ma20/ma60": "简单移动均线",
        "ema12/ema26": "指数移动均线",
        "macd/macd_signal/macd_hist": "MACD 及信号线、柱",
        "rsi14": "相对强弱 RSI(14)",
        "boll_mid/boll_up/boll_low": "布林带中/上/下轨(20,2)",
        "atr14": "真实波幅均值 ATR(14)",
        "mom10": "10 日动量(收益率)",
        "ret1": "单日收益率",
        "vol20": "20 日收益波动率",
    }
    return [{"columns": k, "meaning": v} for k, v in desc.items()]
