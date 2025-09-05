from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid

from app.tasks import process_video_task
from app.ws import websocket_endpoint

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class JobIn(BaseModel):
    url: str
    target_lang: str
    source_lang: Optional[str] = None
    hardcode: bool = True
    process_playlist: bool = False

class JobOut(BaseModel):
    job_id: str
    status: str

@app.post("/enqueue", response_model=JobOut)
async def enqueue_job(req: JobIn):
    job_id = uuid.uuid4().hex
    process_video_task.delay(req.url, req.target_lang, job_id, req.hardcode, req.source_lang, req.process_playlist)
    return {"job_id": job_id, "status": "queued"}

app.add_api_websocket_route("/ws/{job_id}", websocket_endpoint)

