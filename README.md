# Proyecto 2: PFSP con AG, AM y ACS

Algoritmos Metaheurísticos Inspirados en la Naturaleza (AMIN), UCSC.

Comparación de tres metaheurísticas sobre el *Permutation Flow Shop Scheduling Problem*
(PFSP), minimizando el makespan $C_{max}$ en instancias de Taillard:

- **AG**: Algoritmo Genético.
- **AM**: Algoritmo Memético (AG + búsqueda local por inserción).
- **ACS**: Ant Colony System, adaptado del preproyecto TSP (Berlin52).

## Requisitos

Python 3.10 o superior, con numpy y matplotlib (este último solo para `graficar.py`).

```bash
pip install numpy matplotlib
```

## Estructura

```
ag.py            AG: bucle del algoritmo y CLI (con frec_bl > 0 es el AM)
am.py            AM: CLI que reutiliza ag.py con búsqueda local
acs.py           ACS: bucle del algoritmo y CLI
operadores.py    Operadores: lectura, Cmax, RPD, CSV y operadores de AG, AM y ACS
tests.py         Pruebas de los operadores y de los tres algoritmos
experimentos.py  Batería comparativa: 3 algoritmos x 3 instancias x 10 semillas
graficar.py      Convergencia y boxplots a partir de experimentos.csv
datos/           Instancias de Taillard: tai20_5, tai50_10, tai100_10
resultados/      CSV de corridas y resumen
graficos/        Convergencia y dispersión por instancia (PNG)
```

Los scripts `ag.py`, `am.py` y `acs.py` describen **qué** hace cada algoritmo.
`operadores.py` describe **cómo** se hace cada operación.

## Uso

Cada algoritmo recibe sus parámetros en orden fijo:

```bash
python ag.py  instancia semilla poblacion iteraciones pc pm salida.csv
python am.py  instancia semilla poblacion iteraciones pc pm frec_bl salida.csv
python acs.py instancia semilla hormigas iteraciones alfa beta q0 salida.csv
```

Ejemplos (parámetros usados en los experimentos):

```bash
python ag.py  datos/tai20_5.txt 12345 50 200 0.8 0.1 resultados/res_ag.csv
python am.py  datos/tai20_5.txt 12345 50 200 0.8 0.1 10 resultados/res_am.csv
python acs.py datos/tai20_5.txt 12345 50 200 0.1 1.0 0.9 resultados/res_acs.csv
```

| Parámetro | Significado | Rango |
| :--- | :--- | :--- |
| `instancia` | Archivo Taillard: `n m semilla UB LB` y luego m filas de n tiempos | archivo existente |
| `semilla` | Semilla del generador aleatorio | entero |
| `poblacion` / `hormigas` | Individuos por generación / hormigas por iteración | ≥ 1 |
| `iteraciones` | Generaciones (AG, AM) o ciclos de la colonia (ACS) | ≥ 1 |
| `pc`, `pm` | Probabilidad de cruce y de mutación | [0, 1] |
| `frec_bl` | Búsqueda local sobre el mejor individuo cada `frec_bl` generaciones | ≥ 1 |
| `alfa` | Evaporación de feromona, en la actualización local y en la global | (0, 1] |
| `beta` | Peso de la visibilidad η | ≥ 0 |
| `q0` | Probabilidad de explotación en la regla de transición | [0, 1] |

Cada ejecución muestra el progreso cada 10 % de las iteraciones y al final la mejor
secuencia, el makespan, el RPD y el tiempo. Si un parámetro no es válido, el script
termina con un mensaje que indica cuál y por qué.

**Reproducibilidad:** cada ejecución usa su propio `random.Random(semilla)`. Con la
misma instancia, semilla y parámetros se obtienen el mismo makespan y la misma
secuencia final.

### Formato del CSV de salida

Hay una fila por iteración, con el mismo formato para los tres algoritmos:

| Columna | Contenido |
| :--- | :--- |
| `algoritmo` | AG, AM o ACS |
| `instancia`, `semilla`, `parametros` | Configuración de la corrida |
| `iteracion` | 1 … iteraciones |
| `mejor_cmax` | Mejor makespan encontrado hasta esa iteración |
| `rpd` | $100 \cdot (C_{max} - UB) / UB$ |
| `tiempo` | Segundos transcurridos desde el inicio |
| `mejor_secuencia` | Trabajos separados por `-`, numerados desde 0 |

## Pruebas, experimentos y gráficos

```bash
python tests.py                                # 20 pruebas con assert
python experimentos.py                         # 90 corridas, ~13 min
python graficar.py resultados/experimentos.csv
```

- `experimentos.py` usa las semillas 1 a 10. Escribe `resultados/experimentos.csv` (todas
  las iteraciones) y `resultados/resumen.csv` (una fila por instancia y algoritmo), e
  imprime la tabla resumen.
- `graficar.py` crea dos figuras por instancia:
  - `graficos/convergencia_<instancia>.png`: media del mejor $C_{max}$ por iteración.
  - `graficos/dispersion_<instancia>.png`: boxplot del $C_{max}$ final de las semillas,
    con cada semilla como punto.

  Úsalo con `experimentos.csv`: con un CSV de una sola corrida sobrescribe las figuras
  de esa instancia.

## Diseño de los algoritmos

