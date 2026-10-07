# Registro de investigación

Una entrada por experimento. Separar siempre **lo que creemos** de **lo que los datos
demuestran**. Un componente solo pasa a "demostrado" con veredicto ✅ en in-sample y
confirmación en out-of-sample.

## Estado de los componentes

| Componente | Creemos | Datos (in-sample) | Out-of-sample | Estado |
|---|---|---|---|---|
| trend_m5 | filtra contra-tendencia | ❌ oro, ➖ NAS | — | probado con stop 1·ATR M1 |
| ema_9_20 | | ❌ ambos | — | probado con stop 1·ATR M1 |
| vwap | | ✅ ambos (+~0.03 R) | — | probado con stop 1·ATR M1 |
| opening_range | | ✅ NAS, ➖ oro | — | probado con stop 1·ATR M1 |
| structure_break | | ❌ ambos | — | probado con stop 1·ATR M1 |
| impulse | | ❌ ambos | — | probado con stop 1·ATR M1 |
| pullback | | ✅ ambos (+~0.03 R) | — | probado con stop 1·ATR M1 |
| retest | | — | — | sin implementar |
| rejection_candle | | ✅ NAS, ➖ oro | — | probado con stop 1·ATR M1 |
| wick_body_ratio | | ❌ ambos | — | probado con stop 1·ATR M1 |
| volume | | ❌ ambos | — | probado con stop 1·ATR M1 |
| volatility | | ✅ ambos (reduce coste relativo) | — | probado con stop 1·ATR M1 |
| spread | | ✅ ambos (reduce coste relativo) | — | probado con stop 1·ATR M1 |
| session_hours | | ✅ ambos (reduce coste relativo) | — | probado con stop 1·ATR M1 |
| score | | — | — | sin implementar |
| gestión 1:2 / 1:3 | | — | — | sin probar |

## Plantilla de experimento

```
### AAAA-MM-DD · <instrumento> · <config> · modo <single|ladder|loo>
Hipótesis:
Datos: <periodo in-sample> / <periodo out-of-sample>, coste supuesto
Resultado (con tabla de results/):
Qué demuestra:
Qué NO demuestra:
Decisión / siguiente hipótesis:
```

## Experimentos

### 2026-10-07 · XAUUSD y NAS100 · xauusd_v1 / nas100_v1 · modo single

**Hipótesis:** el baseline (ruptura de 5 barras M1, stop 1·ATR, 1:2, salida a 30 min) tiene ventaja y algunos filtros la mejoran.

**Datos:** Exness XAUUSDm / USTECm M1, in-sample 27/10/2021 → 30/06/2025 (out-of-sample sin mirar). Coste: spread de cada barra + deslizamiento 0.05 (oro) / 0.3 (NAS) en entrada y salida.

**Resultado:**

- Baseline: **−0.69 R** por operación en oro y **−0.90 R** en NAS100. Peor que el benchmark aleatorio (−0.60 / −0.81).
- Sin costes, el baseline queda en ≈ 0 R (oro −0.005 [−0.012, +0.001]; NAS +0.009 [+0.003, +0.016]). La señal de ruptura no tiene dirección útil; casi toda la pérdida es coste.
- Coste ida y vuelta / riesgo (stop 1·ATR M1), mediana: **0.57 R en oro**, **0.94 R en NAS100**. En las 2 h tras la apertura de NY baja a 0.28 / 0.39 R.
- Filtros con ✅ en los dos instrumentos: `spread`, `session_hours`, `volatility`, `vwap`, `pullback`. Los tres primeros mejoran mucho (oro hasta −0.18 R, NAS −0.11 R con `spread`) porque eligen momentos donde el coste es menor respecto al stop, no porque acierten la dirección. `vwap` y `pullback` mejoran poco (~0.03 R) pero de forma consistente en ambos.
- Solo en NAS100: `rejection_candle` y `opening_range` ✅. En oro, ➖.
- ❌ en ambos: `ema_9_20`, `structure_break`, `impulse`, `volume`, `wick_body_ratio`. `trend_m5`: ❌ en oro, ➖ en NAS.
- Ninguna variante tiene expectativa > 0 (todas con p ≈ 1).

