"""Biblioteca de operadores para PFSP: lectura, evaluacion y operadores de AG, AM y ACS."""

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
