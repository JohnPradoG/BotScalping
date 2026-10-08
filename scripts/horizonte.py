# Marcos mayores (H1/H4): ruptura de canal + stop dinámico, sin objetivo fijo. ¿Hay ventaja cuando el coste
# deja de pesar? Uso: PYTHONPATH=. python scripts/horizonte.py configs/nas100.toml [--validate]
import sys, itertools, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv, split_by_date
from botscalping.indicators import resample_ohlc
from botscalping import components as comps, stats
from botscalping.engine import StrategySpec, build_signals, run_backtest, Exits
cfg = load_config(sys.argv[1]); oos = "--validate" in sys.argv
is_b, oos_b = split_by_date(load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz), cfg.in_sample_until)
base = oos_b if oos else is_b
rows = []
for tf, hold in [("1h", 24 * 20), ("4h", 6 * 20)]:
    b = resample_ohlc(base, tf)
    ctx = comps.Context(b, cfg.spec)
    for lb, sl, trail, lado in itertools.product([20, 55], [2.0, 3.0], [2.0, 3.0], ["ambos", "solo_largos"]):
        ex = Exits(0, hold, trail_atr=trail)
        for setup, params in [("breakout", {"lookback": lb, "sl_atr": sl}), ("random", {"prob": 0.02, "sl_atr": sl})]:
            lo, sh, st, _ = build_signals(ctx, StrategySpec(setup, params, [], ex))
            if lado == "solo_largos": sh = np.zeros_like(sh)
            t = run_backtest(b, lo, sh, st, ex, cfg.costs)
            r = t["r"].to_numpy()
            if setup == "random":
                rows[-1]["azar_r"] = r.mean(); continue
            bs = stats.bootstrap_mean(r, n_boot=1000)
            yr = t.groupby(t["entry_time"].dt.year)["r"].mean()
            rows.append(dict(tf=tf, canal=lb, stop_atr=sl, trail_atr=trail, lado=lado, n=len(r), exp_r=r.mean(),
                             ci_lo=bs["ci_low"], ci_hi=bs["ci_high"], acierto=(r > 0).mean(), total_r=r.sum(),
                             años_pos=f"{int((yr > 0).sum())}/{len(yr)}", horas_med=(t["exit_time"] - t["entry_time"]).dt.total_seconds().median() / 3600))
df = pd.DataFrame(rows); df["p_holm"] = stats.holm([float((df.exp_r.iloc[i] <= 0)) for i in range(len(df))])  # marcador
df = df.drop(columns="p_holm")
pd.set_option("display.width", 250)
bh = base["close"].iloc[-1] / base["close"].iloc[0] - 1
print(f"{cfg.spec.symbol} {'OOS' if oos else 'in-sample'} | comprar y mantener: {bh:+.1%} | netas > 0: {int((df.exp_r > 0).sum())}/{len(df)}")
print(df.sort_values("ci_lo", ascending=False).round(3).to_string(index=False))
