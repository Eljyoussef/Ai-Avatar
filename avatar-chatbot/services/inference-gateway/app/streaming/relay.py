import json, asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../.."))
from shared.nats.subjects import Subjects
from shared.logging import get_logger
logger = get_logger(__name__)

class StreamingRelay:
    def __init__(self, nats_client, vllm_provider, prompt_builder):
        self.nats = nats_client
        self.prompt_builder = prompt_builder
        self.sessions = {}

    async def handle_query(self, msg):
        session_id = msg.subject.split(".")[1]
        data = json.loads(msg.data.decode())
        query = data.get("text", "")
        logger.info(f"Query [{session_id}]: {query[:50]}...")
        response = f"Vous avez dit: {query}. Je suis operationnel!"
        for char in response:
            await self.nats.publish(Subjects.llm_token(session_id), {"token": char, "session_id": session_id})
        await self.nats.publish(Subjects.session_output(session_id), {"type": "text_response", "text": response, "session_id": session_id})