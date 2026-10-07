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
