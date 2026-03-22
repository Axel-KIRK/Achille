# Déploiement local — Guide pas à pas

## Prérequis

- macOS avec Homebrew
- Claude Code déjà installé et authentifié (abo GitGuardian Max)
- Python 3.12+
- Un compte Telegram

## Étape 1 — Créer le bot Telegram (2 min)

1. Ouvre Telegram, cherche **@BotFather**
2. Envoie `/newbot`
3. Choisis un nom : `Achille`
4. Choisis un username : `achille_daemon_bot` (doit finir par `_bot`)
5. **Copie le token** qu'il te donne

Pour trouver ton **chat ID** :
1. Envoie un message à ton nouveau bot
2. Va sur `https://api.telegram.org/bot<TON_TOKEN>/getUpdates`
3. Cherche `"chat":{"id":XXXXXXXX}` — c'est ton chat ID

## Étape 2 — Installer CLIProxyAPI (3 min)

```bash
# Installer
brew tap router-for-me/tap
brew install cliproxyapi

# Login avec ton compte Claude (celui de GitGuardian)
cliproxyapi --claude-login
# → S'ouvre dans le navigateur, tu autorises, c'est fait

# Créer la config
mkdir -p ~/.cli-proxy-api
cat > ~/.cli-proxy-api/config.yaml << 'EOF'
port: 8317
remote-management:
  allow-remote: false
  secret-key: ""
auth-dir: "~/.cli-proxy-api"
auth:
  providers: []
debug: false
EOF

# Lancer (en arrière-plan)
brew services start cliproxyapi

# Vérifier que ça marche
curl -s http://127.0.0.1:8317/v1/models \
  -H "Authorization: Bearer test" | python3 -m json.tool
```

Tu devrais voir la liste des modèles Claude disponibles.

## Étape 3 — Cloner et configurer Achille (3 min)

```bash
# Cloner le repo (les fichiers mémoire)
cd ~
git clone git@github.com:Axel-KIRK/Achille.git achille-brain

# Créer le .env
cd achille-brain/achille
cp .env.example .env
```

Édite `.env` :
```
TELEGRAM_BOT_TOKEN=<le token de BotFather>
AXEL_CHAT_ID=<ton chat ID>

# CLIProxyAPI — pas besoin de vraie clé
PROXY_BASE_URL=http://127.0.0.1:8317/v1
PROXY_API_KEY=dummy

# Pas besoin de ANTHROPIC_API_KEY ni OPENAI_API_KEY pour le MVP

# Path vers les fichiers mémoire
BRAIN_REPO_PATH=/Users/<ton_user>/achille-brain
```

## Étape 4 — Installer les dépendances Python (1 min)

```bash
cd ~/achille-brain/achille
pip install -r requirements.txt
```

## Étape 5 — Lancer Achille (10 sec)

```bash
cd ~/achille-brain/achille
python main.py
```

Tu devrais voir :
```
Achille démarrage...
Brain repo: /Users/.../achille-brain
Chat ID: XXXXXXXX
Scheduler: 4 tâches programmées
  - Briefing matin → cron[...]
  - Check-in soir → cron[...]
  - Revue hebdomadaire → cron[...]
  - Check inactivité → cron[...]
Achille en ligne.
```

## Étape 6 — Tester

Envoie un message à ton bot sur Telegram. Par exemple :
- "Salut Achille" → devrait répondre selon le SYSTEM_PROMPT
- "Comment avance mon projet daemon ?" → devrait charger `projects/daemon.md`
- "Je me demande si je devrais quitter mon job" → devrait passer en mode Couche 2-3

## Architecture locale

```
Ta machine Mac
│
├── CLIProxyAPI (port 8317)
│   └── Authentifié via ton OAuth Claude Code (abo GitGuardian)
│   └── Expose endpoint OpenAI-compatible
│
├── Achille daemon (Python)
│   └── Telegram polling
│   └── Appelle http://localhost:8317/v1/chat/completions
│   └── Lit/écrit dans ~/achille-brain/
│
└── ~/achille-brain/ (repo Git)
    └── Tous les fichiers MD mémoire
    └── Auto-commit + push vers GitHub
```

## Problèmes courants

### CLIProxyAPI ne répond pas
```bash
# Vérifier qu'il tourne
brew services list | grep cliproxyapi
# Relancer si besoin
brew services restart cliproxyapi
```

### Token OAuth expiré
```bash
cliproxyapi --claude-login
# Re-autoriser dans le navigateur
```

### Bot Telegram ne répond pas
- Vérifie que le AXEL_CHAT_ID est correct
- Vérifie que le bot est démarré (`python main.py` tourne)
- Regarde les logs dans le terminal

## Pour plus tard : Docker (simuler Oracle Cloud)

```bash
# Dockerfile fourni dans achille/
docker build -t achille .
docker run -d \
  --env-file .env \
  -v ~/.cli-proxy-api:/root/.cli-proxy-api \
  -v ~/achille-brain:/root/achille-brain \
  --network host \
  achille
```

Note : `--network host` est nécessaire pour que le container accède à CLIProxyAPI sur localhost:8317.
