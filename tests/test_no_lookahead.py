"""Si un componente mira el futuro, su valor en la barra i cambia al añadir barras
posteriores. Aquí se compara el cálculo sobre la serie completa vs truncada."""
import numpy as np
import pytest

from botscalping import components as comps
from botscalping.data import InstrumentSpec, synthetic_bars

SPEC = InstrumentSpec("TEST", 0.01)
BARS = synthetic_bars(4000, seed=3)


@pytest.mark.parametrize("name", sorted(n for n, c in comps.REGISTRY.items() if c.kind == "filter"))
def test_filter_has_no_lookahead(name):
    comp, p = comps.resolve(name)
    full_l, full_s = comp.fn(comps.Context(BARS, SPEC), **p)
    for cut in (1500, 2777, 3333):
        tl, ts = comp.fn(comps.Context(BARS.iloc[:cut], SPEC), **p)
        assert np.array_equal(full_l[:cut], tl), f"{name} largo cambia con datos futuros (cut={cut})"
        assert np.array_equal(full_s[:cut], ts), f"{name} corto cambia con datos futuros (cut={cut})"


def test_breakout_setup_has_no_lookahead():
    comp, p = comps.resolve("breakout")
    fl, fs, fstop = comp.fn(comps.Context(BARS, SPEC), **p)
    tl, ts, tstop = comp.fn(comps.Context(BARS.iloc[:2000], SPEC), **p)
    assert np.array_equal(fl[:2000], tl) and np.array_equal(fs[:2000], ts)
    assert np.allclose(fstop[:2000], tstop, equal_nan=True)


@pytest.mark.parametrize("cut", [2003, 2777])
def test_breakout_m5_has_no_lookahead(cut):
    comp, p = comps.resolve("breakout", {"tf": "5min"})
    fl, fs, fstop = comp.fn(comps.Context(BARS, SPEC), **p)
    tl, ts, tstop = comp.fn(comps.Context(BARS.iloc[:cut], SPEC), **p)
    assert np.array_equal(fl[:cut], tl) and np.array_equal(fs[:cut], ts)
    assert np.allclose(fstop[:cut], tstop, equal_nan=True)
    # una señal M5 aparece solo en la barra M1 que cierra la barra M5 (minuto 4, 9, ...)
    minutes = BARS.index.minute.to_numpy()
    assert set(minutes[fl | fs] % 5) <= {4}
