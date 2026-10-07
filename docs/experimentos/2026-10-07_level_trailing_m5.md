### 2026-10-07 · XAUUSD y NAS100 · Rebote en nivel M5 siguiendo el precio (sin objetivo fijo)

(Continuación de `docs/registro.md`.)

John corrige: no quiere objetivo fijo; quiere seguir el precio y dejarla correr. `scripts/level_trailing.py`: `level_bounce` en M5 con trailing 1/2·ATR, break-even + trailing y cierre al cruzar la EMA20. **0 de 40 netas positivas.** Sin costes, entre −0.12 y +0.05 R. Hay operaciones que corren mucho (hasta 600 pts en NAS100), pero aciertan el 13–30 % y las pérdidas pequeñas se acumulan.

```
NAS100 | netas > 0: 0 de 20
 horas_nivel  mecha                 salida  exp_bruto  exp_neto     n  acierto  ci_lo  ci_hi  mejor_op_pts  ganancia_media_pts  perdida_media_pts
         8.0    0.4         trailing 2 ATR      0.027    -0.441  2649    0.169 -0.496 -0.380       600.268              43.367            -13.264
         8.0    0.4 BE 1R + trailing 2 ATR      0.041    -0.443  2657    0.155 -0.499 -0.386       600.268              44.850            -12.582
         8.0    0.4 BE 1R + trailing 1 ATR      0.048    -0.444  2674    0.242 -0.489 -0.396       220.069              27.131            -13.997
         8.0    0.4         trailing 1 ATR      0.042    -0.452  2759    0.197 -0.491 -0.409       235.449              23.303            -11.083
         8.0    0.4 cierre al cruzar EMA20      0.003    -0.471  2785    0.213 -0.500 -0.439       235.344              14.132             -9.801
         8.0    0.0         trailing 1 ATR      0.016    -0.491  4832    0.177 -0.524 -0.455       320.494              24.605            -10.494
         8.0    0.0 BE 1R + trailing 1 ATR      0.023    -0.499  4601    0.204 -0.535 -0.463       469.123              28.328            -12.532
         8.0    0.0 BE 1R + trailing 2 ATR     -0.001    -0.500  4551    0.132 -0.542 -0.457       600.268              46.729            -11.567
         8.0    0.0         trailing 2 ATR     -0.023    -0.503  4524    0.144 -0.549 -0.453       600.268              45.093            -12.298
         8.0    0.0 cierre al cruzar EMA20     -0.002    -0.511  4869    0.207 -0.537 -0.486       409.078              14.441             -9.500
         2.0    0.4 cierre al cruzar EMA20      0.000    -0.521 11662    0.182 -0.540 -0.504       646.438              14.547             -8.749
         2.0    0.4         trailing 1 ATR      0.023    -0.522 11653    0.179 -0.540 -0.503       320.088              20.650             -9.967
         2.0    0.4 BE 1R + trailing 1 ATR      0.023    -0.527 11141    0.211 -0.548 -0.506       304.248              23.588            -11.925
         2.0    0.4         trailing 2 ATR      0.028    -0.532 10636    0.148 -0.560 -0.504       600.268              36.243            -11.631
         2.0    0.4 BE 1R + trailing 2 ATR      0.022    -0.535 10631    0.132 -0.560 -0.510       600.268              37.038            -10.841
         2.0    0.0         trailing 1 ATR      0.031    -0.549 20557    0.166 -0.564 -0.534       320.494              21.338             -9.493
         2.0    0.0 BE 1R + trailing 1 ATR      0.031    -0.553 18972    0.192 -0.569 -0.537       469.123              24.353            -11.101
         2.0    0.0 cierre al cruzar EMA20      0.008    -0.554 20598    0.181 -0.566 -0.542       646.438              13.397             -8.422
         2.0    0.0 BE 1R + trailing 2 ATR      0.017    -0.572 17786    0.121 -0.592 -0.553       600.268              37.227            -10.214
         2.0    0.0         trailing 2 ATR      0.026    -0.573 17786    0.133 -0.595 -0.554       600.268              36.714            -10.900

XAUUSD | netas > 0: 0 de 20
 horas_nivel  mecha                 salida  exp_bruto  exp_neto     n  acierto  ci_lo  ci_hi  mejor_op_pts  ganancia_media_pts  perdida_media_pts
         8.0    0.4 cierre al cruzar EMA20     -0.034    -0.310  3485    0.294 -0.344 -0.278        44.696               1.010             -0.909
         2.0    0.4         trailing 1 ATR      0.005    -0.317 12897    0.252 -0.338 -0.297        33.038               1.644             -0.966
         8.0    0.4         trailing 1 ATR     -0.041    -0.319  3419    0.249 -0.357 -0.283        16.559               1.700             -1.046
         2.0    0.4 BE 1R + trailing 2 ATR      0.012    -0.321 11223    0.183 -0.351 -0.291        58.048               3.092             -1.081
         2.0    0.4 BE 1R + trailing 1 ATR      0.002    -0.322 11993    0.298 -0.345 -0.299        33.038               1.840             -1.244
         8.0    0.4 BE 1R + trailing 1 ATR     -0.060    -0.326  3231    0.300 -0.371 -0.285        20.191               2.000             -1.400
         2.0    0.4 cierre al cruzar EMA20     -0.007    -0.327 13076    0.279 -0.343 -0.309        55.679               0.973             -0.802
         2.0    0.4         trailing 2 ATR     -0.004    -0.331 11155    0.207 -0.361 -0.298        58.048               3.102             -1.204
         8.0    0.0         trailing 1 ATR      0.008    -0.331  5541    0.235 -0.363 -0.297        21.115               1.823             -0.966
         2.0    0.0 BE 1R + trailing 1 ATR      0.025    -0.336 19445    0.271 -0.356 -0.317        41.877               1.978             -1.142
         2.0    0.0 BE 1R + trailing 2 ATR      0.022    -0.337 17730    0.171 -0.363 -0.310        76.944               3.223             -1.013
         2.0    0.0         trailing 1 ATR      0.029    -0.337 21815    0.239 -0.354 -0.318        62.777               1.744             -0.922
         8.0    0.0 BE 1R + trailing 1 ATR     -0.013    -0.337  5096    0.266 -0.379 -0.302        23.284               2.103             -1.212
         2.0    0.0 cierre al cruzar EMA20      0.015    -0.345 22096    0.276 -0.360 -0.331        50.699               1.001             -0.781
         2.0    0.0         trailing 2 ATR      0.018    -0.347 17468    0.196 -0.373 -0.321        76.944               3.112             -1.124
         8.0    0.0 cierre al cruzar EMA20     -0.023    -0.359  5604    0.282 -0.385 -0.332        44.696               1.011             -0.863
         8.0    0.4 BE 1R + trailing 2 ATR     -0.118    -0.359  3200    0.186 -0.405 -0.307        17.549               2.913             -1.212
         8.0    0.0 BE 1R + trailing 2 ATR     -0.037    -0.363  5024    0.169 -0.409 -0.318        30.707               3.054             -1.076
         8.0    0.0         trailing 2 ATR     -0.039    -0.376  4962    0.189 -0.421 -0.329        30.707               2.997             -1.179
         8.0    0.4         trailing 2 ATR     -0.109    -0.377  3191    0.205 -0.427 -0.327        23.636               2.897             -1.323
```
