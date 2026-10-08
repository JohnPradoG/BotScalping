"""¿Se puede APRENDER qué mechas son trampas? Modelo sobre todas las señales a la vez.

Entrena con 2022-2023, prueba con 2024-2025H1 (ambos dentro del in-sample; el out-of-sample
sigue sin tocar). Si el modelo no distingue (AUC ≈ 0.5) no hay patrón aprendible en estas señales.
Uso: PYTHONPATH=. python scripts/ml_mechas.py configs/nas100_mechas.toml
"""
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv, split_by_date
from botscalping import components as comps, indicators as ind
from botscalping.engine import StrategySpec, build_signals, run_backtest, Costs

cfg = load_config(sys.argv[1])
bars, _ = split_by_date(load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz), cfg.in_sample_until)
res = {}
for lab, b, costs in [("bruto", bars.assign(spread=0.0), Costs()), ("neto", bars, cfg.costs)]:
    ctx = comps.Context(b, cfg.spec)
    lo, sh, st, _ = build_signals(ctx, StrategySpec(cfg.setup, cfg.setup_params, [], cfg.exits))
    res[lab] = (ctx, run_backtest(b, lo, sh, st, cfg.exits, costs))
ctx, t = res["bruto"]
net = res["neto"][1].set_index("signal_idx")["r"]
b = bars
a = ctx.atr()
side = t["side"].to_numpy()
i = t["signal_idx"].to_numpy()
mid = (b["high"] + b["low"]) / 2
ao = (mid.rolling(5).mean() - mid.rolling(34).mean()) / a
d = b["close"].diff()
rsi = 100 - 100 / (1 + d.clip(lower=0).ewm(alpha=1/14).mean() / (-d.clip(upper=0)).ewm(alpha=1/14).mean())
body = (b["close"] - b["open"]) / a
rng = (b["high"] - b["low"]) / a
sess = ctx.session()["minutes_from_open"]
feat = {
    "dist_ema20": (b["close"] - ctx.ema(20)) / a, "dist_ema50": (b["close"] - ctx.ema(50)) / a,
    "dist_ema200": (b["close"] - ctx.ema(200)) / a, "ao": ao, "ao_diff": ao.diff(), "rsi": rsi,
    "body0": body, "body_sum5": body.rolling(5).sum(), "body_sum15": body.rolling(15).sum(),
    "range0": rng, "atr_rel": a / a.rolling(1000, min_periods=250).median(),
    "vol_rel": b["tick_volume"] / b["tick_volume"].rolling(20).mean(), "spread_atr": b["spread"] / a,
    "ret30": (b["close"] - b["close"].shift(30)) / a, "ret120": (b["close"] - b["close"].shift(120)) / a,
    "min_from_open": sess, "dow": pd.Series(b.index.dayofweek, index=b.index),
}
X = pd.DataFrame({k: v.to_numpy()[i] for k, v in feat.items()})
# orientar las señales direccionales al lado de la operación (para cortos, invertir signo)
for k in ["dist_ema20", "dist_ema50", "dist_ema200", "ao", "ao_diff", "body0", "body_sum5", "body_sum15", "ret30", "ret120"]:
    X[k] = X[k] * side
X["rsi"] = np.where(side == 1, X["rsi"], 100 - X["rsi"])
y = (t["r"].to_numpy() > 0).astype(int)
yr = t["entry_time"].dt.year.to_numpy()
train, test = (yr >= 2022) & (yr <= 2023), yr >= 2024
m = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300, min_samples_leaf=200, random_state=0)
m.fit(X[train], y[train])
p = m.predict_proba(X[test])[:, 1]
r_test = t["r"].to_numpy()[test]
net_test = net.reindex(i[test]).to_numpy()
print(f"{cfg.spec.symbol}: entrenamiento {train.sum()} operaciones, prueba {test.sum()}")
print(f"AUC prueba = {roc_auc_score(y[test], p):.3f}  (0.5 = no distingue)")
q = pd.qcut(p, 5, labels=False, duplicates="drop")
out = pd.DataFrame({"quintil": q, "r_bruto": r_test, "r_neto": net_test}).groupby("quintil").agg(
    n=("r_bruto", "size"), exp_bruto=("r_bruto", "mean"), exp_neto=("r_neto", "mean"))
print("Operaciones de prueba por quintil de probabilidad predicha (4 = las que el modelo cree mejores):")
print(out.round(3).to_string())
