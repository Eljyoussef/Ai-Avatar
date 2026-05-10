import sys, os, json, uuid, io
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger

logger = get_logger(__name__)
nats_client = NATSClient()

app = FastAPI(title="Avatar Chatbot Gateway")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


GLOBAL_SESSION = "__global__"


@app.on_event("startup")
async def startup():
    await nats_client.connect()
    logger.info("Gateway NATS connected")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}

@app.get("/api/accents")
async def get_accents():
    return {"accents": [
        {"code": "fr-FR", "name": "Français standard", "flag": "🇫🇷"},
        {"code": "fr-CA", "name": "Français québécois", "flag": "🇨🇦"},
        {"code": "fr-AF", "name": "Français africain", "flag": "🌍"},
        {"code": "fr-BE", "name": "Français belge", "flag": "🇧🇪"},
        {"code": "fr-CH", "name": "Français suisse", "flag": "🇨🇭"},
        {"code": "fr-MG", "name": "Français maghrébin", "flag": "🌅"},
    ]}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    text = ""
    try:
        filename = file.filename or ""
        if filename.endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif filename.endswith(".docx"):
            from docx import Document
            doc = Document(io.BytesIO(content))
            text = "\n".join(p.text for p in doc.paragraphs)
        elif filename.endswith(".txt") or filename.endswith(".md"):
            text = content.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Text extraction failed: {e}")
    
    doc_id = str(uuid.uuid4())
    # USE GLOBAL SESSION so ALL queries can find these docs
    await nats_client.publish("document.upload", {
        "document_id": doc_id, "filename": file.filename, "text": text, "size": len(content),
        "session_id": GLOBAL_SESSION
    })
    return JSONResponse({"document_id": doc_id, "filename": file.filename, "status": "ok", "text_length": len(text)})

@app.websocket("/ws/{session_id}")
async def ws_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    await websocket.send_json({"type": "connected", "session_id": session_id})
    logger.info(f"WS connected: {session_id}")
    
    async def forward(msg):
        try:
            await websocket.send_json(json.loads(msg.data.decode()))
        except:
            try:
                await websocket.send_bytes(msg.data)
            except:
                pass
    
    sub = await nats_client.subscribe(Subjects.session_output(session_id), forward)
    sub_audio = await nats_client.subscribe(Subjects.audio_output(session_id), forward)
    
    try:
        while True:
            raw = await websocket.receive()
            if "text" in raw:
                msg = json.loads(raw["text"])
                if msg.get("type") == "chat" and msg.get("content", "").strip():
                    content = msg["content"].strip()
                    gender = msg.get("gender", "neutral")
                    accent = msg.get("accent", "fr-FR")
                    
                    # Publish to ASR (text = final transcript)
                    await nats_client.publish(Subjects.asr_final(session_id), {
                        "text": content, "source": "text", "is_partial": False
                    })
                    
                    # RAG IS THE ORCHESTRATOR — it will trigger LLM after retrieval
                    await nats_client.publish(Subjects.rag_query(session_id), {
                        "query": content, "gender": gender, "accent": accent
                    })
                    
                elif msg.get("type") == "interrupt":
                    await nats_client.publish(Subjects.interrupt(session_id), {})
                elif msg.get("type") == "accent_change":
                    await nats_client.publish(f"session.{session_id}.accent.update", {"accent": msg.get("accent")})
                elif msg.get("type") == "gender_change":
                    await nats_client.publish(f"session.{session_id}.gender.update", {"gender": msg.get("gender")})
            elif "bytes" in raw:
                await nats_client.publish(Subjects.audio_input(session_id), raw["bytes"])
    except WebSocketDisconnect:
        logger.info(f"WS disconnected: {session_id}")
    finally:
        await sub.unsubscribe()
        await sub_audio.unsubscribe()
