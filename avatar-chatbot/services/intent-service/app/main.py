import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger
from .config import IntentConfig
from .classifiers.intent_classifier import IntentClassifier

logger = get_logger(__name__)

async def main():
    nats_client = NATSClient()
    await nats_client.connect()
    
    config = IntentConfig()
    classifier = IntentClassifier(config)
    await classifier.load_model()
    
    async def handle_partial_asr(msg):
        """Handle partial ASR results for early intent detection."""
        subject = msg.subject
        session_id = subject.split(".")[1]
        data = json.loads(msg.data.decode())
        text = data.get("text", "")
        
        if len(text.split()) < 2:
            return  # Too short
        
        intent, confidence = await classifier.classify(text)
        
        await nats_client.publish(
            f"session.{session_id}.intent.detected",
            {
                "intent": intent,
                "confidence": confidence,
                "text": text,
                "needs_rag": classifier.needs_rag(intent),
                "should_prefetch": classifier.should_prefetch(intent)
            }
        )
        
        # If intent suggests RAG is needed, trigger prefetch
        if classifier.should_prefetch(intent) and confidence > 0.7:
            await nats_client.publish(
                f"session.{session_id}.rag.query",
                {"query": text, "prefetch": True}
            )
            logger.debug(f"RAG prefetch triggered: {session_id}")
    
    await nats_client.subscribe("session.*.asr.partial", handle_partial_asr)
    
    logger.info("Intent Service running")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())