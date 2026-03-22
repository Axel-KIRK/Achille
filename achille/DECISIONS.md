# Decisions techniques — Achille

Historique des choix techniques et architecturaux. A consulter avant toute modification du code.

---

## D001 — CLIProxyAPI comme proxy Claude (2026-03-22)

**Contexte** : Achille a besoin d'appeler Claude. Axel a un abo Claude Max via GitGuardian.

**Options considérées** :
- A) API Anthropic directe (~10€/mois)
- B) CLIProxyAPI qui proxy via l'abo Max (gratuit)
- C) Tunnel depuis la VM vers le Mac local

**Choix** : B — CLIProxyAPI. Gratuit, fonctionne via OAuth avec auto-refresh toutes les 15 min.

**Consequence** : Le token OAuth expire. Un healthcheck sur le Mac d'Axel sync le token toutes les 6h vers Fly.io (`healthcheck.sh` + launchd).

---

## D002 — Fly.io au lieu d'Oracle Cloud (2026-03-22)

**Contexte** : Besoin d'un hébergement gratuit 24/7 pour le daemon.

**Options considérées** :
- Oracle Cloud free tier — inscription échouée
- Google Cloud e2-micro — trop de setup
- AWS t2.micro — 12 mois seulement
- Fly.io free tier — simple, `fly deploy`
- Mac local avec launchd — Mac doit rester allumé

**Choix** : Fly.io. Free tier (1 VM shared-cpu-1x, 256MB, 1GB volume), region cdg (Paris). Deploy en une commande.

**Consequence** : CLIProxyAPI tourne dans le même container (pas de service séparé). Volume persistant `/data` pour le repo brain, l'auth et la DB SQLite.

---

## D003 — Scheduler dans le post_init du bot (2026-03-22)

**Contexte** : APScheduler AsyncIOScheduler a besoin d'un event loop. `python-telegram-bot` v21 crée le sien dans `run_polling()`.

**Problème** : Démarrer le scheduler avant le bot causait `RuntimeError: no running event loop`.

**Choix** : Démarrer le scheduler dans le callback `post_init` de l'Application telegram, qui s'exécute dans l'event loop du bot.

**Consequence** : `create_app()` accepte un `post_init_callback`. Le scheduler est créé et démarré dedans.

---

## D004 — Consolidation mémoire : auto + assisté (2026-03-22)

**Contexte** : Les fichiers MD grossissent avec le temps. Sans consolidation, doublons, contradictions périmées, fichiers trop longs.

**Options considérées** :
- A) Tout automatique — risque de perte d'info
- B) Tout assisté — trop de pings Telegram
- C) Mix : auto pour le mécanique, assisté pour le sens

**Choix** : C. Dédoublonnage et archivage auto. Contradictions et croyances validées par Axel via Telegram (oui/non).

**Consequences** :
- Tourne à 3h du matin (Paris) — zéro concurrence avec l'extractor
- Max 2 pings Telegram par nuit
- Rapport intégré au briefing matin (7h30)
- Pending state dans `/data/consolidation_pending.json` (pas dans git)

---

## D005 — Opus pour le raisonnement, Sonnet pour la synthèse (2026-03-22)

**Contexte** : Quel modèle pour la consolidation ?

**Choix** : Opus (claude-opus-4-6) pour tout ce qui touche au sens (dédoublonnage, contradictions, croyances, splits). Sonnet (claude-sonnet-4-6) pour la synthèse mécanique (résumé journaux, mise à jour INDEX). Haiku uniquement pour le classifier et l'extractor temps réel.

**Raison** : La consolidation touche à la mémoire long-terme. Un mauvais résumé ou un doublon mal détecté est pire que pas de consolidation. La qualité prime sur le coût (gratuit via abo Max de toute façon).

---

## D006 — Split de fichiers en arbre avec frontmatter (2026-03-22)

**Contexte** : Les fichiers MD vont grossir. Comment les gérer ?

**Options considérées** :
- A) Split automatique en sous-fichiers quand > 100 lignes
- B) Compaction (réécrire le fichier sans les infos obsolètes)

**Choix** : A. Quand un fichier dépasse 100 lignes, Opus le découpe en sous-fichiers thématiques. Chaque fichier a un header YAML (description, keywords, last_consolidated, lines, parent).

**Consequences** :
- `reader.py` strip le frontmatter avant de passer le contenu au LLM
- `read_header()` permet au classifier de router sans ouvrir les fichiers
- INDEX.md est la source de vérité des fichiers existants
- L'ancien fichier est supprimé (reste dans git history)
- Validation Python : si le line count des splits diverge de > 5% de l'original, le split est annulé

---

## D007 — Pas de redirect files pour les splits (2026-03-22)

**Contexte** : Quand un fichier est splitté, le classifier pourrait pointer vers l'ancien path.

**Options considérées** :
- A) Fichier redirect ("splitté en → ...")
- B) Suppression directe, INDEX.md comme source de vérité

**Choix** : B. Les redirects ajoutent de la complexité (reader.py devrait les interpréter). INDEX.md est toujours à jour (mis à jour dans le même commit que le split). Si le classifier hallucine un chemin obsolète, `reader.py` retourne "[fichier introuvable]" — pas de crash.

---

## D008 — Journal : résumé + suppression (pas conservation) (2026-03-22)

**Contexte** : Les journaux quotidiens s'accumulent. Que faire des vieux ?

**Options considérées** :
- A) Résumé en 2-3 lignes dans une archive mensuelle + suppression du fichier
- B) Résumé + conservation du fichier original

**Choix** : A. Le résumé capture l'essentiel. Le fichier original reste dans l'historique git si besoin. Ca garde le repo léger.
