"""Algoritmo Genetico (AG) para PFSP.

Uso: python ag.py instancia semilla poblacion iteraciones pc pm salida.csv
"""

import argparse
import os
from random import Random
from time import perf_counter

import operadores as op


def ejecutar_ag(p, ub, instancia, semilla, tam_poblacion, iteraciones, pc, pm,
                mostrar_progreso=False):
    """Ejecuta el AG y devuelve (mejor_secuencia, mejor_cmax, filas), con una fila CSV por iteracion."""
    inicio = perf_counter()
    rng = Random(semilla)
    parametros = f"poblacion={tam_poblacion} pc={pc} pm={pm}"

    # Inicializar
    poblacion = op.poblacion_inicial(tam_poblacion, len(p), rng)
    cmax = [op.makespan(s, p) for s in poblacion]
    mejor = min(range(tam_poblacion), key=lambda i: cmax[i])
    mejor_sec, mejor_cmax = poblacion[mejor], cmax[mejor]
    filas = []

    for iteracion in range(1, iteraciones + 1):
        # Seleccion, cruce y mutacion
        hijos = []
        while len(hijos) < tam_poblacion:
            padre1 = op.torneo(poblacion, cmax, rng)
            padre2 = op.torneo(poblacion, cmax, rng)
            hijo = op.cruce_ox(padre1, padre2, rng) if rng.random() < pc else list(padre1)
            if rng.random() < pm:
                hijo = op.mutacion_insercion(hijo, rng)
            hijos.append(hijo)
        cmax_hijos = [op.makespan(s, p) for s in hijos]

        # Reemplazo generacional con elitismo: el mejor historico sustituye al peor hijo
        peor = max(range(tam_poblacion), key=lambda i: cmax_hijos[i])
        hijos[peor], cmax_hijos[peor] = mejor_sec, mejor_cmax
        poblacion, cmax = hijos, cmax_hijos

        # Actualizar mejor solucion
        mejor = min(range(tam_poblacion), key=lambda i: cmax[i])
        mejor_sec, mejor_cmax = poblacion[mejor], cmax[mejor]

        tiempo = perf_counter() - inicio
        filas.append(["AG", instancia, semilla, parametros, iteracion, mejor_cmax,
                      round(op.rpd(mejor_cmax, ub), 4), round(tiempo, 4),
                      "-".join(map(str, mejor_sec))])
        if mostrar_progreso and iteracion % max(1, iteraciones // 10) == 0:
            print(f"  Iteracion {iteracion:>5}/{iteraciones}  mejor Cmax = {mejor_cmax}")

    return mejor_sec, mejor_cmax, filas


def main():
    parser = argparse.ArgumentParser(description="Algoritmo Genetico para PFSP")
    parser.add_argument("instancia")
    parser.add_argument("semilla", type=int)
    parser.add_argument("poblacion", type=int)
    parser.add_argument("iteraciones", type=int)
    parser.add_argument("pc", type=float, help="probabilidad de cruce, en [0, 1]")
    parser.add_argument("pm", type=float, help="probabilidad de mutacion, en [0, 1]")
    parser.add_argument("salida", metavar="salida.csv")
    args = parser.parse_args()

    if not os.path.isfile(args.instancia):
        parser.error(f"no existe el archivo de instancia '{args.instancia}'")
    if args.poblacion < 1 or args.iteraciones < 1:
        parser.error("poblacion e iteraciones deben ser enteros mayores que cero")
    if not (0 <= args.pc <= 1 and 0 <= args.pm <= 1):
        parser.error("pc y pm deben estar en [0, 1]")
    try:
        p, ub = op.leer_instancia(args.instancia)
    except ValueError as error:
        parser.error(str(error))

    print(f"AG | {args.instancia} | {p.shape[0]} trabajos x {p.shape[1]} maquinas | UB = {ub}")
    print(f"Parametros: semilla={args.semilla} poblacion={args.poblacion} "
          f"iteraciones={args.iteraciones} pc={args.pc} pm={args.pm}")
    secuencia, cmax, filas = ejecutar_ag(
        p, ub, args.instancia, args.semilla, args.poblacion, args.iteraciones,
        args.pc, args.pm, mostrar_progreso=True,
    )
    op.guardar_csv(args.salida, filas)

    print(f"Mejor secuencia: {secuencia}")
    print(f"Makespan: {cmax} | RPD: {op.rpd(cmax, ub):.2f} % | Tiempo: {filas[-1][7]:.2f} s")
    print(f"Resultados guardados en {args.salida}")


if __name__ == "__main__":
    main()