**AG:**
- Población aleatoria de permutaciones.
- Selección por torneo de tamaño 3.
- Cruce OX: un tramo de padre1 conserva su lugar y el resto se completa en el orden de padre2.
- Mutación por inserción.
- Reemplazo generacional con elitismo: el mejor histórico reemplaza al peor hijo.

**AM:** el mismo AG. Cada `frec_bl` generaciones aplica al mejor individuo una pasada
de búsqueda local por inserción: cada trabajo se prueba en todas las posiciones y
queda en la mejor si reduce el $C_{max}$.

**ACS** (adaptación del preproyecto TSP):
- **Grafo:** trabajo → trabajo. $\tau_{ij}$ es la deseabilidad de programar $j$
  inmediatamente después de $i$. Es dirigida: $\tau_{ij} \neq \tau_{ji}$.
- **Visibilidad SPT:** $\eta_j = 1 / \sum_k p_{j,k}$. Prefiere los trabajos de menor
  tiempo total.
- **Feromona inicial:** $\tau_0 = 1 / (n \cdot C_{max}^{SPT})$.
- **Construcción:** cada hormiga parte en un trabajo al azar.
  - Con probabilidad $q_0$ elige el máximo $\tau_{ij}\,\eta_j^{\beta}$.
  - Si no, sortea con probabilidad proporcional a ese valor (ruleta).
- **Actualización local**, en cada arista recorrida: $\tau_{ij} \leftarrow (1-\alpha)\tau_{ij} + \alpha\tau_0$.
- **Actualización global**, solo en las aristas de la mejor secuencia global:
  $\tau_{ij} \leftarrow (1-\alpha)\tau_{ij} + \alpha / C_{max}^{mejor}$.

**Por qué estas opciones** (el enunciado ofrece alternativas; se eligió una sola de cada una):
- **Torneo k=3, no ruleta:** la ruleta exige transformar el Cmax, y como los Cmax de una
  población son muy parecidos, las probabilidades quedan casi uniformes. El torneo solo
  compara. k=3 da una presión moderada.
- **OX, no PMX:** el Cmax depende del orden relativo de los trabajos, y OX lo conserva.
- **Inserción, no intercambio:** mueve un solo trabajo y es el vecindario estándar del PFSP
  (el de NEH). La búsqueda local del AM usa el mismo vecindario. 2-opt se descartó porque
  invierte precedencias.
- **BL una pasada, solo al mejor:** cada pasada cuesta n² evaluaciones; aplicarla a toda
  la población multiplicaría ese costo por 50.
- **Elitismo de 1:** es lo mínimo para que el mejor Cmax nunca empeore.
- **SPT, no NEH reducida:** con NEH no se distinguiría su aporte del de la colonia.
- **Refuerzo con la mejor global:** es la forma original del ACS (Dorigo y Gambardella, 1997).

## Resultados

Configuración:
- Semillas 1 a 10. Mismo presupuesto para todos: 50 individuos u hormigas × 200 iteraciones.
- AG/AM: pc = 0.8, pm = 0.1, frec_bl = 10.
- ACS: α = 0.1, β = 1.0, q0 = 0.9.

| Instancia | Alg | Mejor | Media ± desv | RPD medio | Tiempo medio |
| :--- | :---: | ---: | ---: | ---: | ---: |
| tai20_5 (UB 1278) | AG | 1297 | 1297.0 ± 0.0 | 1.49 % | 0.45 s |
| | AM | 1278 | 1295.1 ± 6.0 | 1.34 % | 0.66 s |
| | ACS | 1297 | 1316.3 ± 13.1 | 3.00 % | 1.58 s |
| tai50_10 (UB 3025) | AG | 3122 | 3195.7 ± 34.5 | 5.64 % | 1.39 s |
| | AM | 3070 | 3123.0 ± 29.4 | 3.24 % | 7.48 s |
| | ACS | 3446 | 3467.2 ± 18.8 | 14.62 % | 5.14 s |
| tai100_10 (UB 5770) | AG | 5970 | 6049.8 ± 57.0 | 4.85 % | 2.79 s |
| | AM | 5826 | 5855.5 ± 28.0 | 1.48 % | 52.70 s |
| | ACS | 6304 | 6330.8 ± 14.4 | 9.72 % | 12.62 s |

- El AM obtiene el menor RPD en las tres instancias y alcanza el UB en tai20_5. Su costo
  es el tiempo: en tai100_10 la búsqueda local multiplica unas 19 veces el tiempo del AG.
- ACS es el más estable entre semillas en 50×10 y 100×10, pero converge temprano a
  soluciones peores. La visibilidad SPT sola da secuencias con 15–25 % de RPD, así que
  orienta poco hacia un buen makespan.

**Decisiones de parámetros:** el presupuesto 50×200, pc, pm, frec_bl y q0 son los valores
del ejemplo del enunciado (q0 = 0.9 es también el valor de Dorigo y Gambardella) y no se
calibraron. Solo cambian dos:
- **β = 1.0 en lugar de 2.0** (el valor del ejemplo del enunciado). Con 5 semillas en
  tai20_5, el RPD medio fue:

  | β | 0 | 1 | 2 | 5 |
  | :--- | :---: | :---: | :---: | :---: |
  | RPD medio | 3.19 % | 2.90 % | 3.35 % | 5.60 % |

- **α = 0.1 en lugar de 1.0.** Con α = 1 cada actualización reemplazaría toda la feromona
  acumulada y ACS perdería su memoria.
