"""Pruebas de los operadores PFSP. Ejecutar con: python tests.py."""

import tempfile
from random import Random

import numpy as np

import acs
import ag
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


def test_poblacion_inicial():
    poblacion = op.poblacion_inicial(30, 8, Random(0))
    assert len(poblacion) == 30
    assert all(sorted(s) == list(range(8)) for s in poblacion)
    assert len({tuple(s) for s in poblacion}) > 1


def test_torneo():
    poblacion, cmax = [[0], [1], [2]], [30, 10, 20]
    rng = Random(0)
    ganadores = [op.torneo(poblacion, cmax, rng)[0] for _ in range(3000)]
    # k=3 con reposicion: P(mejor) = 1 - (2/3)^3 = 0.704; P(peor) = (1/3)^3 = 0.037.
    assert abs(ganadores.count(1) / 3000 - 0.704) < 0.03
    assert abs(ganadores.count(0) / 3000 - 0.037) < 0.015


def test_cruce_ox():
    padre1, padre2 = [0, 1, 2, 3, 4, 5, 6, 7], [7, 5, 3, 1, 6, 4, 2, 0]
    rng = Random(0)
    for _ in range(200):
        hijo = op.cruce_ox(padre1, padre2, rng)
        assert sorted(hijo) == list(range(8))
        # Debe existir un tramo copiado de padre1 en su lugar; el resto sigue el orden de padre2.
        assert any(hijo[a:b] == padre1[a:b]
                   and hijo[:a] + hijo[b:] == [t for t in padre2 if t not in padre1[a:b]]
                   for a in range(8) for b in range(a + 1, 9))
    assert op.cruce_ox(padre1, padre1, rng) == padre1


def test_mutacion_insercion():
    original = list(range(10))
    rng = Random(0)
    for _ in range(200):
        mutada = op.mutacion_insercion(original, rng)
        assert sorted(mutada) == original and mutada != original
        # Quitar el trabajo movido deja el resto en el mismo orden.
        assert any([t for t in mutada if t != x] == [t for t in original if t != x]
                   for x in original)
    assert original == list(range(10))  # No modifica la entrada.


def test_ag_reproducible_y_elitista():
    p, ub = op.leer_instancia("datos/tai20_5.txt")
    sec, cmax, filas = ag.ejecutar_ag(p, ub, "tai20_5", 7, 20, 30, 0.8, 0.1)
    sec2, cmax2, _ = ag.ejecutar_ag(p, ub, "tai20_5", 7, 20, 30, 0.8, 0.1)
    assert sec == sec2 and cmax == cmax2
    assert sorted(sec) == list(range(20)) and op.makespan(sec, p) == cmax
    historial = [fila[5] for fila in filas]
    assert len(filas) == 30 and historial[-1] == cmax
    assert all(a >= b for a, b in zip(historial, historial[1:]))  # Elitismo: nunca empeora.


if __name__ == "__main__":
    pruebas = [f for nombre, f in list(globals().items()) if nombre.startswith("test_")]
    for prueba in pruebas:
        prueba()
    print(f"Todas las pruebas pasaron correctamente ({len(pruebas)}/{len(pruebas)}).")
