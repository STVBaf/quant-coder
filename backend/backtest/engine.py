"""Vectorized backtest engine.

Given daily bars and a strategy, compute the equity curve and performance
metrics. Positions are shifted one bar to avoid look-ahead: today's signal is
realized against tomorrow's return.
"""
import numpy as np
import pandas as pd

from .strategies import REGISTRY

TRADING_DAYS = 252


def run(bars: list, kind: str, params: dict) -> dict:
    """Run a backtest and return metrics, equity curve, and trade markers."""
    if kind not in REGISTRY:
        raise ValueError(f"unknown strategy: {kind}")
    if len(bars) < 30:
        raise ValueError("not enough data to backtest (need >= 30 bars)")

    df = pd.DataFrame(
        {"close": [b.close for b in bars]},
        index=pd.to_datetime([b.date for b in bars]),
    )

    position = REGISTRY[kind](df, **params)
    # Act on the next bar; strategy returns are position(t-1) * return(t).
    daily_ret = df["close"].pct_change().fillna(0.0)
    strat_ret = position.shift(1).fillna(0.0) * daily_ret

    equity = (1 + strat_ret).cumprod()
    metrics = _metrics(strat_ret, equity)
    trades = _trades(position, df)

    return {
        "metrics": metrics,
        "equity_curve": [
            [d.strftime("%Y-%m-%d"), round(v, 4)] for d, v in equity.items()
        ],
        "trades": trades,
    }


def _metrics(strat_ret: pd.Series, equity: pd.Series) -> dict:
    total_return = equity.iloc[-1] - 1
    peak = equity.cummax()
    max_drawdown = ((equity - peak) / peak).min()

    std = strat_ret.std()
    sharpe = (strat_ret.mean() / std * np.sqrt(TRADING_DAYS)) if std > 0 else 0.0

    active = strat_ret[strat_ret != 0]
    win_rate = (active > 0).mean() if len(active) else 0.0

    return {
        "total_return": round(float(total_return), 4),
        "max_drawdown": round(float(max_drawdown), 4),
        "sharpe": round(float(sharpe), 2),
        "win_rate": round(float(win_rate), 4),
    }


def _trades(position: pd.Series, df: pd.DataFrame) -> list:
    """Buy/sell points where the position flips, for chart markers."""
    flips = position.diff().fillna(position)
    out = []
    for d, change in flips[flips != 0].items():
        out.append(
            {
                "date": d.strftime("%Y-%m-%d"),
                "price": round(float(df.loc[d, "close"]), 2),
                "action": "buy" if change > 0 else "sell",
            }
        )
    return out
