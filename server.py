import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

rooms = {}

@app.websocket("/ws/{room_code}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, player_id: str):
    await websocket.accept()
    
    if room_code not in rooms:
        rooms[room_code] = {"player1": websocket, "player2": None}
        await websocket.send_json({"type": "waiting", "message": "Ожидание второго игрока..."})
    elif rooms[room_code]["player2"] is None:
        rooms[room_code]["player2"] = websocket
        if rooms[room_code]["player1"]:
            await rooms[room_code]["player1"].send_json({"type": "start", "message": "Игрок 2 подключился! Ваш ход (Белые)"})
        await websocket.send_json({"type": "start", "message": "Вы подключились! Ждите хода (Черные)"})
    else:
        await websocket.send_json({"type": "error", "message": "Комната заполнена"})
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_json()
            if rooms[room_code]["player1"] == websocket and rooms[room_code]["player2"]:
                await rooms[room_code]["player2"].send_json(data)
            elif rooms[room_code]["player2"] == websocket and rooms[room_code]["player1"]:
                await rooms[room_code]["player1"].send_json(data)
    except WebSocketDisconnect:
        if room_code in rooms:
            if rooms[room_code]["player1"] == websocket and rooms[room_code]["player2"]:
                await rooms[room_code]["player2"].send_json({"type": "disconnect", "message": "Противник отключился"})
            elif rooms[room_code]["player2"] == websocket and rooms[room_code]["player1"]:
                await rooms[room_code]["player1"].send_json({"type": "disconnect", "message": "Противник отключился"})
            
            if rooms[room_code]["player1"] is None and rooms[room_code]["player2"] is None:
                del rooms[room_code]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
