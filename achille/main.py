"""
Achille — Point d'entrée
Bot Telegram + Scheduler (briefing matin, check-in soir, revue hebdo)
"""
import sys
import os

# Ajouter le dossier achille au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.telegram_handler import create_app
from scheduler.cron_jobs import create_scheduler


def check_config():
    """Vérifie que la configuration est complète."""
    from config.settings import TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, AXEL_CHAT_ID, BRAIN_REPO_PATH
    
    errors = []
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN manquant")
    if not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY manquant")
    if not AXEL_CHAT_ID:
        errors.append("AXEL_CHAT_ID manquant")
    if not os.path.exists(BRAIN_REPO_PATH):
        errors.append(f"Brain repo introuvable: {BRAIN_REPO_PATH}")
    elif not os.path.exists(os.path.join(BRAIN_REPO_PATH, "INDEX.md")):
        errors.append(f"INDEX.md manquant dans {BRAIN_REPO_PATH}")
    
    if errors:
        for e in errors:
            print(f"ERREUR: {e}")
        sys.exit(1)
    
    print(f"Brain repo: {BRAIN_REPO_PATH}")
    print(f"Chat ID: {AXEL_CHAT_ID}")


def main():
    print("Achille démarrage...")
    check_config()
    
    # Scheduler (briefing matin, check-in soir, revue hebdo, inactivité)
    scheduler = create_scheduler()
    scheduler.start()
    
    jobs = scheduler.get_jobs()
    print(f"Scheduler: {len(jobs)} tâches programmées")
    for job in jobs:
        print(f"  - {job.name} → {job.trigger}")
    
    # Bot Telegram (polling bloquant — le scheduler tourne en arrière-plan)
    print("Achille en ligne.")
    app = create_app()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
