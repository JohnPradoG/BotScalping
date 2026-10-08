# 2026-10-07 · Solo compras: caída → soporte → vela de rechazo

**Idea de John.** Operar solo en compra. Esperar a que el precio caiga, que llegue a un soporte y deje una vela de rechazo, y comprar.

**Prueba.** `scripts/solo_compras.py`, sobre los datos de oct 2021 a jun 2025.
- **Caída:** el cierre está al menos 2 o 3 ATR por debajo del máximo de las 12 velas previas.
- **Soporte:** último mínimo de swing de 3 o 5 velas (setup `sr_bounce`), tocado y cerrado por encima.
- **Rechazo:** la vela cierra en el tercio alto de su rango.
- **Marcos:** M5, M15 y H1.
- **Salidas:** 1:1, 1:2, trailing 1 ATR, y BE 1R + trailing 2 ATR.
- **Costes:** reales (spread + slippage).
- **Referencia:** el mismo número de compras al azar con la misma salida.

**Resultado.**
- NAS100: 0/48 netas positivas. Solo 7/48 superan a comprar al azar.
- Oro: 0/48 netas positivas. Solo 6/48 superan a comprar al azar.
- En M5 el coste se lleva 0,35–0,7 R por operación. En M15 y H1 el coste baja a 0,1–0,3 R y aun así sigue negativo.
- La mayoría de las configuraciones rinden **peor que comprar al azar**, aunque los dos activos subieron (+44 % y +84 %). Comprar justo tras una caída fuerte a corto plazo tiende a coger el precio que sigue cayendo. Las caídas tienen inercia; el rebote que se ve en el gráfico no es lo típico.

No se valida fuera de muestra: no hay ninguna candidata que validar.

|Lo que creemos|Lo que muestran los datos|
|---|---|
|Tras una caída, la vela de rechazo en soporte marca el giro|Rinde peor que comprar en un momento cualquiera|
