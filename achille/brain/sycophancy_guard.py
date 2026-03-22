"""
Achille — Sycophancy Guard
Vérifie et corrige la réponse avant envoi.
"""
import re
from datetime import datetime
from memory.writer import append
from config.settings import MAX_VALIDATIONS_PER_CONVERSATION

# Compteur par conversation (reset à chaque nouvelle conversation)
_validation_count = 0
_conversation_id = None

FORBIDDEN_STARTS = [
    r"^(Bonne|Excellente|Super|Très bonne|Grande|Belle)\s+(question|observation|remarque|idée|réflexion|analyse)",
    r"^C'est\s+(une?\s+)?(très\s+)?(bon|bonne|excellente|pertinente|intéressante)",
    r"^(Quelle|Quel)\s+(bonne|excellente|super)\s+(question|idée|remarque)",
    r"^Merci (de|pour|d'avoir)\s+(partager|partag|poser|cette)",
    r"^J'apprécie\s+(ta|cette|que tu)",
]

FORBIDDEN_PATTERNS = [
    r"Tu as\s+(tout à fait\s+|complètement\s+|absolument\s+)?raison",
    r"Je comprends\s+(parfaitement\s+|tout à fait\s+)?(ce que tu ressens|ta frustration|ton sentiment)",
    r"C'est (tout à fait |complètement )?normal de (ressentir|penser|vouloir|se sentir)",
    r"Tu es sur la bonne voie",
    r"Je suis (fier|content|impressionné)",
    r"C'est (vraiment )?(courageux|brave|admirable|impressionnant) de ta part",
]

VALIDATION_PATTERNS = [
    r"(Oui|Effectivement|Exactement|Absolument|Tout à fait),?\s",
    r"Tu (as|fais) bien de\s",
    r"C'est (un bon|le bon) (choix|réflexe|instinct)",
]


def reset_conversation(conversation_id: str) -> None:
    """Reset le compteur pour une nouvelle conversation."""
    global _validation_count, _conversation_id
    _validation_count = 0
    _conversation_id = conversation_id


def check(response: str, conversation_id: str) -> str:
    """
    Vérifie une réponse pour la sycophancy.
    Retourne la réponse corrigée.
    """
    global _validation_count, _conversation_id
    
    if _conversation_id != conversation_id:
        reset_conversation(conversation_id)
    
    original = response
    flagged = []
    
    # 1. Supprimer les débuts flatteurs
    for pattern in FORBIDDEN_STARTS:
        match = re.match(pattern, response, re.IGNORECASE)
        if match:
            response = response[match.end():].lstrip(" .!,\n")
            # Capitaliser la première lettre
            if response:
                response = response[0].upper() + response[1:]
            flagged.append(f"start_flattery: {pattern}")
    
    # 2. Logger les patterns interdits (sans les supprimer — ils sont dans le corps du texte)
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            flagged.append(f"forbidden_pattern: {pattern}")
    
    # 3. Compter les validations
    for pattern in VALIDATION_PATTERNS:
        if re.match(pattern, response, re.IGNORECASE):
            _validation_count += 1
            if _validation_count > MAX_VALIDATIONS_PER_CONVERSATION:
                flagged.append(f"validation_limit_exceeded: {_validation_count}")
            break
    
    # 4. Logger si sycophancy détectée
    if flagged:
        _log_sycophancy(flagged, original, response)
    
    return response


def _log_sycophancy(flags: list[str], original: str, corrected: str) -> None:
    """Log une instance de sycophancy dans sycophancy_log.md."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"""
### {timestamp}
- **Flags** : {', '.join(flags)}
- **Original** : {original[:200]}...
- **Corrigé** : {corrected[:200]}...
"""
    try:
        append("sycophancy_log.md", entry)
    except Exception as e:
        print(f"[sycophancy_log error] {e}")
