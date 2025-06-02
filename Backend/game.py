
import random

class Buscaminas:
    def __init__(self, filas, columnas, minas):
        self.filas = filas
        self.columnas = columnas
        self.minas = minas
        self.tablero = [[0 for _ in range(columnas)] for _ in range(filas)]
        self.revelado = [[False for _ in range(columnas)] for _ in range(filas)]
        self.generar_tablero()

    def generar_tablero(self):
        minas_colocadas = 0
        while minas_colocadas < self.minas:
            f = random.randint(0, self.filas - 1)
            c = random.randint(0, self.columnas - 1)
            if self.tablero[f][c] != -1:
                self.tablero[f][c] = -1
                self.incrementar_alrededor(f, c)
                minas_colocadas += 1

    def incrementar_alrededor(self, fila, columna):
        for i in range(fila - 1, fila + 2):
            for j in range(columna - 1, columna + 2):
                if 0 <= i < self.filas and 0 <= j < self.columnas and self.tablero[i][j] != -1:
                    self.tablero[i][j] += 1

    def revelar(self, fila, columna):
        if self.revelado[fila][columna]:
            return []
        self.revelado[fila][columna] = True
        if self.tablero[fila][columna] == 0:
            celdas = [(fila, columna)]
            for i in range(fila - 1, fila + 2):
                for j in range(columna - 1, columna + 2):
                    if 0 <= i < self.filas and 0 <= j < self.columnas:
                        celdas.extend(self.revelar(i, j))
            return celdas
        return [(fila, columna)]

    def resolver(self):
        return [(i, j) for i in range(self.filas) for j in range(self.columnas) if self.tablero[i][j] == -1]

