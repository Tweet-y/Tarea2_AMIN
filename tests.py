"""Pruebas sencillas de operadores TSP y ACS. Ejecutar con: python tests.py."""

from random import Random

import numpy as np

import operadores as op


def test_leer_instancia():
    coords = op.leer_instancia("datos/berlin52.tsp")
    assert len(coords) == 52
    assert coords[0] == (565.0, 575.0)
    assert coords[51] == (480.0, 1705.0)


def test_matriz_distancias():
    coords = op.leer_instancia("datos/berlin52.tsp")
    D = op.matriz_distancias(coords)
    assert isinstance(D, np.ndarray)
    assert D.shape == (52, 52)
    assert np.all(np.diag(D) == 0)
    assert np.array_equal(D, D.T)
    assert D[0, 1] == 666

    # TSPLIB redondea 2.5 hacia 3, no hacia el entero par 2.
    pequena = op.matriz_distancias([(0, 0), (2.5, 0)])
    assert pequena[0, 1] == pequena[1, 0] == 3


def test_matriz_visibilidad():
    coords = op.leer_instancia("datos/berlin52.tsp")
    D = op.matriz_distancias(coords)
    eta = op.matriz_visibilidad(D)
    assert eta.shape == D.shape
    assert np.allclose(eta[D > 0], 1.0 / D[D > 0])
    assert np.all(np.diag(eta) == 0)
    assert np.isfinite(eta).all()

    # Ciudades distintas con las mismas coordenadas: transicion favorable.
    assert coords[7] == coords[49]
    assert D[7, 49] == 0
    assert eta[7, 49] == eta[49, 7] == 1.0


def test_evaluar_ruta():
    D = np.array([[0, 3, 4], [3, 0, 5], [4, 5, 0]])
    assert op.evaluar_ruta([0, 1, 2], D) == 12  # 3 + 5 + 4 (regreso).
    assert op.evaluar_ruta([0, 1], D) == 6  # 3 de ida + 3 de regreso.


def test_heuristica_vecino_mas_cercano():
    coords = op.leer_instancia("datos/berlin52.tsp")
    D = op.matriz_distancias(coords)
    ruta, costo = op.heuristica_vecino_mas_cercano(D)
    assert ruta[0] == 0
    assert len(ruta) == len(set(ruta)) == 52
    assert set(ruta) == set(range(52))
    assert np.isclose(costo, op.evaluar_ruta(ruta, D))

    pequena = np.array([[0, 3, 4], [3, 0, 5], [4, 5, 0]])
    ruta, costo = op.heuristica_vecino_mas_cercano(pequena)
    assert ruta == [0, 1, 2]
    assert costo == 12


def test_inicializar_feromonas():
    D = np.array([[0, 3, 4], [3, 0, 5], [4, 5, 0]])
    _, L_nn = op.heuristica_vecino_mas_cercano(D)
    tau = op.inicializar_feromonas(len(D), L_nn)
    assert isinstance(tau, np.ndarray)
    assert tau.shape == (3, 3)
    assert np.allclose(tau, 1.0 / 36)  # 1 / (3 * 12).


def test_siguiente_ciudad_explotacion():
    tau = np.ones((4, 4))
    eta = np.ones((4, 4))
    tau[0, 1] = 4
    eta[0, 1] = 0.5
    tau[0, 3] = 1000  # Ciudad visitada, excluida de las candidatas.
    candidatas = {1, 2}

    # beta=1: pesos 2 y 1. beta=3: pesos 0.5 y 1.
    for beta, esperada in [(1, 1), (3, 2)]:
        ciudad = op.siguiente_ciudad(0, candidatas, tau, eta, beta, 1, Random(42))
        assert ciudad in candidatas
        assert ciudad == esperada
    assert op.siguiente_ciudad(0, {2}, tau, eta, 2, 1, Random(42)) == 2


def test_siguiente_ciudad_exploracion():
    tau = np.ones((4, 4))
    eta = np.ones((4, 4))
    tau[0, 2] = 3
    tau[0, 3] = 1000
    candidatas = {1, 2}

    # Pesos 1 y 3: probabilidades 1/4 y 3/4. El segundo sorteo
    # de Random(42) cae bajo 1/4; el de Random(1), sobre 1/4.
    for semilla, esperada in [(42, 1), (1, 2)]:
        ciudad = op.siguiente_ciudad(0, candidatas, tau, eta, 2, 0, Random(semilla))
        assert ciudad in candidatas
        assert ciudad == esperada


def test_siguiente_ciudad_reproducible():
    tau = np.ones((4, 4))
    eta = np.ones((4, 4))
    tau[0, 2] = 3
    for crear_rng in (Random, np.random.default_rng):
        rng1, rng2 = crear_rng(42), crear_rng(42)
        # El orden de entrada tampoco debe cambiar la secuencia.
        secuencia1 = [op.siguiente_ciudad(0, [2, 1], tau, eta, 2, 0.5, rng1)
                      for _ in range(20)]
        secuencia2 = [op.siguiente_ciudad(0, [1, 2], tau, eta, 2, 0.5, rng2)
                      for _ in range(20)]
        assert secuencia1 == secuencia2
        assert set(secuencia1) <= {1, 2}


def test_actualizar_local():
    tau = np.full((3, 3), 2.0)
    op.actualizar_local(tau, 0, 1, rho=0.25, tau0=0.5)
    # (1 - 0.25) * 2 + 0.25 * 0.5 = 1.625.
    esperada = np.array([[2, 1.625, 2], [1.625, 2, 2], [2, 2, 2]])
    assert np.allclose(tau, esperada)
    assert np.array_equal(tau, tau.T)


def test_actualizar_global():
    tau = np.full((4, 4), 2.0)
    op.actualizar_global(tau, [0, 1, 2, 3], mejor_costo=10, alfa=0.25)
    # (1 - 0.25) * 2 + 0.25 * (1 / 10) = 1.525.
    esperada = np.array([
        [2, 1.525, 2, 1.525],
        [1.525, 2, 1.525, 2],
        [2, 1.525, 2, 1.525],
        [1.525, 2, 1.525, 2],
    ])
    assert np.allclose(tau, esperada)
    assert np.isclose(tau[3, 0], 1.525)  # Arista de regreso.
    assert tau[0, 2] == tau[1, 3] == 2  # Aristas ajenas a la ruta.
    assert np.array_equal(tau, tau.T)


if __name__ == "__main__":
    pruebas = [
        test_leer_instancia,
        test_matriz_distancias,
        test_matriz_visibilidad,
        test_evaluar_ruta,
        test_heuristica_vecino_mas_cercano,
        test_inicializar_feromonas,
        test_siguiente_ciudad_explotacion,
        test_siguiente_ciudad_exploracion,
        test_siguiente_ciudad_reproducible,
        test_actualizar_local,
        test_actualizar_global,
    ]
    for prueba in pruebas:
        prueba()
    print(f"Todas las pruebas pasaron correctamente ({len(pruebas)}/{len(pruebas)}).")
