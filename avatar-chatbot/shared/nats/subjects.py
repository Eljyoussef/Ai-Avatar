class Subjects:
    @staticmethod
    def audio_input(session_id): return f"session.{session_id}.audio.input"
    
    @staticmethod
    def audio_output(session_id): return f"session.{session_id}.audio.output"
    
    @staticmethod
    def asr_partial(session_id): return f"session.{session_id}.asr.partial"
    
    @staticmethod
    def asr_final(session_id): return f"session.{session_id}.asr.final"
    
    @staticmethod
    def llm_token(session_id): return f"session.{session_id}.llm.token"
    
    @staticmethod
    def rag_query(session_id): return f"session.{session_id}.rag.query"
    
    @staticmethod
    def rag_results(session_id): return f"session.{session_id}.rag.results"
    
    @staticmethod
    def control_interrupt(session_id): return f"session.{session_id}.control.interrupt"
    
    @staticmethod
    def session_output(session_id): return f"session.{session_id}.output"