# RSI-2 diario NAS100 con stop de protección en puntos y lote fijo. Uso: PYTHONPATH=. python scripts/rsi2_stop.py configs/nas100.toml
import sys, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv
cfg = load_config(sys.argv[1]); SWAP = 0.0002; USD_PT_LOT = 100.0  # 0,05 lote = 5 $/punto (dato de John)
b = load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz)
ny = b.tz_localize("UTC").tz_convert("America/New_York") if b.index.tz is None else b.tz_convert("America/New_York")
ny = ny[ny.index.dayofweek < 5]
d = ny.resample("1D").agg({"open": "first", "low": "min", "close": "last", "spread": "last"}).dropna()  # 24 h para el stop
dc = ny.between_time("09:30", "15:59").resample("1D").agg({"close": "last", "spread": "last"}).dropna()
d = d.loc[dc.index]; c = dc["close"]; ch = c.diff()
up = ch.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-ch.clip(upper=0)).ewm(alpha=.5, adjust=False).mean()
r2 = 100 - 100 / (1 + up / dn); ma200, ma5 = c.rolling(200).mean(), c.rolling(5).mean()
def run(stop):
    tr, i = [], 0
    while i < len(d) - 1:
        if r2.iloc[i] < 20 and c.iloc[i] > ma200.iloc[i]:
            e = c.iloc[i] + dc["spread"].iloc[i] + cfg.costs.slippage; j = i + 1; res = None
            while True:
                if stop and d["low"].iloc[j] <= e - stop:  # el low de 24 h puede incluir horas previas al cierre del día anterior: conservador
                    res = min(d["open"].iloc[j], e - stop) - cfg.costs.slippage - e; break
                if c.iloc[j] > ma5.iloc[j] or j - i >= 10 or j == len(d) - 1: res = c.iloc[j] - cfg.costs.slippage - e; break
                j += 1
            tr.append((d.index[i], res - SWAP * e * (j - i))); i = j
        i += 1
    return pd.Series(dict(tr))
for stop in [0, 300, 500, 800]:
    p = run(stop)
    for lot in [0.01, 0.02, 0.05]:
        usd = p * lot * USD_PT_LOT; eq = 1000 + usd.cumsum(); dd = (eq.cummax() - eq).max()
        print(f"stop {stop or 'sin':>4} pts | lote {lot} | ops {len(p)} acierto {(p>0).mean():.0%} | ganancia {usd.sum():>8,.0f} $ | "
              f"peor op {usd.min():>7,.0f} $ | mínimo de la cuenta {eq.min():>7,.0f} $ | caída máx {dd:,.0f} $ | por año {usd.groupby(usd.index.year).sum().round(0).to_dict()}")
