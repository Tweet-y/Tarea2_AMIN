"""Pruebas de los operadores PFSP. Ejecutar con: python tests.py."""

import tempfile
from random import Random

import numpy as np

import acs
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


P_CHICA = np.array([[3, 2], [1, 4], [2, 1]])  # Totales 5, 5, 3.


def test_visibilidad_spt():
    assert np.allclose(op.visibilidad_spt(P_CHICA), [1 / 5, 1 / 5, 1 / 3])


def test_inicializar_feromonas():
    tau, tau0 = op.inicializar_feromonas(P_CHICA)
    # SPT = [2, 0, 1]. M1: 2, 5, 6.  M2: 3, max(3,5)+2=7, max(7,6)+4=11.
    assert op.makespan([2, 0, 1], P_CHICA) == 11
    assert np.isclose(tau0, 1 / (3 * 11))
    assert tau.shape == (3, 3) and np.allclose(tau, tau0)


def test_siguiente_trabajo_explotacion():
    tau = np.ones((4, 4))
    eta = np.ones(4)
    tau[0, 1], eta[1] = 4, 0.5
    tau[0, 3] = 1000  # Trabajo ya programado: no es candidato.
    # beta=1: pesos 2 (trabajo 1) y 1 (trabajo 2). beta=3: pesos 0.5 y 1.
    assert op.siguiente_trabajo(0, [1, 2], tau, eta, 1, 1, Random(0)) == 1
    assert op.siguiente_trabajo(0, [1, 2], tau, eta, 3, 1, Random(0)) == 2
    assert op.siguiente_trabajo(0, [2], tau, eta, 2, 0, Random(0)) == 2


def test_siguiente_trabajo_exploracion():
    tau = np.ones((3, 3))
    tau[0, 2] = 3
    rng = Random(0)
    # Pesos 1 y 3: la ruleta debe elegir el trabajo 2 cerca del 75 % de las veces.
    elegidos = [op.siguiente_trabajo(0, [1, 2], tau, np.ones(3), 2, 0, rng) for _ in range(4000)]
    assert set(elegidos) == {1, 2}
    assert abs(elegidos.count(2) / 4000 - 0.75) < 0.03


def test_actualizar_local():
    tau = np.full((3, 3), 2.0)
    op.actualizar_local(tau, 0, 1, alfa=0.25, tau0=0.5)
    assert tau[0, 1] == 0.75 * 2 + 0.25 * 0.5  # 1.625
    assert tau[1, 0] == 2  # Dirigida: 1 tras 0 no es lo mismo que 0 tras 1.
    assert (tau == 2).sum() == 8


def test_actualizar_global():
    tau = np.full((4, 4), 2.0)
    op.actualizar_global(tau, [2, 0, 3, 1], cmax=10, alfa=0.25)
    reforzadas = [(2, 0), (0, 3), (3, 1)]
    for i, j in reforzadas:
        assert np.isclose(tau[i, j], 0.75 * 2 + 0.25 / 10)  # 1.525
    assert tau[1, 2] == 2  # Sin arista de cierre: la secuencia no es un ciclo.
    assert (tau == 2).sum() == 16 - len(reforzadas)


def test_construir_secuencia():
    p, _ = op.leer_instancia("datos/tai20_5.txt")
    eta = op.visibilidad_spt(p)
    tau, tau0 = op.inicializar_feromonas(p)
    tau *= 2  # Asi la actualizacion local se nota: cada arista recorrida baja hacia tau0.
    secuencia = op.construir_secuencia(tau, eta, 2, 0.9, 0.1, tau0, Random(1))
    assert sorted(secuencia) == list(range(20))
    recorridas = list(zip(secuencia, secuencia[1:]))
    for i, j in recorridas:
        assert np.isclose(tau[i, j], 0.9 * 2 * tau0 + 0.1 * tau0)
    assert np.isclose(tau, 2 * tau0).sum() == 400 - len(recorridas)


def test_acs_reproducible_y_monotono():
    p, ub = op.leer_instancia("datos/tai20_5.txt")
    corrida1 = acs.ejecutar_acs(p, ub, "tai20_5", 7, 5, 15, 0.1, 2, 0.9)
    corrida2 = acs.ejecutar_acs(p, ub, "tai20_5", 7, 5, 15, 0.1, 2, 0.9)
    sec, cmax, filas = corrida1
    assert sec == corrida2[0] and cmax == corrida2[1]
    assert sorted(sec) == list(range(20)) and op.makespan(sec, p) == cmax
    historial = [fila[5] for fila in filas]
    assert len(filas) == 15 and historial[-1] == cmax
    assert all(a >= b for a, b in zip(historial, historial[1:]))  # Nunca empeora.


if __name__ == "__main__":
    pruebas = [f for nombre, f in list(globals().items()) if nombre.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"Todas las pruebas pasaron correctamente ({len(pruebas)}/{len(pruebas)}).")
