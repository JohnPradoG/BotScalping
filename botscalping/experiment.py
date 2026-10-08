"""Experimentos de ablación: qué componentes mejoran la expectativa y cuáles no.

Modos:

* ``ladder``  baseline → +A → +A+B → ... (el orden del config). Responde: "¿añadir X al
  sistema que ya tengo mejora?".
* ``single``  baseline + cada filtro por separado. Responde: "¿X aporta algo por sí solo?".
* ``loo``     sistema completo menos cada filtro. Responde: "¿X sigue aportando cuando
  ya están los demás o es redundante?".

Para cada componente probado se compara, dentro de las operaciones del sistema "padre",
las que el filtro CONSERVA frente a las que ELIMINA (test de permutación, corregido por
Holm). Un filtro solo "aporta valor" si lo que quita es significativamente peor que lo
que deja Y el sistema resultante mantiene muestra suficiente.

Uso:
    python -m botscalping.experiment configs/xauusd.toml --mode ladder
    python -m botscalping.experiment configs/xauusd.toml --mode single --synthetic
"""
from __future__ import annotations

import argparse
import dataclasses
import tomllib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import components as comps
from . import stats
from .data import InstrumentSpec, load_mt5_csv, split_by_date, synthetic_bars
from .engine import Costs, Exits, StrategySpec, build_signals, run_backtest

ALPHA = 0.05


@dataclass
class Config:
    name: str
    spec: InstrumentSpec
    data_path: str | None
    broker_tz: str
    in_sample_until: str | None
    setup: str
    setup_params: dict
    exits: Exits
    costs: Costs
    filters: list[tuple[str, dict]]
    base_filters: list[tuple[str, dict]]  # siempre activos (parte de la hipótesis), no se evalúan
    min_trades: int
    benchmark_random: bool


def load_config(path: str) -> Config:
    raw = tomllib.loads(Path(path).read_text())
    d, s, st = raw["data"], raw.get("split", {}), raw["strategy"]
    spec = InstrumentSpec(d["symbol"], d["point"], d.get("session_tz", "America/New_York"), d.get("session_open", "09:30"))
    c = raw.get("costs", {})
    costs = Costs(c.get("commission", 0.0), c.get("slippage_points", 0) * spec.point)
    filters = [(f["component"], f.get("params", {})) for f in raw.get("filters", [])]
    base = [(f["component"], f.get("params", {})) for f in st.get("base_filters", [])]
    for name, params in filters + base:
        comps.resolve(name, params)  # valida nombres y parámetros antes de correr nada
    return Config(
        name=raw.get("name", Path(path).stem), spec=spec, data_path=d.get("path"), broker_tz=d.get("broker_tz", "UTC"),
        in_sample_until=s.get("in_sample_until"), setup=st["setup"], setup_params=st.get("setup_params", {}),
        exits=Exits(**{f.name: st[f.name] for f in dataclasses.fields(Exits) if f.name in st}), costs=costs, filters=filters, base_filters=base,
        min_trades=raw.get("analysis", {}).get("min_trades", 100),
        benchmark_random=raw.get("analysis", {}).get("benchmark_random", True),
    )


def plan(cfg: Config, mode: str) -> list[tuple[str, list, list, str | None]]:
    """Lista de (etiqueta, filtros_variante, filtros_padre, filtro_probado)."""
    f = cfg.filters
    rows = [("baseline", [], [], None)]
    if mode == "ladder":
        for k in range(len(f)):
            rows.append((f"+ {f[k][0]}", f[: k + 1], f[:k], f[k][0]))
    elif mode == "single":
        rows += [(f"baseline + {x[0]}", [x], [], x[0]) for x in f]
    elif mode == "loo":
        rows.append(("completo", f, f, None))
        for x in f:
            rest = [y for y in f if y is not x]
            rows.append((f"completo - {x[0]}", rest, rest, x[0]))
    else:
        raise ValueError(mode)
    return rows


