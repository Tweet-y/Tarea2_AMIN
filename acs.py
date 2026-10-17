"""Ant Colony System (ACS) para PFSP.

Uso: python acs.py instancia semilla hormigas iteraciones alfa beta q0 salida.csv
"""

import argparse
import os
from random import Random
from time import perf_counter

import operadores as op


def ejecutar_acs(p, ub, instancia, semilla, hormigas, iteraciones, alfa, beta, q0,
                 mostrar_progreso=False):
    """Ejecuta ACS y devuelve (mejor_secuencia, mejor_cmax, filas), con una fila CSV por iteracion."""
    inicio = perf_counter()
    rng = Random(semilla)
    parametros = f"hormigas={hormigas} alfa={alfa} beta={beta} q0={q0}"

    # Inicializar
    eta = op.visibilidad_spt(p)
    tau, tau0 = op.inicializar_feromonas(p)
    mejor_sec, mejor_cmax = None, float("inf")
    filas = []

    for iteracion in range(1, iteraciones + 1):
        for _ in range(hormigas):
            # Construir solucion (incluye actualizacion local) y evaluarla
            secuencia = op.construir_secuencia(tau, eta, beta, q0, alfa, tau0, rng)
            cmax = op.makespan(secuencia, p)
            # Actualizar mejor solucion
            if cmax < mejor_cmax:
                mejor_sec, mejor_cmax = secuencia, cmax

        # Actualizar feromonas (global, sobre la mejor solucion)
        op.actualizar_global(tau, mejor_sec, mejor_cmax, alfa)

        tiempo = perf_counter() - inicio
        filas.append(["ACS", instancia, semilla, parametros, iteracion, mejor_cmax,
                      round(op.rpd(mejor_cmax, ub), 4), round(tiempo, 4),
                      "-".join(map(str, mejor_sec))])
        if mostrar_progreso and iteracion % max(1, iteraciones // 10) == 0:
            print(f"  Iteracion {iteracion:>5}/{iteraciones}  mejor Cmax = {mejor_cmax}")

    return mejor_sec, mejor_cmax, filas


def main():
    parser = argparse.ArgumentParser(description="Ant Colony System para PFSP")
    parser.add_argument("instancia")
    parser.add_argument("semilla", type=int)
    parser.add_argument("hormigas", type=int)
    parser.add_argument("iteraciones", type=int)
    parser.add_argument("alfa", type=float, help="evaporacion, en (0, 1]")
    parser.add_argument("beta", type=float, help="peso de la heuristica, >= 0")
    parser.add_argument("q0", type=float, help="probabilidad de explotacion, en [0, 1]")
    parser.add_argument("salida", metavar="salida.csv")
    args = parser.parse_args()

    if not os.path.isfile(args.instancia):
        parser.error(f"no existe el archivo de instancia '{args.instancia}'")
    if args.hormigas < 1 or args.iteraciones < 1:
        parser.error("hormigas e iteraciones deben ser enteros mayores que cero")
    if not 0 < args.alfa <= 1:
        parser.error("alfa debe estar en (0, 1]")
    if args.beta < 0:
        parser.error("beta debe ser mayor o igual que cero")
    if not 0 <= args.q0 <= 1:
        parser.error("q0 debe estar en [0, 1]")
    try:
        p, ub = op.leer_instancia(args.instancia)
    except ValueError as error:
        parser.error(str(error))

    print(f"ACS | {args.instancia} | {p.shape[0]} trabajos x {p.shape[1]} maquinas | UB = {ub}")
    print(f"Parametros: semilla={args.semilla} hormigas={args.hormigas} "
          f"iteraciones={args.iteraciones} alfa={args.alfa} beta={args.beta} q0={args.q0}")
    secuencia, cmax, filas = ejecutar_acs(
        p, ub, args.instancia, args.semilla, args.hormigas, args.iteraciones,
        args.alfa, args.beta, args.q0, mostrar_progreso=True,
    )
    op.guardar_csv(args.salida, filas)

    print(f"Mejor secuencia: {secuencia}")
    print(f"Makespan: {cmax} | RPD: {op.rpd(cmax, ub):.2f} % | Tiempo: {filas[-1][7]:.2f} s")
    print(f"Resultados guardados en {args.salida}")


if __name__ == "__main__":
    main()
