# Achille

Un daemon IA personnel qui apprend à te connaître progressivement, sans imposer de direction.

## Philosophie

Ce n'est PAS un système d'objectifs. C'est un miroir avec une mémoire.
Le dossier `open-questions/` est la feature principale, pas un bug.
Le fichier `SYCOPHANCY.md` empêche le daemon de devenir un yes-man.

## Structure

```
daemon-brain/
├── SYSTEM_PROMPT.md       ← L'âme du daemon (chargé à chaque session)
├── SYCOPHANCY.md          ← Protocole anti-sycophancy (chargé à chaque session)
├── INDEX.md               ← Carte du terrain (chargé à chaque session)
├── HEARTBEAT.md           ← Tâches proactives (lu par le cron)
├── sycophancy_log.md      ← Log des instances de sycophancy
├── profile/               ← Qui est Axel
│   ├── facts.md           ← Faits objectifs
│   ├── beliefs.md         ← Croyances avec niveau de confiance (1-5)
│   └── inherited.md       ← Croyances héritées identifiées
├── open-questions/        ← LE CŒUR DU SYSTÈME
│   ├── who-am-i.md        ← Questions identitaires ouvertes
│   ├── what-matters.md    ← Qu'est-ce qui compte vraiment
│   └── contradictions.md  ← Contradictions détectées (arme anti-biais)
├── work/                  ← Carrière et travail
│   ├── gitguardian.md     ← Contexte entreprise
│   ├── skills.md          ← Compétences et apprentissages
│   ├── current-sprint.md  ← Semaine en cours
│   └── career-direction.md← Exploration direction carrière
├── relations/
│   ├── julie.md           ← Dynamique couple
│   └── network.md         ← Relations clés
├── health/
│   ├── investigations.md  ← Fatigue, Lyme, mycotoxines, mercure
│   ├── fitness.md         ← Sport et physique
│   ├── cognitive.md       ← Capacités cognitives
│   └── mental.md          ← Psy, patterns émotionnels
├── projects/
│   ├── daemon.md          ← Ce projet
│   └── side-projects.md   ← StackDigest, micro-tools
├── experiments/
│   ├── active.md          ← Expériences en cours (pas des objectifs)
│   └── observations.md    ← Observations brutes
└── journal/
    └── YYYY-MM-DD.md      ← Entrées quotidiennes auto-générées
```

## Trois couches de maturité

- **Couche 1 (Suivi)** : Agenda, santé, sprint. Le daemon est directif.
- **Couche 2 (Orientation)** : Carrière, projets, lieu de vie. Le daemon challenge.
- **Couche 3 (Profondeur)** : Identité, relations, sens. Le daemon écoute et questionne.

## Stack technique

- Python daemon sur Oracle Cloud free tier
- Telegram Bot + Claude API (routing Haiku/Sonnet/Opus)
- Git auto-commit toutes les 30 min
- SQLite FTS5 pour la recherche (quand le volume le justifie)
