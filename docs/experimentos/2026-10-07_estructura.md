# 2026-10-07 · "Leer la estructura": tendencia por máximos y mínimos crecientes y entrada en el retroceso

**Idea de John** (captura USTEC_x100m M1 del 7-oct). La tendencia la marcan máximos y mínimos crecientes con el precio sobre la media. Se entra en el retroceso a la media o al último mínimo.

**Prueba.** `scripts/estructura.py`, datos de oct 2021 a jun 2025.
- **Tendencia alcista:** los dos últimos swings confirmados (fractal de k = 3 o 5 velas) suben, tanto los máximos como los mínimos, y el cierre está sobre la EMA 20 o 50. La bajista, al revés.
- **Entrada:** la vela toca la EMA o el último mínimo creciente y cierra en su 40 % alto.
- **Stop:** bajo el último mínimo, con un mínimo de 0,5 ATR.
- **Salidas:** 1:1, 1:2, trailing 1 ATR, y BE 1R + trailing 2 ATR.
- **Marcos:** M1 y M5, ambos lados, costes reales.
- **Referencia:** entradas al azar dentro de la misma tendencia.

**Resultado.**
- **Sin costes:** NAS100 24/32 y oro 23/32 salen ligeramente positivas, de 0 a +0,10 R.
- **Con costes:** 0/32 positivas en los dos instrumentos. M5 queda entre −0,11 y −0,47 R; M1 entre −0,32 y −0,77 R.
- **Stop mediano:** en NAS100, 5–11 puntos en M1 y 14–28 en M5. En oro, 0,6–1,2 $ en M1 y 1,5–3 $ en M5. El spread y el slippage se comen de 0,15 a 0,8 R por operación.
- **Frente al azar:** las entradas al azar dentro de la misma tendencia no rinden peor. La estructura sí identifica tendencia (bruto ligeramente positivo), pero el retroceso no añade ventaja.

**Lectura.** En el gráfico la tendencia se ve clara a posteriori, y entrar en los retrocesos parece fácil. Con miles de casos, la ventaja bruta es de unos pocos céntimos de R, muy por debajo de lo que cuesta cada operación con un stop tan cercano.

## Varios marcos de tiempo (`scripts/estructura_mtf.py`)
**Montaje.**
- La tendencia se lee en M15 o H1: dos máximos y dos mínimos crecientes, cierre sobre la EMA20 de ese marco, alineado sin mirar el futuro.
- La entrada se afina en M1 o M5: retroceso a la EMA20 del marco menor o a su último mínimo, con vela que cierra fuerte.
- Dos stops: "ajustado" (último mínimo del marco menor) y "amplio" (último mínimo del marco mayor).
- 32 variantes por instrumento.

**In-sample.**
- NAS100: 0/32 netas positivas; 27/32 superan al azar dentro de la misma tendencia. La mejor es H1 + M5, stop amplio, trailing: −0,08 R.
- Oro: 1/32 positiva (H1 + M5, stop amplio, 1:2, +0,014 R, IC −0,06 a +0,08, 3/5 años); 29/32 superan al azar.
- Leer la tendencia en el marco mayor sí ayuda frente al azar, y el stop amplio reduce el peso del coste. Pero la ventaja bruta sigue en 0–0,08 R.

**Fuera de muestra (jul 2025 – oct 2026), solo la familia oro H1 + M5 con stop amplio.**
- 1:2: +0,087 R (IC −0,04 a +0,22), 312 operaciones.
- BE + trailing: +0,13 R (IC +0,03).
- 1:1: +0,09 R.
- Al azar en la misma tendencia: +0,02 a +0,06 R. El oro subió con fuerza en este periodo.
- Stop mediano: unos 10 $ in-sample y unos 38 $ fuera de muestra. Para arriesgar 20 $, eso son lotes de 0,005–0,02, no 0,05 con stop de 4 $.

**Lectura.** Es la primera variante de scalping/intradía que no pierde ni dentro ni fuera de muestra. Pero se eligió entre 64 y ninguna pasa la corrección de Holm. Es un candidato para seguir probando (más datos o en demo), no algo demostrado.

## Mejoras sobre la candidata del oro (`scripts/estructura_mejoras.py`)
Se elige solo con in-sample. Fuera de muestra se muestra para ver si aguanta. $ = arriesgando 20 $ por operación (lote ajustado al stop), oct 2021 – oct 2026.

| Oro H1 + M5, stop bajo mínimo H1 | in-sample | fuera de muestra | total 20 $/op | ops/día |
|---|---|---|---|---|
| base 24/5, 1:2 | +0,013 R (3/5 años) | +0,094 R | +848 $ | 0,86 |
| + tendencia H4 a favor, 1:2 | +0,048 R (p = 0,21) | +0,178 R | +780 $ (caída máx 410 $) | 0,33 |
| + volumen, 1:2 | +0,003 R | +0,053 R | +353 $ | 0,73 |
| solo 7–20 h UTC | −0,01 R | +0,16 R | +719 $ | 0,72 |
| stop ≤ 3 ATR(M5) (más ajustado) | −0,24 R | ≈ 0 | −2.100 $ | 0,34 |

- **NAS100:** ninguna mejora lo pone en positivo (in-sample entre −0,08 y −0,40 R).
- **Lección:** ajustar el stop (entrar "más preciso") es lo que más daño hace. Lo que ayuda es pedir más acuerdo de tendencia (H4) y dejar el stop amplio.
- **Por hora:** operar 24/5 frente a solo Londres/NY no cambia mucho.
- **Significancia:** la mejor variante no es significativa (p = 0,21 in-sample).
