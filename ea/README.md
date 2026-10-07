# Bots para MT5

## RSI2_Nasdaq.mq5
Compra el Nasdaq (o el S&P 500: ponlo en un gráfico de US500m/US500_x100m) tras una caída de 1–2 días (RSI de 2 días < 20) cuando está sobre su media de 200 días, y cierra cuando vuelve a cerrar sobre la media de 5 días (máximo 10 días). Es la regla que ganó dentro y fuera de muestra en `scripts/rsi2_diario.py` (ver `docs/experimentos/2026-10-07_estacionalidad_y_rsi2.md`).

**Instalación**
1. Copia `RSI2_Nasdaq.mq5` a `MQL5/Experts/` (en MT5: Archivo → Abrir carpeta de datos).
2. Ábrelo en MetaEditor y pulsa Compilar.
3. En MT5, abre un gráfico de **USTECm** (contrato 1) en M5 y deja que cargue historial: necesita unos 260 días hábiles de velas M5.
4. Arrastra el EA al gráfico y activa "Algo Trading". **Primero en cuenta demo.**

**Parámetros**
- `Lotes`: 0,20 por cada 1.000 $ en USTECm. En USTEC_x100m (contrato 100) el lote mínimo de 0,01 ya es demasiado para 1.000 $.
- `StopATR`: stop de emergencia a 3 × ATR(14) diario (por defecto). En el backtest casi no quita ganancia (en el Nasdaq la mejora) y reduce la peor operación a la mitad. Los stops de 1–1,5 ATR estropean la estrategia. Con 0 se usa `StopPuntos` (0 = sin stop).
- `OffsetServidorUTC`: 0 en Exness (servidor en UTC).

**Qué esperar**
- Unas 13–15 operaciones al año, de unos 3 días cada una.
- El backtest (feb 2023 – oct 2026) no incluye el swap real.
- No es garantía de resultados futuros.

## Estructura_Oro.mq5
Opera el oro a favor de la tendencia: solo compra cuando H1 y H4 marcan máximos y mínimos crecientes (y vende en el caso contrario), y entra en M5 cuando el precio retrocede a su media o a un mínimo reciente. El stop va bajo el último mínimo de H1 con un margen de 0,5 × ATR(H1) y el objetivo es 2 veces el riesgo. Es la versión "máximo 2 por dirección" de `scripts/estructura_ajustes.py` (ver `docs/experimentos/2026-10-07_estructura.md`).

**Instalación**
1. Copia `Estructura_Oro.mq5` a `MQL5/Experts/` y compílalo en MetaEditor.
2. Abre un gráfico de **XAUUSDm** en **M5** y arrastra el EA. **Primero en cuenta demo.**

**Parámetros**
- `RiesgoUSD` = 20: dinero que se pierde si salta el stop. El lote se calcula solo (unos 0,01 con stops de 16 $). Si el stop es tan grande que hace falta menos del lote mínimo, no entra.
- `MaxPorDireccion` = 2: como mucho 2 compras y 2 ventas abiertas. Sin límite el backtest llegó a 47 operaciones a la vez y una racha de −2.189 $.
- `RR` = 2, `MaxHoras` = 24 (cierra a las 24 h si no tocó stop ni objetivo), `MargenATRH1` = 0,5.

**Qué esperar (backtest 2021–2026, 20 $ por operación)**
- Unas 170 operaciones al año, ~40 % ganadoras.
- +1.710 $ en 5 años, peor racha −340 $. Fuera de muestra +0,21R por operación.
- Es una ventaja pequeña que no supera las pruebas estadísticas estrictas: tómalo como experimento en demo.
