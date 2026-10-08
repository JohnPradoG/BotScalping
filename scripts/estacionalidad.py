# Ventajas "de calendario" muy documentadas en índices: sesgo por hora del día e impulso intradía
# (la dirección de la primera media hora predice la última media hora; Gao et al. 2018).
# Uso: PYTHONPATH=. python scripts/estacionalidad.py configs/nas100.toml
import sys, numpy as np, pandas as pd
from botscalping.experiment import load_config
from botscalping.data import load_mt5_csv
cfg = load_config(sys.argv[1])
b = load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz)
cost = b["spread"] + 2 * cfg.costs.slippage
cut = pd.Timestamp(cfg.in_sample_until, tz=b.index.tz) if b.index.tz else pd.Timestamp(cfg.in_sample_until)
ny = b.tz_localize("UTC").tz_convert("America/New_York") if b.index.tz is None else b.tz_convert("America/New_York")
ny["cost"] = cost.to_numpy()
pd.set_option("display.width", 250)

def tstat(x): x = pd.Series(x).dropna(); return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 else np.nan

# A) Hora del día (NY): comprar a la apertura de la hora y cerrar a la siguiente. Resultado neto en % del precio.
h = ny.resample("1h").agg({"open": "first", "close": "last", "cost": "first"}).dropna()
h["ret_pct"] = 100 * (h["close"] - h["open"]) / h["open"]
h["cost_pct"] = 100 * h["cost"] / h["open"]
h["is"] = h.index.tz_convert("UTC").tz_localize(None) <= pd.Timestamp(cfg.in_sample_until)
rows = []
for hr, g in h.groupby(h.index.hour):
    gi, go = g[g["is"]], g[~g["is"]]
    yr = gi.groupby(gi.index.year)["ret_pct"].mean()
    rows.append(dict(hora_NY=hr, n_is=len(gi), bruto_is=gi.ret_pct.mean(), t_is=tstat(gi.ret_pct), coste=gi.cost_pct.mean(),
                     años_mismo_signo=f"{int((np.sign(yr) == np.sign(gi.ret_pct.mean())).sum())}/{len(yr)}",
                     bruto_oos=go.ret_pct.mean(), t_oos=tstat(go.ret_pct)))
df = pd.DataFrame(rows)
df["neto_mejor_lado_is"] = df.bruto_is.abs() - df.coste
print(f"## {cfg.spec.symbol}: rendimiento medio por hora (NY), % del precio. Neto = |bruto| − coste (operando a favor del sesgo)")
print(df.round(4).to_string(index=False))

# B) Impulso intradía: signo de (09:30→10:00) decide la operación 15:30→15:59.
d = []
for day, g in ny.groupby(ny.index.date):
    g = g.between_time("09:30", "15:59")
    if len(g) < 300: continue
    o = g["open"].iloc[0]; c10 = g.loc[:g.index[0] + pd.Timedelta("29min"), "close"].iloc[-1]
    late = g.between_time("15:30", "15:59")
    if late.empty: continue
    s = np.sign(c10 - o)
    d.append(dict(dia=pd.Timestamp(day), s=s, r_late=100 * (late["close"].iloc[-1] - late["open"].iloc[0]) / late["open"].iloc[0],
                  c=100 * late["cost"].iloc[0] / late["open"].iloc[0]))
d = pd.DataFrame(d).set_index("dia"); d["neto"] = d.s * d.r_late - d.c
d["is"] = d.index <= pd.Timestamp(cfg.in_sample_until)
for lab, g in [("in-sample", d[d["is"]]), ("OOS", d[~d["is"]])]:
    print(f"## {cfg.spec.symbol} impulso intradía {lab}: n={len(g)} bruto={(g.s*g.r_late).mean():.4f}% neto={g.neto.mean():.4f}% "
          f"t_neto={tstat(g.neto):.2f} acierto={(g.neto>0).mean():.2f} | por año: {g.groupby(g.index.year).neto.mean().round(4).to_dict()}")
