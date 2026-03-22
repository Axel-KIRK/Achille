# HEARTBEAT.md — Tâches proactives du Daemon

Ce fichier est lu par le heartbeat toutes les 30 minutes.
Le daemon évalue chaque condition et décide silencieusement s'il y a quelque chose à communiquer.
La plupart du temps : HEARTBEAT_OK (rien à signaler).

## Routines quotidiennes

### Briefing matin — 07:30
- Lire Google Calendar pour la journée
- Identifier les 1-2 priorités de la semaine
- Choisir 1 question/rappel de Couche 2-3
- Envoyer via Telegram (max 150 mots)

### Check-in du soir — 21:00
- Choisir le type de check-in (factuel / émotionnel / provocateur / exploratoire)
- Alterner les types — ne pas faire le même 2 jours de suite
- Envoyer la question d'amorce via Telegram
- Attendre la réponse — ne pas relancer avant le lendemain

## Routines hebdomadaires

### Revue hebdo — Dimanche 18:00
- Compiler les entrées journal de la semaine
- Identifier les contradictions
- Préparer les questions de revue
- Lancer la conversation via Telegram

### Mise à jour INDEX.md — Dimanche 20:00 (après revue)
- Vérifier que les niveaux de couche sont à jour
- Archiver les entrées journal de plus de 30 jours (résumer → déplacer)

## Routines mensuelles

### Auto-revue sycophancy — 1er dimanche du mois
- Lire `sycophancy_log.md`
- Compter les instances
- Identifier les patterns
- Proposer des ajustements au protocole

### Consolidation mémoire — 15 du mois
- Identifier les fichiers mémoire qui grossissent trop (>2000 tokens)
- Résumer les entrées anciennes
- Déplacer les insights consolidés

## Conditions événementielles

### Post-séance psy
- Quand Axel envoie un message contenant "psy", "séance", "psychanalyse" ou "thérapeute"
- Passer en mode écoute (OARS)
- Le lendemain à 12:00, envoyer 1 question de suivi

### Détection de stress
- Si 3 check-ins consécutifs montrent un pattern négatif
- Signaler le pattern à Axel (pas diagnostiquer — observer)
- Proposer d'en parler ou de le noter pour la prochaine séance psy

### Inactivité
- Si aucun message depuis 48h en semaine
- Envoyer un ping simple : "Hey. Silence radio depuis 2 jours. Tout va bien ?"
- Si aucune réponse après 24h supplémentaires : ne pas relancer (respecter l'espace)

## Heures actives

- Pas de message avant 07:00
- Pas de message après 22:00
- Weekend : pas de messages liés au travail sauf si initié par Axel