**Qué demuestra:** a escala M1 con stop de 1·ATR la estrategia no es viable con los costes de Exness; el coste por sí solo es 0.6–0.9 R.

**Qué NO demuestra:** que los filtros ✅ den una ventaja direccional; con este nivel de coste dominan los filtros que reducen el coste relativo. Tampoco que los ❌ no sirvan en otra escala de stop.

**Observación de método:** sin costes, el benchmark aleatorio sale ligeramente positivo (+0.02 R) por la deriva alcista de ambos activos en el periodo; conviene compararlo también por lado (largos/cortos).

**Siguiente hipótesis:** subir la escala del riesgo para que el coste pese < 0.15 R (stop más ancho o setup en M5) y operar solo en la ventana de apertura; repetir `single` con los filtros.

<details><summary>Tabla oro (in-sample)</summary>

| variante | n | win_rate | expectancy_r | ci_low | ci_high | p_gt_0 | profit_factor | max_dd_r | conserva_exp | elimina_exp | p_aporta_holm | veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark aleatorio | 24601 | 0.169 | -0.598 | -0.613 | -0.584 | 1.000 | 0.359 | 14721.056 |  |  |  |  |
| baseline | 214403 | 0.145 | -0.689 | -0.693 | -0.684 | 1.000 | 0.295 | 147640.760 |  |  |  |  |
| baseline + trend_m5 | 131261 | 0.147 | -0.680 | -0.687 | -0.674 | 1.000 | 0.300 | 89319.112 | -0.694 | -0.681 | 1.000 | ❌ empeora |
| baseline + vwap | 130386 | 0.151 | -0.666 | -0.672 | -0.660 | 1.000 | 0.310 | 86874.182 | -0.673 | -0.709 | 0.003 | ✅ aporta valor |
| baseline + rejection_candle | 188996 | 0.147 | -0.682 | -0.687 | -0.677 | 1.000 | 0.299 | 128836.587 | -0.690 | -0.681 | 1.000 | ➖ sin evidencia |
| baseline + volume | 82844 | 0.150 | -0.668 | -0.676 | -0.660 | 1.000 | 0.308 | 55327.652 | -0.697 | -0.684 | 1.000 | ❌ empeora |
| baseline + ema_9_20 | 155896 | 0.146 | -0.685 | -0.690 | -0.679 | 1.000 | 0.297 | 106741.817 | -0.702 | -0.663 | 1.000 | ❌ empeora |
| baseline + opening_range | 80341 | 0.148 | -0.675 | -0.683 | -0.668 | 1.000 | 0.304 | 54256.234 | -0.685 | -0.690 | 1.000 | ➖ sin evidencia |
| baseline + structure_break | 139346 | 0.145 | -0.686 | -0.692 | -0.680 | 1.000 | 0.296 | 95570.112 | -0.709 | -0.661 | 1.000 | ❌ empeora |
| baseline + impulse | 68744 | 0.132 | -0.738 | -0.746 | -0.730 | 1.000 | 0.262 | 50705.239 | -0.743 | -0.664 | 1.000 | ❌ empeora |
| baseline + pullback | 156697 | 0.148 | -0.678 | -0.683 | -0.672 | 1.000 | 0.302 | 106186.140 | -0.680 | -0.712 | 0.003 | ✅ aporta valor |
| baseline + wick_body_ratio | 22196 | 0.151 | -0.658 | -0.673 | -0.643 | 1.000 | 0.313 | 14614.513 | -0.794 | -0.682 | 1.000 | ❌ empeora |
| baseline + volatility | 127707 | 0.184 | -0.532 | -0.538 | -0.525 | 1.000 | 0.406 | 67950.309 | -0.532 | -0.912 | 0.003 | ✅ aporta valor |
| baseline + spread | 19238 | 0.283 | -0.181 | -0.201 | -0.162 | 1.000 | 0.755 | 3485.141 | -0.178 | -0.738 | 0.003 | ✅ aporta valor |
| baseline + session_hours | 15282 | 0.250 | -0.295 | -0.315 | -0.274 | 1.000 | 0.626 | 4513.913 | -0.294 | -0.719 | 0.003 | ✅ aporta valor |

