# Datos

Los ficheros de datos no se versionan. Coloca aquí los históricos exportados de MetaTrader 5
(Centro de historial → Barras → Exportar), por ejemplo:

- `XAUUSD_M1.csv`
- `NAS100_M1.csv`

Formato esperado (el exportador de MT5 lo genera así, separado por tabuladores):

```
<DATE>	<TIME>	<OPEN>	<HIGH>	<LOW>	<CLOSE>	<TICKVOL>	<VOL>	<SPREAD>
2025.01.02	01:00:00	2624.51	2625.10	2624.20	2624.80	153	0	25
```

- Los precios son **bid**. El spread viene en **puntos** y se convierte a precio con `point` del instrumento.
- La hora es la del servidor del bróker: indica su zona en `data.broker_tz` del config.

## Históricos incluidos (exportados de MT5, Exness)

| Fichero | Símbolo bróker | Desde | Hasta | Barras M1 | point |
|---|---|---|---|---|---|
| `XAUUSD_M1.csv.gz` | XAUUSDm | 2021-10-27 | 2026-10-07 | 1.746.031 | 0.001 |
| `NAS100_M1.csv.gz` | USTECm | 2021-10-27 | 2026-10-07 | 1.704.628 | 0.01 |

- Hora del servidor Exness = UTC. Precios bid, spread en puntos.
- 2021-10-27 es la primera fecha M1 que ofrece el servidor; no hay más historia.
- pandas lee el `.gz` directamente (sin descomprimir).
- Exportados con el script MQL5 `tools/ExportM1.mq5` (solo lectura).
