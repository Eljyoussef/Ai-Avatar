import asyncio, json, sys, os, time, struct
from collections import deque

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger

logger = get_logger(__name__)

# ----- Whisper loading -------------------------------------------------
_whisper_model = None
try:
    from faster_whisper import WhisperModel
    _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    logger.info("Whisper tiny loaded (CPU)")
except Exception as e:
    logger.warning(f"Whisper not available: {e}")


def _transcribe_sync(audio: np.ndarray) -> str:
    if _whisper_model is None:
        return ""
    segments, _ = _whisper_model.transcribe(audio, language="fr", beam_size=5,
                                            vad_filter=True,
                                            vad_parameters=dict(min_silence_duration_ms=700))
    return " ".join(s.text.strip() for s in segments).strip()


async def transcribe(audio: np.ndarray) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _transcribe_sync, audio)


# ----- Session state ----------------------------------------------------
class ASRSession:
    def __init__(self):
        self.frames: deque[bytes] = deque(maxlen=200)      # ~2 sec at 16k/10ms
        self.is_speaking = False
        self.speech_frames = 0
        self.silence_frames = 0
        self.last_voice_ts = time.time()

    SPEECH_START = 8
    SILENCE_END = 25


async def main():
    nats_client = NATSClient()
    await nats_client.connect()
    sessions: dict[str, ASRSession] = {}

    async def on_audio(msg):
        sid = msg.subject.split(".")[1]
        chunk = msg.data

        sess = sessions.setdefault(sid, ASRSession())
        sess.frames.append(chunk)
        sess.last_voice_ts = time.time()

        # Simple energy-based VAD (16-bit PCM little-endian)
        samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
        energy = np.sqrt(np.mean(samples ** 2))
        is_speech = energy > 150.0

        if is_speech:
            sess.speech_frames += 1
            sess.silence_frames = 0
        else:
            sess.silence_frames += 1

        if not sess.is_speaking and sess.speech_frames > ASRSession.SPEECH_START:
            sess.is_speaking = True
            logger.debug(f"ASR [{sid}] speech started")

    # Background finalizer
    async def finalizer():
        while True:
            await asyncio.sleep(0.3)
            now = time.time()
            for sid, sess in list(sessions.items()):
                if not sess.is_speaking:
                    continue
                if sess.silence_frames < ASRSession.SILENCE_END:
                    continue
                if now - sess.last_voice_ts < 1.2:
                    continue

                # Finalise utterance
                raw = b"".join(sess.frames)
                sess.frames.clear()
                sess.is_speaking = False
                sess.speech_frames = 0
                sess.silence_frames = 0

                audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                text = await transcribe(audio)

                if text:
                    logger.info(f"ASR FINAL [{sid}]: {text[:100]}")
                    await nats_client.publish(Subjects.asr_final(sid), {
                        "text": text, "source": "voice", "is_partial": False
                    })
                    await nats_client.publish(Subjects.session_output(sid), {
                        "type": "asr_final", "text": text
                    })

    asyncio.create_task(finalizer())
    await nats_client.subscribe("session.*.audio.input", on_audio)
    logger.info("ASR Service running (Whisper + VAD)")
    await asyncio.Event().wait()