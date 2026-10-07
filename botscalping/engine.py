"""Motor de backtest barra a barra.

Supuestos (deliberadamente conservadores):

* La señal se evalúa al cierre de la barra ``i``; la entrada es a la apertura de ``i+1``.
* Precios de las barras = bid. Largo compra al ask (bid + spread) y sale al bid; corto vende
  al bid y recompra al ask. El spread de cada barra se usa tal cual.
* Si en una misma barra se tocan stop y take profit, se asume que salta el STOP.
* Si la barra abre más allá del stop (gap), se sale a la apertura, no al stop.
* Una sola posición a la vez. Se cierra por stop, objetivo o tiempo máximo (``max_bars``).
* El resultado se mide en R = beneficio / riesgo inicial (distancia de stop).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import components as comps
from .data import InstrumentSpec


@dataclass(frozen=True)
class Costs:
    commission: float = 0.0  # en precio, por operación completa
    slippage: float = 0.0  # en precio, en entrada y en salida a mercado/stop


@dataclass(frozen=True)
class Exits:
    rr: float = 2.0
    max_bars: int = 30


@dataclass
class StrategySpec:
    setup: str
    setup_params: dict
    filters: list[tuple[str, dict]]
    exits: Exits

    def label(self) -> str:
        return " + ".join([self.setup] + [f for f, _ in self.filters]) or self.setup


def build_signals(ctx: comps.Context, strat: StrategySpec):
    """Devuelve (long, short, stop_dist, filter_masks) con los filtros aplicados.

    ``filter_masks`` guarda, para cada filtro, sus arrays (allow_long, allow_short), útil para
    etiquetar operaciones y medir qué quita cada filtro."""
    setup, params = comps.resolve(strat.setup, strat.setup_params)
    long_, short_, stop = setup.fn(ctx, **params)
    long_, short_ = long_.copy(), short_.copy()
    masks = {}
    for name, fparams in strat.filters:
        comp, p = comps.resolve(name, fparams)
        if comp.kind != "filter":
            raise ValueError(f"'{name}' no es un filtro")
        al, as_ = comp.fn(ctx, **p)
        masks[name] = (al, as_)
        long_ &= al
        short_ &= as_
    return long_, short_, stop, masks


def run_backtest(bars: pd.DataFrame, long_: np.ndarray, short_: np.ndarray, stop_dist: np.ndarray,
                 exits: Exits, costs: Costs = Costs()) -> pd.DataFrame:
    o, h, l, c = (bars[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    spr = bars["spread"].to_numpy(float)
    idx = bars.index
    n = len(bars)
    valid = np.isfinite(stop_dist) & (stop_dist > 0)
    sig = np.flatnonzero((long_ | short_) & valid)
    trades = []
    next_free = 0  # primera barra en la que se puede evaluar una nueva señal
    for i in sig:
        if i < next_free or i + 1 >= n:
            continue
        side = 1 if long_[i] else -1  # si coinciden ambos, prima el largo (raro; documentado)
        d = stop_dist[i]
        e = i + 1
        if side == 1:
            entry = o[e] + spr[e] + costs.slippage
            sl, tp = entry - d, entry + exits.rr * d
        else:
            entry = o[e] - costs.slippage
            sl, tp = entry + d, entry - exits.rr * d
        exit_px, reason, j = np.nan, "time", e
        last = min(n - 1, e + exits.max_bars - 1)
        for j in range(e, last + 1):
            if side == 1:
                if o[j] <= sl and j > e:
                    exit_px, reason = o[j] - costs.slippage, "stop_gap"; break
                if l[j] <= sl:
                    exit_px, reason = sl - costs.slippage, "stop"; break
                if h[j] >= tp:
                    exit_px, reason = tp, "target"; break
            else:
                ask_o, ask_h, ask_l = o[j] + spr[j], h[j] + spr[j], l[j] + spr[j]
                if ask_o >= sl and j > e:
                    exit_px, reason = ask_o + costs.slippage, "stop_gap"; break
                if ask_h >= sl:
                    exit_px, reason = sl + costs.slippage, "stop"; break
                if ask_l <= tp:
                    exit_px, reason = tp, "target"; break
        else:
            j = last
            exit_px = (c[j] - costs.slippage) if side == 1 else (c[j] + spr[j] + costs.slippage)
        pnl = (exit_px - entry) * side - costs.commission
        trades.append((idx[i], idx[e], idx[j], i, side, entry, exit_px, d, pnl / d, reason, j - e + 1))
        next_free = j  # al cierre de la barra de salida ya estamos fuera: puede haber nueva señal
    cols = ["signal_time", "entry_time", "exit_time", "signal_idx", "side", "entry", "exit", "risk", "r", "reason", "bars"]
    return pd.DataFrame(trades, columns=cols)


def backtest_strategy(bars: pd.DataFrame, spec: InstrumentSpec, strat: StrategySpec, costs: Costs = Costs()):
    ctx = comps.Context(bars, spec)
    long_, short_, stop, masks = build_signals(ctx, strat)
    trades = run_backtest(bars, long_, short_, stop, strat.exits, costs)
    return trades, ctx
