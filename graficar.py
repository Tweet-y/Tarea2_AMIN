"""Genera los graficos de convergencia y mejor ruta a partir del CSV de ACS."""

import argparse
import csv
from pathlib import Path
from tempfile import TemporaryDirectory

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from acs import ejecutar_acs
from operadores import evaluar_ruta, leer_instancia, matriz_distancias


def generar_graficos(ruta_csv):
    """Lee los resultados, reconstruye la ruta y guarda ambos graficos."""
    with open(ruta_csv, newline="", encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    if not filas:
        raise ValueError("El CSV no contiene resultados.")

    parametros = filas[0]
    iteraciones = [int(fila["iteracion"]) for fila in filas]
    costos = [float(fila["mejor_costo"]) for fila in filas]
    total_iteraciones = int(parametros["iteraciones"])
    if iteraciones != list(range(1, total_iteraciones + 1)):
        raise ValueError("El CSV debe contener un registro por iteracion, en orden.")
    if not np.isfinite(costos).all() or np.any(np.diff(costos) > 0):
        raise ValueError("Los costos del CSV deben ser finitos y no aumentar.")

    with TemporaryDirectory() as temporal:
        ruta, costo, _ = ejecutar_acs(
            parametros["instancia"],
            int(parametros["hormigas"]),
            total_iteraciones,
            float(parametros["alfa"]),
            float(parametros["beta"]),
            float(parametros["q0"]),
            int(parametros["semilla"]),
            Path(temporal) / "reconstruccion.csv",
        )

    coords = np.asarray(leer_instancia(parametros["instancia"]))
    if len(ruta) != len(coords) or set(ruta) != set(range(len(coords))):
        raise ValueError("La ruta reconstruida no visita cada ciudad exactamente una vez.")
    costo_evaluado = evaluar_ruta(ruta, matriz_distancias(coords))
    # Los costos TSPLIB son enteros, aunque las matrices los almacenen como float.
    if costo != costos[-1] or costo_evaluado != costo:
        raise ValueError(
            f"El costo reconstruido ({costo:g}) o evaluado ({costo_evaluado:g}) "
            f"no coincide con el costo final del CSV ({costos[-1]:g})."
        )

    salida = Path("graficos")
    salida.mkdir(exist_ok=True)
    convergencia = salida / "convergencia_berlin52.png"
    mejor_ruta = salida / "ruta_berlin52.png"
    nombre = Path(parametros["instancia"]).stem

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(iteraciones, costos, color="tab:blue", linewidth=1.8)
    ax.set_title(f"Convergencia de ACS - {nombre}")
    ax.set_xlabel("Iteración")
    ax.set_ylabel("Mejor costo global")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(convergencia, dpi=160)
    plt.close(fig)

    recorrido = coords[ruta + [ruta[0]]]
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.plot(recorrido[:, 0], recorrido[:, 1], color="tab:blue", linewidth=1.2)
    ax.scatter(coords[:, 0], coords[:, 1], color="0.2", s=22, zorder=3)
    ax.scatter(
        coords[ruta[0], 0], coords[ruta[0], 1], marker="*", s=180,
        color="tab:orange", edgecolors="black", linewidths=0.6, zorder=4,
        label=f"Inicio (índice {ruta[0]})",
    )
    ax.set_title(f"Mejor ruta ACS - {nombre} | costo: {costo:g}")
    ax.set_xlabel("Coordenada X")
    ax.set_ylabel("Coordenada Y")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(mejor_ruta, dpi=160)
    plt.close(fig)

    print(f"Convergencia: {convergencia}")
    print(f"Mejor ruta: {mejor_ruta}")
    print(f"Costo de la mejor solución: {costo:g}")


def main():
    parser = argparse.ArgumentParser(description="Graficos de resultados ACS para TSP")
    parser.add_argument("resultados_csv")
    args = parser.parse_args()
    try:
        generar_graficos(args.resultados_csv)
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
