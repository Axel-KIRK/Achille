"""
Achille — Responder
Appelle Claude via CLIProxyAPI (OpenAI-compatible, abo Max).
"""
from brain.api_client import chat, chat_with_thinking
from config.settings import MODELS


def select_model(layer: int) -> str:
    """Sélectionne le modèle selon la couche."""
    return MODELS.get(layer, MODELS[2])


async def generate(context: dict, user_message: str) -> str:
    """
    Génère une réponse.
    context = { system, messages, layer, subject }
    """
    layer = context["layer"]
    model = select_model(layer)
    
    # Ajouter le message de l'utilisateur
    messages = context["messages"] + [
        {"role": "user", "content": user_message}
    ]
    
    try:
        if layer == 3:
            return chat_with_thinking(
                messages=messages,
                model=model,
                system=context["system"],
            )
        else:
            return chat(
                messages=messages,
                model=model,
                system=context["system"],
            )
    except Exception as e:
        print(f"[responder error] {e}")
        return "Erreur lors de la génération. Réessaie."


async def generate_with_model(prompt: str, model: str, system: str = "") -> str:
    """Appel direct avec un modèle spécifique (pour classifier, dual-prompt, etc.)."""
    try:
        return chat(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            system=system,
            max_tokens=2000,
        )
    except Exception as e:
        print(f"[generate_with_model error] {e}")
        return ""
