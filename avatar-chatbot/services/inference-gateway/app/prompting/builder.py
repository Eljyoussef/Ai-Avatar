from typing import List, Dict

class PromptBuilder:
    GENDER_INSTRUCTIONS = {
        "female": "Tu t'adresses à une femme. Utilise les formes féminines.",
        "male": "Tu t'adresses à un homme. Utilise les formes masculines.",
        "neutral": "Utilise des formulations neutres."
    }
    
    def build(self, query: str, gender: str = "neutral", accent: str = "fr-FR", 
              documents: List[Dict] = None, history: List[Dict] = None) -> list:
        gender_instruction = self.GENDER_INSTRUCTIONS.get(gender, self.GENDER_INSTRUCTIONS["neutral"])
        doc_text = "Aucun document disponible."
        if documents:
            doc_text = "\n".join([d.get("text", "") for d in documents[:3]])
        
        return [
            {"role": "system", "content": f"Assistant vocal français. {gender_instruction}\nDocuments: {doc_text}"},
            {"role": "user", "content": query}
        ]