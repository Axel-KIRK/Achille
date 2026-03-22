"""
Achille — Heartbeat
Lit HEARTBEAT.md et évalue les conditions pour envoyer des messages proactifs.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from brain.responder import generate_with_model
from brain.context_assembler import build
from memory.reader import read, read_index
from bot.sender import send_sync
from config.settings import (
    MODELS, TIMEZONE,
    MORNING_BRIEFING_HOUR, MORNING_BRIEFING_MINUTE,
    EVENING_CHECKIN_HOUR, EVENING_CHECKIN_MINUTE,
)

tz = ZoneInfo(TIMEZONE)


async def morning_briefing():
    """Briefing matin — agenda + priorités + question du jour."""
    
    sprint = read("work/current-sprint.md")
    beliefs = read("profile/beliefs.md")
    open_q = read("open-questions/what-matters.md")
    index = read_index()
    
    prompt = f"""Tu es Achille, le daemon d'Axel. Génère le briefing matin.
    
Règles :
- Max 150 mots
- Commence directement, pas de "Bonjour Axel" ou flatterie
- 1-2 priorités de la semaine
- 1 question liée à un sujet de Couche 2 ou 3 (tire de open-questions ou beliefs)
- Ton direct et concis

Contexte :
Sprint en cours : {sprint}
Croyances : {beliefs}
Questions ouvertes : {open_q}
INDEX : {index}
Date : {datetime.now(tz).strftime('%A %d %B %Y')}
"""
    
    response = await generate_with_model(prompt, MODELS[1])  # Haiku
    if response:
        send_sync(response)


async def evening_checkin():
    """Check-in du soir — question adaptée au contexte."""
    
    # Lire le journal du jour pour savoir ce qui s'est passé
    today = datetime.now(tz).strftime("%Y-%m-%d")
    journal = read(f"journal/{today}.md")
    contradictions = read("open-questions/contradictions.md")
    experiments = read("experiments/active.md")
    
    # Déterminer le type de check-in (rotation)
    day_of_week = datetime.now(tz).weekday()
    checkin_types = [
        "factual",      # lundi
        "emotional",    # mardi
        "provocateur",  # mercredi
        "exploratoire", # jeudi
        "factual",      # vendredi
        "emotional",    # samedi
        "exploratoire", # dimanche
    ]
    checkin_type = checkin_types[day_of_week]
    
    prompt = f"""Tu es Achille, le daemon d'Axel. Génère le check-in du soir.

Type de check-in : {checkin_type}
- factual : "Qu'est-ce que tu as fait aujourd'hui ?" ou variante
- emotional : "Comment tu te sens ce soir ?" ou variante
- provocateur : Signale une contradiction ou un écart entre intention et action
- exploratoire : Pose une question sur un sujet non abordé récemment

Règles :
- UNE seule question, courte
- Pas de flatterie, pas de "j'espère que tu as passé une bonne journée"
- Si provocateur, base-toi sur les contradictions ou le journal
- Ton naturel, comme un message Telegram entre humains

Journal du jour : {journal}
Contradictions connues : {contradictions}
Expériences actives : {experiments}
"""
    
    response = await generate_with_model(prompt, MODELS[1])  # Haiku
    if response:
        send_sync(response)


async def weekly_review():
    """Revue hebdomadaire — dimanche soir."""
    
    # Compiler les journaux de la semaine
    week_journals = []
    now = datetime.now(tz)
    for i in range(7):
        from datetime import timedelta
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        content = read(f"journal/{day}.md")
        if content and "[fichier introuvable" not in content:
            week_journals.append(content)
    
    contradictions = read("open-questions/contradictions.md")
    experiments = read("experiments/active.md")
    beliefs = read("profile/beliefs.md")
    
    prompt = f"""Tu es Achille. Génère le message d'ouverture de la revue hebdomadaire.

Règles :
- Résume ce qui s'est passé cette semaine (basé sur les journaux)
- Signale les contradictions détectées
- État des expériences en cours
- Pose 2-3 questions pour lancer la discussion
- Pas de flatterie. Factuel. Direct.
- Max 300 mots

Journaux de la semaine :
{chr(10).join(week_journals) if week_journals else "(aucune entrée cette semaine)"}

Contradictions : {contradictions}
Expériences : {experiments}
Croyances : {beliefs}
"""
    
    response = await generate_with_model(prompt, MODELS[2])  # Sonnet pour la revue
    if response:
        send_sync(response)


async def inactivity_check():
    """Vérifie si Axel est inactif depuis 48h."""
    import sqlite3
    from pathlib import Path
    from config.settings import BRAIN_REPO_PATH
    
    db_path = Path(BRAIN_REPO_PATH).parent / "achille_history.db"
    if not db_path.exists():
        return
    
    conn = sqlite3.connect(str(db_path))
    last_msg = conn.execute(
        "SELECT timestamp FROM messages WHERE role = 'user' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    
    if not last_msg:
        return
    
    from datetime import timedelta
    last_time = datetime.fromisoformat(last_msg[0])
    hours_since = (datetime.now() - last_time).total_seconds() / 3600
    
    if 48 <= hours_since < 72:
        send_sync("Silence radio depuis 2 jours. Tout va bien ?")
    # Après 72h : ne pas relancer (respecter l'espace)