</details>

<details><summary>Tabla NAS100 (in-sample)</summary>

| variante | n | win_rate | expectancy_r | ci_low | ci_high | p_gt_0 | profit_factor | max_dd_r | conserva_exp | elimina_exp | p_aporta_holm | veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark aleatorio | 24362 | 0.092 | -0.807 | -0.818 | -0.796 | 1.000 | 0.183 | 19654.659 |  |  |  |  |
| baseline | 266420 | 0.065 | -0.899 | -0.902 | -0.896 | 1.000 | 0.125 | 239401.916 |  |  |  |  |
| baseline + trend_m5 | 156029 | 0.069 | -0.887 | -0.891 | -0.883 | 1.000 | 0.133 | 138364.274 | -0.900 | -0.897 | 1.000 | ➖ sin evidencia |
| baseline + vwap | 155746 | 0.073 | -0.873 | -0.877 | -0.869 | 1.000 | 0.141 | 135889.142 | -0.881 | -0.922 | 0.003 | ✅ aporta valor |
| baseline + rejection_candle | 225492 | 0.069 | -0.886 | -0.890 | -0.883 | 1.000 | 0.133 | 199876.978 | -0.894 | -0.921 | 0.003 | ✅ aporta valor |
| baseline + volume | 81190 | 0.072 | -0.880 | -0.885 | -0.874 | 1.000 | 0.140 | 71413.112 | -0.907 | -0.895 | 1.000 | ❌ empeora |
| baseline + ema_9_20 | 186234 | 0.068 | -0.889 | -0.893 | -0.885 | 1.000 | 0.131 | 165585.824 | -0.906 | -0.883 | 1.000 | ❌ empeora |
| baseline + opening_range | 98493 | 0.071 | -0.879 | -0.885 | -0.875 | 1.000 | 0.137 | 86627.462 | -0.889 | -0.904 | 0.003 | ✅ aporta valor |
| baseline + structure_break | 167889 | 0.068 | -0.889 | -0.892 | -0.885 | 1.000 | 0.131 | 149193.062 | -0.908 | -0.885 | 1.000 | ❌ empeora |
| baseline + impulse | 82851 | 0.064 | -0.905 | -0.910 | -0.900 | 1.000 | 0.122 | 74978.393 | -0.911 | -0.893 | 1.000 | ❌ empeora |
| baseline + pullback | 190443 | 0.068 | -0.890 | -0.893 | -0.886 | 1.000 | 0.131 | 169416.960 | -0.892 | -0.915 | 0.003 | ✅ aporta valor |
| baseline + wick_body_ratio | 22715 | 0.088 | -0.824 | -0.836 | -0.812 | 1.000 | 0.173 | 18718.262 | -0.948 | -0.895 | 1.000 | ❌ empeora |
| baseline + volatility | 132458 | 0.078 | -0.833 | -0.837 | -0.828 | 1.000 | 0.156 | 110295.636 | -0.836 | -0.959 | 0.003 | ✅ aporta valor |
| baseline + spread | 6683 | 0.305 | -0.110 | -0.144 | -0.076 | 1.000 | 0.845 | 761.307 | -0.110 | -0.919 | 0.003 | ✅ aporta valor |
| baseline + session_hours | 17013 | 0.200 | -0.429 | -0.447 | -0.411 | 1.000 | 0.480 | 7301.611 | -0.429 | -0.931 | 0.003 | ✅ aporta valor |

</details>
