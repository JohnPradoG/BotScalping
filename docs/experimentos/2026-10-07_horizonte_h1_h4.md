# 2026-10-07 · Marcos mayores (H1/H4): ruptura de canal + stop dinámico, sin objetivo

**Pregunta.** En M1/M5 el coste se come cualquier ventaja. ¿Aparece ventaja al subir a H1/H4, donde el coste es casi nulo frente al stop?

**Prueba.** `scripts/horizonte.py`. Ruptura del máximo/mínimo de 20 o 55 velas; stop de 2 o 3 ATR; trailing de 2 o 3 ATR; sin objetivo fijo. Se prueban dos versiones, ambos lados y solo largos: 32 variantes por instrumento. Referencia: entradas al azar con la misma gestión y el mismo lado. Costes: spread real más slippage. **No incluye el swap**, que con 1–4 noches de media restaría unos 0,01–0,05 R.

**In-sample (oct 2021 – jun 2025).**
- NAS100: 31/32 variantes netas positivas, pero casi todas son "solo largos" en un índice que subió un 44 %. La mejor es H4, canal 55, stop 2 ATR, trailing 2 ATR, solo largos: +0,26 R (IC 0,08–0,46), 89 operaciones, 5/5 años positivos. Al azar solo largos con la misma gestión: −0,12 R.
- Oro: 22/32. Las entradas al azar en largo rinden igual o más que la ruptura, así que no hay ventaja de entrada; es la subida del oro (+84 %).

**Out-of-sample (jul 2025 – oct 2026), solo la candidata elegida antes de mirar.**
- NAS100: +0,09 R (IC −0,25 a 0,43), 35 operaciones. Al azar solo largos: +0,16 R. **No le gana al azar.**
- Oro: +0,54 R (IC 0,18–0,92), 33 operaciones. Al azar: +0,21 R. Las 32 variantes salen positivas porque el oro subió con fuerza; con 33 operaciones no se distingue de estar comprado.

**Conclusión.** Subir de marco quita el problema del coste, pero no aparece ventaja de entrada. Lo que gana es estar comprado en dos activos que han subido: es beta, no un sistema. Con 30–90 operaciones tampoco hay muestra para afirmar más.

| |Lo que creemos|Lo que muestran los datos|
|---|---|---|
|Ruptura H4 en NAS|tiene ventaja|in-sample sí frente al azar; OOS no|
|Ruptura en oro|tiene ventaja|el azar en largo rinde igual|
