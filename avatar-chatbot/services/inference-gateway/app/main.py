import asyncio, json, sys, os, httpx
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger

logger = get_logger(__name__)

VLLM_URL = os.getenv("VLLM_BASE_URL", "http://vllm:8000/v1")
VLLM_MODEL = os.getenv("VLLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
active_tasks: dict[str, asyncio.Task] = {}


async def call_vllm_stream(messages: list):
    try:
        timeout = httpx.Timeout(120.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", f"{VLLM_URL}/chat/completions", json={
                "model": VLLM_MODEL, "messages": messages,
                "max_tokens": 256, "temperature": 0.7, "stream": True
            }) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk == "[DONE]":
                            break
                        try:
                            delta = json.loads(chunk)["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
                        except Exception:
                            continue
    except Exception as e:
        logger.warning(f"vLLM: {e}")


def build_prompt(text: str, gender: str, accent: str, docs: list) -> list:
    accent_map = {
        "fr-FR": "français standard", "fr-CA": "québécois", "fr-AF": "africain",
        "fr-BE": "belge", "fr-CH": "suisse", "fr-MG": "maghrébin"
    }
    gender_map = {"female": "une femme", "male": "un homme", "neutral": "une personne"}
    
    system = (
        f"Tu es un assistant vocal {accent_map.get(accent, 'français')}. "
        f"Tu t'adresses à {gender_map.get(gender, 'une personne')}. "
        f"Réponds UNIQUEMENT à partir des documents fournis. "
        f"Si les documents ne contiennent pas la réponse, dis-le honnêtement. "
        f"Réponds en français (2-3 phrases max). NE JAMAIS INVENTER."
    )
    
    if docs:
        chunks = "\n---\n".join([d.get("text", "")[:600] for d in docs[:3]])
        system += f"\n\nDocuments de référence :\n{chunks}"
    
    return [{"role": "system", "content": system}, {"role": "user", "content": text}]


def build_fallback_response(docs: list) -> str:
    """Generate a response when vLLM is unavailable."""
    if docs:
        content = docs[0].get("text", "")[:500]
        return f"D'après vos documents :\n\n{content}\n\nQue souhaitez-vous savoir de plus ?"
    return "Je n'ai pas trouvé d'information pertinente dans vos documents pour cette question."


async def handle_llm_request(msg):
    sid = msg.subject.split(".")[1]
    data = json.loads(msg.data.decode())
    text = data.get("text", "")
    gender = data.get("gender", "neutral")
    accent = data.get("accent", "fr-FR")
    docs = data.get("documents", [])
    
    if not docs:
        await nats_client.publish(Subjects.session_output(sid), {
            "type": "text_response",
            "text": "Aucune information pertinente trouvée dans vos documents pour cette question."
        })
        return
    
    prev = active_tasks.pop(sid, None)
    if prev:
        prev.cancel()
    
    async def _process():
        messages = build_prompt(text, gender, accent, docs)
        logger.info(f"LLM [{sid}]: streaming with {len(docs)} docs")
        
        full_text = ""
        nats = NATSClient()
        await nats.connect()
        try:
            async for token in call_vllm_stream(messages):
                full_text += token
                await nats.publish(Subjects.llm_token(sid), {"token": token})
                await nats.publish(Subjects.session_output(sid), {"type": "token", "token": token})
            
            final = full_text.strip()
            if not final:
                final = build_fallback_response(docs)
            
            await nats.publish(Subjects.session_output(sid), {"type": "text_response", "text": final})
            logger.info(f"LLM [{sid}] done: {final[:80]}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"LLM [{sid}]: {e}")
            fallback = build_fallback_response(docs)
            await nats.publish(Subjects.session_output(sid), {"type": "text_response", "text": fallback})
        finally:
            await nats.close()
    
    active_tasks[sid] = asyncio.create_task(_process())


async def handle_interrupt(msg):
    sid = msg.subject.split(".")[1]
    task = active_tasks.pop(sid, None)
    if task:
        task.cancel()


async def main():
    global nats_client
    nats_client = NATSClient()
    await nats_client.connect()
    
    await nats_client.subscribe(Subjects.llm_request("*"), handle_llm_request)
    await nats_client.subscribe(Subjects.interrupt("*"), handle_interrupt)
    
    logger.info("Inference Gateway running (STRICT document mode)")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())