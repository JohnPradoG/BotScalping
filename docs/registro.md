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

### 2026-10-07 · XAUUSD y NAS100 · Estrategia 2: más riesgo por operación · modo single

**Hipótesis:** si el stop es lo bastante grande para que el coste pese < 0.15 R, la ruptura y algunos filtros muestran ventaja. Condición fija: solo entradas en las 2 h tras la apertura de NY (`session_hours` como filtro de base).

**Paso 1, escala del stop** (in-sample, ruptura de 5 barras, 1:2; `coste_R` = coste ida y vuelta / riesgo, mediana):

<details><summary>Rejilla NAS100</summary>

```
   tf  sl_atr    setup  tipo     n    exp  ci_lo  ci_hi  coste_R  largos_exp  cortos_exp
 1min       1 breakout bruto 15240  0.019 -0.003  0.041      NaN         NaN         NaN
 1min       1 breakout  neto 17013 -0.429 -0.447 -0.411    0.416      -0.419      -0.438
 1min       1   random bruto  2057  0.038 -0.028  0.097      NaN         NaN         NaN
 1min       1   random  neto  2097 -0.358 -0.412 -0.303    0.395      -0.359      -0.358
 1min       3 breakout bruto  4487  0.026 -0.010  0.062      NaN         NaN         NaN
 1min       3 breakout  neto  4877 -0.152 -0.189 -0.117    0.144      -0.153      -0.151
 1min       3   random bruto  1477 -0.036 -0.101  0.025      NaN         NaN         NaN
 1min       3   random  neto  1520 -0.176 -0.232 -0.117    0.132      -0.196      -0.157
 5min       1 breakout bruto  3973  0.008 -0.034  0.053      NaN         NaN         NaN
 5min       1 breakout  neto  4051 -0.224 -0.262 -0.184    0.215      -0.231      -0.217
 5min       1   random bruto  1761 -0.020 -0.084  0.041      NaN         NaN         NaN
 5min       1   random  neto  1793 -0.201 -0.263 -0.143    0.213      -0.232      -0.172
 5min       2 breakout bruto  2521  0.026 -0.024  0.074      NaN         NaN         NaN
 5min       2 breakout  neto  2583 -0.106 -0.153 -0.057    0.112      -0.096      -0.115
 5min       2   random bruto  1361 -0.061 -0.129  0.010      NaN         NaN         NaN
 5min       2   random  neto  1398 -0.160 -0.227 -0.097    0.108      -0.180      -0.140
15min       1 breakout bruto  1742  0.081  0.017  0.149      NaN         NaN         NaN
15min       1 breakout  neto  1750 -0.090 -0.153 -0.026    0.168      -0.078      -0.102
15min       1   random bruto  1655 -0.049 -0.110  0.011      NaN         NaN         NaN
15min       1   random  neto  1684 -0.208 -0.275 -0.151    0.174      -0.254      -0.164
15min       2 breakout bruto  1339  0.081  0.008  0.154      NaN         NaN         NaN
15min       2 breakout  neto  1331 -0.006 -0.077  0.063    0.086      -0.018       0.007
15min       2   random bruto  1250 -0.011 -0.087  0.063      NaN         NaN         NaN
15min       2   random  neto  1270 -0.104 -0.173 -0.033    0.088      -0.136      -0.072
```
</details>

<details><summary>Rejilla oro</summary>

