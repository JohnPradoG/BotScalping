# Registro de investigación

Una entrada por experimento. Separar siempre **lo que creemos** de **lo que los datos
demuestran**. Un componente solo pasa a "demostrado" con veredicto ✅ en in-sample y
confirmación en out-of-sample.

## Estado de los componentes

| Componente | Creemos | Datos (in-sample) | Out-of-sample | Estado |
|---|---|---|---|---|
| trend_m5 | filtra contra-tendencia | — | — | sin probar |
| ema_9_20 | | — | — | sin probar |
| vwap | | — | — | sin probar |
| opening_range | | — | — | sin probar |
| structure_break | | — | — | sin probar |
| impulse | | — | — | sin probar |
| pullback | | — | — | sin probar |
| retest | | — | — | sin implementar |
| rejection_candle | | — | — | sin probar |
| wick_body_ratio | | — | — | sin probar |
| volume | | — | — | sin probar |
| volatility | | — | — | sin probar |
| spread | | — | — | sin probar |
| session_hours | | — | — | sin probar |
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
