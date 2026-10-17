"""Ejecucion de Ant Colony System para una instancia TSP."""

import argparse
import csv
from pathlib import Path
from random import Random
from time import perf_counter

import operadores as op


def ejecutar_acs(instancia, hormigas, iteraciones, alfa, beta, q0, semilla, resultados_csv):
    """Ejecuta ACS, guarda el progreso y devuelve mejor ruta, costo y tiempo."""
    inicio = perf_counter()
    rng = Random(semilla)
    rho = 0.1

    coords = op.leer_instancia(instancia)
    D = op.matriz_distancias(coords)
    eta = op.matriz_visibilidad(D)
    n = len(coords)
    _, L_nn = op.heuristica_vecino_mas_cercano(D)
    tau = op.inicializar_feromonas(n, L_nn)
    tau0 = 1.0 / (n * L_nn)

    mejor_ruta = None
    mejor_costo = float("inf")
    salida = Path(resultados_csv)
    salida.parent.mkdir(parents=True, exist_ok=True)

    with salida.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow([
            "instancia", "semilla", "hormigas", "iteraciones", "alfa", "beta",
            "q0", "iteracion", "mejor_costo", "tiempo",
        ])

        for iteracion in range(1, iteraciones + 1):
            for _ in range(hormigas):
                ruta = [rng.randrange(n)]
                no_visitadas = set(range(n)) - {ruta[0]}

                while no_visitadas:
                    actual = ruta[-1]
                    siguiente = op.siguiente_ciudad(
                        actual, no_visitadas, tau, eta, beta, q0, rng
                    )
                    op.actualizar_local(tau, actual, siguiente, rho, tau0)
                    ruta.append(siguiente)
                    no_visitadas.remove(siguiente)

                op.actualizar_local(tau, ruta[-1], ruta[0], rho, tau0)
                costo = op.evaluar_ruta(ruta, D)
                if costo < mejor_costo:
                    mejor_ruta = ruta.copy()
                    mejor_costo = costo

            op.actualizar_global(tau, mejor_ruta, mejor_costo, alfa)
            escritor.writerow([
                instancia, semilla, hormigas, iteraciones, alfa, beta, q0,
                iteracion, mejor_costo, perf_counter() - inicio,
            ])

    return mejor_ruta, mejor_costo, perf_counter() - inicio


def main():
    parser = argparse.ArgumentParser(description="Ant Colony System para TSP")
    parser.add_argument("instancia")
    parser.add_argument("hormigas", type=int)
    parser.add_argument("iteraciones", type=int)
    parser.add_argument("alfa", type=float)
    parser.add_argument("beta", type=float)
    parser.add_argument("q0", type=float)
    parser.add_argument("semilla", type=int)
    parser.add_argument("resultados_csv", metavar="resultados.csv")
    args = parser.parse_args()

    if args.hormigas < 1 or args.iteraciones < 1:
        parser.error("hormigas e iteraciones deben ser mayores que cero")
    if not 0 <= args.alfa <= 1 or not 0 <= args.q0 <= 1:
        parser.error("alfa y q0 deben estar entre 0 y 1")
    if args.beta < 0:
        parser.error("beta debe ser mayor o igual que cero")

    ruta, costo, tiempo = ejecutar_acs(
        args.instancia, args.hormigas, args.iteraciones, args.alfa,
        args.beta, args.q0, args.semilla, args.resultados_csv,
    )
    print("Mejor ruta:", ruta)
    print(f"Mejor costo: {costo:g}")
    print(f"Tiempo total: {tiempo:.6f} segundos")


if __name__ == "__main__":
    main()
