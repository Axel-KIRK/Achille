"""
Achille — Classifier
Appel Haiku via CLIProxyAPI pour déterminer le sujet, la couche, et les fichiers à charger.
"""
import json
from brain.api_client import chat
from config.settings import CLASSIFIER_MODEL
from memory.reader import read_index

CLASSIFIER_PROMPT = """Tu es le routeur de contexte d'Achille, un daemon personnel.
Analyse le message d'Axel et retourne un JSON pour router la conversation.

INDEX.md actuel :
<index>
{index_content}
</index>

Message d'Axel :
<message>
{message}
</message>

Retourne UNIQUEMENT un JSON valide, rien d'autre :
{{
  "subject": "string — le sujet principal en un mot (julie, boulot, santé, carrière, existentiel, daemon, side-project, fitness, psy, etc.)",
  "layer": 1 ou 2 ou 3,
  "files": ["chemin/fichier.md", "chemin/autre.md"],
  "mood": "factual" ou "emotional" ou "reflective" ou "urgent",
  "is_strong_conviction": true ou false,
  "keywords_for_contradiction_check": ["mot1", "mot2"]
}}

Règles de routage :
- Si Axel parle de tâches, agenda, rappels → layer 1
- Si Axel parle de direction carrière, side projects, lieu de vie, finances → layer 2
- Si Axel parle d'identité, relations profondes, traumas, sens de la vie, émotions → layer 3
- is_strong_conviction = true si Axel affirme quelque chose avec certitude sur un sujet de couche 2-3
- Charge toujours 2-4 fichiers max, les plus pertinents
"""


async def classify(message: str) -> dict:
    """Classifie un message et retourne le routage."""
    index_content = read_index()
    
    prompt = CLASSIFIER_PROMPT.format(
        index_content=index_content,
        message=message
    )
    
    try:
        text = chat(
            messages=[{"role": "user", "content": prompt}],
            model=CLASSIFIER_MODEL,
            max_tokens=500,
        )
        
        # Nettoyer si le modèle ajoute des backticks
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        
        return json.loads(text)
    
    except (json.JSONDecodeError, Exception) as e:
        print(f"[classifier error] {e}")
        # Fallback : couche 2, charger les basiques
        return {
            "subject": "general",
            "layer": 2,
            "files": ["profile/beliefs.md"],
            "mood": "reflective",
            "is_strong_conviction": False,
            "keywords_for_contradiction_check": []
        }