```
   tf  sl_atr    setup  tipo     n    exp  ci_lo  ci_hi  coste_R  largos_exp  cortos_exp
 1min       1 breakout bruto 14621  0.008 -0.015  0.033      NaN         NaN         NaN
 1min       1 breakout  neto 15282 -0.295 -0.316 -0.274    0.287      -0.286      -0.303
 1min       1   random bruto  2085  0.042 -0.022  0.103      NaN         NaN         NaN
 1min       1   random  neto  2111 -0.265 -0.321 -0.210    0.276      -0.266      -0.264
 1min       3 breakout bruto  3914  0.028 -0.010  0.066      NaN         NaN         NaN
 1min       3 breakout  neto  4063 -0.066 -0.103 -0.030    0.098      -0.046      -0.087
 1min       3   random bruto  1460  0.013 -0.043  0.075      NaN         NaN         NaN
 1min       3   random  neto  1474 -0.093 -0.150 -0.039    0.090      -0.133      -0.053
 5min       1 breakout bruto  3131  0.010 -0.039  0.061      NaN         NaN         NaN
 5min       1 breakout  neto  3138 -0.108 -0.152 -0.060    0.126      -0.064      -0.150
 5min       1   random bruto  1617  0.040 -0.023  0.108      NaN         NaN         NaN
 5min       1   random  neto  1647 -0.078 -0.139 -0.013    0.123      -0.099      -0.056
 5min       2 breakout bruto  1835  0.031 -0.027  0.088      NaN         NaN         NaN
 5min       2 breakout  neto  1875 -0.038 -0.092  0.018    0.063      -0.017      -0.060
 5min       2   random bruto  1190 -0.014 -0.076  0.048      NaN         NaN         NaN
 5min       2   random  neto  1204 -0.076 -0.137 -0.011    0.061      -0.106      -0.047
15min       1 breakout bruto  1230 -0.003 -0.083  0.075      NaN         NaN         NaN
15min       1 breakout  neto  1223 -0.066 -0.142  0.003    0.087       0.030      -0.163
15min       1   random bruto  1415  0.023 -0.045  0.093      NaN         NaN         NaN
15min       1   random  neto  1431 -0.086 -0.154 -0.021    0.089      -0.099      -0.073
15min       2 breakout bruto   986  0.034 -0.029  0.102      NaN         NaN         NaN
15min       2 breakout  neto   990 -0.027 -0.095  0.036    0.044       0.035      -0.089
15min       2   random bruto  1050 -0.012 -0.078  0.055      NaN         NaN         NaN
15min       2   random  neto  1055 -0.052 -0.114  0.012    0.045      -0.032      -0.072
```
</details>

- El coste baja de 0.3–0.4 R (stop 1·ATR M1) a **0.06 R (oro) y 0.11 R (NAS) con stop 2·ATR(M5)**, y a 0.04–0.09 R en M15.
- Sin costes, la ruptura no tiene ventaja significativa en ninguna escala salvo NAS100 M15 (+0.08 R, IC [+0.01, +0.15]).

**Paso 2, filtros** con ruptura M5 y M15, stop 2·ATR del mismo marco:

| Config | Stop mediano | Duración mediana | Ops/día | Baseline | Benchmark aleatorio |
|---|---|---|---|---|---|
| oro M5 | 4.81 $ | 63 min | 2.0 | −0.04 R [−0.09, +0.02] | −0.08 R |
| oro M15 | 6.86 $ | 278 min | 1.2 | −0.03 R [−0.09, +0.04] | −0.05 R |
| NAS M5 | 46 pts | 31 min | 2.7 | −0.11 R [−0.15, −0.06] | −0.16 R |
| NAS M15 | 60 pts | 71 min | 1.5 | −0.01 R [−0.08, +0.07] | −0.10 R |

- **Ningún filtro sale ✅ ni ❌ tras la corrección por comparaciones múltiples.** Con 1–2.5 mil operaciones solo se detectan diferencias de ~0.1–0.15 R.
- Pistas (sin significación tras Holm): NAS M15 + `spread` **+0.16 R** (p sin corregir 0.04, 223 ops); oro M15 + `volume` +0.06, + `impulse` +0.05, + `structure_break` +0.01 (eliminan operaciones peores en ~0.15 R); NAS M5 + `opening_range` e `impulse` mejoran ~0.03–0.04 R.
- `trend_m5` y `ema_9_20` no cambian casi nada en M5/M15: la ruptura ya va a favor de la tendencia. **Redundantes** a esta escala.
- La ruptura gana al benchmark aleatorio en las 4 configuraciones (0.02–0.10 R), pero no lo he probado formalmente.

**Qué demuestra:** con stop ≥ 2·ATR(M5) y solo en la apertura de NY, el coste deja de ser el problema. La estrategia pasa de −0.7/−0.9 R a ≈ 0 R.

**Qué NO demuestra:** que exista ventaja. Ninguna variante es positiva con significación. Tampoco que los filtros no sirvan; falta muestra para verlo.

**Siguiente hipótesis:** (1) más muestra: ampliar la ventana (apertura de Londres para el oro, sesión completa de NY) y analizar ambos instrumentos juntos; (2) ladder con las pistas: NAS M15 + spread + impulse + opening_range; oro M15 + volume + impulse + structure_break; (3) definir `retest` y `score`; (4) probar gestión 1:1.5 / 1:3 y salida por tiempo.

<details><summary>Tablas completas</summary>

