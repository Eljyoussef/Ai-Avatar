import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)

class IntentClassifier:
    """Intent classifier for early detection and prefetching."""
    
    # Keyword-based quick classification (no model needed)
    KEYWORD_INTENTS = {
        "greeting": ["bonjour", "salut", "coucou", "hey", "hello"],
        "farewell": ["au revoir", "bye", "à bientôt", "bonne journée", "adieu"],
        "clarification": ["répète", "répétez", "comment", "pardon", "quoi"],
        "help": ["aide", "que peux-tu faire", "capacités", "fonctionnalités"],
        "interrupt": ["stop", "arrête", "tais-toi", "silence"],
        "avatar_toggle": ["avatar", "visage", "montre-toi", "affiche-toi"],
    }
    
    def __init__(self, config):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.labels = config.intents
        
    async def load_model(self):
        """Load CamemBERT fine-tuned for intent classification."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.config.model_name,
                num_labels=len(self.labels)
            ).to(self.device)
            self.model.eval()
            logger.info("Intent classifier loaded")
        except Exception as e:
            logger.warning(f"Model loading failed, using keyword fallback: {e}")
    
    async def classify(self, text: str) -> Tuple[str, float]:
        """Classify intent from partial or complete text."""
        text_lower = text.lower().strip()
        
        # Quick keyword check first
        keyword_intent = self._keyword_classify(text_lower)
        if keyword_intent:
            return keyword_intent, 0.95
        
        # Model-based classification
        if self.model and self.tokenizer:
            try:
                inputs = self.tokenizer(
                    text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=128,
                    padding=True
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
                    
                max_prob, max_idx = torch.max(probabilities[0], dim=0)
                confidence = max_prob.item()
                
                if confidence >= self.config.confidence_threshold:
                    intent = self.labels[max_idx.item()]
                else:
                    intent = "question"  # Default
                    
                return intent, confidence
                
            except Exception as e:
                logger.error(f"Classification error: {e}")
        
        # Default fallback
        if "?" in text:
            return "question", 0.8
        return "question", 0.5
    
    def _keyword_classify(self, text: str) -> Tuple[str, float]:
        """Quick keyword-based classification."""
        for intent, keywords in self.KEYWORD_INTENTS.items():
            for keyword in keywords:
                if keyword in text:
                    return intent, 0.95
        return None
    
    def needs_rag(self, intent: str) -> bool:
        """Check if intent requires document retrieval."""
        return intent in ["question", "document_search"]
    
    def should_prefetch(self, intent: str) -> bool:
        """Check if we should prefetch RAG results."""
        return intent in ["question", "document_search"]