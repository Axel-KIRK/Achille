# HANDOFF.md — Briefing pour Claude Code

Tu reprends un projet en cours. Lis ce fichier en entier avant de faire quoi que ce soit.

## Contexte

Axel construit **Achille**, un daemon IA personnel sous forme de bot Telegram. Le code et la mémoire (fichiers Markdown) vivent dans le même repo GitHub : `git@github.com:Axel-KIRK/Achille.git`.

Le système a été designé dans une longue session sur claude.ai. Le code est écrit mais **jamais exécuté**. Il y aura des bugs. Ta mission est de le faire tourner en local sur le Mac d'Axel.

## Architecture en 30 secondes

```
Axel (Telegram) → Bot Python → Classifier (Haiku) → Context Assembler → Claude API → Sycophancy Guard → Réponse
                                                                              ↑
                                                      Fichiers MD (mémoire) ──┘
                                                              ↓
                                                   Post-traitement async (extraction faits, contradictions, git commit)
```

L'API Claude n'est PAS appelée directement. Tout passe par **CLIProxyAPI** — un proxy local (port 8317) qui expose un endpoint OpenAI-compatible et utilise le token OAuth de l'abonnement Claude Max d'Axel (payé par GitGuardian). Zéro coût API additionnel.

## Structure du repo

```
Achille/
├── achille/                    # Code Python du daemon
│   ├── main.py                 # Point d'entrée (bot + scheduler)
│   ├── .env.example            # Template des variables d'environnement
│   ├── requirements.txt        # Dépendances Python
│   ├── setup_local.sh          # Script de setup (interactif)
│   ├── bot/
│   │   ├── telegram_handler.py # Handler principal — orchestre le pipeline
│   │   ├── sender.py           # Envoi messages proactifs
│   │   └── voice.py            # Transcription Whisper
│   ├── brain/
│   │   ├── api_client.py       # Client OpenAI pointé vers CLIProxyAPI
│   │   ├── classifier.py       # Haiku — détermine sujet, couche, fichiers
│   │   ├── context_assembler.py # Assemble system prompt + mémoire + historique
│   │   ├── responder.py        # Appelle Claude via le proxy
│   │   ├── dual_prompt.py      # Contre-arguments auto (convictions C2-C3)
│   │   └── sycophancy_guard.py # Filtre anti-sycophancy avant envoi
│   ├── memory/
│   │   ├── reader.py           # Lit les fichiers MD
│   │   ├── writer.py           # Écrit les MD + git auto-commit
│   │   └── extractor.py        # Extraction post-conversation (async)
│   ├── scheduler/
│   │   ├── heartbeat.py        # Briefing matin, check-in soir, revue hebdo
│   │   └── cron_jobs.py        # Config APScheduler
│   ├── config/
│   │   └── settings.py         # Toute la config centralisée
│   └── systemd/
│       └── achille.service     # Pour déploiement Oracle Cloud (plus tard)
│
├── profile/                    # Fichiers mémoire Markdown
├── open-questions/
├── work/
├── relations/
├── health/
├── projects/
├── experiments/
├── journal/
├── INDEX.md                    # Carte du terrain — lu à chaque conversation
├── SYSTEM_PROMPT.md            # Le "cerveau" d'Achille
├── SYCOPHANCY.md               # Protocole anti-sycophancy
├── HEARTBEAT.md                # Tâches proactives
└── ARCHITECTURE.md             # Doc technique détaillée
```

## Ce qu'il faut faire pour déployer en local

### Étape 1 : CLIProxyAPI

CLIProxyAPI est un binaire qui proxy les appels OpenAI-compatible vers le CLI Claude Code.

```bash
# Installer
# Option A : depuis les releases GitHub
# https://github.com/router-for-me/CLIProxyAPI/releases
# Télécharger le binaire macOS arm64, le rendre exécutable, le mettre dans le PATH

# Option B : vérifier si un brew tap existe
brew search cli-proxy-api

# Authentifier (ouvre le navigateur — connexion Claude avec le compte GitGuardian)
cli-proxy-api auth login

# Configurer
mkdir -p ~/.cli-proxy-api
cat > ~/.cli-proxy-api/config.yaml << 'EOF'
host: "127.0.0.1"
port: 8317
auth-dir: "~/.cli-proxy-api"
api-keys: []
debug: false
EOF

# Lancer (dans un terminal dédié ou en background)
cli-proxy-api serve
```

**Vérifier que ça marche :**
```bash
curl http://127.0.0.1:8317/v1/models
# Doit retourner une liste de modèles Claude
```

### Étape 2 : Telegram Bot

```bash
# 1. Ouvrir Telegram, chercher @BotFather
# 2. Envoyer /newbot
# 3. Nom : Achille
# 4. Username : quelque chose d'unique, ex: achille_daemon_XXXX_bot
# 5. Copier le token

# 6. Envoyer un message au bot (n'importe quoi)
# 7. Récupérer le chat ID :
curl https://api.telegram.org/bot<TOKEN>/getUpdates | python3 -m json.tool | grep '"id"'
# Le premier "id" sous "chat" est le chat ID d'Axel
```

### Étape 3 : Clone et config

```bash
# Si pas déjà fait
git clone git@github.com:Axel-KIRK/Achille.git ~/achille-brain

# Créer le .env
cd ~/achille-brain/achille
cp .env.example .env

# Éditer .env avec les vraies valeurs :
# TELEGRAM_BOT_TOKEN=<token du BotFather>
# AXEL_CHAT_ID=<chat id récupéré>
# CLIPROXY_BASE_URL=http://127.0.0.1:8317/v1
# BRAIN_REPO_PATH=~/achille-brain  (le repo lui-même sert de brain)
```

