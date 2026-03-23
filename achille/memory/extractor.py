"""
Achille — Extractor
Post-conversation : extrait faits, contradictions, et journal entry.
Tourne en async après l'envoi de la réponse.
"""
import json
from bot.notify import notify_error
from brain.responder import generate_with_model
from memory.reader import read
from memory.writer import append, append_journal_entry, auto_commit
from config.settings import EXTRACTOR_MODEL

EXTRACTION_PROMPT = """Analyse cette conversation entre Axel et son daemon Achille.

Message d'Axel :
<user_message>
{user_message}
</user_message>

Réponse d'Achille :
<response>
{response}
</response>

Croyances actuelles d'Axel :
<beliefs>
{beliefs}
</beliefs>

Contradictions connues :
<contradictions>
{contradictions}
</contradictions>

Retourne UNIQUEMENT un JSON valide :
{{
  "new_facts": [
    {{"content": "fait nouveau", "target_file": "chemin/fichier.md"}}
  ],
  "new_contradictions": [
    {{"statement_a": "citation A (avec date)", "statement_b": "citation B (avec date)", "tension": "description de la tension"}}
  ],
  "journal_summary": "résumé de 2-3 phrases de cette conversation pour le journal",
  "belief_updates": [
    {{"belief": "la croyance", "new_confidence": 1-5, "reason": "pourquoi le niveau change"}}
  ],
  "layer_changes": [
    {{"subject": "sujet", "old_layer": 2, "new_layer": 3, "reason": "pourquoi"}}
  ]
}}

Sois strict : ne retourne des contradictions que si elles sont RÉELLES (pas des nuances).
Ne retourne des faits que s'ils sont NOUVEAUX (pas déjà dans beliefs/facts).
journal_summary doit être factuel et court.
"""


async def extract_and_update(user_message: str, response: str, classification: dict) -> None:
    """Extraction post-conversation complète."""
    
    beliefs = read("profile/beliefs.md")
    contradictions = read("open-questions/contradictions.md")
    
    prompt = EXTRACTION_PROMPT.format(
        user_message=user_message,
        response=response,
        beliefs=beliefs,
        contradictions=contradictions,
    )
    
    try:
        result_text = await generate_with_model(prompt, EXTRACTOR_MODEL)
        
        # Nettoyer
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1].rsplit("```", 1)[0]
        
        result = json.loads(result_text)
        
        # 1. Nouveaux faits
        for fact in result.get("new_facts", []):
            if fact.get("content") and fact.get("target_file"):
                append(fact["target_file"], f"\n- {fact['content']}")
        
        # 2. Nouvelles contradictions
        for c in result.get("new_contradictions", []):
            entry = f"""
### {classification.get('subject', 'general')}
- **A** : {c.get('statement_a', '')}
- **B** : {c.get('statement_b', '')}
- **Tension** : {c.get('tension', '')}
- **Résolution** : Non résolu
"""
            append("open-questions/contradictions.md", entry)
        
        # 3. Journal
        summary = result.get("journal_summary", "")
        if summary:
            subject = classification.get("subject", "general")
            layer = classification.get("layer", 2)
            entry = f"**Sujet** : {subject} (Couche {layer})\n{summary}"
            append_journal_entry(entry)
        
        # 4. Git commit
        auto_commit(f"extract: {classification.get('subject', 'conversation')}")
    
    except (json.JSONDecodeError, Exception) as e:
        print(f"[extractor error] {e}")
        await notify_error("extractor", e, verbose=False)
        # Log minimal même en cas d'erreur
        append_journal_entry(f"Conversation sur {classification.get('subject', '?')} (extraction échouée)")
        auto_commit("extract: error fallback")
