"""
Achille — Configuration
Variables d'environnement dans .env
"""
import os

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
AXEL_CHAT_ID = int(os.environ.get("AXEL_CHAT_ID", "0"))

# CLIProxyAPI (proxy OpenAI-compatible → abo Claude Max)
CLIPROXY_BASE_URL = os.environ.get("CLIPROXY_BASE_URL", "http://127.0.0.1:8317/v1")

# OpenAI (Whisper) — optionnel, pour les vocaux
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# GitHub
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Paths
BRAIN_REPO_PATH = os.environ.get("BRAIN_REPO_PATH", os.path.expanduser("~/achille-brain"))

# Models par couche
MODELS = {
    1: "claude-haiku-4-5-20251001",
    2: "claude-sonnet-4-6",
    3: "claude-opus-4-6",
}

# Classifier toujours Haiku
CLASSIFIER_MODEL = "claude-haiku-4-5-20251001"

# Extraction post-conversation toujours Haiku
EXTRACTOR_MODEL = "claude-haiku-4-5-20251001"

# Context budget (tokens)
MAX_CONTEXT_TOKENS = 12000
MAX_HISTORY_MESSAGES = 10

# Scheduler
MORNING_BRIEFING_HOUR = 7
MORNING_BRIEFING_MINUTE = 30
EVENING_CHECKIN_HOUR = 21
EVENING_CHECKIN_MINUTE = 0
TIMEZONE = "Europe/Paris"

# Sycophancy
MAX_VALIDATIONS_PER_CONVERSATION = 3
