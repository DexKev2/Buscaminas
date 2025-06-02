import asyncio
import websockets
import logging
import os
import signal
from game_server import GameServer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BuscaminasApp:
    """
    Aplicación principal del servidor Buscaminas
    """
    
    def __init__(self):
        self.server = GameServer()
        self.host = os.getenv('HOST', 'localhost')
        self.port = int(os.getenv('PORT', 8765))
        self.running = False
        self.websocket_server = None
    
    async def start_server(self):
        """Inicia el servidor WebSocket"""
        try:
            logger.info(f"Iniciando servidor Buscaminas en {self.host}:{self.port}")
            
            # Para producción (Render), usar 0.0.0.0
            if os.getenv('RENDER'):
                self.host = '0.0.0.0'
                logger.info("Modo producción detectado, usando host 0.0.0.0")
            
            self.running = True
            
            # Crear el servidor WebSocket
            self.websocket_server = await websockets.serve(
                self.server.handle_client, 
                self.host, 
                self.port,
                ping_interval=30,  # Ping cada 30 segundos
                ping_timeout=10,   # Timeout de 10 segundos
                max_size=2**20,    # Máximo 1MB por mensaje
                max_queue=32       # Máximo 32 mensajes en cola
            )
            
            logger.info(f"Servidor corriendo en ws://{self.host}:{self.port}")
            logger.info("Presiona Ctrl+C para detener el servidor")
            
            # Mantener el servidor corriendo
            await self.keep_alive()
                
        except Exception as e:
            logger.error(f"Error iniciando servidor: {str(e)}")
            raise
    
    async def keep_alive(self):
        """Mantiene el servidor corriendo indefinidamente"""
        try:
            self._last_stats_time = asyncio.get_event_loop().time()
            
            while self.running:
                await asyncio.sleep(1)
                
                # Mostrar estadísticas cada 60 segundos
                if asyncio.get_event_loop().time() - self._last_stats_time > 60:
                    await self.show_stats()
                    
        except asyncio.CancelledError:
            logger.info("Servidor detenido por cancelación")
        except KeyboardInterrupt:
            logger.info("Servidor detenido por usuario")
        finally:
            self.running = False
    
    async def show_stats(self):
        """Muestra estadísticas del servidor"""
        stats = self.server.get_stats()
        logger.info(f"Estadísticas - Clientes: {stats['clientes_conectados']}, "
                   f"Juegos activos: {stats['juegos_activos']}")
        self._last_stats_time = asyncio.get_event_loop().time()
    
    def setup_signal_handlers(self):
        """Configura manejadores de señales para shutdown graceful"""
        def signal_handler(signum, frame):
            logger.info(f"Señal {signum} recibida, deteniendo servidor...")
            self.running = False
            # Crear una tarea para el shutdown asíncrono
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def shutdown(self):
        """Detiene el servidor de forma graceful"""
        logger.info("Iniciando shutdown del servidor...")
        self.running = False
        
        # Cerrar todas las conexiones activas
        for client_id, websocket in list(self.server.clientes.items()):
            try:
                await websocket.close()
                logger.info(f"Conexión cerrada para cliente: {client_id}")
            except Exception as e:
                logger.warning(f"Error cerrando conexión {client_id}: {str(e)}")
        
        # Cerrar el servidor WebSocket
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        
        logger.info("Servidor detenido correctamente")

async def main():
    """Función principal asíncrona"""
    app = BuscaminasApp()
    
    try:
        # Configurar manejadores de señales
        app.setup_signal_handlers()
        
        # Iniciar servidor
        await app.start_server()
        
    except KeyboardInterrupt:
        logger.info("Interrupción de teclado recibida")
    except Exception as e:
        logger.error(f"Error en main: {str(e)}")
    finally:
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n¡Servidor detenido!")
    except Exception as e:
        print(f"Error fatal: {e}")
        exit(1)