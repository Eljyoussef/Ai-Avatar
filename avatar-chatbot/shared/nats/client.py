import json
import nats
from nats.aio.client import Client as NATS

class NATSClient:
    def __init__(self, hosts=None):
        self.hosts = hosts or ["nats://localhost:4222"]
        self.nc = NATS()
        self._subscriptions = []

    async def connect(self):
        await self.nc.connect(servers=self.hosts)
        print(f"Connected to NATS: {self.hosts}")

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