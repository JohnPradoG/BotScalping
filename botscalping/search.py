"""Búsqueda amplia de setups: muchas combinaciones de entrada × gestión × sesión.

Probar muchas variantes garantiza que alguna salga "ganadora" por azar. Por eso:

1. Todo se ordena SOLO con in-sample, y los p-valores se corrigen (Holm) por el nº de pruebas.
2. Se exige estabilidad: expectativa positiva en la mayoría de los años in-sample.
3. Solo las mejores candidatas (``--top``) se evalúan UNA vez en out-of-sample.

Uso:
    python -m botscalping.search configs/xauusd.toml configs/nas100.toml --top 5
"""
from __future__ import annotations

import argparse
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from . import components as comps
from . import stats
from .data import load_mt5_csv, split_by_date
from .engine import Exits, StrategySpec, build_signals, run_backtest
from .experiment import load_config

# Ventanas en minutos desde la apertura de NY (09:30 Nueva York). Londres 03:00 NY = +1050.
WINDOWS = {
    "apertura_NY_2h": (0, 120),
    "sesion_NY": (0, 390),
    "apertura_Londres_2h": (1050, 1170),
    "todo_el_dia": None,
}
MAX_BARS = {"1min": 60, "5min": 180, "15min": 390}
RRS = [1.0, 1.5, 2.0]


def setups():
    for tf, lb in itertools.product(["1min", "5min", "15min"], [10, 20]):
        yield "sweep", {"tf": tf, "lookback": lb}, MAX_BARS[tf], list(WINDOWS)
    for minutes, sl in itertools.product([15, 30], [1.0, 2.0]):
        yield "orb", {"minutes": minutes, "sl_atr": sl}, 180, ["apertura_NY_2h", "sesion_NY"]
    for tf in ["5min", "15min"]:
        yield "breakout", {"tf": tf, "sl_atr": 2.0}, MAX_BARS[tf], list(WINDOWS)


def run_grid(bars: pd.DataFrame, cfg, years: list[int]) -> tuple[pd.DataFrame, dict]:
    ctx = comps.Context(bars, cfg.spec)
    rows, trades_by_key = [], {}
    for setup, params, max_bars, windows in setups():
        for win in windows:
            filt = [] if WINDOWS[win] is None else [("session_hours", {"start": WINDOWS[win][0], "end": WINDOWS[win][1]})]
            for rr in RRS:
                strat = StrategySpec(setup, params, filt, Exits(rr, max_bars))
                lo, sh, stop, _ = build_signals(ctx, strat)
                t = run_backtest(bars, lo, sh, stop, strat.exits, cfg.costs)
                key = f"{setup} {params} | {win} | 1:{rr:g}"
                trades_by_key[key] = t
                r = t["r"].to_numpy()
                row = {"variante": key, "setup": setup, "ventana": win, "rr": rr, **stats.summary(r),
                       **stats.bootstrap_mean(r, n_boot=2000)}
                if len(t):
                    by_year = t.groupby(t["entry_time"].dt.year)["r"].mean()
                    row["años_positivos"] = int((by_year.reindex(years) > 0).sum())
                    row["peor_año_r"] = float(by_year.reindex(years).min())
                rows.append(row)
    df = pd.DataFrame(rows)
    df["p_holm"] = stats.holm(df["p_gt_0"].tolist())
    return df.sort_values("ci_low", ascending=False), trades_by_key


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("configs", nargs="+")
    ap.add_argument("--top", type=int, default=5, help="candidatas por instrumento que se validan en out-of-sample")
    ap.add_argument("--min-trades", type=int, default=200)
    ap.add_argument("--out", default="results/search")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for path in a.configs:
        cfg = load_config(path)
        bars = load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz)
        is_bars, oos_bars = split_by_date(bars, cfg.in_sample_until)
        years = sorted(set(is_bars.index.year) - {is_bars.index.year.min()})  # el primer año está incompleto
        is_df, _ = run_grid(is_bars, cfg, years)
        is_df.to_csv(out / f"{cfg.spec.symbol}_in_sample.csv", index=False)

        need = max(2, len(years) - 1)
        cands = is_df[(is_df["n"] >= a.min_trades) & (is_df["expectancy_r"] > 0) & (is_df["años_positivos"] >= need)]
        top = cands.head(a.top)
        print(f"\n## {cfg.spec.symbol}: {len(is_df)} variantes probadas, {len(cands)} candidatas estables, "
              f"{int((is_df['p_holm'] < 0.05).sum())} significativas tras Holm")
        print(is_df.head(15)[["variante", "n", "win_rate", "expectancy_r", "ci_low", "p_gt_0", "p_holm",
                              "años_positivos", "max_dd_r"]].round(3).to_string(index=False))
        if top.empty:
            print("Ninguna candidata para validar.")
            continue
        oos_df, _ = run_grid(oos_bars, cfg, sorted(set(oos_bars.index.year)))
        val = top[["variante", "n", "expectancy_r", "ci_low"]].merge(
            oos_df[["variante", "n", "win_rate", "expectancy_r", "ci_low", "ci_high", "p_gt_0", "max_dd_r"]],
            on="variante", suffixes=("_is", "_oos"))
        val.to_csv(out / f"{cfg.spec.symbol}_validacion.csv", index=False)
        print(f"\n### {cfg.spec.symbol}: validación out-of-sample de las {len(top)} candidatas")
        print(val.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
