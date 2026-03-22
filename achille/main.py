"""
Achille — Point d'entrée
Bot Telegram + Scheduler (briefing matin, check-in soir, revue hebdo)
"""
import sys
import os

# Ajouter le dossier achille au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Charger .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from bot.telegram_handler import create_app
from scheduler.cron_jobs import create_scheduler


def check_config():
    """Vérifie que la configuration est complète."""
    from config.settings import TELEGRAM_BOT_TOKEN, CLIPROXY_BASE_URL, AXEL_CHAT_ID, BRAIN_REPO_PATH

    errors = []
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN manquant")
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
    print(f"Proxy: {CLIPROXY_BASE_URL}")


async def post_init(application):
    """Callback exécuté après le démarrage du bot, dans l'event loop."""
    scheduler = create_scheduler()
    scheduler.start()

    jobs = scheduler.get_jobs()
    print(f"Scheduler: {len(jobs)} tâches programmées")
    for job in jobs:
        print(f"  - {job.name} → {job.trigger}")

    print("Achille en ligne.")


def main():
    print("Achille démarrage...")
    check_config()

    # Bot Telegram avec scheduler démarré dans post_init (dans l'event loop)
    app = create_app(post_init_callback=post_init)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
