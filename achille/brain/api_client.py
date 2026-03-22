"""
Achille — API Client
Abstraction qui parle soit à CLIProxyAPI (OpenAI-compatible, abo Max)
soit à l'API Anthropic directe.

CLIProxyAPI expose un endpoint OpenAI-compatible sur localhost:8317.
On utilise le SDK openai pointé vers ce proxy.
"""
import os
from openai import OpenAI
from config.settings import CLIPROXY_BASE_URL

# Mapping des noms de modèles Anthropic → ce que CLIProxyAPI comprend
MODEL_MAP = {
    "claude-haiku-4-5-20251001": "claude-haiku-4-5-20251001",
    "claude-sonnet-4-6": "claude-sonnet-4-6",
    "claude-opus-4-6": "claude-opus-4-6",
}


def get_client() -> OpenAI:
    """Retourne un client OpenAI pointé vers CLIProxyAPI."""
    return OpenAI(
        base_url=CLIPROXY_BASE_URL,
        api_key=os.environ.get("CLIPROXY_API_KEY", "not-needed"),
    )


def chat(
    messages: list[dict],
    model: str = "claude-sonnet-4-6",
    system: str = "",
    max_tokens: int = 4096,
    temperature: float = 1.0,
) -> str:
    """
    Appel chat completion via CLIProxyAPI.
    Compatible OpenAI format.
    """
    client = get_client()
    
    # Le system prompt va en premier message avec role "system"
    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)
    
    mapped_model = MODEL_MAP.get(model, model)
    
    try:
        response = client.chat.completions.create(
            model=mapped_model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        return response.choices[0].message.content or ""
    
    except Exception as e:
        print(f"[api_client error] {e}")
        return f"[Erreur API: {e}]"


def chat_with_thinking(
    messages: list[dict],
    model: str = "claude-opus-4-6",
    system: str = "",
    max_tokens: int = 16000,
    thinking_budget: int = 10000,
) -> str:
    """
    Appel avec extended thinking (Couche 3).
    Note: CLIProxyAPI peut ne pas supporter le thinking nativement.
    Fallback : on ajoute une instruction dans le system prompt.
    """
    # Enrichir le system prompt pour simuler le thinking
    thinking_instruction = (
        "\n\nAVANT de répondre, réfléchis en profondeur. "
        "Considère les contre-arguments, les biais possibles, "
        "les contradictions avec le contexte fourni. "
        "Prends le temps d'analyser avant de formuler ta réponse."
    )
    
    enriched_system = (system or "") + thinking_instruction
    
    return chat(
        messages=messages,
        model=model,
        system=enriched_system,
        max_tokens=max_tokens,
    )