#### oro M5
| variante | n | win_rate | expectancy_r | ci_low | ci_high | p_gt_0 | profit_factor | max_dd_r | conserva_exp | elimina_exp | p_aporta_holm | veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark aleatorio | 1204 | 0.387 | -0.076 | -0.138 | -0.012 | 0.991 | 0.861 | 106.020 |  |  |  |  |
| baseline | 1875 | 0.391 | -0.038 | -0.091 | 0.017 | 0.924 | 0.931 | 80.109 |  |  |  |  |
| baseline + trend_m5 | 1834 | 0.395 | -0.031 | -0.086 | 0.024 | 0.875 | 0.943 | 64.113 | -0.036 | -0.089 | 1.000 | ➖ sin evidencia |
| baseline + vwap | 1845 | 0.392 | -0.040 | -0.093 | 0.015 | 0.924 | 0.929 | 84.789 | -0.036 | -0.104 | 1.000 | ➖ sin evidencia |
| baseline + rejection_candle | 1402 | 0.414 | -0.008 | -0.069 | 0.055 | 0.604 | 0.985 | 28.779 | -0.029 | -0.048 | 1.000 | ➖ sin evidencia |
| baseline + volume | 1069 | 0.395 | -0.027 | -0.102 | 0.044 | 0.762 | 0.951 | 49.061 | 0.001 | -0.064 | 1.000 | ➖ sin evidencia |
| baseline + ema_9_20 | 1874 | 0.392 | -0.038 | -0.092 | 0.017 | 0.914 | 0.932 | 79.101 | -0.038 | -1.008 |  | datos insuficientes |
| baseline + opening_range | 1309 | 0.391 | -0.055 | -0.116 | 0.008 | 0.961 | 0.898 | 80.767 | -0.065 | -0.014 | 1.000 | ➖ sin evidencia |
| baseline + structure_break | 1804 | 0.389 | -0.047 | -0.102 | 0.009 | 0.951 | 0.915 | 92.306 | -0.048 | 0.047 | 1.000 | ➖ sin evidencia |
| baseline + impulse | 1087 | 0.404 | 0.006 | -0.065 | 0.081 | 0.436 | 1.011 | 29.911 | 0.021 | -0.080 | 0.407 | ➖ sin evidencia |
| baseline + pullback | 987 | 0.385 | -0.089 | -0.160 | -0.013 | 0.992 | 0.843 | 108.156 | -0.086 | -0.013 | 1.000 | ➖ sin evidencia |
| baseline + wick_body_ratio | 842 | 0.406 | -0.035 | -0.114 | 0.046 | 0.807 | 0.935 | 60.471 | -0.043 | -0.037 | 1.000 | ➖ sin evidencia |
| baseline + volatility | 1428 | 0.422 | 0.007 | -0.054 | 0.068 | 0.410 | 1.013 | 27.933 | -0.011 | -0.083 | 0.948 | ➖ sin evidencia |
| baseline + spread | 793 | 0.402 | -0.033 | -0.116 | 0.053 | 0.780 | 0.940 | 31.817 | -0.022 | -0.048 | 1.000 | ➖ sin evidencia |

