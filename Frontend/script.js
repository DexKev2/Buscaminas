class BuscaminasClient {
    constructor() {
        this.ws = null;
        this.gameData = null;
        this.clientId = null;
        this.isConnected = false;
        
        // Elementos del DOM
        this.elements = {
            // Conexión
            connectionStatus: document.getElementById('connectionStatus'),
            statusIndicator: document.getElementById('statusIndicator'),
            statusText: document.getElementById('statusText'),
            
            // Configuración
            configPanel: document.getElementById('configPanel'),
            filasInput: document.getElementById('filas'),
            columnasInput: document.getElementById('columnas'),
            minasInput: document.getElementById('minas'),
            nuevoJuegoBtn: document.getElementById('nuevoJuegoBtn'),
            
            // Información del juego
            gameInfo: document.getElementById('gameInfo'),
            minasTotal: document.getElementById('minasTotal'),
            celdasReveladas: document.getElementById('celdasReveladas'),
            celdasTotales: document.getElementById('celdasTotales'),
            estadoJuego: document.getElementById('estadoJuego'),
            
            // Controles
            gameControls: document.getElementById('gameControls'),
            resolverBtn: document.getElementById('resolverBtn'),
            reiniciarBtn: document.getElementById('reiniciarBtn'),
            
            // Tablero y mensajes
            gameBoard: document.getElementById('gameBoard'),
            messageContainer: document.getElementById('messageContainer'),
            
            // Modal
            resultModal: document.getElementById('resultModal'),
            modalTitle: document.getElementById('modalTitle'),
            modalMessage: document.getElementById('modalMessage'),
            modalNewGame: document.getElementById('modalNewGame'),
            modalClose: document.getElementById('modalClose'),
            closeModal: document.getElementById('closeModal')
        };
        
        this.initializeEventListeners();
        this.connect();
    }
    
    initializeEventListeners() {
        // Botones principales
        this.elements.nuevoJuegoBtn.addEventListener('click', () => this.crearNuevoJuego());
        this.elements.resolverBtn.addEventListener('click', () => this.resolverJuego());
        this.elements.reiniciarBtn.addEventListener('click', () => this.reiniciarJuego());
        
        // Modal
        this.elements.modalNewGame.addEventListener('click', () => {
            this.closeModal();
            this.crearNuevoJuego();
        });
        this.elements.modalClose.addEventListener('click', () => this.closeModal());
        this.elements.closeModal.addEventListener('click', () => this.closeModal());
        
        // Cerrar modal al hacer clic fuera
        this.elements.resultModal.addEventListener('click', (e) => {
            if (e.target === this.elements.resultModal) {
                this.closeModal();
            }
        });
        
        // Validación de inputs
        this.elements.minasInput.addEventListener('input', () => this.validateMinas());
        this.elements.filasInput.addEventListener('input', () => this.validateMinas());
        this.elements.columnasInput.addEventListener('input', () => this.validateMinas());
    }
    
    validateMinas() {
        const filas = parseInt(this.elements.filasInput.value);
        const columnas = parseInt(this.elements.columnasInput.value);
        const maxMinas = (filas * columnas) - 1;
        
        if (this.elements.minasInput.value > maxMinas) {
            this.elements.minasInput.value = maxMinas;
        }
        
        this.elements.minasInput.max = maxMinas;
    }
    
    connect() {
        try {
            // Determinar la URL del WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const host = window.location.hostname;
            const port = window.location.port || (protocol === 'wss:' ? '443' : '80');
            
            // Para desarrollo local
            let wsUrl = `${protocol}//${host}:8765`;
            
            // Para producción en Render
            if (host.includes('render.com') || host.includes('onrender.com')) {
                wsUrl = `wss://${host}`;
            }
            
            this.showMessage(`Conectando a ${wsUrl}...`, 'info');
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.isConnected = true;
                this.updateConnectionStatus('Conectado', true);
                this.showMessage('Conexión establecida correctamente', 'success');
                this.elements.nuevoJuegoBtn.disabled = false;
            };
            
            this.ws.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };
            
            this.ws.onclose = () => {
                this.isConnected = false;
                this.updateConnectionStatus('Desconectado', false);
                this.showMessage('Conexión cerrada. Intentando reconectar...', 'error');
                this.elements.nuevoJuegoBtn.disabled = true;
                
                // Intentar reconectar después de 3 segundos
                setTimeout(() => {
                    if (!this.isConnected) {
                        this.connect();
                    }
                }, 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('Error WebSocket:', error);
                this.showMessage('Error de conexión. Verificando...', 'error');
            };
            
        } catch (error) {
            console.error('Error conectando:', error);
            this.showMessage('Error al conectar: ' + error.message, 'error');
        }
    }
    
    handleMessage(data) {
        console.log('Mensaje recibido:', data);
        
        switch (data.action) {
            case 'conectado':
                this.clientId = data.client_id;
                this.showMessage(data.mensaje, 'success');
                break;
                
            case 'juego_creado':
                this.gameData = data;
                this.mostrarJuego();
                this.crearTablero();
                this.showMessage('¡Nuevo juego creado! Haz clic en las celdas para revelarlas.', 'success');
                break;
                
            case 'resultado_jugada':
                this.actualizarJuego(data);
                if (data.juego_terminado) {
                    this.mostrarResultado(data);
                }
                break;
                
            case 'solucion':
                this.mostrarSolucion(data);
                break;
                
            case 'estado_juego':
                this.actualizarEstado(data);
                break;
                
            case 'error':
                this.showMessage('Error: ' + data.message, 'error');
                break;
                
            default:
                console.log('Acción no reconocida:', data.action);
        }
    }
    
    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            this.showMessage('No hay conexión con el servidor', 'error');
        }
    }
    
    crearNuevoJuego() {
        const filas = parseInt(this.elements.filasInput.value);
        const columnas = parseInt(this.elements.columnasInput.value);
        const minas = parseInt(this.elements.minasInput.value);
        
        if (filas < 5 || filas > 30 || columnas < 5 || columnas > 30 || minas < 1) {
            this.showMessage('Parámetros inválidos. Verifica los valores.', 'error');
            return;
        }
        
        if (minas >= filas * columnas) {
            this.showMessage('Demasiadas minas para el tamaño del tablero.', 'error');
            return;
        }
        
        this.sendMessage({
            action: 'nuevo_juego',
            filas: filas,
            columnas: columnas,
            minas: minas
        });
    }
    
    hacerJugada(fila, col) {
        if (!this.gameData || this.gameData.juego_terminado) {
            return;
        }
        
        this.sendMessage({
            action: 'hacer_jugada',
            fila: fila,
            col: col
        });
    }
    
    resolverJuego() {
        this.sendMessage({
            action: 'resolver'
        });
    }
    
    reiniciarJuego() {
        this.crearNuevoJuego();
    }
    
    mostrarJuego() {
        // Ocultar panel de configuración en móviles
        if (window.innerWidth <= 768) {
            this.elements.configPanel.style.display = 'none';
        }
        
        // Mostrar información y controles del juego
        this.elements.gameInfo.style.display = 'flex';
        this.elements.gameControls.style.display = 'flex';
        
        // Actualizar información
        this.elements.minasTotal.textContent = this.gameData.minas;
        this.elements.celdasTotales.textContent = this.gameData.celdas_totales;
        this.elements.celdasReveladas.textContent = '0';
        this.elements.estadoJuego.textContent = 'Jugando';
        this.elements.estadoJuego.className = 'estado-jugando';
    }
    
    crearTablero() {
        const tablero = this.gameData.tablero;
        const filas = tablero.length;
        const columnas = tablero[0].length;
        
        // Configurar grid
        this.elements.gameBoard.style.gridTemplateColumns = `repeat(${columnas}, 1fr)`;
        this.elements.gameBoard.innerHTML = '';
        
        // Crear celdas
        for (let i = 0; i < filas; i++) {
            for (let j = 0; j < columnas; j++) {
                const celda = document.createElement('button');
                celda.className = 'cell hidden';
                celda.dataset.fila = i;
                celda.dataset.col = j;
                
                celda.addEventListener('click', () => {
                    this.hacerJugada(i, j);
                });
                
                this.elements.gameBoard.appendChild(celda);
            }
        }
    }
    
    actualizarJuego(data) {
        const tablero = data.tablero;
        const celdas = this.elements.gameBoard.querySelectorAll('.cell');
        
        // Actualizar información
        if (data.celdas_reveladas !== undefined) {
            this.elements.celdasReveladas.textContent = data.celdas_reveladas;
        }
        
        // Actualizar celdas
        celdas.forEach(celda => {
            const fila = parseInt(celda.dataset.fila);
            const col = parseInt(celda.dataset.col);
            const valor = tablero[fila][col];
            
            if (valor !== '?') {
                celda.classList.remove('hidden');
                celda.classList.add('revealed');
                
                if (valor === 'M') {
                    celda.classList.add('mine');
                    celda.textContent = '💣';
                } else if (valor === '0') {
                    celda.textContent = '';
                } else {
                    celda.textContent = valor;
                    celda.classList.add(`number-${valor}`);
                }
            }
        });
        
        // Actualizar estado del juego
        this.gameData = { ...this.gameData, ...data };
    }
    
    mostrarSolucion(data) {
        const solucion = data.solucion;
        const celdas = this.elements.gameBoard.querySelectorAll('.cell');
        
        celdas.forEach(celda => {
            const fila = parseInt(celda.dataset.fila);
            const col = parseInt(celda.dataset.col);
            const valor = solucion[fila][col];
            
            celda.classList.remove('hidden');
            celda.classList.add('revealed');
            
            if (valor === 'M') {
                celda.classList.add('mine');
                celda.textContent = '💣';
            } else if (valor === '0') {
                celda.textContent = '';
            } else {
                celda.textContent = valor;
                celda.classList.add(`number-${valor}`);
            }
        });
        
        // Actualizar estado
        this.elements.estadoJuego.textContent = 'Solución';
        this.elements.estadoJuego.className = 'estado-solucion';
        
        this.showMessage('Solución mostrada. Las minas están marcadas con 💣', 'info');
    }
    
    mostrarResultado(data) {
        // Actualizar estado visual
        if (data.victoria) {
            this.elements.estadoJuego.textContent = '¡Ganaste!';
            this.elements.estadoJuego.className = 'estado-ganado';
            this.elements.modalTitle.textContent = '🎉 ¡Felicidades!';
        } else {
            this.elements.estadoJuego.textContent = 'Perdiste';
            this.elements.estadoJuego.className = 'estado-perdido';
            this.elements.modalTitle.textContent = '💣 ¡Boom!';
        }
        
        // Mostrar modal con el resultado
        this.elements.modalMessage.textContent = data.mensaje;
        this.elements.resultModal.style.display = 'block';
        
        // Deshabilitar interacciones con el tablero
        const celdas = this.elements.gameBoard.querySelectorAll('.cell');
        celdas.forEach(celda => {
            celda.style.pointerEvents = 'none';
        });
    }
    
    actualizarEstado(data) {
        this.gameData = { ...this.gameData, ...data };
        
        // Actualizar información mostrada
        this.elements.celdasReveladas.textContent = data.celdas_reveladas || 0;
        this.elements.celdasTotales.textContent = data.celdas_totales || 0;
        
        if (data.juego_terminado) {
            if (data.victoria) {
                this.elements.estadoJuego.textContent = '¡Ganaste!';
                this.elements.estadoJuego.className = 'estado-ganado';
            } else {
                this.elements.estadoJuego.textContent = 'Perdiste';
                this.elements.estadoJuego.className = 'estado-perdido';
            }
        }
    }
    
    updateConnectionStatus(status, connected) {
        this.elements.statusText.textContent = status;
        if (connected) {
            this.elements.statusIndicator.classList.add('connected');
        } else {
            this.elements.statusIndicator.classList.remove('connected');
        }
    }
    
    showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        
        // Limpiar mensajes anteriores
        this.elements.messageContainer.innerHTML = '';
        this.elements.messageContainer.appendChild(messageDiv);
        
        // Auto-ocultar mensajes después de 5 segundos (excepto errores)
        if (type !== 'error') {
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.remove();
                }
            }, 5000);
        }
    }
    
    closeModal() {
        this.elements.resultModal.style.display = 'none';
        
        // Rehabilitar interacciones si el juego no ha terminado
        if (!this.gameData?.juego_terminado) {
            const celdas = this.elements.gameBoard.querySelectorAll('.cell');
            celdas.forEach(celda => {
                celda.style.pointerEvents = 'auto';
            });
        }
    }
    
    // Método para manejar cambios de tamaño de ventana
    handleResize() {
        if (window.innerWidth > 768 && this.elements.configPanel.style.display === 'none') {
            this.elements.configPanel.style.display = 'block';
        }
    }
}

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    const client = new BuscaminasClient();
    
    // Manejar cambios de tamaño de ventana
    window.addEventListener('resize', () => {
        client.handleResize();
    });
    
    // Manejar visibilidad de la página para reconexión
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden && !client.isConnected) {
            setTimeout(() => {
                if (!client.isConnected) {
                    client.connect();
                }
            }, 1000);
        }
    });
    
    // Prevenir el cierre accidental de la página durante un juego
    window.addEventListener('beforeunload', (e) => {
        if (client.gameData && !client.gameData.juego_terminado) {
            e.preventDefault();
            e.returnValue = '¿Estás seguro de que quieres salir? El juego actual se perderá.';
            return e.returnValue;
        }
    });
});

// Funciones de utilidad adicionales
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// Detectar dispositivos táctiles para mejorar la experiencia móvil
function isTouchDevice() {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
}

// Configurar eventos específicos para dispositivos táctiles
if (isTouchDevice()) {
    document.addEventListener('DOMContentLoaded', () => {
        // Prevenir zoom en doble tap
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (event) => {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // Mejorar la experiencia táctil en las celdas
        document.addEventListener('touchstart', (e) => {
            if (e.target.classList.contains('cell')) {
                e.target.style.transform = 'scale(0.9)';
            }
        });
        
        document.addEventListener('touchend', (e) => {
            if (e.target.classList.contains('cell')) {
                e.target.style.transform = '';
            }
        });
    });
}