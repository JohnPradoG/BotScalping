"""Motor de backtest barra a barra.

Supuestos (deliberadamente conservadores):

* La señal se evalúa al cierre de la barra ``i``; la entrada es a la apertura de ``i+1``.
* Precios de las barras = bid. Largo compra al ask (bid + spread) y sale al bid; corto vende
  al bid y recompra al ask. El spread de cada barra se usa tal cual.
* Si en una misma barra se tocan stop y take profit, se asume que salta el STOP.
* Si la barra abre más allá del stop (gap), se sale a la apertura, no al stop.
* Una sola posición a la vez. Se cierra por stop, objetivo o tiempo máximo (``max_bars``).
* Salidas dinámicas opcionales ("dejarla correr y cerrar si se gira"): break-even, stop
  dinámico (trailing) a k·ATR del mejor precio y cierre si una vela cierra al otro lado de la
  EMA. Se actualizan con la barra ya CERRADA y se aplican desde la barra siguiente.
* El resultado se mide en R = beneficio / riesgo inicial (distancia de stop).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import components as comps
from . import indicators as ind
from .data import InstrumentSpec


@dataclass(frozen=True)
class Costs:
    commission: float = 0.0  # en precio, por operación completa
    slippage: float = 0.0  # en precio, en entrada y en salida a mercado/stop


@dataclass(frozen=True)
class Exits:
    rr: float = 2.0  # <= 0: sin objetivo fijo
    max_bars: int = 30
    breakeven_r: float = 0.0  # > 0: al ir +x R a favor, el stop pasa a la entrada
    trail_atr: float = 0.0  # > 0: stop dinámico a k·ATR del mejor precio alcanzado
    trail_start_r: float = 0.0  # el trailing se activa al ir +x R a favor
    exit_ema: int = 0  # > 0: cierra si una vela cierra al otro lado de esta EMA (se "devuelve")


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
    atr = ind.atr(bars).to_numpy() if exits.trail_atr > 0 else None
    ema = ind.ema(bars["close"], exits.exit_ema).to_numpy() if exits.exit_ema > 0 else None
    no_tp = exits.rr <= 0
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
            sl, tp = entry - d, (np.inf if no_tp else entry + exits.rr * d)
        else:
            entry = o[e] - costs.slippage
            sl, tp = entry + d, (-np.inf if no_tp else entry - exits.rr * d)
        best = entry
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
                best = max(best, h[j])
                if ema is not None and c[j] < ema[j]:
                    exit_px, reason = c[j] - costs.slippage, "reversal"; break
                if exits.breakeven_r > 0 and best - entry >= exits.breakeven_r * d:
                    sl = max(sl, entry)
                if atr is not None and best - entry >= exits.trail_start_r * d:
                    sl = max(sl, best - exits.trail_atr * atr[j])
            else:
                ask_o, ask_h, ask_l = o[j] + spr[j], h[j] + spr[j], l[j] + spr[j]
                if ask_o >= sl and j > e:
                    exit_px, reason = ask_o + costs.slippage, "stop_gap"; break
                if ask_h >= sl:
                    exit_px, reason = sl + costs.slippage, "stop"; break
                if ask_l <= tp:
                    exit_px, reason = tp, "target"; break
                best = min(best, ask_l)
                if ema is not None and c[j] > ema[j]:
                    exit_px, reason = c[j] + spr[j] + costs.slippage, "reversal"; break
                if exits.breakeven_r > 0 and entry - best >= exits.breakeven_r * d:
                    sl = min(sl, entry)
                if atr is not None and entry - best >= exits.trail_start_r * d:
                    sl = min(sl, best + exits.trail_atr * atr[j])
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
