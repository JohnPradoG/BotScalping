# 2026-10-07 · ¿Cuánto coste aguanta el método de mechas de John?

**Pregunta.** John dice que Exness casi no cobra spread. ¿El método S/R con mecha (setup `sr_bounce`, M1 y M5) pasaría a ganar con un coste más bajo?

**Prueba.** `scripts/coste_sensibilidad.py`. Se corren las 48 variantes sin coste y luego se resta, operación a operación, una fracción del coste real: spread de la barra de entrada + 2·slippage, dividido por la distancia de stop. In-sample, oct 2021 – jun 2025.

**Spread de los datos (cuenta Exness tipo Standard, símbolos con "m").** NAS100: mediana de 4–5 puntos en 2021–24 y de unos 2 en 2025–26. Oro: unos 0,20 $. John opera USTEC_x100m; el sufijo "m" apunta a una cuenta Standard, es decir, el mismo tipo de coste que los datos (inferido, no confirmado).

**Resultado.**

| Coste respecto al real | NAS100 positivas | Oro positivas |
|---|---|---|
| 0 % (gratis) | 33/48 | 31/48 |
| 10 % | 0/48 | 4/48 (≤ +0,008 R) |
| 25 % | 0 | 0 |
| 50 % | 0 | 0 |
| 100 % | 0 | 0 |

- La ventaja sin coste es de +0,05 a +0,15 R por operación. El coste real es de 1–2 R en M1 y de 0,4–0,75 R en M5.
- El método solo aguanta un coste de entre el 7 % y el 12 % del actual. Solo el slippage supuesto ya supera ese margen en NAS100.
- Ni con el spread de 2025–26 (la mitad que antes) ni con una cuenta de spread cero más comisión sale positivo.
- Además, la entrada al azar con la misma salida rinde casi igual sin coste (ver registro): esa pequeña ventaja es de la salida, no de la mecha.

**Conclusión.** El coste no es lo que separa este método de ganar. Haría falta que operar costara alrededor de una décima parte de lo que cuesta hoy, y aun así la ventaja sería mínima.
