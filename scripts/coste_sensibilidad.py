# ¿Cuánto coste aguanta el método de John? Corre sin coste y resta k·(spread real + 2·slippage)/riesgo por operación.
# Uso: PYTHONPATH=. python scripts/coste_sensibilidad.py configs/nas100.toml
import sys, itertools, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv, split_by_date
from botscalping import components as comps
from botscalping.engine import StrategySpec, build_signals, run_backtest, Costs, Exits
cfg = load_config(sys.argv[1])
b, _ = split_by_date(load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz), cfg.in_sample_until)
z = b.assign(spread=0.0); ctx = comps.Context(z, cfg.spec)
EXITS = {"1:1": (1, 0, 0, 0), "1:2": (2, 0, 0, 0), "trailing 1ATR": (0, 0, 1.0, 0), "BE 1R + trailing 2ATR": (0, 1.0, 2.0, 1.0)}
K = [0, 0.1, 0.25, 0.5, 1.0]
rows = []
for tf, k, wick, (en, (rr, be, tr, ts)) in itertools.product(["1min", "5min"], [3, 5, 10], [0.0, 0.4], EXITS.items()):
    ex = Exits(rr, {"1min": 120, "5min": 390}[tf], breakeven_r=be, trail_atr=tr, trail_start_r=ts)
    lo, sh, st, _ = build_signals(ctx, StrategySpec("sr_bounce", {"tf": tf, "k": k, "wick": wick}, [], ex))
    t = run_backtest(z, lo, sh, st, ex, Costs())
    c = (b["spread"].reindex(t["entry_time"]).to_numpy() + 2 * cfg.costs.slippage) / t["risk"].to_numpy()
    r = t["r"].to_numpy()
    row = dict(tf=tf, k=k, mecha=wick, salida=en, n=len(r), coste_real_R=np.nanmean(c))
    for f in K: row[f"exp_{int(f*100)}%"] = r.mean() - f * np.nanmean(c)
    row["coste_max_%"] = 100 * r.mean() / np.nanmean(c) if r.mean() > 0 else 0.0
    rows.append(row)
df = pd.DataFrame(rows); pd.set_option("display.width", 250)
print(cfg.spec.symbol, "| positivas por nivel de coste:", {f"{int(f*100)}%": int((df[f'exp_{int(f*100)}%'] > 0).sum()) for f in K}, "de", len(df))
print(df.sort_values("exp_0%", ascending=False).head(15).round(3).to_string(index=False))
