# Método de John "leer la estructura": tendencia = máximos y mínimos crecientes (o decrecientes) y precio del lado
# correcto de la EMA; entrar en el retroceso a la EMA o al último mínimo creciente, con vela que cierra a favor.
# Stop bajo el último mínimo (sobre el último máximo). Referencia: entradas al azar EN LA MISMA tendencia, mismo lado,
# misma salida. Uso: PYTHONPATH=. python scripts/estructura.py configs/nas100.toml [--validate]
import sys, itertools, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv, split_by_date
from botscalping.indicators import resample_ohlc, atr, ema
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
for tf, k, ema_n in itertools.product(["1min", "5min"], [3, 5], [20, 50]):
    b = base if tf == "1min" else resample_ohlc(base, tf)
    a, e, c = atr(b), ema(b["close"], ema_n), b["close"]
    sh, sh0, sl, sl0 = swings(b, k)
    up = (sh > sh0) & (sl > sl0) & (c > e); dn = (sh < sh0) & (sl < sl0) & (c < e)
    rng = (b["high"] - b["low"]).replace(0, np.nan); pos = (c - b["low"]) / rng
    L = up & ((b["low"] <= e + 0.1 * a) | (b["low"] <= sl + 0.25 * a)) & (pos >= 0.6)
    S = dn & ((b["high"] >= e - 0.1 * a) | (b["high"] >= sh - 0.25 * a)) & (pos <= 0.4)
    L &= ~L.shift(fill_value=False); S &= ~S.shift(fill_value=False)
    dl = (c - (sl - 0.1 * a)).clip(lower=0.5 * a); ds = ((sh + 0.1 * a) - c).clip(lower=0.5 * a)
    stop = dl.where(L, ds.where(S)).to_numpy(float)
    rg = np.random.default_rng(0)
    pL = L.sum() / max(up.sum(), 1); pS = S.sum() / max(dn.sum(), 1)
    RL = up.to_numpy() & (rg.random(len(b)) < pL); RS = dn.to_numpy() & (rg.random(len(b)) < pS)
    rstop = np.where(RL, dl, ds)
    for en, ex in {"1:1": Exits(1, 120), "1:2": Exits(2, 120), "trailing 1ATR": Exits(0, 240, trail_atr=1.0),
                   "BE 1R + trailing 2ATR": Exits(0, 240, breakeven_r=1.0, trail_atr=2.0, trail_start_r=1.0)}.items():
        t = run_backtest(b, L.to_numpy(), S.to_numpy(), stop, ex, cfg.costs); r = t["r"].to_numpy()
        g = run_backtest(b.assign(spread=0.0), L.to_numpy(), S.to_numpy(), stop, ex, Costs())["r"].to_numpy()
        ra = run_backtest(b, RL, RS, rstop, ex, cfg.costs)["r"].to_numpy()
        bs = stats.bootstrap_mean(r, n_boot=1000); yr = t.groupby(t["entry_time"].dt.year)["r"].mean()
        rows.append(dict(tf=tf, k=k, ema=ema_n, salida=en, n=len(r), bruto=g.mean(), neto=r.mean(), ci_lo=bs["ci_low"],
                         acierto=(r > 0).mean(), años_pos=f"{int((yr > 0).sum())}/{len(yr)}", azar_neto=ra.mean(),
                         stop_med=np.nanmedian(t["risk"])))
df = pd.DataFrame(rows); pd.set_option("display.width", 250)
print(f"{cfg.spec.symbol} {'OOS' if oos else 'in-sample'} | netas>0: {int((df.neto>0).sum())}/{len(df)} | brutas>0: {int((df.bruto>0).sum())} | "
      f"mejores que azar: {int((df.neto>df.azar_neto).sum())}")
print(df.sort_values("neto", ascending=False).round(3).to_string(index=False))
