# Achille — Architecture technique

## Structure du projet

```
achille/
├── bot/
│   ├── __init__.py
│   ├── telegram_handler.py    # Réception messages Telegram (webhook)
│   ├── voice.py               # Whisper transcription
│   └── sender.py              # Envoi messages + notifications
│
├── brain/
│   ├── __init__.py
│   ├── classifier.py          # Haiku — détecte sujet, couche, fichiers
│   ├── context_assembler.py   # Lit INDEX.md → charge les bons fichiers
│   ├── model_router.py        # Couche 1→Haiku, 2→Sonnet, 3→Opus+thinking
│   ├── dual_prompt.py         # Génère contre-arguments sur sujets C2-C3
│   ├── sycophancy_guard.py    # Vérifie la réponse avant envoi
│   └── responder.py           # Appel Claude API final
│
├── memory/
│   ├── __init__.py
│   ├── reader.py              # Lit les fichiers MD depuis le repo
│   ├── writer.py              # Écrit/met à jour les fichiers MD
│   ├── extractor.py           # Post-conversation : extraire faits, contradictions
│   ├── consolidator.py        # Mensuel : résumer les vieux fichiers
│   └── git_ops.py             # Auto-commit + push
│
├── integrations/
│   ├── __init__.py
│   ├── google_calendar.py     # Lecture agenda via API
│   ├── gitlab_activity.py     # Résumé MRs, commits (futur)
│   └── slack_digest.py        # Résumé channels (futur)
│
├── scheduler/
│   ├── __init__.py
│   ├── heartbeat.py           # Lit HEARTBEAT.md, évalue les conditions
│   ├── cron_jobs.py           # Briefing matin, check-in soir, revue hebdo
│   └── triggers.py            # Détection patterns (post-psy, stress, inactivité)
│
├── config/
│   ├── settings.py            # Tokens, paths, modèles par couche
│   └── costs.py               # Tracking coûts API
│
├── brain-repo/                # ← clone du repo Achille (les fichiers MD)
│   ├── INDEX.md
│   ├── SYSTEM_PROMPT.md
│   ├── SYCOPHANCY.md
│   ├── HEARTBEAT.md
│   ├── profile/
│   ├── open-questions/
│   ├── work/
│   ├── relations/
│   ├── health/
│   ├── projects/
│   ├── experiments/
│   └── journal/
│
├── main.py                    # Point d'entrée
├── requirements.txt
├── Dockerfile
└── systemd/
    └── achille.service        # Service systemd pour Oracle Cloud
```

## Pipeline d'un message

### Étape 1 : Réception (telegram_handler.py)

```python
async def handle_message(update):
    text = update.message.text
    
    # Si c'est un vocal, transcrire
    if update.message.voice:
        text = await voice.transcribe(update.message.voice)
    
    # Classifier le message
    classification = await classifier.classify(text)
    # → { subject: "julie", layer: 3, files: ["relations/julie.md", "profile/beliefs.md"], 
    #     mood: "reflective", is_strong_conviction: false }
    
    # Assembler le contexte
    context = await context_assembler.build(classification)
    
    # Router vers le bon modèle
    model = model_router.select(classification.layer)
    
    # Dual-prompt si conviction forte sur C2-C3
    if classification.is_strong_conviction and classification.layer >= 2:
        counter_args = await dual_prompt.generate(text, context)
        context.add_counter_arguments(counter_args)
    
    # Générer la réponse
    response = await responder.generate(text, context, model)
    
    # Vérifier la sycophancy
    response = await sycophancy_guard.check(response, context)
    
    # Envoyer
    await sender.send(update.chat_id, response)
    
    # Post-traitement async (ne bloque pas la réponse)
    asyncio.create_task(post_process(text, response, classification))
```

### Étape 2 : Classification (classifier.py)

Un appel Haiku (~0.001$) qui analyse le message entrant et retourne :
- **subject** : le sujet principal (julie, boulot, santé, existentiel, daemon, etc.)
- **layer** : 1, 2 ou 3 (déterminé en croisant le sujet avec INDEX.md)
- **files** : liste des fichiers MD à charger
- **mood** : factuel, émotionnel, réflexif, urgence
- **is_strong_conviction** : est-ce qu'Axel affirme quelque chose avec force ?
- **contradiction_check** : mots-clés à vérifier contre contradictions.md

```python
CLASSIFIER_PROMPT = """Tu es un routeur de contexte. Analyse ce message et retourne un JSON.

INDEX.md actuel :
{index_content}

Message d'Axel :
{message}

Retourne UNIQUEMENT un JSON :
{
  "subject": "string",
  "layer": 1|2|3,
  "files": ["path/file.md", ...],
  "mood": "factual|emotional|reflective|urgent",
  "is_strong_conviction": true|false,
  "keywords_for_contradiction_check": ["mot1", "mot2"]
}
"""
```

### Étape 3 : Assemblage du contexte (context_assembler.py)

Le budget token est clé. Voici la répartition :

