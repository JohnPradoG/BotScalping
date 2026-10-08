# 2026-10-07 · Horas del día, impulso intradía y "comprar la caída" diario (RSI-2)

John no conectará su cuenta real, así que se prueban ventajas conocidas en índices y oro.

## Sesgo por hora del día (`scripts/estacionalidad.py`)
Se compra en la apertura de cada hora (hora de Nueva York) y se cierra una hora después; a la hora con sesgo bajista se le aplica la venta.
- Ninguna hora tiene un sesgo mayor que el coste: el mejor neto es ≈ 0 (oro, 16 h).

## Impulso intradía (Gao et al. 2018)
Se toma la dirección de 09:30–10:00 y se opera en ese sentido de 15:30 a 16:00.
- Negativo incluso antes de costes en NAS100 y oro, tanto in-sample como fuera de muestra.

## RSI-2 diario, solo compras (Connors) (`scripts/rsi2_diario.py`)
**Regla.** Comprar al cierre de NY si RSI(2) < 20 y el precio está sobre su media de 200 días. Vender al cierre del día en que cierra sobre la media de 5 días; máximo 10 días.
**Costes.** Spread, slippage y un swap estimado de 0,02 % por noche.

| | n | media/op | acierto | azar con la misma duración |
|---|---|---|---|---|
| NAS100 in-sample | 52 | +0,68 % | 79 % | +0,24 % |
| NAS100 fuera de muestra | 24 | +0,60 % | 75 % | +0,24 % |
| Oro in-sample | 45 | +0,39 % | 71 % | +0,25 % |
| Oro fuera de muestra | 16 | −0,07 % | 69 % | +0,25 % |

**NAS100, todas las operaciones.**
- 76 operaciones, t = 4,4.
- Peor operación: −4,8 %. Caída máxima de la curva: 4,8 %.
- Positivo todos los años: 2023 +12 %, 2024 +19 %, 2025 +8 %, 2026 +10 %. Por la media de 200 días no hay operaciones antes de 2023: los datos empiezan en oct 2021 y en 2022 el índice estuvo bajo esa media.
- Duración: unos 3 días, unas 15 operaciones al año.
- Umbrales 5 y 10 también positivos en los dos periodos.

**Lectura.** Es la primera regla que gana fuera de muestra y supera claramente a comprar al azar. No es scalping. Tiene a su favor que es una regla publicada hace años (2008), así que no la "encontramos" buscando entre miles. En contra: la muestra es pequeña (76 operaciones) y solo cubre un mercado alcista. En el oro no funciona, igual que en la literatura: el oro no revierte como los índices.

## Solo compras en oro M15 con rechazo en el VWAP
Ejecutado en el PC de John (`scalping_research/bt_rechazo_v2.py`).
- Candidato: +0,05 a +0,17 R en los dos periodos.
- Con t ≈ 1 entre unas 170 combinaciones probadas, es compatible con azar.