#### oro M15
| variante | n | win_rate | expectancy_r | ci_low | ci_high | p_gt_0 | profit_factor | max_dd_r | conserva_exp | elimina_exp | p_aporta_holm | veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark aleatorio | 1055 | 0.409 | -0.052 | -0.116 | 0.014 | 0.942 | 0.895 | 94.625 |  |  |  |  |
| baseline | 990 | 0.429 | -0.027 | -0.092 | 0.040 | 0.793 | 0.943 | 46.484 |  |  |  |  |
| baseline + trend_m5 | 990 | 0.429 | -0.027 | -0.092 | 0.040 | 0.793 | 0.943 | 46.484 | -0.027 |  |  | datos insuficientes |
| baseline + vwap | 975 | 0.430 | -0.026 | -0.092 | 0.039 | 0.766 | 0.944 | 47.202 | -0.024 | -0.175 | 1.000 | ➖ sin evidencia |
| baseline + rejection_candle | 564 | 0.436 | -0.032 | -0.121 | 0.058 | 0.760 | 0.933 | 39.310 | 0.003 | -0.052 | 1.000 | ➖ sin evidencia |
| baseline + volume | 272 | 0.452 | 0.062 | -0.073 | 0.193 | 0.168 | 1.138 | 18.797 | 0.069 | -0.053 | 0.569 | ➖ sin evidencia |
| baseline + ema_9_20 | 990 | 0.429 | -0.027 | -0.092 | 0.040 | 0.793 | 0.943 | 46.484 | -0.027 |  |  | datos insuficientes |
| baseline + opening_range | 823 | 0.426 | -0.025 | -0.097 | 0.044 | 0.752 | 0.945 | 44.797 | -0.002 | -0.079 | 0.887 | ➖ sin evidencia |
| baseline + structure_break | 602 | 0.449 | 0.007 | -0.078 | 0.093 | 0.436 | 1.016 | 19.116 | 0.039 | -0.092 | 0.216 | ➖ sin evidencia |
| baseline + impulse | 394 | 0.452 | 0.047 | -0.061 | 0.161 | 0.204 | 1.105 | 16.631 | 0.078 | -0.076 | 0.190 | ➖ sin evidencia |
| baseline + pullback | 289 | 0.426 | -0.050 | -0.174 | 0.074 | 0.775 | 0.899 | 21.495 | 0.020 | -0.039 | 1.000 | ➖ sin evidencia |
| baseline + wick_body_ratio | 339 | 0.419 | -0.085 | -0.190 | 0.023 | 0.944 | 0.822 | 34.771 | -0.058 | -0.019 | 1.000 | ➖ sin evidencia |
| baseline + volatility | 673 | 0.415 | -0.053 | -0.130 | 0.027 | 0.909 | 0.888 | 43.832 | -0.056 | 0.017 | 1.000 | ➖ sin evidencia |
| baseline + spread | 426 | 0.437 | 0.003 | -0.097 | 0.103 | 0.468 | 1.007 | 28.690 | 0.020 | -0.059 | 0.887 | ➖ sin evidencia |

#### NAS100 M5
| variante | n | win_rate | expectancy_r | ci_low | ci_high | p_gt_0 | profit_factor | max_dd_r | conserva_exp | elimina_exp | p_aporta_holm | veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark aleatorio | 1398 | 0.318 | -0.160 | -0.223 | -0.095 | 1.000 | 0.758 | 225.935 |  |  |  |  |
| baseline | 2583 | 0.338 | -0.106 | -0.153 | -0.057 | 1.000 | 0.836 | 278.599 |  |  |  |  |
| baseline + trend_m5 | 2539 | 0.337 | -0.111 | -0.161 | -0.062 | 1.000 | 0.828 | 290.867 | -0.111 | 0.018 | 1.000 | ➖ sin evidencia |
| baseline + vwap | 2504 | 0.340 | -0.102 | -0.152 | -0.054 | 1.000 | 0.842 | 270.394 | -0.108 | -0.054 | 1.000 | ➖ sin evidencia |
| baseline + rejection_candle | 1891 | 0.351 | -0.089 | -0.144 | -0.032 | 0.999 | 0.859 | 193.906 | -0.101 | -0.111 | 1.000 | ➖ sin evidencia |
| baseline + volume | 996 | 0.308 | -0.126 | -0.206 | -0.042 | 0.999 | 0.818 | 135.899 | -0.136 | -0.089 | 1.000 | ➖ sin evidencia |
| baseline + ema_9_20 | 2575 | 0.339 | -0.103 | -0.151 | -0.055 | 1.000 | 0.840 | 272.549 | -0.104 | -0.461 | 1.000 | ➖ sin evidencia |
| baseline + opening_range | 1482 | 0.361 | -0.068 | -0.131 | -0.003 | 0.983 | 0.890 | 121.979 | -0.084 | -0.121 | 1.000 | ➖ sin evidencia |
| baseline + structure_break | 2463 | 0.341 | -0.102 | -0.154 | -0.052 | 1.000 | 0.840 | 256.637 | -0.104 | -0.124 | 1.000 | ➖ sin evidencia |
| baseline + impulse | 1583 | 0.345 | -0.075 | -0.141 | -0.010 | 0.990 | 0.884 | 132.116 | -0.092 | -0.121 | 1.000 | ➖ sin evidencia |
| baseline + pullback | 1512 | 0.315 | -0.158 | -0.222 | -0.095 | 1.000 | 0.765 | 250.953 | -0.163 | -0.055 | 1.000 | ➖ sin evidencia |
| baseline + wick_body_ratio | 1075 | 0.354 | -0.075 | -0.152 | 0.000 | 0.973 | 0.879 | 109.341 | -0.079 | -0.114 | 1.000 | ➖ sin evidencia |
| baseline + volatility | 535 | 0.350 | -0.104 | -0.207 | 0.002 | 0.976 | 0.835 | 59.761 | -0.105 | -0.106 | 1.000 | ➖ sin evidencia |
| baseline + spread | 413 | 0.385 | 0.006 | -0.121 | 0.131 | 0.466 | 1.009 | 25.547 | 0.018 | -0.128 | 0.228 | ➖ sin evidencia |

