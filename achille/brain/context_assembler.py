"""
Achille — Context Assembler
Assemble le contexte complet à envoyer à Claude.
"""
from memory.reader import (
    read, read_system_prompt, read_sycophancy_protocol,
    read_index, read_contradictions, read_facts, estimate_tokens
)
from config.settings import MAX_CONTEXT_TOKENS


def build(classification: dict, conversation_history: list[dict]) -> dict:
    """
    Assemble le contexte complet.
    Retourne { system: str, messages: list[dict] }
    """
    # --- System prompt (toujours) ---
    system_parts = [
        read_system_prompt(),
        "\n\n---\n\n# Protocole anti-sycophancy (résumé)\n\n",
        read_sycophancy_protocol(),
    ]
    system = "".join(system_parts)
    
    # --- Contexte utilisateur (injecté comme premier message user) ---
    context_parts = []
    
    # INDEX — toujours
    context_parts.append(f"## INDEX.md\n{read_index()}")
    
    # Contradictions — toujours
    context_parts.append(f"## Contradictions\n{read_contradictions()}")
    
    # Facts — toujours
    context_parts.append(f"## Faits\n{read_facts()}")
    
    # Fichiers pertinents (du classifier)
    for filepath in classification.get("files", []):
        content = read(filepath)
        if content and "[fichier introuvable" not in content:
            context_parts.append(f"## {filepath}\n{content}")
    
    context_block = "\n\n---\n\n".join(context_parts)
    
    # --- Budget check ---
    total_tokens = estimate_tokens(system) + estimate_tokens(context_block)
    if total_tokens > MAX_CONTEXT_TOKENS:
        # Tronquer les fichiers pertinents (garder les 100 premières lignes de chaque)
        context_parts_trimmed = context_parts[:3]  # INDEX, contradictions, facts
        for filepath in classification.get("files", []):
            content = read(filepath, summary=True)
            if content:
                context_parts_trimmed.append(f"## {filepath}\n{content}")
        context_block = "\n\n---\n\n".join(context_parts_trimmed)
    
    # --- Assembler les messages ---
    messages = []
    
    # Contexte comme premier message (invisible pour l'utilisateur mais lu par Claude)
    messages.append({
        "role": "user",
        "content": f"<context>\n{context_block}\n</context>\n\nVoici le contexte actuel de ma mémoire. Ne le mentionne pas explicitement dans ta réponse."
    })
    messages.append({
        "role": "assistant",
        "content": "Compris. J'ai intégré le contexte. Je suis prêt."
    })
    
    # Historique de conversation
    for msg in conversation_history:
        messages.append(msg)
    
    return {
        "system": system,
        "messages": messages,
        "layer": classification.get("layer", 2),
        "subject": classification.get("subject", "general"),
    }
