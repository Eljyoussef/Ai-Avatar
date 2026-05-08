from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class AccentProfile:
    code: str
    name: str
    region: str
    asr_model: str
    tts_voice_male: str
    tts_voice_female: str
    vocabulary_bias: List[str]
    pronunciation_rules: Dict[str, str]

# Accent profiles for all supported French variants
ACCENT_PROFILES = {
    "fr-FR": AccentProfile(
        code="fr-FR",
        name="Français standard",
        region="France métropolitaine",
        asr_model="whisper-fr-standard",
        tts_voice_male="fr-FR-male",
        tts_voice_female="fr-FR-female",
        vocabulary_bias=[
            "du coup", "voilà", "quoi", "en fait",
            "c'est-à-dire", "genre", "truc", "machin"
        ],
        pronunciation_rules={
            "default": "standard",
            "un": "ɛ̃",
            "in": "ɛ̃",
        }
    ),
    "fr-CA": AccentProfile(
        code="fr-CA",
        name="Français québécois",
        region="Québec, Canada",
        asr_model="whisper-fr-quebecois",
        tts_voice_male="fr-CA-male",
        tts_voice_female="fr-CA-female",
        vocabulary_bias=[
            "tabarnak", "tu sais", "fait que", "icitte",
            "magasiner", "char", "blonde", "chum",
            "dépanneur", "cégep", "achalant", "pantoute"
        ],
        pronunciation_rules={
            "default": "quebecois",
            "oi": "wɛ",
            "ê": "aɪ",
            "â": "ɑ",
        }
    ),
    "fr-AF": AccentProfile(
        code="fr-AF",
        name="Français africain",
        region="Afrique francophone",
        asr_model="whisper-fr-african",
        tts_voice_male="fr-AF-male",
        tts_voice_female="fr-AF-female",
        vocabulary_bias=[
            "on dit quoi", "y'a pas match", "c'est comment",
            "ça va aller", "vraiment hein", "même",
            "daba", "s'enjailler", "boucantier", "go"
        ],
        pronunciation_rules={
            "default": "african",
            "r": "r",  # Rolled R
        }
    ),
    "fr-BE": AccentProfile(
        code="fr-BE",
        name="Français belge",
        region="Belgique",
        asr_model="whisper-fr-belgian",
        tts_voice_male="fr-BE-male",
        tts_voice_female="fr-BE-female",
        vocabulary_bias=[
            "une fois", "s'il vous plaît", "septante",
            "nonante", "dringuelle", "brol", "kot",
            "frite", "baraque", "pain français"
        ],
        pronunciation_rules={
            "default": "belgian",
            "ui": "wi",
        }
    ),
    "fr-CH": AccentProfile(
        code="fr-CH",
        name="Français suisse",
        region="Suisse romande",
        asr_model="whisper-fr-swiss",
        tts_voice_male="fr-CH-male",
        tts_voice_female="fr-CH-female",
        vocabulary_bias=[
            "septante", "huitante", "nonante",
            "natel", "panosse", "carnotzet",
            "papet", "bonnard", "services"
        ],
        pronunciation_rules={
            "default": "swiss",
        }
    ),
    "fr-MG": AccentProfile(
        code="fr-MG",
        name="Français maghrébin",
        region="Maghreb",
        asr_model="whisper-fr-maghrebi",
        tts_voice_male="fr-MG-male",
        tts_voice_female="fr-MG-female",
        vocabulary_bias=[
            "wesh", "zarma", "kif-kif", "bled",
            "flouze", "maboul", "toubib", "clebs",
            "chouïa", "fissa", "bicrave"
        ],
        pronunciation_rules={
            "default": "maghrebi",
            "r": "ʁ",  # Guttural R
        }
    ),
}