**IMPORTANT** : `BRAIN_REPO_PATH` pointe vers la racine du repo (là où sont INDEX.md et les dossiers profile/, work/, etc.). C'est `~/achille-brain`, PAS `~/achille-brain/achille`.

### Étape 4 : Dépendances Python

```bash
cd ~/achille-brain/achille
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Étape 5 : Lancer

```bash
# Terminal 1 : le proxy
cli-proxy-api serve

# Terminal 2 : Achille
cd ~/achille-brain/achille
source .venv/bin/activate
python main.py
```

**Output attendu :**
```
Achille démarrage...
Brain repo: /Users/axel/achille-brain
Chat ID: XXXXXXX
Proxy: http://127.0.0.1:8317/v1
Scheduler: 4 tâches programmées
  - Briefing matin → cron[...]
  - Check-in soir → cron[...]
  - Revue hebdomadaire → cron[...]
  - Check inactivité → cron[...]
Achille en ligne.
```

Envoyer un message au bot Telegram pour tester.

## Problèmes probables et comment les résoudre

### Le code n'a jamais été exécuté

Il y aura des bugs. Probablement :

1. **Imports circulaires** — les modules se réfèrent les uns aux autres. Si ça plante au démarrage avec `ImportError`, refactorer les imports pour les rendre lazy (import inside function).

2. **async/sync mismatch** — certaines fonctions sont `async def` mais appelées sans `await`, ou l'inverse. Le classifier et le responder sont `async` mais `api_client.chat()` est synchrone (SDK OpenAI synchrone). Soit rendre `api_client` async avec `AsyncOpenAI`, soit wrapper les appels sync dans `asyncio.to_thread()`.

3. **BRAIN_REPO_PATH** — si les fichiers MD ne sont pas trouvés, vérifier que le path pointe bien vers la racine du repo (là où il y a INDEX.md), pas vers le dossier achille/.

4. **CLIProxyAPI format** — le proxy attend du format OpenAI (messages avec role system/user/assistant). Si les réponses sont vides ou erreur 400, c'est probablement un problème de format. Vérifier que `api_client.py` envoie bien le bon format.

5. **Modèles non reconnus** — CLIProxyAPI peut ne pas reconnaître les noms de modèles exacts. Tester avec `curl` d'abord :
```bash
curl http://127.0.0.1:8317/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet-4-6","messages":[{"role":"user","content":"test"}],"max_tokens":50}'
```
Si le modèle n'est pas reconnu, adapter les noms dans `config/settings.py` et `brain/api_client.py`.

6. **python-telegram-bot version** — la v21 a une API async. Si erreur avec `run_polling`, vérifier que c'est bien la v21+ installée.

### Si CLIProxyAPI n'existe pas ou ne marche pas

Alternative : utiliser directement le SDK Anthropic avec une clé API. Axel peut créer un compte sur console.anthropic.com, charger 10$ de crédits, et utiliser une `ANTHROPIC_API_KEY`. Dans ce cas :

1. Remplacer `api_client.py` par des appels directs via `import anthropic`
2. Remettre `anthropic` dans `requirements.txt`
3. Ajouter `ANTHROPIC_API_KEY` dans `.env`

Le code original (avant adaptation CLIProxyAPI) est dans l'historique Git, commit `97bc2f9`.

## Comment le code fonctionne (pour debug)

### Pipeline d'un message

```
telegram_handler.handle_message()
  ├── classifier.classify(message)           # Haiku → JSON {subject, layer, files}
  ├── context_assembler.build(classification) # Lit SYSTEM_PROMPT + INDEX + fichiers MD
  ├── [si conviction forte C2-3]
  │   └── dual_prompt.run(message)           # Sonnet → contre-arguments
  ├── responder.generate(context, message)   # Modèle selon couche
  ├── sycophancy_guard.check(response)       # Regex + compteur
  ├── telegram.send(response)                # Envoi
  └── [async] extractor.extract_and_update() # Extraction faits + git commit
```

### Flux de données

```
Message Axel → classifier → { layer: 2, files: ["work/career-direction.md"] }
                                  ↓
                    context_assembler charge :
                    - SYSTEM_PROMPT.md (toujours)
                    - INDEX.md (toujours)
                    - contradictions.md (toujours)
                    - facts.md (toujours)
                    - work/career-direction.md (du classifier)
                                  ↓
                    responder appelle Sonnet (layer 2) via CLIProxyAPI
                                  ↓
                    sycophancy_guard vérifie la réponse
                                  ↓
                    extractor (async) met à jour les MD + git commit
```

## Règles pour Claude Code

- Ne modifie PAS les fichiers MD (profile/, open-questions/, etc.) — c'est la mémoire d'Axel.
- Ne modifie PAS SYSTEM_PROMPT.md ni SYCOPHANCY.md — c'est le "cerveau", seul Axel décide des changements.
- Tu peux modifier tout le code Python dans achille/.
- Si tu crées de nouveaux fichiers, suis la structure existante.
- Commit avec des messages descriptifs en français.
- Si un bug est lié à CLIProxyAPI, propose d'abord un test curl isolé avant de changer le code.

## État actuel

- [x] Structure mémoire (27 fichiers MD)
- [x] System prompt v1
- [x] Protocole anti-sycophancy
- [x] Bot Telegram (handler, classifier, context assembler, responder)
- [x] Sycophancy guard
- [x] Memory reader/writer/extractor
- [x] Scheduler (briefing matin, check-in soir, revue hebdo)
- [x] Dual-prompt (contre-arguments)
- [x] Adaptation CLIProxyAPI
- [ ] **Premier lancement et debug** ← TU ES LÀ
- [ ] Intégration Google Calendar
- [ ] Voice transcription (Whisper)
- [ ] Déploiement Oracle Cloud
