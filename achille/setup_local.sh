#!/bin/bash
# =============================================================
# Achille — Setup local (Mac)
# Utilise CLIProxyAPI pour passer par ton abo Claude Max
# =============================================================

set -e

echo "=== Achille — Setup local ==="
echo ""

# ----- 1. CLIProxyAPI -----
echo "--- 1/5 CLIProxyAPI ---"
echo ""

# Vérifier si CLIProxyAPI est déjà installé
if command -v cli-proxy-api &> /dev/null; then
    echo "CLIProxyAPI déjà installé."
else
    echo "Installation de CLIProxyAPI..."
    echo "Va sur https://github.com/router-for-me/CLIProxyAPI/releases"
    echo "Télécharge le binaire macOS (arm64 ou amd64 selon ta machine)"
    echo "Place-le dans /usr/local/bin/cli-proxy-api"
    echo ""
    echo "Ou via Homebrew si disponible:"
    echo "  brew install router-for-me/tap/cli-proxy-api"
    echo ""
    read -p "Appuie sur Entrée quand c'est fait..."
fi

# Authentifier CLIProxyAPI
echo ""
echo "Authentification OAuth (va ouvrir ton navigateur)..."
echo "Connecte-toi avec ton compte Claude (celui de GitGuardian)"
echo ""
cli-proxy-api auth login
echo ""
echo "Token OAuth sauvegardé dans ~/.cli-proxy-api/"

# Config CLIProxyAPI
mkdir -p ~/.cli-proxy-api
cat > ~/.cli-proxy-api/config.yaml << 'EOF'
host: "127.0.0.1"
port: 8317
auth-dir: "~/.cli-proxy-api"
api-keys: []
debug: false
EOF

echo "Config CLIProxyAPI écrite dans ~/.cli-proxy-api/config.yaml"
echo ""

# ----- 2. Brain repo -----
echo "--- 2/5 Brain repo ---"
echo ""

BRAIN_PATH="$HOME/achille-brain"
if [ -d "$BRAIN_PATH" ]; then
    echo "Brain repo existe déjà: $BRAIN_PATH"
    cd "$BRAIN_PATH" && git pull origin main
else
    echo "Clone du brain repo..."
    git clone git@github.com:Axel-KIRK/Achille.git "$BRAIN_PATH"
fi
echo ""

# ----- 3. Telegram Bot -----
echo "--- 3/5 Telegram Bot ---"
echo ""
echo "Si pas encore fait :"
echo "  1. Ouvre Telegram, cherche @BotFather"
echo "  2. Envoie /newbot"
echo "  3. Choisis un nom (ex: Achille) et un username (ex: achille_daemon_bot)"
echo "  4. Copie le token"
echo ""
read -p "Token Telegram bot : " TELEGRAM_TOKEN
echo ""
echo "Maintenant envoie un message à ton bot sur Telegram,"
echo "puis ouvre cette URL dans ton navigateur :"
echo "  https://api.telegram.org/bot${TELEGRAM_TOKEN}/getUpdates"
echo "Cherche \"chat\":{\"id\":XXXXXXX} dans la réponse."
echo ""
read -p "Ton chat ID : " CHAT_ID
echo ""

# ----- 4. Fichier .env -----
echo "--- 4/5 Configuration ---"
echo ""

ENV_FILE="$BRAIN_PATH/achille/.env"
cat > "$ENV_FILE" << EOF
TELEGRAM_BOT_TOKEN=${TELEGRAM_TOKEN}
AXEL_CHAT_ID=${CHAT_ID}
BRAIN_REPO_PATH=${BRAIN_PATH}

# CLIProxyAPI — pas besoin de clé API Anthropic
# On utilise le proxy local qui tape dans ton abo Max
CLIPROXY_BASE_URL=http://127.0.0.1:8317/v1

# OpenAI (Whisper) — optionnel, pour les vocaux
OPENAI_API_KEY=
EOF

echo ".env écrit dans $ENV_FILE"
echo ""

# ----- 5. Dépendances Python -----
echo "--- 5/5 Dépendances Python ---"
echo ""

cd "$BRAIN_PATH/achille"
pip install -r requirements.txt
pip install openai  # pour le client compatible CLIProxyAPI

echo ""
echo "=== Setup terminé ==="
echo ""
echo "Pour lancer Achille :"
echo "  Terminal 1 : cli-proxy-api serve"
echo "  Terminal 2 : cd $BRAIN_PATH/achille && python main.py"
echo ""
echo "Envoie un message à ton bot Telegram pour tester."