#### NAS100 M15
| variante | n | win_rate | expectancy_r | ci_low | ci_high | p_gt_0 | profit_factor | max_dd_r | conserva_exp | elimina_exp | p_aporta_holm | veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| benchmark aleatorio | 1270 | 0.327 | -0.104 | -0.175 | -0.035 | 0.998 | 0.843 | 158.769 |  |  |  |  |
| baseline | 1331 | 0.365 | -0.006 | -0.076 | 0.067 | 0.558 | 0.991 | 66.956 |  |  |  |  |
| baseline + trend_m5 | 1331 | 0.365 | -0.006 | -0.076 | 0.067 | 0.558 | 0.991 | 66.956 | -0.006 |  |  | datos insuficientes |
| baseline + vwap | 1295 | 0.367 | -0.004 | -0.076 | 0.070 | 0.536 | 0.993 | 63.623 | -0.005 | -0.032 | 1.000 | ➖ sin evidencia |
| baseline + rejection_candle | 832 | 0.359 | -0.040 | -0.128 | 0.050 | 0.816 | 0.936 | 67.899 | -0.061 | 0.048 | 1.000 | ➖ sin evidencia |
| baseline + volume | 90 | 0.356 | -0.060 | -0.348 | 0.230 | 0.660 | 0.909 | 10.386 | 0.055 | -0.009 | 1.000 | datos insuficientes |
| baseline + ema_9_20 | 1330 | 0.365 | -0.005 | -0.077 | 0.067 | 0.558 | 0.992 | 66.956 | -0.004 | -1.007 | 0.424 | datos insuficientes |
| baseline + opening_range | 971 | 0.364 | -0.022 | -0.104 | 0.063 | 0.717 | 0.964 | 52.269 | -0.048 | 0.048 | 1.000 | ➖ sin evidencia |
| baseline + structure_break | 888 | 0.368 | -0.012 | -0.099 | 0.076 | 0.610 | 0.980 | 58.960 | -0.012 | 0.001 | 1.000 | ➖ sin evidencia |
| baseline + impulse | 520 | 0.362 | 0.007 | -0.107 | 0.123 | 0.453 | 1.012 | 19.655 | 0.019 | -0.018 | 1.000 | ➖ sin evidencia |
| baseline + pullback | 485 | 0.365 | 0.016 | -0.104 | 0.141 | 0.412 | 1.025 | 34.894 | -0.064 | 0.014 | 1.000 | ➖ sin evidencia |
| baseline + wick_body_ratio | 468 | 0.353 | -0.071 | -0.189 | 0.048 | 0.881 | 0.888 | 58.929 | -0.129 | 0.034 | 1.000 | ➖ sin evidencia |
| baseline + volatility | 228 | 0.355 | -0.129 | -0.281 | 0.030 | 0.953 | 0.789 | 32.517 | -0.205 | 0.018 | 1.000 | ➖ sin evidencia |
| baseline + spread | 223 | 0.417 | 0.163 | -0.014 | 0.349 | 0.040 | 1.289 | 9.928 | 0.164 | -0.040 | 0.227 | ➖ sin evidencia |

</details>

### 2026-10-07 · XAUUSD y NAS100 · Búsqueda amplia (`python -m botscalping.search`)

**Hipótesis (idea de John):** entrar en las mechas (barridas de liquidez) o en la ruptura del rango de apertura, con gestión 1:1 a 1:2, da una ventaja neta.

**Qué se probó (in-sample):** 120 variantes por instrumento: `sweep` (barrida con mecha y cierre de vuelta; M1/M5/M15; lookback 10/20), `orb` (rango de apertura 15/30 min; stop 1–2·ATR M5), `breakout` M5/M15 como referencia. Gestión 1:1, 1:1.5, 1:2. Ventanas: apertura NY 2 h, sesión NY, apertura Londres 2 h, todo el día. Además, momentum intradía (señal de la primera media hora → operar la última media hora).

**Resultado:**

