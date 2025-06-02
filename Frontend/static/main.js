let socket;
function iniciarJuego() {
    socket = new WebSocket("wss://tu-backend-en-render.onrender.com/ws/usuario1");
    socket.onopen = () => {
        socket.send(JSON.stringify({accion: "iniciar", filas: 5, columnas: 5, minas: 5}));
    };
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data);
    };
}
