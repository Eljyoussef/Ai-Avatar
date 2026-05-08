import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger

logger = get_logger(__name__)

class StreamingRelay:
    def __init__(self, nats_client: NATSClient, vllm_provider, prompt_builder):
        self.nats = nats_client
        self.vllm = vllm_provider
        self.prompt_builder = prompt_builder
        self.sessions = {}
        
    async def handle_query(self, msg):
        subject = msg.subject
        session_id = subject.split(".")[1]
        data = json.loads(msg.data.decode())
        
        query = data.get("text", "")
        gender = data.get("gender", "neutral")
        accent = data.get("accent", "fr-FR")
        documents = data.get("documents", [])
        history = data.get("history", [])
        
        # Track if interrupted
        self.sessions[session_id] = {"interrupted": False}
        
        # Build prompt
        messages = self.prompt_builder.build(
            query=query,
            gender=gender,
            accent=accent,
            documents=documents,
            history=history
        )
        
        logger.info(f"Inference [{session_id}]: {query[:50]}...")
        
        try:
            full_response = []
            
            async for token in self.vllm.generate_stream(messages, session_id):
                # Check for interruption
                if self.sessions.get(session_id, {}).get("interrupted"):
                    logger.info(f"Generation interrupted: {session_id}")
                    break
                
                full_response.append(token)
                
                # Publish token for TTS
                await self.nats.publish(
                    Subjects.llm_token(session_id),
                    {"token": token, "session_id": session_id}
                )
            
            complete_text = "".join(full_response)
            
            # Send final response to session output
            await self.nats.publish(
                Subjects.session_output(session_id),
                {
                    "type": "text_response",
                    "text": complete_text,
                    "session_id": session_id
                }
            )
            
            # Save to memory
            await self.nats.publish(
                "session." + session_id + ".memory.update",
                {
                    "role": "assistant",
                    "content": complete_text,
                    "timestamp": asyncio.get_event_loop().time()
                }
            )
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            await self.nats.publish(
                Subjects.session_output(session_id),
                {
                    "type": "text_response",
                    "text": "Désolé, une erreur est survenue.",
                    "session_id": session_id
                }
            )
        
        finally:
            self.sessions.pop(session_id, None)