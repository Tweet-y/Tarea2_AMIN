"""Biblioteca de operadores para Ant Colony System (ACS) aplicado a TSP."""

import numpy as np


def leer_instancia(ruta_archivo):
    """Lee coordenadas de ciudades desde archivo TSPLIB o formato texto.

    Retorna: lista de tuplas (x, y) indexadas desde 0.
    """
    coordenadas = []
    en_seccion_coords = False

    with open(ruta_archivo, "r", encoding="utf-8") as f:
        for linea in f:
            texto = linea.strip()
            if not texto:
                continue

            if texto == "NODE_COORD_SECTION":
                en_seccion_coords = True
                continue

            if texto in ("EOF", "DEMAND_SECTION", "DEPOT_SECTION"):
                break

            partes = texto.split()
            # Formato TSPLIB: id x y
            if en_seccion_coords and len(partes) >= 3 and partes[0].isdigit():
                coordenadas.append((float(partes[1]), float(partes[2])))
            # Soporte formato plano sin cabecera TSPLIB: id x y  o  x y
            elif not en_seccion_coords:
                if len(partes) == 3 and partes[0].isdigit():
                    coordenadas.append((float(partes[1]), float(partes[2])))
                elif len(partes) == 2:
                    try:
                        coordenadas.append((float(partes[0]), float(partes[1])))
                    except ValueError:
                        continue

    return coordenadas


def calcular_distancia(coordenadas):
    """Calcula matriz de distancias euclidianas redondeadas segun norma TSPLIB usando NumPy."""
    puntos = np.array(coordenadas)
    diferencias = puntos[:, np.newaxis, :] - puntos[np.newaxis, :, :]
    return np.rint(np.sqrt((diferencias ** 2).sum(axis=2)))


# Alias de compatibilidad
matriz_distancias = calcular_distancia


def matriz_visibilidad(D):
    """Calcula visibilidad heuristica eta_ij = 1 / d_ij para i != j."""
    D_arr = np.asarray(D, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(D_arr > 0, 1.0 / D_arr, 0.0)


def calcular_costos(ruta, distancias):
    """Calcula el costo total de un ciclo cerrado para la ruta dada."""
    costo = 0
    n = len(ruta)
    for i in range(n):
        costo += distancias[ruta[i]][ruta[(i + 1) % n]]
    return int(costo)


# Alias de compatibilidad
evaluar_ruta = calcular_costos


def heuristica_vecino_mas_cercano(D, ciudad_inicio=0):
    """Construye un tour voraz usando vecino mas cercano y calcula su costo (L_nn)."""
    n = len(D)
    visitadas = [ciudad_inicio]
    no_visitadas = set(range(n)) - {ciudad_inicio}
    actual = ciudad_inicio

    while no_visitadas:
        siguiente = min(no_visitadas, key=lambda c: D[actual][c])
        visitadas.append(siguiente)
        no_visitadas.remove(siguiente)
        actual = siguiente

    costo_nn = calcular_costos(visitadas, D)
    return visitadas, costo_nn


def inicializar_feromonas(n, tau0):
    """Crea e inicializa la matriz de feromonas n x n con valor tau0."""
    return np.full((n, n), tau0, dtype=float)


def siguiente_ciudad(actual, no_visitadas, tau, eta, beta, q0, rng):
    """Selecciona la siguiente ciudad usando regla pseudoaleatoria proporcional de ACS (Ec. 1 y 2)."""
    candidatas = list(no_visitadas)
    if len(candidatas) == 1:
        return candidatas[0]

    pesos = [tau[actual, j] * (eta[actual, j] ** beta) for j in candidatas]

    # Regla pseudoaleatoria: explotacion con probabilidad q0
    if rng.random() <= q0:
        max_peso = -1.0
        mejor_idx = 0
        for idx, peso in enumerate(pesos):
            if peso > max_peso:
                max_peso = peso
                mejor_idx = idx
        return candidatas[mejor_idx]

    # Exploracion: seleccion proporcional tipo ruleta con probabilidad (1 - q0)
    total_pesos = sum(pesos)
    if total_pesos <= 0.0:
        return rng.choice(candidatas)

    r = rng.random() * total_pesos
    acum = 0.0
    for ciudad, peso in zip(candidatas, pesos):
        acum += peso
        if acum >= r:
            return ciudad

    return candidatas[-1]


def actualizar_local(tau, i, j, rho, tau0):
    """Actualizacion local de feromona al recorrer la arista (i, j) en construccion (Ec. 4)."""
    nuevo_valor = (1.0 - rho) * tau[i, j] + (rho * tau0)
    tau[i, j] = nuevo_valor
    tau[j, i] = nuevo_valor


def actualizar_global(tau, mejor_ruta, mejor_costo, alfa):
    """Actualizacion global de feromona sobre las aristas de la mejor solucion (Ec. 3)."""
    delta = 1.0 / mejor_costo
    n = len(mejor_ruta)
    for k in range(n):
        i = mejor_ruta[k]
        j = mejor_ruta[(k + 1) % n]
        nuevo_valor = (1.0 - alfa) * tau[i, j] + (alfa * delta)
        tau[i, j] = nuevo_valor
        tau[j, i] = nuevo_valor


if __name__ == "__main__":
    coords = leer_instancia("datos/berlin52.tsp")
    dist = calcular_distancia(coords)
    print("Dimension distancias:", dist.shape)
    print("d(0, 1):", dist[0, 1])
    print("Costo ruta [0..51]:", calcular_costos(list(range(52)), dist))
