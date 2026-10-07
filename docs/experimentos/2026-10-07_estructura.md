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
