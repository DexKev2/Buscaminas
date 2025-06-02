import random
from typing import Dict, List, Tuple, Set

class Buscaminas:
    """
    Clase que maneja la lógica del juego Buscaminas
    """
    
    def __init__(self, filas: int, columnas: int, minas: int):
        """
        Inicializa un nuevo juego de Buscaminas
        
        Args:
            filas: Número de filas del tablero
            columnas: Número de columnas del tablero
            minas: Número de minas a colocar
        """
        self.filas = filas
        self.columnas = columnas
        self.minas = minas
        self.tablero = [[0 for _ in range(columnas)] for _ in range(filas)]
        self.tablero_visible = [['?' for _ in range(columnas)] for _ in range(filas)]
        self.posiciones_minas: Set[Tuple[int, int]] = set()
        self.juego_terminado = False
        self.victoria = False
        self.celdas_reveladas = 0
        self.celdas_totales = filas * columnas - minas
        
        self._generar_minas()
        self._calcular_numeros()
    
    def _generar_minas(self) -> None:
        """Genera las minas aleatoriamente en el tablero"""
        posiciones = [(i, j) for i in range(self.filas) for j in range(self.columnas)]
        self.posiciones_minas = set(random.sample(posiciones, self.minas))
        
        for fila, col in self.posiciones_minas:
            self.tablero[fila][col] = -1  # -1 representa una mina
    
    def _calcular_numeros(self) -> None:
        """Calcula los números alrededor de cada celda"""
        for fila in range(self.filas):
            for col in range(self.columnas):
                if self.tablero[fila][col] != -1:  # Si no es una mina
                    count = self._contar_minas_adyacentes(fila, col)
                    self.tablero[fila][col] = count
    
    def _contar_minas_adyacentes(self, fila: int, col: int) -> int:
        """
        Cuenta las minas adyacentes a una celda específica
        
        Args:
            fila: Fila de la celda
            col: Columna de la celda
            
        Returns:
            Número de minas adyacentes
        """
        count = 0
        for df in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if df == 0 and dc == 0:
                    continue
                nf, nc = fila + df, col + dc
                if (self._es_posicion_valida(nf, nc) and 
                    self.tablero[nf][nc] == -1):
                    count += 1
        return count
    
    def _es_posicion_valida(self, fila: int, col: int) -> bool:
        """
        Verifica si una posición está dentro del tablero
        
        Args:
            fila: Fila a verificar
            col: Columna a verificar
            
        Returns:
            True si la posición es válida
        """
        return 0 <= fila < self.filas and 0 <= col < self.columnas
    
    def _revelar_recursivo(self, fila: int, col: int, visitadas: Set[Tuple[int, int]]) -> None:
        """
        Revela celdas recursivamente cuando no hay minas alrededor
        
        Args:
            fila: Fila de la celda
            col: Columna de la celda
            visitadas: Set de celdas ya visitadas para evitar loops infinitos
        """
        if (fila, col) in visitadas:
            return
        
        if not self._es_posicion_valida(fila, col):
            return
        
        if self.tablero_visible[fila][col] != '?':
            return
        
        visitadas.add((fila, col))
        
        if self.tablero[fila][col] == -1:  # Es una mina
            return
        
        # Revelar la celda actual
        self.tablero_visible[fila][col] = str(self.tablero[fila][col])
        self.celdas_reveladas += 1
        
        # Si es 0, revelar celdas adyacentes recursivamente
        if self.tablero[fila][col] == 0:
            for df in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if df == 0 and dc == 0:
                        continue
                    nf, nc = fila + df, col + dc
                    self._revelar_recursivo(nf, nc, visitadas)
    
    def hacer_jugada(self, fila: int, col: int) -> Dict:
        """
        Procesa una jugada del jugador
        
        Args:
            fila: Fila de la celda clickeada
            col: Columna de la celda clickeada
            
        Returns:
            Diccionario con el resultado de la jugada
        """
        if self.juego_terminado:
            return {"error": "El juego ya terminó"}
        
        if not self._es_posicion_valida(fila, col):
            return {"error": "Posición inválida"}
        
        if self.tablero_visible[fila][col] != '?':
            return {"error": "Celda ya revelada"}
        
        # Si es una mina, el juego termina
        if self.tablero[fila][col] == -1:
            self._finalizar_juego_perdido()
            return {
                "juego_terminado": True,
                "victoria": False,
                "tablero": self.tablero_visible,
                "mensaje": "¡Boom! Pisaste una mina 💥"
            }
        
        # Revelar la celda y posiblemente las adyacentes
        visitadas = set()
        self._revelar_recursivo(fila, col, visitadas)
        
        # Verificar si el jugador ganó
        if self.celdas_reveladas >= self.celdas_totales:
            self.juego_terminado = True
            self.victoria = True
            return {
                "juego_terminado": True,
                "victoria": True,
                "tablero": self.tablero_visible,
                "mensaje": "¡Felicidades! Has ganado 🎉"
            }
        
        return {
            "juego_terminado": False,
            "tablero": self.tablero_visible,
            "celdas_reveladas": self.celdas_reveladas,
            "celdas_totales": self.celdas_totales
        }
    
    def _finalizar_juego_perdido(self) -> None:
        """Finaliza el juego cuando el jugador pierde, revelando todas las minas"""
        self.juego_terminado = True
        self.victoria = False
        # Revelar todas las minas
        for mf, mc in self.posiciones_minas:
            self.tablero_visible[mf][mc] = 'M'
    
    def resolver(self) -> Dict:
        """
        Muestra la solución completa del juego
        
        Returns:
            Diccionario con la solución del juego
        """
        solucion = [fila[:] for fila in self.tablero_visible]
        
        for fila in range(self.filas):
            for col in range(self.columnas):
                if self.tablero[fila][col] == -1:
                    solucion[fila][col] = 'M'  # Mina
                else:
                    solucion[fila][col] = str(self.tablero[fila][col])
        
        return {
            "solucion": solucion,
            "posiciones_minas": list(self.posiciones_minas),
            "tablero_completo": self.tablero
        }
    
    def obtener_estado(self) -> Dict:
        """
        Obtiene el estado actual del juego
        
        Returns:
            Diccionario con el estado del juego
        """
        return {
            "filas": self.filas,
            "columnas": self.columnas,
            "minas": self.minas,
            "tablero": self.tablero_visible,
            "juego_terminado": self.juego_terminado,
            "victoria": self.victoria,
            "celdas_reveladas": self.celdas_reveladas,
            "celdas_totales": self.celdas_totales
        }