- **Netas de costes: 0 de 240 variantes con expectativa positiva estable.** Ninguna candidata llegó a la validación out-of-sample. La mejor (ruptura M15, apertura NY, 1:1.5) queda en −0.002 R.
- **Sin costes**, las mechas en M1 sí tienen una ventaja pequeña: +0.02 a +0.04 R (oro, sesión NY: +0.037 R, IC [+0.019, +0.056]; NAS todo el día +0.041 R). Es la única señal consistente en los dos activos (Holm p ≈ 0.06). Las barridas en M15 de Londres en NAS dan +0.13 R bruto con solo ~800 operaciones (no significativo tras Holm).
- Esa ventaja **desaparece al agrandar el stop**: con stop mínimo de 3–5·ATR M1 queda en ≈ 0 R bruto. Solo existe a escala de ~0.6 $ (oro) / ~5–9 pts (NAS), donde el coste es 0.5–0.8 R, unas 15–20 veces la ventaja.
- Momentum intradía: sin ventaja in-sample (oro −0.23 $/día neto, NAS −5.6 pts/día).

**Qué demuestra:** con los costes de Exness Standard, ninguna de estas ideas de scalping en M1–M15 gana. La intuición de las mechas tiene algo real, pero vale ~0.02 $ por operación en oro frente a ~0.3 $ de coste.

**Qué NO demuestra:** que no exista ventaja con otra información (ticks, libro de órdenes, noticias) o en horizontes más largos donde el coste pesa poco.

**Nota sobre el lotaje:** el tamaño multiplica el resultado por operación pero no cambia su signo. Con expectativa negativa, más lotaje solo acelera la pérdida.

<details><summary>Salidas</summary>

