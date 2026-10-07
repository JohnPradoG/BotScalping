# BotScalping

Laboratorio de backtest para scalping en **XAUUSD** y **NAS100** (operaciones de segundos a
minutos). No busca la estrategia perfecta al primer intento: descompone la estrategia en
componentes y deja que los datos digan cuáles mejoran la expectativa.

```
Hipótesis → Backtest → Análisis → Extraer componentes útiles → Nueva hipótesis → Validación
```

## Arquitectura

```
botscalping/
  data.py         carga de CSV de MT5 → barras M1 en UTC (bid + spread), split in/out-of-sample
  indicators.py   EMA, ATR, VWAP anclado, Opening Range, swings, alineación M5→M1 sin lookahead
  components.py   registro de componentes: 1 setup (genera entradas) + N filtros (permiten/bloquean)
  engine.py       motor barra a barra: costes, stop/objetivo, salida por tiempo, resultado en R
  stats.py        expectativa, IC bootstrap, test de permutación, corrección de Holm, estabilidad
  experiment.py   ablación: ladder / single / loo → tabla + veredicto por componente
configs/          un TOML por experimento (activar/desactivar componentes sin tocar código)
docs/registro.md  lo que CREEMOS vs lo que los datos DEMUESTRAN, experimento a experimento
tests/            motor, ausencia de lookahead en cada componente, estadística
```

### Cómo encaja

1. **Setup** (uno): genera entradas candidatas y la distancia de stop. El *baseline* es
   `breakout` (cierre rompe el máximo/mínimo de N barras) sin filtros. Junto a él corre un
   **benchmark aleatorio** con la misma gestión: si un setup no le gana, no tiene ventaja.
2. **Filtros** (N): cada uno devuelve barra a barra si permite largos y/o cortos. Un filtro
   nunca crea operaciones, solo las quita. Esto permite medir exactamente **qué quita** y
   si lo que quita era peor que lo que deja.
3. **Gestión**: `rr` (1:2, 1:3…) y `max_bars` (salida por tiempo) en el config.
4. **Motor**: señal al cierre de la barra, entrada a la apertura de la siguiente; largos
   pagan el spread; si stop y objetivo caen en la misma barra, cuenta como stop.

### Componentes disponibles

| Componente | Tipo | Idea |
|---|---|---|
| `breakout` | setup | Baseline: ruptura del rango de N barras, stop = k·ATR |
| `random` | setup | Benchmark aleatorio |
| `sweep` | setup | Barrida con mecha: perfora el extremo de N velas y cierra dentro → entrada en contra |
| `orb` | setup | Primer cierre fuera del rango de apertura de NY |
| `trend_m5` | filtro | Cierre M5 vs EMA M5 (alineado sin mirar el futuro) |
| `ema_9_20` | filtro | EMA 9 vs EMA 20 en M1 |
| `vwap` | filtro | Precio vs VWAP anclado a la apertura |
| `opening_range` | filtro | Fuera del rango de los primeros N minutos |
| `structure_break` | filtro | Cierre más allá del último swing confirmado |
| `impulse` | filtro | Vela de impulso (cuerpo > k·ATR) reciente a favor |
| `pullback` | filtro | Retroceso a la EMA lenta en las últimas N barras |
| `rejection_candle` | filtro | Cierre en el tercio favorable de la vela |
| `wick_body_ratio` | filtro | Mecha contraria / cuerpo ≥ ratio |
| `volume` | filtro | Tick volume > media |
| `volatility` | filtro | ATR relativo dentro de una banda |
| `spread` | filtro | Spread ≤ fracción del ATR |
| `session_hours` | filtro | Ventana horaria desde la apertura |

Pendientes de definir antes de implementar: `retest` y `score`.

Añadir un componente es una función con `@register(...)` en `components.py`; el test de
lookahead lo cubre automáticamente.

## Método estadístico

Para cada componente probado se comparan, dentro de las operaciones del sistema "padre",
las que el filtro **conserva** frente a las que **elimina** (test de permutación). Con
muchos componentes alguno "funciona" por azar, así que los p-valores se corrigen con Holm.

| Veredicto | Significa |
|---|---|
| ✅ aporta valor | lo que elimina es significativamente peor que lo que conserva |
| ❌ empeora | elimina operaciones significativamente mejores |
| ➖ sin evidencia | no se puede afirmar nada (no es lo mismo que "no sirve") |
| datos insuficientes | menos de `min_trades` operaciones |

Tres modos, porque responden preguntas distintas:

- `single`: baseline + cada filtro solo. ¿Aporta algo por sí mismo? **Empezar por aquí.**
- `ladder`: baseline → +A → +A+B… en el orden del config. ¿Añadirlo al sistema actual mejora?
- `loo`: sistema completo menos cada uno. ¿Sigue aportando o es redundante?

Las decisiones se toman **solo con in-sample**. El out-of-sample se mira una vez al final,
para confirmar la Estrategia N; si se usa para elegir, deja de ser validación.

## Uso

```bash
pip install -e ".[dev]"
pytest

# Datos: exportar M1 desde MT5 a data/ (ver data/README.md) y ajustar configs/*.toml
python -m botscalping.experiment configs/xauusd.toml --mode single
python -m botscalping.experiment configs/xauusd.toml --mode ladder
python -m botscalping.experiment configs/nas100.toml --mode loo

# Validación final de la Estrategia N (una sola vez): añade el out-of-sample
python -m botscalping.experiment configs/xauusd.toml --mode ladder --validate

# Sin datos: prueba del pipeline con un paseo aleatorio (no debe salir ventaja)
python -m botscalping.experiment configs/xauusd.toml --mode ladder --synthetic
```

Los resultados quedan en `results/<nombre>/` (CSV + informe Markdown).

Búsqueda amplia de setups × gestión × sesión (ordena con in-sample, corrige por nº de pruebas y valida solo las mejores en out-of-sample):

```bash
python -m botscalping.search configs/xauusd.toml configs/nas100.toml --top 5
```

## Limitaciones conocidas

- Resolución M1: dentro de una barra no se sabe qué se tocó primero (por eso stop primero).
  Para entradas de segundos hará falta histórico de ticks; el motor está aislado para poder
  sustituirlo.
- El spread de MT5 por barra es un valor representativo, no el real en el instante de entrada.
