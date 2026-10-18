"""Experimentos comparativos: AG, AM y ACS sobre las 3 instancias con 10 semillas.

Uso: python experimentos.py
Genera resultados/experimentos.csv (una fila por iteracion de cada corrida) y
resultados/resumen.csv (una fila por instancia y algoritmo), e imprime el resumen.
"""

import csv
from statistics import mean, stdev

import operadores as op
from acs import ejecutar_acs
from ag import ejecutar_ag

INSTANCIAS = ["datos/tai20_5.txt", "datos/tai50_10.txt", "datos/tai100_10.txt"]
SEMILLAS = range(1, 11)

# Mismo presupuesto base para los tres: 50 individuos u hormigas x 200 iteraciones.
TAMANO, ITERACIONES = 50, 200
PC, PM, FREC_BL = 0.8, 0.1, 10
# beta = 1.0 y no 2.0 (ejemplo del enunciado): en tai20_5 con 5 semillas el RPD medio fue
# 3.19 % (beta=0), 2.90 % (beta=1), 3.35 % (beta=2) y 5.60 % (beta=5). La visibilidad SPT
# aporta poco al makespan, asi que conviene darle un peso moderado.
# alfa = 0.1: con alfa = 1.0 cada actualizacion borraria toda la feromona acumulada.
ALFA, BETA, Q0 = 0.1, 1.0, 0.9

ALGORITMOS = {
    "AG": lambda p, ub, inst, s: ejecutar_ag(p, ub, inst, s, TAMANO, ITERACIONES, PC, PM),
    "AM": lambda p, ub, inst, s: ejecutar_ag(p, ub, inst, s, TAMANO, ITERACIONES, PC, PM, FREC_BL),
    "ACS": lambda p, ub, inst, s: ejecutar_acs(p, ub, inst, s, TAMANO, ITERACIONES, ALFA, BETA, Q0),
}

CABECERA_RESUMEN = ["instancia", "algoritmo", "ub", "mejor_cmax", "media_cmax", "desv_cmax",
                    "media_rpd", "media_tiempo"]


def main():
    filas, resumen = [], []
    for instancia in INSTANCIAS:
        p, ub = op.leer_instancia(instancia)
        for algoritmo, ejecutar in ALGORITMOS.items():
            finales = []
            for semilla in SEMILLAS:
                _, cmax, filas_corrida = ejecutar(p, ub, instancia, semilla)
                filas += filas_corrida
                finales.append(filas_corrida[-1])
                print(f"{instancia:<20} {algoritmo:<4} semilla={semilla:<3} Cmax={cmax:<6} "
                      f"tiempo={filas_corrida[-1][7]:.1f} s", flush=True)
            cmaxs = [fila[5] for fila in finales]
            resumen.append([instancia, algoritmo, ub, min(cmaxs), round(mean(cmaxs), 1),
                            round(stdev(cmaxs), 1), round(mean(fila[6] for fila in finales), 2),
                            round(mean(fila[7] for fila in finales), 2)])

    op.guardar_csv("resultados/experimentos.csv", filas)
    with open("resultados/resumen.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(CABECERA_RESUMEN)
        escritor.writerows(resumen)

    print(f"\n{'instancia':<20} {'alg':<4} {'UB':>6} {'mejor':>6} {'media':>8} {'desv':>6} "
          f"{'RPD %':>6} {'tiempo s':>9}")
    for fila in resumen:
        print(f"{fila[0]:<20} {fila[1]:<4} {fila[2]:>6} {fila[3]:>6} {fila[4]:>8} {fila[5]:>6} "
              f"{fila[6]:>6} {fila[7]:>9}")
    print("\nResultados en resultados/experimentos.csv y resultados/resumen.csv")


if __name__ == "__main__":
    main()
