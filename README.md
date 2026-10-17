# Sistema de Colonia de Hormigas (ACS) para el Problema del Vendedor Viajero (TSP)
## Pre Proyecto 2 - Algoritmos Metaheurísticos Inspirados en la Naturaleza (AMIN)

Implementación modular de la metaheurística **Ant Colony System (ACS)** (Dorigo & Gambardella, 1997) aplicada a la instancia **Berlin52** de TSPLIB, desarrollada siguiendo el principio **KISS** (*Keep It Simple*) sin hiperingeniería.

---

## 1. Organización y Modularización

El proyecto separa responsabilidades en dos componentes centrales:

- **`acs.py`**: Explica **qué** hace el algoritmo (flujo de control, ciclo iterativo de hormigas, parámetros CLI y exportación estructurada).
- **`operadores.py`**: Explica **cómo** se ejecutan las operaciones matemáticas y estocásticas (distancias NumPy EUC_2D, visibilidad, regla pseudoaleatoria $q_0$, decaimiento local y refuerzo global).
- **`tests.py`**: Pruebas unitarias nativas con `assert` (11 pruebas sin dependencias externas).
- **`graficar.py`**: Visualización de curvas de convergencia y mapeo 2D del recorrido.

### Estructura de Carpetas

```
Tarea2_AMIN/
├── acs.py                  # Algoritmo principal ACS y CLI
├── operadores.py           # Biblioteca de operadores de soporte y ACS
├── tests.py                # Suite de 11 pruebas unitarias
├── graficar.py             # Generador de gráficos
├── datos/
│   └── berlin52.tsp        # Coordenadas oficiales TSPLIB Berlin52
├── resultados/
│   └── acs_berlin52.csv    # Registro de corrida por iteración
└── graficos/
    ├── convergencia_berlin52.png  # Curva de convergencia
    └── ruta_berlin52.png          # Mapa 2D de la mejor ruta
```

---

## 2. Requisitos e Instalación

Desarrollado en Python 3.9+. Requiere `numpy` para cálculo vectorizado y `matplotlib` para visualización:

```bash
pip install numpy matplotlib
```

---

## 3. Instrucciones de Ejecución

### A. Ejecutar Algoritmo ACS

Formato posicional según requerimiento del enunciado:

```bash
python acs.py <instancia> <n_hormigas> <iteraciones> <alfa> <beta> <q0> <semilla> <resultados.csv>
```

**Ejemplo de ejecución (Berlin52):**

```bash
python acs.py datos/berlin52.tsp 10 100 0.1 2.0 0.9 42 resultados/acs_berlin52.csv
```

**Parámetros:**
- `instancia`: Ruta al archivo TSPLIB (`datos/berlin52.tsp`).
- `n_hormigas`: Cantidad de hormigas por iteración ($m$).
- `iteraciones`: Número de ciclos constructivos.
- `alfa` ($\alpha$): Factor de evaporación/tasa de aprendizaje global (típico: `0.1`).
- `beta` ($\beta$): Peso de la información heurística/visibilidad (típico: `2.0` a `5.0`).
- `q0` ($q_0$): Probabilidad de explotación vs exploración (típico: `0.9`).
- `semilla`: Semilla de números aleatorios para reproducibilidad.
- `resultados.csv`: Ruta del archivo CSV de salida.

### B. Ejecutar Suite de Pruebas

Pruebas unitarias completas de todos los operadores:

```bash
python tests.py
```

### C. Generar Gráficos

Genera la curva de convergencia y el mapa 2D a partir del CSV:

```bash
python graficar.py resultados/acs_berlin52.csv
```

---

## 4. Resultados Experimentales (Berlin52)

Configuración base ejecutada:
- **Hormigas**: 10
- **Iteraciones**: 100
- **Parámetros**: $\alpha = 0.1$, $\beta = 2.0$, $q_0 = 0.9$, $\rho = 0.1$
- **Semilla**: 42

| Métrica | Valor |
| :--- | :--- |
| **Costo Vecino Más Cercano ($L_{nn}$)** | 10323 |
| **Mejor Costo Encontrado (ACS)** | 8857 |
| **Óptimo Conocido TSPLIB** | 7542 |
| **Tiempo de Ejecución** | ~0.65 s |

