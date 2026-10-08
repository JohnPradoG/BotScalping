# Operar SOLO cuando el mercado está en rango: comprar en el suelo y vender en el techo del rango, con rechazo.
# Rango = ADX(14) bajo y ancho de las últimas N velas <= k·ATR. Stop fuera del rango. Referencia: entradas al azar
# DENTRO de rangos con la misma salida. Uso: PYTHONPATH=. python scripts/rango.py configs/nas100.toml [--validate]
import sys, itertools, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv, split_by_date
from botscalping.indicators import resample_ohlc, atr
from botscalping import stats
from botscalping.engine import run_backtest, Exits
cfg = load_config(sys.argv[1]); oos = "--validate" in sys.argv
is_b, oos_b = split_by_date(load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz), cfg.in_sample_until)
base = oos_b if oos else is_b

def adx(b, n=14):
    up, dn = b["high"].diff(), -b["low"].diff()
    pdm = up.where((up > dn) & (up > 0), 0.0); ndm = dn.where((dn > up) & (dn > 0), 0.0)
    tr = atr(b, n)
    pdi = 100 * pdm.ewm(alpha=1 / n, adjust=False).mean() / tr; ndi = 100 * ndm.ewm(alpha=1 / n, adjust=False).mean() / tr
    return (100 * (pdi - ndi).abs() / (pdi + ndi)).ewm(alpha=1 / n, adjust=False).mean()

rows = []
for tf, N in [("15min", 32), ("15min", 64), ("1h", 24), ("1h", 48)]:
    b = resample_ohlc(base, tf); a = atr(b); ax = adx(b)
    hi = b["high"].rolling(N).max().shift(); lo = b["low"].rolling(N).min().shift(); W = hi - lo
    rng = (b["high"] - b["low"]).replace(0, np.nan); pos = (b["close"] - b["low"]) / rng
    for k, adx_max in itertools.product([6.0, 10.0], [20, 25]):
        en_rango = (W <= k * a) & (ax < adx_max)
        L = en_rango & (b["low"] <= lo + 0.15 * W) & (b["close"] > lo) & (pos >= 0.6)
        S = en_rango & (b["high"] >= hi - 0.15 * W) & (b["close"] < hi) & (pos <= 0.4)
        dl = (b["close"] - (lo - 0.25 * a)).clip(lower=0.5 * a); ds = ((hi + 0.25 * a) - b["close"]).clip(lower=0.5 * a)
        stop = dl.where(L, ds.where(S)).to_numpy(float)
        rng_gen = np.random.default_rng(0); p = (L | S).sum() / max(en_rango.sum(), 1)
        hit = en_rango.to_numpy() & (rng_gen.random(len(b)) < p); side = rng_gen.random(len(b)) < .5
        rstop = np.where(side, dl, ds)
        for en, ex in {"1:1": Exits(1, 48), "1:1.5": Exits(1.5, 48), "1:2": Exits(2, 48), "trailing 1ATR": Exits(0, 48, trail_atr=1.0)}.items():
            t = run_backtest(b, L.to_numpy(), S.to_numpy(), stop, ex, cfg.costs); r = t["r"].to_numpy()
            if len(r) < 30: continue
            ra = run_backtest(b, hit & side, hit & ~side, rstop, ex, cfg.costs)["r"].to_numpy()
            bs = stats.bootstrap_mean(r, n_boot=1000); yr = t.groupby(t["entry_time"].dt.year)["r"].mean()
            rows.append(dict(tf=tf, N=N, ancho_atr=k, adx_max=adx_max, salida=en, n=len(r), exp_r=r.mean(), ci_lo=bs["ci_low"],
                             p=bs["p_gt_0"], acierto=(r > 0).mean(), años_pos=f"{int((yr > 0).sum())}/{len(yr)}", azar_r=ra.mean()))
df = pd.DataFrame(rows); df["p_holm"] = stats.holm(df["p"].tolist()); pd.set_option("display.width", 250)
print(f"{cfg.spec.symbol} {'OOS' if oos else 'in-sample'} | netas>0: {int((df.exp_r>0).sum())}/{len(df)} | mejores que el azar: "
      f"{int((df.exp_r>df.azar_r).sum())} | significativas tras Holm: {int((df.p_holm<.05).sum())}")
print(df.sort_values("ci_lo", ascending=False).head(15).round(3).to_string(index=False))
