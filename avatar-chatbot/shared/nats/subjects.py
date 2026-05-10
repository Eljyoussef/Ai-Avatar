class Subjects:

    @staticmethod
    def audio_input(sid: str) -> str: return f"session.{sid}.audio.input"

    @staticmethod
    def asr_partial(sid: str) -> str: return f"session.{sid}.asr.partial"

    @staticmethod
    def asr_final(sid: str) -> str: return f"session.{sid}.asr.final"

    @staticmethod
    def rag_query(sid: str) -> str: return f"session.{sid}.rag.query"

    @staticmethod
    def rag_results(sid: str) -> str: return f"session.{sid}.rag.results"

    @staticmethod
    def llm_request(sid: str) -> str: return f"session.{sid}.llm.request"

    @staticmethod
    def llm_token(sid: str) -> str: return f"session.{sid}.llm.token"

    @staticmethod
    def tts_request(sid: str) -> str: return f"session.{sid}.tts.request"

    @staticmethod
    def audio_output(sid: str) -> str: return f"session.{sid}.audio.output"

    @staticmethod
    def session_output(sid: str) -> str: return f"session.{sid}.output"

    @staticmethod
    def interrupt(sid: str) -> str: return f"session.{sid}.interrupt"