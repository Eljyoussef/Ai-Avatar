from dataclasses import dataclass, field

@dataclass
class IntentConfig:
    model_name: str = "camembert-base"
    confidence_threshold: float = 0.6
    
    intents: list = field(default_factory=lambda: [
        "question",           # General question
        "document_search",    # Search in documents
        "greeting",           # Bonjour, salut
        "farewell",           # Au revoir
        "clarification",      # Can you repeat?
        "accent_change",      # Change accent
        "gender_change",      # Change gender
        "avatar_toggle",      # Enable/disable avatar
        "help",               # What can you do?
        "interrupt",          # Stop speaking
    ])