| Composant | Budget | Chargé quand |
|-----------|--------|--------------|
| SYSTEM_PROMPT.md | ~2000 tokens | Toujours |
| SYCOPHANCY.md (résumé) | ~500 tokens | Toujours |
| INDEX.md | ~800 tokens | Toujours |
| contradictions.md | ~500 tokens | Toujours |
| profile/facts.md | ~400 tokens | Toujours |
| Fichiers pertinents (2-4) | ~3000 tokens | Selon classifier |
| Historique conversation | ~4000 tokens | Derniers 10 messages |
| **Total** | **~11000 tokens** | |

Ça laisse ~100K tokens pour la réponse + thinking sur Opus.

```python
async def build(classification):
    context = Context()
    
    # Toujours chargés
    context.add_system(read("SYSTEM_PROMPT.md"))
    context.add_system(read("SYCOPHANCY.md", summary=True))
    context.add_context(read("INDEX.md"))
    context.add_context(read("open-questions/contradictions.md"))
    context.add_context(read("profile/facts.md"))
    
    # Fichiers pertinents
    for f in classification.files:
        context.add_context(read(f))
    
    # Historique (SQLite — derniers messages de cette conversation)
    context.add_history(get_recent_messages(limit=10))
    
    # Budget check — si > 12000 tokens, résumer les fichiers les plus longs
    context.trim_to_budget(12000)
    
    return context
```

### Étape 4 : Routeur de modèles (model_router.py)

```python
MODELS = {
    1: "claude-haiku-4-5-20251001",     # Couche 1 : rapide, pas cher
    2: "claude-sonnet-4-6",              # Couche 2 : bon équilibre
    3: "claude-opus-4-6",                # Couche 3 : profond, extended thinking
}

def select(layer, override=None):
    if override:
        return override
    return MODELS.get(layer, MODELS[2])

# Extended thinking activé automatiquement pour Couche 3
def get_params(layer):
    params = {"model": select(layer)}
    if layer == 3:
        params["thinking"] = {"type": "enabled", "budget_tokens": 10000}
    return params
```

### Étape 5 : Dual-prompt (dual_prompt.py)

Déclenché quand `is_strong_conviction = true` ET `layer >= 2`.

```python
async def generate(user_message, context):
    # Appel 1 : Générer les contre-arguments (Sonnet, pas besoin d'Opus)
    counter_prompt = f"""Axel vient de dire : "{user_message}"

Contexte de ses croyances : {context.beliefs_summary}

Génère les 3 contre-arguments les plus forts à cette position.
Sois factuel. Cite des contradictions si tu en trouves dans le contexte.
PAS de validation de la position d'Axel."""

    counter_args = await call_claude(counter_prompt, model="sonnet")
    return counter_args
```

### Étape 6 : Sycophancy guard (sycophancy_guard.py)

Vérifie la réponse AVANT de l'envoyer.

```python
SYCOPHANCY_PATTERNS = [
    r"^(Bonne|Excellente|Super|Très bonne) (question|observation|remarque|idée)",
    r"^(C'est|Voilà) (une? )?(très )?(bon|bonne|excellente)",
    r"Tu as (tout à fait |complètement |absolument )?raison",
    r"Je comprends (parfaitement |tout à fait )?(ce que tu ressens|ta frustration)",
    r"C'est normal de (ressentir|penser|vouloir)",
    r"Tu es sur la bonne voie",
]

# Compteur de validations par conversation
validation_count = 0

async def check(response, context):
    global validation_count
    
    # Check patterns interdits
    for pattern in SYCOPHANCY_PATTERNS:
        if re.match(pattern, response, re.IGNORECASE):
            response = re.sub(pattern, "", response).strip()
            log_sycophancy("pattern_removed", pattern)
    
    # Check compteur de validations
    if is_validation(response):
        validation_count += 1
        if validation_count > 3:
            # Forcer l'ajout d'un contre-argument
            counter = await generate_quick_counter(response, context)
            response += f"\n\nCela dit — {counter}"
            log_sycophancy("forced_counter", response)
    
    return response
```

### Étape 7 : Post-traitement (extractor.py)

Après chaque conversation (async, ne bloque pas) :

```python
async def post_process(user_message, response, classification):
    # 1. Extraire les faits nouveaux
    facts = await extract_facts(user_message, response)
    for fact in facts:
        await writer.append_to_file(fact.target_file, fact.content)
    
    # 2. Détecter les contradictions
    contradictions = await detect_contradictions(
        user_message, 
        read("open-questions/contradictions.md"),
        read("profile/beliefs.md")
    )
    for c in contradictions:
        await writer.append_to_file("open-questions/contradictions.md", c)
    
    # 3. Journal entry
    entry = await generate_journal_entry(user_message, response, classification)
    today = datetime.now().strftime("%Y-%m-%d")
    await writer.append_to_file(f"journal/{today}.md", entry)
    
    # 4. Git commit
    await git_ops.auto_commit(f"conversation: {classification.subject}")
```

## Scheduler / Heartbeat (scheduler/)

### Heartbeat (toutes les 30 min)

