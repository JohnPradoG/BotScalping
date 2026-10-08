# Estructura en varios marcos: la tendencia se lee en M15 o H1 (máximos y mínimos crecientes + precio sobre EMA20 del
# marco mayor) y la entrada se afina en M1 o M5 (retroceso a la EMA20 del marco menor o a su último mínimo, vela que cierra
# fuerte). Stop: bajo el último mínimo del marco menor ("ajustado") o del marco mayor ("amplio").
# Uso: PYTHONPATH=. python scripts/estructura_mtf.py configs/nas100.toml [--validate]
import sys, itertools, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv, split_by_date
from botscalping.indicators import resample_ohlc, atr, ema, align_higher_tf
from botscalping import stats
from botscalping.engine import run_backtest, Exits, Costs
cfg = load_config(sys.argv[1]); oos = "--validate" in sys.argv
is_b, oos_b = split_by_date(load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz), cfg.in_sample_until)
base = oos_b if oos else is_b

def swings(b, k):
    hi, lo = b["high"], b["low"]; w = 2 * k + 1
    sh = hi.where(hi == hi.rolling(w, center=True).max()).dropna(); sl = lo.where(lo == lo.rolling(w, center=True).min()).dropna()
    f = lambda s: s.reindex(b.index).ffill().shift(k)
    return f(sh), f(sh.shift(1)), f(sl), f(sl.shift(1))

rows = []
for htf, ltf in [("15min", "1min"), ("1h", "1min"), ("1h", "5min"), ("15min", "5min")]:
    b = base if ltf == "1min" else resample_ohlc(base, ltf)
    H = resample_ohlc(base, htf)
    hsh, hsh0, hsl, hsl0 = swings(H, 3); he = ema(H["close"], 20)
    up_h = (hsh > hsh0) & (hsl > hsl0) & (H["close"] > he); dn_h = (hsh < hsh0) & (hsl < hsl0) & (H["close"] < he)
    al = lambda s: align_higher_tf(s.astype(float), b.index, htf, ltf)
    up, dn = al(up_h) > 0.5, al(dn_h) > 0.5
    hsl_l, hsh_l = al(hsl), al(hsh)
    a, e, c = atr(b), ema(b["close"], 20), b["close"]
    sh, _, sl, _ = swings(b, 3)
    rng = (b["high"] - b["low"]).replace(0, np.nan); pos = (c - b["low"]) / rng
    L = up & (c > e) & ((b["low"] <= e + 0.1 * a) | (b["low"] <= sl + 0.25 * a)) & (pos >= 0.6)
    S = dn & (c < e) & ((b["high"] >= e - 0.1 * a) | (b["high"] >= sh - 0.25 * a)) & (pos <= 0.4)
    L &= ~L.shift(fill_value=False); S &= ~S.shift(fill_value=False)
    for stop_lab, lo_lvl, hi_lvl in [("ajustado", sl, sh), ("amplio", hsl_l, hsh_l)]:
        dl = (c - (lo_lvl - 0.1 * a)).clip(lower=0.5 * a); ds = ((hi_lvl + 0.1 * a) - c).clip(lower=0.5 * a)
        stop = dl.where(L, ds.where(S)).to_numpy(float)
        rg = np.random.default_rng(0)
        RL = up.to_numpy() & (rg.random(len(b)) < L.sum() / max(up.sum(), 1)); RS = dn.to_numpy() & (rg.random(len(b)) < S.sum() / max(dn.sum(), 1))
        rstop = np.where(RL, dl, ds)
        mb = 480 if ltf == "1min" else 288
        for en, ex in {"1:1": Exits(1, mb), "1:2": Exits(2, mb), "trailing 1ATR": Exits(0, mb, trail_atr=1.0),
                       "BE 1R + trailing 2ATR": Exits(0, mb, breakeven_r=1.0, trail_atr=2.0, trail_start_r=1.0)}.items():
            t = run_backtest(b, L.to_numpy(), S.to_numpy(), stop, ex, cfg.costs); r = t["r"].to_numpy()
            if len(r) < 30: continue
            g = run_backtest(b.assign(spread=0.0), L.to_numpy(), S.to_numpy(), stop, ex, Costs())["r"].to_numpy()
            ra = run_backtest(b, RL, RS, rstop, ex, cfg.costs)["r"].to_numpy()
            bs = stats.bootstrap_mean(r, n_boot=1000); yr = t.groupby(t["entry_time"].dt.year)["r"].mean()
            rows.append(dict(tendencia=htf, entrada=ltf, stop=stop_lab, salida=en, n=len(r), bruto=g.mean(), neto=r.mean(),
                             ci_lo=bs["ci_low"], p=bs["p_gt_0"], acierto=(r > 0).mean(), años_pos=f"{int((yr > 0).sum())}/{len(yr)}",
                             azar_neto=ra.mean(), stop_med=np.nanmedian(t["risk"])))
df = pd.DataFrame(rows); df["p_holm"] = stats.holm(df["p"].tolist()); pd.set_option("display.width", 250)
print(f"{cfg.spec.symbol} {'OOS' if oos else 'in-sample'} | netas>0: {int((df.neto>0).sum())}/{len(df)} | brutas>0: {int((df.bruto>0).sum())} | "
      f"mejores que azar: {int((df.neto>df.azar_neto).sum())} | Holm<0.05: {int((df.p_holm<.05).sum())}")
print(df.sort_values("neto", ascending=False).drop(columns="p").round(3).to_string(index=False))
