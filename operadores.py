"""Biblioteca de operadores para PFSP: lectura, evaluacion y operadores de AG, AM y ACS."""

import csv
import os

import numpy as np


def leer_instancia(ruta):
    """Lee una instancia de Taillard.

    Archivo: cabecera `n m semilla UB LB` y luego m filas de n tiempos (una por maquina).
    Retorna (p, ub), con p[i, j] = tiempo del trabajo i en la maquina j (forma n x m).
    """
    with open(ruta, encoding="utf-8") as f:
        n, m, _, ub, _ = (int(x) for x in f.readline().split())
        p = np.loadtxt(f, dtype=int, ndmin=2).T
    if p.shape != (n, m):
        raise ValueError(
            f"{ruta}: la cabecera indica {n} trabajos x {m} maquinas, "
            f"pero se leyeron {p.shape[0]} x {p.shape[1]} tiempos."
        )
    return p, ub


def makespan(secuencia, p):
    """Cmax con C(i, j) = max(C(i-1, j), C(i, j-1)) + p[pi_i, j].

    C guarda solo la fila del trabajo anterior: C[j] = C(i-1, j) antes de actualizarla.
    """
    C = [0] * p.shape[1]
    for tiempos in p[secuencia].tolist():
        C[0] += tiempos[0]
        for j in range(1, len(C)):
            C[j] = max(C[j], C[j - 1]) + tiempos[j]
    return C[-1]


def rpd(cmax, ub):
    """Desviacion porcentual relativa respecto de la mejor cota conocida."""
    return 100 * (cmax - ub) / ub


CABECERA_CSV = ["algoritmo", "instancia", "semilla", "parametros", "iteracion",
                "mejor_cmax", "rpd", "tiempo", "mejor_secuencia"]


def guardar_csv(ruta, filas):
    """Escribe la cabecera comun y una fila por iteracion; crea la carpeta si falta."""
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(CABECERA_CSV)
        escritor.writerows(filas)


# ---------------------------------------------------------------- ACS

def visibilidad_spt(p):
    """eta_j = 1 / tiempo total del trabajo j (SPT): los trabajos cortos atraen mas."""
    return 1.0 / p.sum(axis=1)


def inicializar_feromonas(p):
    """tau0 = 1 / (n * Cmax_SPT); devuelve (tau n x n llena de tau0, tau0)."""
    n = len(p)
    spt = np.argsort(p.sum(axis=1), kind="stable")
    tau0 = 1.0 / (n * makespan(spt, p))
    return np.full((n, n), tau0), tau0


def siguiente_trabajo(actual, pendientes, tau, eta, beta, q0, rng):
    """Regla pseudoaleatoria proporcional de ACS (Ec. 1 y 2).

    Con probabilidad q0 elige el mayor tau[actual, j] * eta[j]^beta (explotacion);
    si no, sortea j con probabilidad proporcional a ese peso (ruleta).
    """
    pesos = tau[actual, pendientes] * eta[pendientes] ** beta
    if rng.random() < q0:
        return pendientes[int(np.argmax(pesos))]
    acumulado = np.cumsum(pesos)
    idx = np.searchsorted(acumulado, rng.random() * acumulado[-1], side="right")
    return pendientes[min(idx, len(pendientes) - 1)]


def actualizar_local(tau, i, j, alfa, tau0):
    """Ec. 4: tau_ij = (1 - alfa) tau_ij + alfa tau0. Arista dirigida: j se programa tras i."""
    tau[i, j] = (1 - alfa) * tau[i, j] + alfa * tau0


def construir_secuencia(tau, eta, beta, q0, alfa, tau0, rng):
    """Una hormiga parte en un trabajo al azar y agrega trabajos hasta completar la permutacion.

    Aplica la actualizacion local en cada arista recorrida.
    """
    pendientes = list(range(len(eta)))
    secuencia = [pendientes.pop(rng.randrange(len(pendientes)))]
    while pendientes:
        actual = secuencia[-1]
        siguiente = siguiente_trabajo(actual, pendientes, tau, eta, beta, q0, rng)
        actualizar_local(tau, actual, siguiente, alfa, tau0)
        secuencia.append(siguiente)
        pendientes.remove(siguiente)
    return secuencia


def actualizar_global(tau, secuencia, cmax, alfa):
    """Ec. 3: refuerza solo las aristas de la mejor secuencia, con delta = 1 / Cmax."""
    for i, j in zip(secuencia, secuencia[1:]):
        tau[i, j] = (1 - alfa) * tau[i, j] + alfa / cmax


# ---------------------------------------------------------------- AG

def poblacion_inicial(tam, n, rng):
    """tam permutaciones aleatorias de los n trabajos."""
    return [rng.sample(range(n), n) for _ in range(tam)]


def torneo(poblacion, cmax, rng, k=3):
    """Sortea k individuos (con reposicion) y devuelve el de menor Cmax, sin copiarlo."""
    ganador = min((rng.randrange(len(poblacion)) for _ in range(k)), key=lambda i: cmax[i])
    return poblacion[ganador]


def cruce_ox(padre1, padre2, rng):
    """Order Crossover: copia un tramo de padre1 en su lugar y completa los huecos,
    de izquierda a derecha, con los trabajos restantes en el orden de padre2."""
    a, b = sorted(rng.sample(range(len(padre1) + 1), 2))
    tramo = padre1[a:b]
    resto = [trabajo for trabajo in padre2 if trabajo not in tramo]
    return resto[:a] + tramo + resto[a:]


def mutacion_insercion(secuencia, rng):
    """Saca un trabajo al azar y lo inserta en otra posicion al azar (devuelve copia)."""
    mutada = list(secuencia)
    i, j = rng.sample(range(len(mutada)), 2)
    mutada.insert(j, mutada.pop(i))
    return mutada
