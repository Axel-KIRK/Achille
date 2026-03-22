"""
Achille — Dual Prompt
Génère les contre-arguments quand Axel exprime une conviction forte sur un sujet C2-C3.
"""
from brain.responder import generate_with_model
from memory.reader import read
from config.settings import MODELS

COUNTER_PROMPT = """Tu es l'avocat du diable interne d'Achille, un daemon personnel.
Axel vient d'exprimer une conviction. Ton rôle est de générer les contre-arguments les plus forts.

Message d'Axel :
<message>
{user_message}
</message>

Ses croyances connues (avec niveaux de confiance) :
<beliefs>
{beliefs}
</beliefs>

Ses contradictions connues :
<contradictions>
{contradictions}
</contradictions>

Génère exactement 3 contre-arguments :
1. Un contre-argument factuel (données, réalité concrète)
2. Un contre-argument psychologique (biais cognitif possible, croyance héritée ?)
3. Un contre-argument "et si l'inverse ?" (que se passerait-il s'il faisait exactement le contraire ?)

Sois direct. Pas de flatterie. Pas de "c'est une bonne réflexion mais...".
Si tu trouves une contradiction avec ses déclarations passées, mentionne-la.
"""

SYNTHESIS_PROMPT = """Synthétise équitablement la position d'Axel ET les contre-arguments.

Position d'Axel :
<position>
{user_message}
</position>

Contre-arguments générés :
<counter>
{counter_args}
</counter>

Rédige une synthèse équilibrée en 3-5 phrases qui :
- Présente la position d'Axel sans la valider
- Intègre les contre-arguments naturellement
- Termine par une question ouverte qui force la réflexion
- Ne prend PAS parti
"""


async def generate_counter_arguments(user_message: str) -> str:
    """Génère les contre-arguments (appel 1 du dual-prompt)."""
    beliefs = read("profile/beliefs.md")
    contradictions = read("open-questions/contradictions.md")
    
    prompt = COUNTER_PROMPT.format(
        user_message=user_message,
        beliefs=beliefs,
        contradictions=contradictions,
    )
    
    return await generate_with_model(prompt, MODELS[2])  # Sonnet


async def generate_synthesis(user_message: str, counter_args: str) -> str:
    """Synthétise position + contre-arguments (appel 2 du dual-prompt)."""
    prompt = SYNTHESIS_PROMPT.format(
        user_message=user_message,
        counter_args=counter_args,
    )
    
    return await generate_with_model(prompt, MODELS[2])  # Sonnet


async def run(user_message: str) -> str:
    """Pipeline complet dual-prompt : contre-args → synthèse."""
    counter_args = await generate_counter_arguments(user_message)
    if not counter_args:
        return ""
    
    synthesis = await generate_synthesis(user_message, counter_args)
    return synthesis or counter_args
