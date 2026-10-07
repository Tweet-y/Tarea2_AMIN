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

## Verificamos si lee el archivo 
## print(leer_instancia("datos/berlin52.tsp"))

## Calculamos la matriz de distancia
def calcular_distancia(coordenadas):
    puntos = np.array(coordenadas)
    diferencias = puntos[:, np.newaxis, :] - puntos[np.newaxis, :, :]
    
    return np.rint(np.sqrt((diferencias ** 2).sum(axis=2)))

coordenadas = leer_instancia("datos/berlin52.tsp")
distancias = calcular_distancia(coordenadas)

## Pruba distancia
## print(distancias.shape)
## print(distancias[0][1])
## print(distancias[0][4])

## Calculamos el costo total de una ruta
def calcular_costos(ruta, distancias):
    costo = 0
    for i in range (len(ruta)):
        costo += distancias[ruta[i]][ruta[(i + 1) % len(ruta)]]
    
    return costo

## Prueba costos
## ruta = list(range(52))
## print(calcular_costos(ruta, distancias))
## print(calcular_costos([0, 1, 0, 1], distancias))