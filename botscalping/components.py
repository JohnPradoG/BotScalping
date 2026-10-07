"""Componentes intercambiables de la estrategia.

Hay dos tipos:

* **setup**: genera las entradas candidatas (dirección + distancia de stop). Exactamente uno
  por estrategia. El *baseline* es un setup sin ningún filtro.
* **filter**: devuelve, barra a barra, si se PERMITE operar en largo y/o en corto. Un filtro
  nunca crea operaciones, solo elimina candidatas. Así se puede medir exactamente qué
  operaciones quita y si las que quita eran peores que las que deja.

Cada componente se registra con un nombre y parámetros por defecto, y se activa o desactiva
desde el fichero de configuración, sin tocar código.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from . import indicators as ind
from .data import InstrumentSpec

LongShort = tuple[np.ndarray, np.ndarray]


class Context:
    """Barras + caché de indicadores compartidos entre componentes."""

    def __init__(self, bars: pd.DataFrame, spec: InstrumentSpec):
        self.bars = bars
        self.spec = spec
        self._cache: dict = {}

    def cached(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def atr(self, n: int = 14) -> pd.Series:
        return self.cached(("atr", n), lambda: ind.atr(self.bars, n))

    def ema(self, n: int) -> pd.Series:
        return self.cached(("ema", n), lambda: ind.ema(self.bars["close"], n))

    def session(self) -> pd.DataFrame:
        return self.cached(
            "session", lambda: ind.session_frame(self.bars.index, self.spec.session_tz, self.spec.session_open)
        )


@dataclass(frozen=True)
class Component:
    name: str
    kind: str  # "setup" | "filter"
    fn: Callable
    defaults: dict = field(default_factory=dict)
    description: str = ""


REGISTRY: dict[str, Component] = {}


def register(name: str, kind: str, description: str, **defaults):
    def deco(fn):
        REGISTRY[name] = Component(name, kind, fn, defaults, description)
        return fn

    return deco


def get(name: str) -> Component:
    if name not in REGISTRY:
        raise KeyError(f"Componente desconocido '{name}'. Disponibles: {sorted(REGISTRY)}")
    return REGISTRY[name]


def _arr(s: pd.Series) -> np.ndarray:
    return s.fillna(False).to_numpy(bool)


# --------------------------------------------------------------------------- setups
@register("breakout", "setup", "Baseline: cierre rompe el máximo/mínimo de las N barras previas del marco `tf`; stop = sl_atr·ATR(tf).", lookback=5, sl_atr=1.0, tf="1min")
def setup_breakout(ctx: Context, lookback: int, sl_atr: float, tf: str):
    if pd.Timedelta(tf) == pd.Timedelta("1min"):
        b = ctx.bars
        prev_hi = b["high"].rolling(lookback).max().shift()
        prev_lo = b["low"].rolling(lookback).min().shift()
        stop = (ctx.atr() * sl_atr).to_numpy()
        return _arr(b["close"] > prev_hi), _arr(b["close"] < prev_lo), stop
    # Marco superior: la señal se evalúa al cierre de la barra de `tf` y se entra en la siguiente M1.
    htf = ind.resample_ohlc(ctx.bars, tf)
    prev_hi = htf["high"].rolling(lookback).max().shift()
    prev_lo = htf["low"].rolling(lookback).min().shift()
    long_ = ind.align_higher_tf_events(htf["close"] > prev_hi, ctx.bars.index, tf)
    short_ = ind.align_higher_tf_events(htf["close"] < prev_lo, ctx.bars.index, tf)
    stop = (ind.align_higher_tf(ind.atr(htf), ctx.bars.index, tf) * sl_atr).to_numpy()
    return long_, short_, stop


@register("random", "setup", "Benchmark: entradas al azar con la misma gestión. Si un setup no le gana, no tiene ventaja.", prob=0.02, sl_atr=1.0, seed=0, tf="1min")
def setup_random(ctx: Context, prob: float, sl_atr: float, seed: int, tf: str):
    rng = np.random.default_rng(seed)
    n = len(ctx.bars)
    hit = rng.random(n) < prob
    side = rng.random(n) < 0.5
    if pd.Timedelta(tf) == pd.Timedelta("1min"):
        atr = ctx.atr()
    else:
        atr = ind.align_higher_tf(ind.atr(ind.resample_ohlc(ctx.bars, tf)), ctx.bars.index, tf)
    stop = (atr * sl_atr).to_numpy()
    return hit & side, hit & ~side, stop


# -------------------------------------------------------------------------- filtros
@register("trend_m5", "filter", "Tendencia M5: cierre M5 por encima/debajo de su EMA (sin lookahead).", ema=20)
def f_trend_m5(ctx: Context, ema: int) -> LongShort:
    m5 = ind.resample_ohlc(ctx.bars, "5min")
    diff = m5["close"] - ind.ema(m5["close"], ema)
    aligned = ind.align_higher_tf(diff, ctx.bars.index, "5min")
    return _arr(aligned > 0), _arr(aligned < 0)


@register("ema_9_20", "filter", "EMA 9 por encima (largos) / debajo (cortos) de EMA 20 en M1.", fast=9, slow=20)
def f_ema_cross(ctx: Context, fast: int, slow: int) -> LongShort:
    d = ctx.ema(fast) - ctx.ema(slow)
    return _arr(d > 0), _arr(d < 0)


@register("vwap", "filter", "Precio por encima (largos) / debajo (cortos) del VWAP anclado a la apertura.")
def f_vwap(ctx: Context) -> LongShort:
    vwap = ctx.cached("vwap", lambda: ind.anchored_vwap(ctx.bars, ctx.session()["session_date"]))
    c = ctx.bars["close"]
    return _arr(c > vwap), _arr(c < vwap)


@register("opening_range", "filter", "Solo largos sobre el máximo / cortos bajo el mínimo del Opening Range.", minutes=15)
def f_opening_range(ctx: Context, minutes: int) -> LongShort:
    orng = ind.opening_range(ctx.bars, ctx.session(), minutes)
    c = ctx.bars["close"]
    return _arr(c > orng["or_high"]), _arr(c < orng["or_low"])


@register("structure_break", "filter", "Ruptura de estructura: cierre más allá del último swing confirmado.", k=3)
def f_structure(ctx: Context, k: int) -> LongShort:
    sw = ind.swing_levels(ctx.bars, k)
    c = ctx.bars["close"]
    return _arr(c > sw["swing_high"]), _arr(c < sw["swing_low"])


@register("impulse", "filter", "Hubo una vela de impulso (cuerpo > k·ATR) a favor en las últimas N barras.", k=1.5, within=10)
def f_impulse(ctx: Context, k: float, within: int) -> LongShort:
    b = ctx.bars
    body = b["close"] - b["open"]
    a = ctx.atr()
    up = ind.bars_since(body > k * a) < within
    dn = ind.bars_since(body < -k * a) < within
    return _arr(up), _arr(dn)


@register("pullback", "filter", "Retroceso: el precio tocó la EMA lenta en las últimas N barras.", ema=20, within=5)
def f_pullback(ctx: Context, ema: int, within: int) -> LongShort:
    b = ctx.bars
    e = ctx.ema(ema)
    touched_long = ind.bars_since(b["low"] <= e) < within
    touched_short = ind.bars_since(b["high"] >= e) < within
    return _arr(touched_long), _arr(touched_short)


@register("rejection_candle", "filter", "Vela de rechazo: cierra en el tercio favorable de su rango.", close_pos=0.66)
def f_rejection(ctx: Context, close_pos: float) -> LongShort:
    b = ctx.bars
    rng = (b["high"] - b["low"]).replace(0, np.nan)
    pos = (b["close"] - b["low"]) / rng
    return _arr(pos >= close_pos), _arr(pos <= 1 - close_pos)


@register("wick_body_ratio", "filter", "Mecha contraria / cuerpo >= ratio (rechazo fuerte).", ratio=1.5)
def f_wick_body(ctx: Context, ratio: float) -> LongShort:
    b = ctx.bars
    body = (b["close"] - b["open"]).abs().clip(lower=1e-9)
    lower = b[["open", "close"]].min(axis=1) - b["low"]
    upper = b["high"] - b[["open", "close"]].max(axis=1)
    return _arr(lower / body >= ratio), _arr(upper / body >= ratio)


@register("volume", "filter", "Tick volume de la barra > mult × media de N barras.", mult=1.2, n=20)
def f_volume(ctx: Context, mult: float, n: int) -> LongShort:
    v = ctx.bars["tick_volume"]
    ok = _arr(v > mult * v.rolling(n).mean().shift())
    return ok, ok


@register("volatility", "filter", "ATR relativo (ATR / mediana de ATR de N barras) dentro de [lo, hi].", lo=0.8, hi=2.5, n=1000)
def f_volatility(ctx: Context, lo: float, hi: float, n: int) -> LongShort:
    a = ctx.atr()
    rel = a / a.rolling(n, min_periods=n // 4).median()
    ok = _arr((rel >= lo) & (rel <= hi))
    return ok, ok


@register("spread", "filter", "Spread <= max_atr × ATR (el coste no se come el movimiento).", max_atr=0.15)
def f_spread(ctx: Context, max_atr: float) -> LongShort:
    ok = _arr(ctx.bars["spread"] <= max_atr * ctx.atr())
    return ok, ok


@register("session_hours", "filter", "Solo opera entre start y end minutos desde la apertura de sesión.", start=0, end=120)
def f_session_hours(ctx: Context, start: int, end: int) -> LongShort:
    m = ctx.session()["minutes_from_open"]
    ok = _arr((m >= start) & (m < end))
    return ok, ok


# Pendientes (definir con John antes de implementar): "retest" (vuelta al nivel roto
# dentro de N barras con tolerancia en ATR) y "score" (suma ponderada de filtros >= umbral).


def resolve(name: str, params: dict | None = None) -> tuple[Component, dict]:
    comp = get(name)
    merged = {**comp.defaults, **(params or {})}
    unknown = set(merged) - set(comp.defaults)
    if unknown:
        raise ValueError(f"Parámetros desconocidos para '{name}': {sorted(unknown)}")
    return comp, merged
