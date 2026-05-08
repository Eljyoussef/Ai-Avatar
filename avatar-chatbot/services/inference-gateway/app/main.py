import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger
from .config import InferenceConfig
from .prompting.builder import PromptBuilder
from .providers.vllm_provider import VLLMProvider
from .streaming.relay import StreamingRelay

logger = get_logger(__name__)

async def main():
    nats_client = NATSClient()
    await nats_client.connect()
    
    config = InferenceConfig()
    vllm = VLLMProvider(config)
    prompt_builder = PromptBuilder()
    relay = StreamingRelay(nats_client, vllm, prompt_builder)
    
    # Subscribe to final ASR results
    await nats_client.subscribe("session.*.asr.final", relay.handle_query)
    
    # Handle interrupts
    async def handle_interrupt(msg):
        session_id = msg.subject.split(".")[1]
        if session_id in relay.sessions:
            relay.sessions[session_id]["interrupted"] = True
            logger.info(f"Interrupt acknowledged: {session_id}")
    
    await nats_client.subscribe("session.*.control.interrupt", handle_interrupt)
    
    logger.info("Inference Gateway running")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())