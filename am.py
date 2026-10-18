"""Algoritmo Memetico (AM) para PFSP: el AG de ag.py mas busqueda local por insercion
sobre el mejor individuo cada frec_bl iteraciones.

Uso: python am.py instancia semilla poblacion iteraciones pc pm frec_bl salida.csv
"""

from ag import main

if __name__ == "__main__":
    main(memetico=True)
