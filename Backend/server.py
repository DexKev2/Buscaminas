
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from game import Buscaminas

app = FastAPI()

app.mount("/static", StaticFiles(directory="../Frontend/static"), name="static")

@app.get("/")
def get_index():
    return FileResponse("../Frontend/index.html")

juegos = {}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    juego = None

    while True:
        data = await websocket.receive_json()
        accion = data.get("accion")

        if accion == "iniciar":
            filas = data["filas"]
            columnas = data["columnas"]
            minas = data["minas"]
            juego = Buscaminas(filas, columnas, minas)
            juegos[user_id] = juego
            await websocket.send_json({"estado": "juego_iniciado"})

        elif accion == "revelar":
            fila, columna = data["fila"], data["columna"]
            if juego.tablero[fila][columna] == -1:
                await websocket.send_json({"estado": "perdiste"})
            else:
                celdas = juego.revelar(fila, columna)
                await websocket.send_json({"estado": "continuar", "celdas": celdas})

        elif accion == "resolver":
            minas = juego.resolver()
            await websocket.send_json({"estado": "minas", "minas": minas})

