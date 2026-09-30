"""Biblioteca de operadores para Ant Colony System (ACS) aplicado a TSP."""

import math

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


def matriz_distancias(coordenadas):
    """Calcula matriz de distancias euclidianas redondeadas segun norma TSPLIB (EUC_2D).
    
    d_ij = int(sqrt((xi - xj)^2 + (yi - yj)^2) + 0.5)
    """
    n = len(coordenadas)
    d = [[0] * n for _ in range(n)]
    for i in range(n):
        xi, yi = coordenadas[i]
        for j in range(i + 1, n):
            xj, yj = coordenadas[j]
            dist = int(math.hypot(xi - xj, yi - yj) + 0.5)
            d[i][j] = dist
            d[j][i] = dist
    return d


def matriz_visibilidad(D):
    """Calcula visibilidad heuristica eta_ij = 1 / d_ij para i != j."""
    n = len(D)
    eta = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j and D[i][j] > 0:
                eta[i][j] = 1.0 / D[i][j]
    return eta


def evaluar_ruta(ruta, D):
    """Calcula el costo total de un ciclo cerrado para la ruta dada."""
    costo = 0
    n = len(ruta)
    for k in range(n):
        costo += D[ruta[k]][ruta[(k + 1) % n]]
    return costo

