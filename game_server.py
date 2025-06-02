import asyncio
import websockets
import json
import logging
from typing import Dict, Optional
from game_logic import Buscaminas

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GameServer:
    """
    Servidor WebSocket que maneja múltiples clientes jugando Buscaminas
    """
    
    def __init__(self):
        """Inicializa el servidor"""
        self.juegos: Dict[str, Buscaminas] = {}
        self.clientes: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.client_counter = 0
    
    async def handle_client(self, websocket, path=None):
        """
        Maneja la conexión de un cliente
        
        Args:
            websocket: Conexión WebSocket del cliente
            path: Ruta de la conexión (opcional)
        """
        self.client_counter += 1
        client_id = f"client_{self.client_counter}"
        self.clientes[client_id] = websocket
        
        logger.info(f"Cliente conectado: {client_id} desde {websocket.remote_address}")
        
        try:
            # Enviar mensaje de bienvenida
            await self.send_response(client_id, {
                "action": "conectado",
                "client_id": client_id,
                "mensaje": "Conexión establecida correctamente"
            })
            
            # Procesar mensajes del cliente
            async for message in websocket:
                try:
                    await self.process_message(client_id, message)
                except Exception as e:
                    logger.error(f"Error procesando mensaje de {client_id}: {str(e)}")
                    await self.send_error(client_id, f"Error procesando mensaje: {str(e)}")
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Cliente desconectado: {client_id}")
        except websockets.exceptions.ConnectionClosedError:
            logger.info(f"Conexión cerrada inesperadamente: {client_id}")
        except Exception as e:
            logger.error(f"Error con cliente {client_id}: {str(e)}")
        finally:
            await self.cleanup_client(client_id)
    
    async def cleanup_client(self, client_id: str):
        """
        Limpia los recursos del cliente desconectado
        
        Args:
            client_id: ID del cliente a limpiar
        """
        if client_id in self.clientes:
            del self.clientes[client_id]
        if client_id in self.juegos:
            del self.juegos[client_id]
        logger.info(f"Recursos limpiados para cliente: {client_id}")
    
    async def process_message(self, client_id: str, message: str):
        """
        Procesa los mensajes del cliente
        
        Args:
            client_id: ID del cliente que envió el mensaje
            message: Mensaje JSON recibido
        """
        try:
            data = json.loads(message)
            action = data.get("action")
            
            logger.info(f"Cliente {client_id} - Acción: {action}")
            
            if action == "nuevo_juego":
                await self.nuevo_juego(client_id, data)
            elif action == "hacer_jugada":
                await self.hacer_jugada(client_id, data)
            elif action == "resolver":
                await self.resolver(client_id)
            elif action == "obtener_estado":
                await self.obtener_estado(client_id)
            elif action == "ping":
                await self.send_response(client_id, {"action": "pong"})
            else:
                await self.send_error(client_id, f"Acción no válida: {action}")
        
        except json.JSONDecodeError as e:
            await self.send_error(client_id, f"Mensaje JSON inválido: {str(e)}")
        except Exception as e:
            logger.error(f"Error procesando mensaje de {client_id}: {str(e)}")
            await self.send_error(client_id, f"Error del servidor: {str(e)}")
    
    async def nuevo_juego(self, client_id: str, data: Dict):
        """
        Crea un nuevo juego para el cliente
        
        Args:
            client_id: ID del cliente
            data: Datos del juego (filas, columnas, minas)
        """
        try:
            filas = data.get("filas", 10)
            columnas = data.get("columnas", 10)
            minas = data.get("minas", 10)
            
            # Validaciones
            validation_error = self._validate_game_params(filas, columnas, minas)
            if validation_error:
                await self.send_error(client_id, validation_error)
                return
            
            # Crear nuevo juego
            self.juegos[client_id] = Buscaminas(filas, columnas, minas)
            
            response = {
                "action": "juego_creado",
                "filas": filas,
                "columnas": columnas,
                "minas": minas,
                "tablero": self.juegos[client_id].tablero_visible,
                "celdas_totales": self.juegos[client_id].celdas_totales
            }
            
            await self.send_response(client_id, response)
            logger.info(f"Juego creado para {client_id}: {filas}x{columnas} con {minas} minas")
        
        except Exception as e:
            logger.error(f"Error creando juego para {client_id}: {str(e)}")
            await self.send_error(client_id, f"Error creando juego: {str(e)}")
    
    def _validate_game_params(self, filas: int, columnas: int, minas: int) -> Optional[str]:
        """
        Valida los parámetros del juego
        
        Args:
            filas: Número de filas
            columnas: Número de columnas
            minas: Número de minas
            
        Returns:
            Mensaje de error si hay problemas, None si es válido
        """
        if not isinstance(filas, int) or filas < 5 or filas > 30:
            return "Las filas deben ser un número entre 5 y 30"
        
        if not isinstance(columnas, int) or columnas < 5 or columnas > 30:
            return "Las columnas deben ser un número entre 5 y 30"
        
        if not isinstance(minas, int) or minas < 1:
            return "Las minas deben ser al menos 1"
        
        max_minas = (filas * columnas) - 1
        if minas > max_minas:
            return f"Máximo {max_minas} minas para un tablero de {filas}x{columnas}"
        
        return None
    
    async def hacer_jugada(self, client_id: str, data: Dict):
        """
        Procesa una jugada del cliente
        
        Args:
            client_id: ID del cliente
            data: Datos de la jugada (fila, col)
        """
        if client_id not in self.juegos:
            await self.send_error(client_id, "No hay juego activo. Crea un nuevo juego primero")
            return
        
        try:
            fila = data.get("fila")
            col = data.get("col")
            
            if fila is None or col is None:
                await self.send_error(client_id, "Fila y columna son requeridas")
                return
            
            if not isinstance(fila, int) or not isinstance(col, int):
                await self.send_error(client_id, "Fila y columna deben ser números enteros")
                return
            
            resultado = self.juegos[client_id].hacer_jugada(fila, col)
            
            if "error" in resultado:
                await self.send_error(client_id, resultado["error"])
                return
            
            response = {
                "action": "resultado_jugada",
                **resultado
            }
            
            await self.send_response(client_id, response)
            
            # Log del resultado
            if resultado.get("juego_terminado"):
                if resultado.get("victoria"):
                    logger.info(f"Cliente {client_id} ganó el juego!")
                else:
                    logger.info(f"Cliente {client_id} perdió el juego")
        
        except Exception as e:
            logger.error(f"Error procesando jugada de {client_id}: {str(e)}")
            await self.send_error(client_id, f"Error procesando jugada: {str(e)}")
    
    async def resolver(self, client_id: str):
        """
        Envía la solución del juego al cliente
        
        Args:
            client_id: ID del cliente
        """
        if client_id not in self.juegos:
            await self.send_error(client_id, "No hay juego activo")
            return
        
        try:
            solucion = self.juegos[client_id].resolver()
            
            response = {
                "action": "solucion",
                **solucion
            }
            
            await self.send_response(client_id, response)
            logger.info(f"Solución enviada a cliente {client_id}")
        
        except Exception as e:
            logger.error(f"Error obteniendo solución para {client_id}: {str(e)}")
            await self.send_error(client_id, f"Error obteniendo solución: {str(e)}")
    
    async def obtener_estado(self, client_id: str):
        """
        Envía el estado actual del juego al cliente
        
        Args:
            client_id: ID del cliente
        """
        if client_id not in self.juegos:
            await self.send_error(client_id, "No hay juego activo")
            return
        
        try:
            estado = self.juegos[client_id].obtener_estado()
            
            response = {
                "action": "estado_juego",
                **estado
            }
            
            await self.send_response(client_id, response)
        
        except Exception as e:
            logger.error(f"Error obteniendo estado para {client_id}: {str(e)}")
            await self.send_error(client_id, f"Error obteniendo estado: {str(e)}")
    
    async def send_response(self, client_id: str, response: Dict):
        """
        Envía una respuesta al cliente
        
        Args:
            client_id: ID del cliente
            response: Respuesta a enviar
        """
        if client_id in self.clientes:
            try:
                await self.clientes[client_id].send(json.dumps(response))
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"No se pudo enviar mensaje a {client_id}: conexión cerrada")
                await self.cleanup_client(client_id)
            except websockets.exceptions.ConnectionClosedError:
                logger.warning(f"No se pudo enviar mensaje a {client_id}: conexión cerrada inesperadamente")
                await self.cleanup_client(client_id)
            except Exception as e:
                logger.error(f"Error enviando mensaje a {client_id}: {str(e)}")
    
    async def send_error(self, client_id: str, error_message: str):
        """
        Envía un mensaje de error al cliente
        
        Args:
            client_id: ID del cliente
            error_message: Mensaje de error
        """
        response = {
            "action": "error",
            "message": error_message
        }
        await self.send_response(client_id, response)
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas del servidor
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            "clientes_conectados": len(self.clientes),
            "juegos_activos": len(self.juegos),
            "clientes": list(self.clientes.keys())
        }