```

## XAUUSD: 120 variantes probadas, 0 candidatas estables, 0 significativas tras Holm
                                                        variante    n  win_rate  expectancy_r  ci_low  p_gt_0  p_holm  años_positivos  max_dd_r
     breakout {'tf': '15min', 'sl_atr': 2.0} | sesion_NY | 1:1.5 1674     0.452        -0.014  -0.060   0.725     1.0               0    41.575
       breakout {'tf': '15min', 'sl_atr': 2.0} | sesion_NY | 1:1 2008     0.490        -0.026  -0.063   0.909     1.0               0    61.767
breakout {'tf': '15min', 'sl_atr': 2.0} | apertura_NY_2h | 1:1.5 1033     0.456        -0.002  -0.065   0.514     1.0               2    31.136
       breakout {'tf': '15min', 'sl_atr': 2.0} | sesion_NY | 1:2 1535     0.438        -0.018  -0.068   0.756     1.0               1    42.538
  breakout {'tf': '15min', 'sl_atr': 2.0} | apertura_NY_2h | 1:1 1147     0.496        -0.017  -0.068   0.728     1.0               1    48.378
   breakout {'tf': '15min', 'sl_atr': 2.0} | todo_el_dia | 1:1.5 6132     0.408        -0.044  -0.070   0.998     1.0               1   317.966
     breakout {'tf': '15min', 'sl_atr': 2.0} | todo_el_dia | 1:1 7646     0.477        -0.050  -0.073   1.000     1.0               1   428.653
     breakout {'tf': '15min', 'sl_atr': 2.0} | todo_el_dia | 1:2 5504     0.372        -0.050  -0.083   0.998     1.0               1   326.355
       orb {'minutes': 30, 'sl_atr': 2.0} | apertura_NY_2h | 1:1 1002     0.486        -0.027  -0.086   0.828     1.0               1    53.896
   breakout {'tf': '5min', 'sl_atr': 2.0} | apertura_NY_2h | 1:1 2473     0.476        -0.053  -0.087   0.998     1.0               0   137.839
   breakout {'tf': '5min', 'sl_atr': 2.0} | apertura_NY_2h | 1:2 1875     0.391        -0.038  -0.091   0.922     1.0               0    80.109
  breakout {'tf': '15min', 'sl_atr': 2.0} | apertura_NY_2h | 1:2  990     0.429        -0.027  -0.092   0.786     1.0               1    46.484
 breakout {'tf': '5min', 'sl_atr': 2.0} | apertura_NY_2h | 1:1.5 2063     0.414        -0.048  -0.095   0.976     1.0               0   104.421
            orb {'minutes': 30, 'sl_atr': 2.0} | sesion_NY | 1:1 1210     0.477        -0.046  -0.098   0.958     1.0               1    81.050
     orb {'minutes': 30, 'sl_atr': 2.0} | apertura_NY_2h | 1:1.5 1001     0.419        -0.044  -0.113   0.901     1.0               1    52.768
Ninguna candidata para validar.

real	1m48.168s
user	1m37.628s
sys	0m7.467s


## NAS100: 120 variantes probadas, 0 candidatas estables, 0 significativas tras Holm
                                                        variante    n  win_rate  expectancy_r  ci_low  p_gt_0  p_holm  años_positivos  max_dd_r
       breakout {'tf': '15min', 'sl_atr': 2.0} | sesion_NY | 1:2 2348     0.390        -0.021  -0.069   0.800     1.0               2   101.048
  breakout {'tf': '15min', 'sl_atr': 2.0} | apertura_NY_2h | 1:1 1608     0.488        -0.028  -0.076   0.873     1.0               2    80.771
  breakout {'tf': '15min', 'sl_atr': 2.0} | apertura_NY_2h | 1:2 1331     0.365        -0.006  -0.076   0.558     1.0               2    66.956
       breakout {'tf': '15min', 'sl_atr': 2.0} | sesion_NY | 1:1 3124     0.478        -0.046  -0.082   0.994     1.0               1   169.870
     breakout {'tf': '15min', 'sl_atr': 2.0} | sesion_NY | 1:1.5 2612     0.415        -0.048  -0.091   0.986     1.0               0   144.425
breakout {'tf': '15min', 'sl_atr': 2.0} | apertura_NY_2h | 1:1.5 1429     0.404        -0.030  -0.092   0.838     1.0               1    75.243
     breakout {'tf': '15min', 'sl_atr': 2.0} | todo_el_dia | 1:2 5821     0.350        -0.088  -0.119   1.000     1.0               0   538.726
     breakout {'tf': '15min', 'sl_atr': 2.0} | todo_el_dia | 1:1 7849     0.447        -0.106  -0.128   1.000     1.0               0   841.623
        breakout {'tf': '5min', 'sl_atr': 2.0} | sesion_NY | 1:1 6934     0.451        -0.112  -0.135   1.000     1.0               0   781.961
      breakout {'tf': '5min', 'sl_atr': 2.0} | sesion_NY | 1:1.5 5656     0.385        -0.106  -0.135   1.000     1.0               0   609.972
   breakout {'tf': '15min', 'sl_atr': 2.0} | todo_el_dia | 1:1.5 6466     0.380        -0.109  -0.136   1.000     1.0               0   712.849
 breakout {'tf': '5min', 'sl_atr': 2.0} | apertura_NY_2h | 1:1.5 2816     0.381        -0.095  -0.137   1.000     1.0               0   272.254
     orb {'minutes': 30, 'sl_atr': 2.0} | apertura_NY_2h | 1:1.5 1020     0.392        -0.068  -0.140   0.970     1.0               1    91.892
   breakout {'tf': '5min', 'sl_atr': 2.0} | apertura_NY_2h | 1:1 3324     0.448        -0.111  -0.143   1.000     1.0               0   372.401
          orb {'minutes': 30, 'sl_atr': 2.0} | sesion_NY | 1:1.5 1263     0.386        -0.087  -0.147   0.996     1.0               1   131.779
Ninguna candidata para validar.

real	1m46.122s
user	1m35.236s
sys	0m7.651s

XAUUSD SIN COSTES: 120 variantes; exp>0: 64 ; ci_low>0: 10 ; Holm<0.05: 0
                                                        variante      n  win_rate  expectancy_r  ci_low  p_holm  años_positivos
          sweep {'tf': '1min', 'lookback': 20} | sesion_NY | 1:2  23198     0.348         0.037   0.019   0.060               4
          sweep {'tf': '1min', 'lookback': 10} | sesion_NY | 1:2  30012     0.346         0.031   0.015   0.060               4
        sweep {'tf': '1min', 'lookback': 10} | todo_el_dia | 1:2 102878     0.344         0.022   0.013   0.060               2
        sweep {'tf': '1min', 'lookback': 20} | todo_el_dia | 1:2  80595     0.343         0.019   0.009   0.117               2
        sweep {'tf': '1min', 'lookback': 20} | sesion_NY | 1:1.5  24283     0.410         0.022   0.006   0.232               3
     sweep {'tf': '1min', 'lookback': 20} | apertura_NY_2h | 1:2   7509     0.347         0.033   0.002   1.000               4
        sweep {'tf': '1min', 'lookback': 10} | sesion_NY | 1:1.5  32677     0.407         0.014   0.001   1.000               3
sweep {'tf': '1min', 'lookback': 10} | apertura_Londres_2h | 1:2   9607     0.344         0.028   0.001   1.000               2

NAS100 SIN COSTES: 120 variantes; exp>0: 65 ; ci_low>0: 11 ; Holm<0.05: 0
                                                         variante      n  win_rate  expectancy_r  ci_low  p_holm  años_positivos
         sweep {'tf': '1min', 'lookback': 20} | todo_el_dia | 1:2  77263     0.350         0.041   0.031   0.060               3
sweep {'tf': '15min', 'lookback': 20} | apertura_Londres_2h | 1:2    812     0.379         0.133   0.029   0.406               4
         sweep {'tf': '1min', 'lookback': 10} | todo_el_dia | 1:2  99757     0.348         0.037   0.028   0.060               3
sweep {'tf': '15min', 'lookback': 10} | apertura_Londres_2h | 1:2    930     0.373         0.114   0.024   0.741               4
 sweep {'tf': '5min', 'lookback': 20} | apertura_Londres_2h | 1:2   1721     0.370         0.086   0.023   0.518               4
       sweep {'tf': '1min', 'lookback': 20} | todo_el_dia | 1:1.5  80478     0.412         0.025   0.016   0.060               3
       sweep {'tf': '1min', 'lookback': 10} | todo_el_dia | 1:1.5 108029     0.411         0.024   0.016   0.060               3
        breakout {'tf': '15min', 'sl_atr': 2.0} | sesion_NY | 1:2   2314     0.416         0.060   0.010   1.000               3

XAUUSD
 min_stop_atr   ventana  tipo     n  stop_med    exp  ci_lo  ci_hi
          0.5 sesion_NY bruto 22886     0.596  0.038  0.020  0.056
          0.5 sesion_NY  neto 24286     0.587 -0.542 -0.558 -0.526
          0.5      todo bruto 79330     0.506  0.018  0.008  0.027
          0.5      todo  neto 84832     0.495 -0.646 -0.654 -0.639
          1.5 sesion_NY bruto 16067     1.071  0.040  0.018  0.064
          1.5 sesion_NY  neto 18113     1.009 -0.304 -0.323 -0.285
          1.5      todo bruto 58785     0.819  0.010 -0.002  0.022
          1.5      todo  neto 67814     0.775 -0.414 -0.424 -0.405
          3.0 sesion_NY bruto  6882     2.277  0.013 -0.017  0.044
          3.0 sesion_NY  neto  7338     2.219 -0.152 -0.182 -0.121
          3.0      todo bruto 25811     1.618  0.008 -0.008  0.024
          3.0      todo  neto 28399     1.544 -0.220 -0.234 -0.205
          5.0 sesion_NY bruto  4482     3.850 -0.014 -0.046  0.017
          5.0 sesion_NY  neto  4613     3.784 -0.119 -0.147 -0.090
          5.0      todo bruto 15486     2.729  0.002 -0.017  0.020
          5.0      todo  neto 16304     2.665 -0.132 -0.151 -0.115

NAS100
 min_stop_atr   ventana  tipo     n  stop_med    exp  ci_lo  ci_hi
          0.5 sesion_NY bruto 25136     8.998  0.002 -0.015  0.021
          0.5 sesion_NY  neto 26655     8.866 -0.553 -0.566 -0.540
          0.5      todo bruto 76194     4.666  0.040  0.031  0.051
          0.5      todo  neto 82786     4.512 -0.814 -0.820 -0.808
          1.5 sesion_NY bruto 18240    15.489 -0.015 -0.034  0.007
          1.5 sesion_NY  neto 21019    14.841 -0.360 -0.376 -0.342
          1.5      todo bruto 56884     7.758  0.015  0.004  0.027
          1.5      todo  neto 71739     7.018 -0.661 -0.668 -0.653
          3.0 sesion_NY bruto  8195    30.804 -0.008 -0.037  0.022
          3.0 sesion_NY  neto  8930    30.129 -0.191 -0.220 -0.168
          3.0      todo bruto 26214    15.268  0.005 -0.011  0.022
          3.0      todo  neto 35465    12.022 -0.471 -0.482 -0.458
          5.0 sesion_NY bruto  5036    50.411 -0.013 -0.044  0.022
          5.0 sesion_NY  neto  5288    49.760 -0.121 -0.151 -0.089
          5.0      todo bruto 15651    25.604  0.015 -0.003  0.035
          5.0      todo  neto 18671    22.143 -0.296 -0.312 -0.280

```
</details>
