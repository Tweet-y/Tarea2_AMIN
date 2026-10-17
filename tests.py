"""Pruebas de los operadores PFSP. Ejecutar con: python tests.py."""

import tempfile

import numpy as np

import operadores as op


def test_leer_instancia():
    for nombre, n, m, ub in [("tai20_5", 20, 5, 1278), ("tai50_10", 50, 10, 3025),
                             ("tai100_10", 100, 10, 5770)]:
        p, cota = op.leer_instancia(f"datos/{nombre}.txt")
        assert p.shape == (n, m)
        assert cota == ub

    # Filas del archivo = maquinas; filas de p = trabajos.
    p, _ = op.leer_instancia("datos/tai20_5.txt")
    assert p[0, 0] == 54 and p[1, 0] == 83 and p[0, 1] == 79


def test_leer_instancia_invalida():
    with tempfile.NamedTemporaryFile("w", suffix=".txt") as f:
        f.write("3 2 0 10 5\n1 2 3\n")  # Falta la fila de la segunda maquina.
        f.flush()
        try:
            op.leer_instancia(f.name)
        except ValueError:
            return
    raise AssertionError("una instancia incompleta debe lanzar ValueError")


def test_makespan_a_mano():
    p = np.array([[3, 2], [1, 4], [2, 1]])  # 3 trabajos x 2 maquinas.
    # M1: 3, 4, 6.  M2: 3+2=5, max(5,4)+4=9, max(9,6)+1=10.
    assert op.makespan([0, 1, 2], p) == 10
    # M1: 1, 4, 6.  M2: 1+4=5, max(5,4)+2=7, max(7,6)+1=8.
    assert op.makespan([1, 0, 2], p) == 8
    assert op.makespan([2], p) == 3


def test_makespan_taillard():
    p, _ = op.leer_instancia("datos/tai20_5.txt")
    # Secuencia y Cmax obtenidos con la implementacion independiente de la Tarea 1.
    secuencia = [2, 16, 8, 7, 14, 13, 10, 15, 12, 18, 5, 3, 4, 17, 0, 1, 9, 6, 19, 11]
    assert op.makespan(secuencia, p) == 1286

    # Cotas triviales: ninguna maquina ni trabajo termina antes de su carga total.
    cmax = op.makespan(list(range(20)), p)
    assert cmax >= p.sum(axis=0).max()
    assert cmax >= p.sum(axis=1).max()


def test_rpd():
    assert op.rpd(1278, 1278) == 0
    assert np.isclose(op.rpd(1286, 1278), 0.62597809)


if __name__ == "__main__":
    pruebas = [f for nombre, f in list(globals().items()) if nombre.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"Todas las pruebas pasaron correctamente ({len(pruebas)}/{len(pruebas)}).")
