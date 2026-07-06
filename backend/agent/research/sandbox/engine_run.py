"""Self-contained vectorized backtest, mounted read-only into the sandbox.

Metrics mirror backend/backtest/engine.py exactly so sandbox results are
directly comparable to the app's own backtests. Kept dependency-free (only
pandas/numpy) because the sandbox has no Django and no network.
"""
import numpy as np
import pandas as pd

TRADING_DAYS = 252


def run_signals(df: pd.DataFrame, signals: pd.Series) -> dict:
    """Run a position series (1.0 long / 0.0 flat) through the engine.

    Positions are shifted one bar: today's signal is realized on tomorrow's
    return (no look-ahead bias) — identical to the app engine.
    """
    close = df["close"]
    position = pd.Series(signals, index=df.index).fillna(0.0).clip(0.0, 1.0)

    daily_ret = close.pct_change().fillna(0.0)
    strat_ret = position.shift(1).fillna(0.0) * daily_ret
    equity = (1 + strat_ret).cumprod()

    total_return = equity.iloc[-1] - 1
    peak = equity.cummax()
    max_drawdown = ((equity - peak) / peak).min()
    std = strat_ret.std()
    sharpe = (strat_ret.mean() / std * np.sqrt(TRADING_DAYS)) if std > 0 else 0.0
    active = strat_ret[strat_ret != 0]
    win_rate = (active > 0).mean() if len(active) else 0.0

    flips = position.diff().fillna(position)
    trade_count = int((flips != 0).sum())

    return {
        "metrics": {
            "total_return": round(float(total_return), 4),
            "max_drawdown": round(float(max_drawdown), 4),
            "sharpe": round(float(sharpe), 2),
            "win_rate": round(float(win_rate), 4),
        },
        "trade_count": trade_count,
        "equity_curve": [
            [d.strftime("%Y-%m-%d"), round(float(v), 4)] for d, v in equity.items()
        ],
    }
