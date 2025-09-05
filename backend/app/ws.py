from fastapi import WebSocket, WebSocketDisconnect
import asyncio

# A simple in-memory store for websocket connections
connections = {}

async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    connections[job_id] = websocket
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        del connections[job_id]
        print(f"Client {job_id} disconnected")

# A function to send updates to a specific client
async def send_status_update(job_id: str, status: str):
    if job_id in connections:
        await connections[job_id].send_json({"job_id": job_id, "status": status})
