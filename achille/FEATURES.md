# Features — Achille

Liste des fonctionnalités actives. A mettre à jour à chaque modification du code.

Dernière mise à jour : 2026-03-22

---

## Conversation (bot/telegram_handler.py)

- [x] **Messages texte** — pipeline complet : classifier → context assembler → responder → sycophancy guard → réponse
- [x] **Sécurité** — seul AXEL_CHAT_ID peut interagir
- [x] **Historique SQLite** — conversations sauvegardées par jour, 10 derniers messages en contexte
- [x] **Découpage messages** — split automatique si > 4000 chars (limite Telegram)
- [x] **Commande /start** — message d'accueil
- [x] **Commande /status** — compteur messages jour/total
- [x] **Confirmations consolidation** — intercepte oui/non pour valider les changements de mémoire
- [ ] **Messages vocaux** — transcription Whisper (code présent, non testé)

## Intelligence (brain/)

- [x] **Classifier** (Haiku) — détecte sujet, couche (1-3), fichiers pertinents, conviction forte
- [x] **Context assembler** — charge SYSTEM_PROMPT + INDEX + contradictions + facts + fichiers du classifier
- [x] **Responder** — routage par couche : Haiku (C1), Sonnet (C2), Opus+thinking (C3)
- [x] **Dual-prompt** — contre-arguments auto sur convictions fortes C2-C3
- [x] **Sycophancy guard** — regex + compteur de validations par conversation

## Mémoire (memory/)

- [x] **Reader** — lit fichiers MD, strip frontmatter YAML, parse headers
- [x] **Writer** — écrit/append fichiers MD, auto-commit + push, commit ciblé
- [x] **Extractor** (Haiku, async) — post-conversation : extrait faits, contradictions, journal, croyances
- [x] **Consolidation state** — gère les questions en attente (oui/non) avec expiration 48h

## Consolidation nocturne (memory/consolidator.py)

- [x] **Dédoublonnage faits** (Opus) — détection sémantique, auto
- [x] **Archivage journaux** (Sonnet) — résumé 2-3 lignes, archive mensuelle, auto
- [x] **Split fichiers** (Opus) — découpe > 100 lignes en sous-fichiers avec frontmatter, auto
- [x] **Mise à jour INDEX.md** (Sonnet) — sync fichiers existants, auto
- [x] **Check contradictions** (Opus) — détection résolues, ping Telegram, assisté
- [x] **Check croyances** (Opus) — évolution confiance, ping Telegram, assisté
- [x] **Rapport** — JSON écrit sur le volume, lu par le briefing matin

## Messages proactifs (scheduler/heartbeat.py)

- [x] **Briefing matin** (7h30) — priorités + question du jour + rapport consolidation
- [x] **Check-in soir** (21h00) — question selon rotation (factuel/émotionnel/provocateur/exploratoire)
- [x] **Revue hebdo** (dimanche 18h) — résumé semaine + contradictions + questions
- [x] **Check inactivité** (8h/20h) — "silence radio" si 48h sans message

## Infrastructure

- [x] **Fly.io** — VM shared-cpu-1x, 256MB RAM, volume 1GB, region cdg
- [x] **CLIProxyAPI** — proxy OAuth vers abo Claude Max, dans le même container
- [x] **Git auto-commit/push** — mémoire MD pushée vers GitHub après chaque conversation
- [x] **Healthcheck Mac** — toutes les 6h, sync token + vérifie VM/proxy/git/bot (launchd)
- [ ] **Google Calendar** — intégration agenda (non implémenté)
- [ ] **Whisper** — transcription vocaux (code présent, non testé)
- [ ] **Déploiement auto** — CI/CD pour redéployer sur push (non implémenté)