def evaluate(bars: pd.DataFrame, cfg: Config, mode: str) -> pd.DataFrame:
    ctx = comps.Context(bars, cfg.spec)
    cache: dict[tuple, pd.DataFrame] = {}
    masks_all: dict[str, tuple] = {}

    def run(filters) -> pd.DataFrame:
        key = tuple(n for n, _ in filters)
        if key not in cache:
            strat = StrategySpec(cfg.setup, cfg.setup_params, cfg.base_filters + list(filters), cfg.exits)
            lo, sh, stop, masks = build_signals(ctx, strat)
            masks_all.update(masks)
            cache[key] = run_backtest(bars, lo, sh, stop, cfg.exits, cfg.costs)
        return cache[key]

    out = []
    if cfg.benchmark_random:
        rnd_params = {k: cfg.setup_params[k] for k in ("sl_atr", "tf") if k in cfg.setup_params}
        rnd = StrategySpec("random", rnd_params, cfg.base_filters, cfg.exits)
        lo, sh, stop, _ = build_signals(ctx, rnd)
        t = run_backtest(bars, lo, sh, stop, cfg.exits, cfg.costs)
        out.append({"variante": "benchmark aleatorio", "probado": None, **stats.summary(t["r"]), **stats.bootstrap_mean(t["r"])})

    for label, var_f, parent_f, tested in plan(cfg, mode):
        t = run(var_f)
        row = {"variante": label, "probado": tested, **stats.summary(t["r"]), **stats.bootstrap_mean(t["r"])}
        if tested is not None:
            parent = run(parent_f)
            allow = stats.tag_trades(parent, *masks_all.get(tested) or _masks_for(ctx, cfg, tested))
            kept, removed = parent["r"].to_numpy()[allow], parent["r"].to_numpy()[~allow]
            better = stats.permutation_diff(kept, removed)
            worse = stats.permutation_diff(removed, kept)
            row.update({"padre_n": len(parent), "conserva_exp": _mean(kept), "elimina_exp": _mean(removed),
                        "elimina_n": len(removed), "p_aporta": better["p_value"], "p_empeora": worse["p_value"]})
        out.append(row)

    df = pd.DataFrame(out)
    if "p_aporta" in df:
        tested_rows = df["probado"].notna()
        df.loc[tested_rows, "p_aporta_holm"] = stats.holm(df.loc[tested_rows, "p_aporta"].tolist())
        df.loc[tested_rows, "p_empeora_holm"] = stats.holm(df.loc[tested_rows, "p_empeora"].tolist())
        df["veredicto"] = [_verdict(r, cfg.min_trades) for r in df.to_dict("records")]
    return df


def _masks_for(ctx, cfg, name):
    comp, p = comps.resolve(name, dict(cfg.filters).get(name, {}))
    return comp.fn(ctx, **p)


def _mean(x):
    return float(np.mean(x)) if len(x) else np.nan


def _verdict(r: dict, min_trades: int) -> str:
    if pd.isna(r.get("probado")):
        return ""
    if r["n"] < min_trades or r.get("elimina_n", 0) < 10:
        return "datos insuficientes"
    if r["p_aporta_holm"] < ALPHA:
        return "✅ aporta valor"
    if r["p_empeora_holm"] < ALPHA:
        return "❌ empeora"
    return "➖ sin evidencia"


def report(name: str, mode: str, is_df: pd.DataFrame, oos_df: pd.DataFrame | None) -> str:
    cols = ["variante", "n", "win_rate", "expectancy_r", "ci_low", "ci_high", "p_gt_0", "profit_factor", "max_dd_r"]
    extra = ["conserva_exp", "elimina_exp", "p_aporta_holm", "veredicto"]
    lines = [f"# {name} — modo `{mode}`", "",
             "Expectativa en R por operación, costes incluidos. IC 95% bootstrap. `p_gt_0`: H0 expectativa ≤ 0.",
             "Decisiones SOLO con in-sample. El out-of-sample se mira una vez, para confirmar.", "",
             "## In-sample", "", _md(is_df[[c for c in cols + extra if c in is_df]])]
    if oos_df is not None and len(oos_df):
        lines += ["", "## Out-of-sample (validación)", "", _md(oos_df[[c for c in cols if c in oos_df]])]
    return "\n".join(lines) + "\n"


def _md(df: pd.DataFrame) -> str:
    def fmt(v):
        if isinstance(v, float):
            return "" if np.isnan(v) else f"{v:.3f}"
        return "" if v is None else str(v)
    head = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "---|" * len(df.columns)
    body = ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *body])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--mode", choices=["ladder", "single", "loo"], default="ladder")
    ap.add_argument("--synthetic", action="store_true", help="usa barras sintéticas (sin ventaja) en vez del CSV")
    ap.add_argument("--out", default="results")
    ap.add_argument("--sin-costes", action="store_true", help="spread y deslizamiento a 0: mide la ventaja bruta de la señal")
    ap.add_argument("--validate", action="store_true",
                    help="evalúa también el out-of-sample. Solo al final, para confirmar: si se mira antes, deja de ser validación")
    a = ap.parse_args(argv)

    cfg = load_config(a.config)
    bars = synthetic_bars(60_000) if a.synthetic else load_mt5_csv(cfg.data_path, cfg.spec.point, cfg.broker_tz)
    if a.sin_costes:
        bars = bars.assign(spread=0.0)
        cfg = dataclasses.replace(cfg, costs=Costs(), name=cfg.name + "_sin_costes")
    is_bars, oos_bars = split_by_date(bars, None if a.synthetic else cfg.in_sample_until)
    is_df = evaluate(is_bars, cfg, a.mode)
    oos_df = evaluate(oos_bars, cfg, a.mode) if a.validate and len(oos_bars) else None

    out = Path(a.out) / cfg.name
    out.mkdir(parents=True, exist_ok=True)
    is_df.to_csv(out / f"{a.mode}_in_sample.csv", index=False)
    if oos_df is not None:
        oos_df.to_csv(out / f"{a.mode}_out_of_sample.csv", index=False)
    md = report(cfg.name, a.mode, is_df, oos_df)
    (out / f"{a.mode}.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
