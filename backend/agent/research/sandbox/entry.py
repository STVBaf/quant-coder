"""In-sandbox entry point. Runs INSIDE the Docker container, never on the host.

Layout inside the container (all bind-mounted by the runner):
  /work/strategy.py   — agent-written code (read-only)
  /work/out/          — writable; we drop result.json here
  /data/              — materialized datasets, read-only (parquet per code)
  /engine/            — the project's backtest engine, read-only, importable

The agent's strategy.py must define:
  build_signals(df) -> pd.Series   # 1.0 = long, 0.0 = flat, indexed like df
It may call load_data(code, start, end) to get an OHLCV+indicator DataFrame.
We run its signals through the same vectorized engine used everywhere else, so
sandbox results are directly comparable to the app's backtests.
"""
import json
import sys
import traceback
from pathlib import Path

import pandas as pd

DATA_DIR = Path("/data")
OUT = Path("/work/out/result.json")
sys.path.insert(0, "/harness")  # entry.py + engine_run.py are mounted here


def load_data(code: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Read a materialized dataset (OHLCV + indicators) for `code`."""
    fp = DATA_DIR / f"{code}.parquet"
    if not fp.exists():
        raise FileNotFoundError(f"dataset for {code} not materialized")
    df = pd.read_parquet(fp)
    if start:
        df = df[df.index >= pd.to_datetime(start)]
    if end:
        df = df[df.index <= pd.to_datetime(end)]
    return df


def _write(obj):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(obj, ensure_ascii=False, default=str), encoding="utf-8")


def main():
    from engine_run import run_signals  # self-contained, mounted at /harness

    ns: dict = {"load_data": load_data, "pd": pd}
    code = Path("/work/strategy.py").read_text(encoding="utf-8")
    try:
        exec(compile(code, "strategy.py", "exec"), ns)
        if "build_signals" not in ns:
            raise ValueError("strategy.py must define build_signals(df)")
        # Default drives the strategy on the primary requested code if the agent
        # sets CODE; otherwise the agent's build_signals must load its own data.
        target = ns.get("CODE")
        if target:
            df = load_data(target)
            signals = ns["build_signals"](df)
            result = run_signals(df, signals)
            result["code"] = target
        else:
            result = ns["build_signals"].__doc__ or {}
        _write({"ok": True, "result": result})
    except Exception as e:
        _write({"ok": False, "error": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc()})


if __name__ == "__main__":
    main()
