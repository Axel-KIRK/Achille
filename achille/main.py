"""
Achille — Point d'entrée
"""
import sys
import os

# Ajouter le dossier achille au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.telegram_handler import create_app


def main():
    print("Achille démarrage...")
    
    # Vérifications
    from config.settings import TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, AXEL_CHAT_ID, BRAIN_REPO_PATH
    
    if not TELEGRAM_BOT_TOKEN:
        print("ERREUR: TELEGRAM_BOT_TOKEN manquant")
        sys.exit(1)
    if not ANTHROPIC_API_KEY:
        print("ERREUR: ANTHROPIC_API_KEY manquant")
        sys.exit(1)
    if not AXEL_CHAT_ID:
        print("ERREUR: AXEL_CHAT_ID manquant")
        sys.exit(1)
    if not os.path.exists(BRAIN_REPO_PATH):
        print(f"ERREUR: Brain repo introuvable: {BRAIN_REPO_PATH}")
        sys.exit(1)
    if not os.path.exists(os.path.join(BRAIN_REPO_PATH, "INDEX.md")):
        print(f"ERREUR: INDEX.md manquant dans {BRAIN_REPO_PATH}")
        sys.exit(1)
    
    print(f"Brain repo: {BRAIN_REPO_PATH}")
    print(f"Chat ID: {AXEL_CHAT_ID}")
    print("Achille en ligne.")
    
    app = create_app()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
