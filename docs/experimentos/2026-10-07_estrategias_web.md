# 2026-10-07 · Estrategias públicas de la web (scalping y rango)

John pidió buscar en la web un bot o estrategia de scalping y otra de rango. En los resultados hay sobre todo scripts de TradingView y EAs de pago de MQL5. Ninguno publica resultados verificados en cuenta real. Se eligieron tres scripts de código abierto con reglas completas y se programaron tal cual (`scripts/estrategias_web.py`).

**Montaje común.** Datos Exness con spread real + slippage. Señal al cierre de la vela, entrada en la apertura de la siguiente. Stop ATR comprobado dentro de la vela. Dentro de muestra hasta jun 2025, fuera de muestra desde jul 2025.

1. **Scalping a favor de tendencia** — "RSI Scalping Gold (XAUUSD) v5", TradingView.
   - Entrada: RSI(14) cruza 30 hacia arriba (70 hacia abajo), precio sobre la EMA9, EMA9 > SMA20, precio sobre la SMA200, volumen relativo ≥ 1,25.
   - Salida: cruce de vuelta del RSI o cruce de la EMA9 con la SMA20. Stop 1,5 ATR.
   - Con las reglas tal cual casi no opera (0–4 operaciones en 5 años): RSI saliendo de sobreventa con la EMA9 por encima de la SMA20 casi nunca coincide.
   - La versión relajada, sin EMA9 > SMA20, da 14–61 operaciones por caso. Resultados entre −0,68 R y +0,32 R, con intervalos que cruzan el cero: no hay muestra para concluir nada.
2. **Rango: Bollinger + RSI** — "Reversion Guard", TradingView.
   - Entrada: cierre fuera de Bollinger(20,2) con RSI < 30 (> 70).
   - Salida: en la media. Stop 2 ATR.
   - In-sample: −0,07 a −0,24 R por operación, 0 años positivos. Fuera de muestra: −0,02 a −0,06 R.
3. **Rango: bandas de VWAP** — "NQ Phantom Scalper Pro", TradingView.
   - Entrada: toca la banda de 2σ de la VWAP de la sesión de NY con volumen > 1,5× la media. Opera de 9:45 a 16 h, excepto de 12 a 14 h.
   - Salida: en la VWAP. Stop 1,5 ATR.
   - In-sample: −0,10 a −0,13 R. Fuera de muestra: −0,02 a −0,06 R.

**Conclusión.** Las estrategias públicas pierden en estos datos, igual que las nuestras. Las de rango aciertan el 45–54 %, pero pierden más de lo que ganan y los costes rematan. Coincide con lo medido antes: en el oro y el Nasdaq, los bordes del rango y las bandas se rompen más de lo que rebotan.

Fuentes:
- https://www.tradingview.com/script/uXwRMzy9-RSI-Scalping-Gold-XAUUSD-v5
- https://ar.tradingview.com/script/zoY9DmsF-Reversion-Guard-RSI-Bollinger-Band-Customizable/
- https://jp.tradingview.com/script/kP7HmAzw-NQ-Phantom-Scalper-Pro
