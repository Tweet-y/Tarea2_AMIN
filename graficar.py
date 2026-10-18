"""Curvas de convergencia: media del mejor Cmax por iteracion de AG, AM y ACS.

Uso: python graficar.py resultados/experimentos.csv
Genera graficos/convergencia_<instancia>.png, una figura por instancia.
"""

import argparse
import csv
import os
from collections import defaultdict
from statistics import mean

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import operadores as op

# Paleta categorica validada (azul, naranja, aqua). El estilo de linea tambien distingue
# cada algoritmo, para que la figura se lea en escala de grises o con daltonismo.
ESTILOS = {"AG": ("#2a78d6", "-"), "AM": ("#eb6834", "--"), "ACS": ("#1baf7a", ":")}
TINTA, TINTA_SUAVE, GRILLA = "#1f1f1e", "#5c5b55", "#e4e3de"


def leer_curvas(ruta):
    """curvas[instancia][algoritmo][iteracion] = lista de mejor Cmax, uno por semilla."""
    curvas = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    with open(ruta, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            curvas[fila["instancia"]][fila["algoritmo"]][int(fila["iteracion"])].append(
                int(fila["mejor_cmax"]))
    return curvas


def graficar_instancia(instancia, por_algoritmo, ub, salida):
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for algoritmo, (color, estilo) in ESTILOS.items():
        if algoritmo in por_algoritmo:
            iteraciones = sorted(por_algoritmo[algoritmo])
            ax.plot(iteraciones, [mean(por_algoritmo[algoritmo][i]) for i in iteraciones],
                    color=color, linestyle=estilo, linewidth=2, label=algoritmo)
    ax.axhline(ub, color=TINTA_SUAVE, linewidth=1, label=f"UB = {ub}")

    semillas = len(next(iter(next(iter(por_algoritmo.values())).values())))
    nombre = os.path.splitext(os.path.basename(instancia))[0]
    ax.set_title(f"Convergencia en {nombre} (media de {semillas} semillas)", color=TINTA)
    ax.set_xlabel("Iteración", color=TINTA_SUAVE)
    ax.set_ylabel("Mejor Cmax", color=TINTA_SUAVE)
    ax.tick_params(colors=TINTA_SUAVE)
    ax.grid(axis="y", color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(GRILLA)
    ax.legend(frameon=False, labelcolor=TINTA)
    fig.tight_layout()
    fig.savefig(salida, dpi=200)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Curvas de convergencia de AG, AM y ACS")
    parser.add_argument("resultados", metavar="experimentos.csv")
    args = parser.parse_args()
    try:
        curvas = leer_curvas(args.resultados)
        if not curvas:
            parser.error(f"'{args.resultados}' no tiene filas de resultados")
        os.makedirs("graficos", exist_ok=True)
        for instancia, por_algoritmo in curvas.items():
            _, ub = op.leer_instancia(instancia)
            nombre = os.path.splitext(os.path.basename(instancia))[0]
            salida = os.path.join("graficos", f"convergencia_{nombre}.png")
            graficar_instancia(instancia, por_algoritmo, ub, salida)
            print(f"Grafico guardado en {salida}")
    except (OSError, KeyError, ValueError) as error:
        parser.error(f"no se pudo graficar: {error}")


if __name__ == "__main__":
    main()
