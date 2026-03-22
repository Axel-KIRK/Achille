# Projet Daemon (Couche 1)

## Stack technique décidée
- **Infra** : Oracle Cloud free tier (ARM A1, 4 CPU, 24GB RAM)
- **Bot** : Python + python-telegram-bot (async)
- **LLM** : Claude API (Haiku/Sonnet/Opus routing)
- **Mémoire** : Markdown dans Git repo privé, auto-commit
- **Recherche** : SQLite FTS5 + sqlite-vec (quand le volume le justifie)
- **Notifications** : Telegram natif + ntfy.sh (optionnel)
- **Voice** : Whisper API pour transcription vocaux Telegram
- **Intégrations** : Google Calendar API, GitLab API (Phase 2), Slack API (Phase 3)

## Base de code de départ
Fork de **claudegram** (github.com/roombawulf/claudegram) — Telegram + Claude API avec :
- Routage Haiku/Sonnet
- Mémoire persistante JSON
- Historique SQLite avec auto-summarization
- Prompt caching
- Streaming
- Fichier systemd

## Phases de build
1. ✅ Structure repo mémoire + system prompt + SYCOPHANCY.md
2. ⬜ Fork claudegram, adapter pour le daemon
3. ⬜ Intégrer le chargement dynamique des fichiers MD (INDEX → routing)
4. ⬜ Heartbeat (cron) pour briefings et check-ins
5. ⬜ Google Calendar integration
6. ⬜ GitLab API integration
7. ⬜ Voice input (Whisper)
8. ⬜ Écoute ambiante (Phase future — évaluer Bee/Limitless)

## Projets de référence étudiés
- danielmiessler/Personal_AI_Infrastructure (PAI) — hooks, mémoire 3 tiers
- roombawulf/claudegram — Telegram + Claude base
- davo20019/aidaemon — daemon personnel avec outils
- ComposioHQ/secure-openclaw — multi-messenger
- khoj-ai/khoj — second brain self-hosted
