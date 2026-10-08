# "Comprar tras la caída" a escala diaria (Connors RSI-2): compra al cierre si RSI(2) < umbral y el precio está
# sobre su media de 200 días; vende al cierre cuando cierra sobre la media de 5. Costes: spread + slippage + swap
# estimado de 0,02 % del precio por noche. Referencia: compras al azar con la misma duración.
# Uso: PYTHONPATH=. python scripts/rsi2_diario.py configs/nas100.toml
import sys, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv
cfg = load_config(sys.argv[1]); SWAP = 0.0002
b = load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz)
ny = b.tz_localize("UTC").tz_convert("America/New_York") if b.index.tz is None else b.tz_convert("America/New_York")
ny = ny[ny.index.dayofweek < 5]
d = ny.between_time("09:30", "15:59").resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last", "spread": "last"}).dropna()
c = d["close"]; ch = c.diff()
def rsi(n):
    up = ch.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(); dn = (-ch.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)
r2, ma200, ma5 = rsi(2), c.rolling(200).mean(), c.rolling(5).mean()
cut = pd.Timestamp(cfg.in_sample_until).tz_localize("America/New_York")
rng = np.random.default_rng(0)
for thr in [5, 10, 20]:
    trades, i, idx = [], 0, d.index
    while i < len(d) - 1:
        if r2.iloc[i] < thr and c.iloc[i] > ma200.iloc[i]:
            j = i + 1
            while j < len(d) - 1 and c.iloc[j] <= ma5.iloc[j] and j - i < 10: j += 1
            e, x = c.iloc[i] + d["spread"].iloc[i] + cfg.costs.slippage, c.iloc[j] - cfg.costs.slippage
            trades.append(dict(t=idx[i], dias=j - i, ret=100 * ((x - e) / e - SWAP * (j - i))))
            i = j
        i += 1
    t = pd.DataFrame(trades).set_index("t")
    # azar: mismas duraciones, días de entrada al azar (sobre la media de 200 también)
    ok = np.where((c > ma200).to_numpy()[:-11])[0]
    rnd = [100 * ((c.iloc[k + n] - cfg.costs.slippage) / (c.iloc[k] + d["spread"].iloc[k] + cfg.costs.slippage) - 1 - SWAP * n)
           for _ in range(200) for k, n in zip(rng.choice(ok, len(t)), t["dias"])]
    for lab, g in [("in-sample", t[t.index <= cut]), ("OOS", t[t.index > cut])]:
        print(f"{cfg.spec.symbol} RSI2<{thr} {lab}: n={len(g)} media={g.ret.mean():.3f}% acierto={(g.ret>0).mean():.2f} "
              f"total={g.ret.sum():.1f}% días_med={g.dias.median():.0f}")
    print(f"   azar con las mismas duraciones: media={np.mean(rnd):.3f}% por operación")
    if thr == 20:
        g = t.ret; eq = g.cumsum()
        print(f"   todo: n={len(g)} t={g.mean()/(g.std(ddof=1)/np.sqrt(len(g))):.2f} peor_op={g.min():.2f}% "
              f"max_caída={(eq.cummax()-eq).max():.1f}% por año={g.groupby(g.index.year).sum().round(1).to_dict()}")
