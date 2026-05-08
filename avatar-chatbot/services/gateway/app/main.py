import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from shared.nats.client import NATSClient
from shared.logging import get_logger

logger = get_logger(__name__)
nats_client = NATSClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await nats_client.connect()
    logger.info("Gateway started")
    yield
    await nats_client.close()

app = FastAPI(title="Avatar Chatbot Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}

# WebSocket endpoint
from .websocket.ws_handler import router as ws_router
app.include_router(ws_router)