Gráficos generados:
- Curva de convergencia: `graficos/convergencia_berlin52.png`
- Ruta resultante: `graficos/ruta_berlin52.png`

---

## 5. Transferencia a un Problema Más Complejo: Permutation Flow Shop (PFSP)

Análisis de transferencia metodológica desde TSP hacia **PFSP (Taillard)**:

### Tabla Comparativa

| Aspecto | Berlin52 (TSP) | Permutation Flow Shop (PFSP) |
| :--- | :--- | :--- |
| **Dominio** | Ruteo en grafo de ciudades | Secuenciación de $N$ trabajos en $M$ máquinas |
| **Representación** | Permutación cíclica (arista de retorno $c_{n-1} \to c_0$) | Permutación lineal sin retorno $\pi = [j_1, j_2, \dots, j_n]$ |
| **Semántica Feromona ($\tau$)** | $\tau_{i, j}$: Deseabilidad de recorrer la arista $i \to j$ | $\tau_{k, j}$: Deseabilidad de asignar el **trabajo $j$** en la **posición $k$** |
| **Visibilidad Heurística ($\eta$)** | $\eta_{ij} = 1 / d_{ij}$ (inversa de distancia euclidiana) | $\eta_j = 1 / \sum_{m=1}^{M} p_{j, m}$ (regla SPT: trabajos más cortos primero) |
| **Función Objetivo** | Distancia euclidiana total (suma de aristas) | Makespan ($C_{\max}$): tiempo de completación del último trabajo |
| **Complejidad Evaluación** | $O(N)$ suma lineal | $O(N \cdot M)$ programación dinámica |

### Respuestas a las Preguntas Guía (Sección 7 del Enunciado)

#### 1. ¿Qué partes de `acs.py` podrían mantenerse?
Se mantiene intacto el **esqueleto del bucle principal**:
- Inicialización de hormigas, parámetros ($\alpha, \beta, q_0, \rho$) y matriz de feromonas.
- Bucle de iteraciones con construcción paso a paso de cada hormiga.
- Actualización local de feromona en cada paso de asignación.
- Detección y almacenamiento de la mejor solución global ($L_{gb}$).
- Actualización global de feromona al cierre de la iteración.
- Esquema de logging a CSV y reproducibilidad mediante semilla.

#### 2. ¿Qué operaciones de `operadores.py` deberían modificarse o reemplazarse?
- **`leer_instancia`**: Reemplazar lectura de coordenadas 2D por lectura de matriz de tiempos de procesamiento $p_{j, m}$ (formato Taillard de $N$ trabajos $\times$ $M$ máquinas).
- **`matriz_visibilidad`**: Cambiar $\eta_{ij} = 1 / d_{ij}$ por la heurística SPT (Shortest Processing Time): $\eta_j = 1 / \sum_{m=1}^M p_{jm}$.
- **`heuristica_vecino_mas_cercano`**: Reemplazar por heurística constructiva clásica de PFSP, como la heurística **NEH** (Nawaz-Enscore-Ham), para obtener una cota base $C_{NEH}$ con la cual inicializar $\tau_0$.
- **`actualizar_local` y `actualizar_global`**: La actualización pasa de aristas $(i, j)$ a pares posición-trabajo $(k, \pi[k])$.

#### 3. ¿Qué nueva información necesitaría representar una solución?
- En TSP, la solución es un ciclo donde el orden relativo entre nodos adyacentes define aristas de viaje.
- En PFSP, una solución es una **secuencia ordenada de trabajos** $\pi = [\pi_1, \pi_2, \dots, \pi_n]$ donde cada trabajo se ejecuta en el mismo orden en todas las $M$ máquinas, sin arista de cierre entre el último y el primer trabajo.

#### 4. ¿Qué cambiaría en la función que evalúa una solución?
- Se sustituye la suma de distancias por el cálculo del **Makespan ($C_{\max}$)** mediante la recurrencia canónica de Flow Shop:
  $$C(j, m) = \max(C(j - 1, m), C(j, m - 1)) + p_{\pi[j], m}$$
  donde $C(j, m)$ es el instante de finalización del trabajo en la posición $j$ sobre la máquina $m$. La función objetivo es $C(N, M)$.
