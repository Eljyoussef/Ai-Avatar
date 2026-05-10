import json
import os
import nats
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout
from shared.logging import get_logger
import asyncio

logger = get_logger(__name__)

class NATSClient:
    def __init__(self, hosts=None):
        nats_host = os.getenv("NATS_HOST", "nats")
        nats_port = os.getenv("NATS_PORT", "4222")
        self.hosts = hosts or [f"nats://{nats_host}:{nats_port}"]
        self.nc = NATS()
        self._subscriptions = []

    async def connect(self):
        for attempt in range(5):
            try:
                await self.nc.connect(
                    servers=self.hosts,
                    reconnect_time_wait=2,
                    max_reconnect_attempts=-1
                )
                logger.info(f"Connected to NATS at {self.hosts}")
                return
            except Exception as e:
                logger.warning(f"NATS attempt {attempt+1}: {e}")
                if attempt < 4:
                    await asyncio.sleep(2)
        logger.error("Could not connect to NATS after 5 attempts")

    async def publish(self, subject, data):
        if isinstance(data, dict):
            data = json.dumps(data).encode()
        await self.nc.publish(subject, data)

    async def subscribe(self, subject, callback):
        sub = await self.nc.subscribe(subject, cb=callback)
        self._subscriptions.append(sub)
        return sub

    async def close(self):
        for sub in self._subscriptions:
            await sub.unsubscribe()
        await self.nc.close()