```python
# heartbeat.py
async def tick():
    now = datetime.now()
    heartbeat = read("HEARTBEAT.md")
    
    # Parse les tâches et conditions
    tasks = parse_heartbeat(heartbeat)
    
    for task in tasks:
        if task.should_trigger(now):
            # Assembler le contexte pertinent pour cette tâche
            context = await context_assembler.build_for_task(task)
            
            # Évaluer si ça vaut le coup de notifier
            decision = await classifier.should_notify(task, context)
            
            if decision.notify:
                message = await responder.generate_proactive(task, context)
                await sender.send(AXEL_CHAT_ID, message)
```

### Cron jobs

```python
# cron_jobs.py
schedule = {
    "morning_briefing": "0 7 30 * * *",    # 07:30 tous les jours
    "evening_checkin":  "0 21 0 * * *",     # 21:00 tous les jours
    "weekly_review":    "0 18 0 * * 0",     # 18:00 le dimanche
    "monthly_syco":     "0 10 0 1 * *",     # 10:00 le 1er du mois
    "consolidation":    "0 3 0 15 * *",     # 03:00 le 15 du mois
}
```

### Briefing matin

```python
async def morning_briefing():
    # Google Calendar
    events = await google_calendar.get_today()
    
    # Priorités de la semaine
    sprint = read("work/current-sprint.md")
    
    # Question du jour (Couche 2-3, rotation)
    question = await pick_daily_question()
    
    # Générer le briefing (Haiku — court et factuel)
    briefing = await responder.generate(
        prompt=f"""Briefing matin pour Axel. Max 150 mots.
        Agenda : {events}
        Sprint : {sprint}
        Question du jour : {question}""",
        model="haiku"
    )
    
    await sender.send(AXEL_CHAT_ID, briefing)
```

## Stack technique

### Dépendances Python

```
python-telegram-bot==21.x    # Async Telegram bot
anthropic==0.40.x            # Claude API
google-api-python-client     # Google Calendar
google-auth-oauthlib         # OAuth flow
openai                       # Whisper API (ou faster-whisper local)
apscheduler                  # Cron jobs
aiohttp                      # HTTP async
gitpython                    # Git operations
```

### Hébergement

**Oracle Cloud Always Free** :
- 1x ARM VM (2 OCPU, 12 GB RAM) — largement suffisant
- Ubuntu 24.04, Python 3.12, systemd
- Le repo `brain-repo/` est cloné sur la VM
- Git push vers GitHub toutes les 30 min (ou à chaque commit)

### Coûts API estimés (par mois)

| Usage | Modèle | Appels/mois | Coût estimé |
|-------|--------|-------------|-------------|
| Classification | Haiku | ~900 (30/jour) | ~$0.90 |
| Conversations C1 | Haiku | ~300 | ~$0.30 |
| Conversations C2 | Sonnet | ~200 | ~$3.00 |
| Conversations C3 | Opus + thinking | ~50 | ~$5.00 |
| Dual-prompt | Sonnet | ~30 | ~$0.45 |
| Briefings/check-ins | Haiku | ~60 | ~$0.06 |
| Post-traitement | Haiku | ~900 | ~$0.90 |
| **Total** | | | **~$10.65/mois** |

Avec prompt caching (90% réduction sur le contexte répété), le coût réel serait probablement **~$3-5/mois**.

## Déploiement (MVP)

```bash
# Sur la VM Oracle Cloud
git clone git@github.com:Axel-KIRK/Achille.git brain-repo
pip install -r requirements.txt
cp config/settings.example.py config/settings.py
# Éditer settings.py avec les tokens

# Lancer
python main.py

# Ou via systemd
sudo cp systemd/achille.service /etc/systemd/system/
sudo systemctl enable achille
sudo systemctl start achille
```

## Ordre de build recommandé

### Sprint 1 — Le minimum viable (1 weekend)
1. `telegram_handler.py` — recevoir un message
2. `context_assembler.py` — charger SYSTEM_PROMPT + INDEX + fichiers
3. `responder.py` — appeler Claude, renvoyer la réponse
4. `memory/reader.py` — lire les fichiers MD
→ **Résultat** : tu peux parler à Achille via Telegram avec le contexte complet

### Sprint 2 — L'intelligence (1 weekend)
5. `classifier.py` — routage automatique
6. `model_router.py` — bon modèle par couche
7. `sycophancy_guard.py` — vérification avant envoi
8. `memory/writer.py` + `extractor.py` — mise à jour des fichiers après conversation
9. `git_ops.py` — auto-commit
→ **Résultat** : Achille route intelligemment, se protège de la sycophancy, et met à jour sa mémoire

### Sprint 3 — La proactivité (1 weekend)
10. `heartbeat.py` + `cron_jobs.py` — briefing matin, check-in soir
11. `google_calendar.py` — intégration agenda
12. `triggers.py` — détection patterns (post-psy, stress, inactivité)
→ **Résultat** : Achille t'envoie des messages de lui-même

### Sprint 4 — Le polish (itératif)
13. `voice.py` — transcription vocale
14. `dual_prompt.py` — contre-arguments automatiques
15. `consolidator.py` — nettoyage mémoire mensuel
16. `costs.py` — monitoring des coûts
→ **Résultat** : système complet
