"""
Achille — Responder
Appelle Claude API avec le bon modèle et les bons paramètres.
"""
import anthropic
from config.settings import ANTHROPIC_API_KEY, MODELS

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def select_model(layer: int) -> str:
    """Sélectionne le modèle selon la couche."""
    return MODELS.get(layer, MODELS[2])


def get_api_params(layer: int) -> dict:
    """Retourne les paramètres d'appel API selon la couche."""
    params = {
        "model": select_model(layer),
        "max_tokens": 4096,
    }
    
    # Extended thinking pour Couche 3
    if layer == 3:
        params["max_tokens"] = 16000
        params["thinking"] = {
            "type": "enabled",
            "budget_tokens": 10000,
        }
    
    return params


async def generate(context: dict, user_message: str) -> str:
    """
    Génère une réponse via Claude API.
    context = { system, messages, layer, subject }
    """
    params = get_api_params(context["layer"])
    
    # Ajouter le message de l'utilisateur
    messages = context["messages"] + [
        {"role": "user", "content": user_message}
    ]
    
    try:
        response = client.messages.create(
            system=context["system"],
            messages=messages,
            **params,
        )
        
        # Extraire le texte (ignorer les blocs thinking)
        text_parts = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
        
        return "\n".join(text_parts)
    
    except Exception as e:
        print(f"[responder error] {e}")
        return "Erreur lors de la génération. Réessaie."


async def generate_with_model(prompt: str, model: str, system: str = "") -> str:
    """Appel direct avec un modèle spécifique (pour classifier, dual-prompt, etc.)."""
    try:
        kwargs = {
            "model": model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        
        response = client.messages.create(**kwargs)
        return response.content[0].text
    
    except Exception as e:
        print(f"[generate_with_model error] {e}")
        return ""
