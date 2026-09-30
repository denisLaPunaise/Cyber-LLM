# Architecture de Cyber-LLM

Ce document explique **comment le projet est construit** et **comment chaque
version fonctionne**. Il sert de référence technique (et de support pour
présenter le projet).

---

## Philosophie

Cyber-LLM est un **copilote de pentest**, pas un outil qui attaque tout seul.
L'utilisateur colle la sortie d'une commande, l'assistant raisonne avec lui et
**propose** les étapes suivantes selon la méthodologie de pentest.
**L'humain garde toujours la décision et exécute lui-même les commandes.**
Cadre d'usage : **labs autorisés uniquement** (TryHackMe, HackTheBox, CTF).

On n'entraîne aucun modèle : on **oriente** un modèle existant (API Claude) avec
un prompt système qui joue le rôle de « méthodologie ».

---

## Vue d'ensemble des modules

| Fichier | Rôle |
|---|---|
| `src/config.py` | Lit le `.env`, expose les réglages (modèle, effort, workspace) et les valide. |
| `src/llm_client.py` | **Seul** point qui parle à l'API Claude. Cache, réflexion, gestion des erreurs/refus. |
| `src/memoire.py` | Mémoire de session : l'historique des échanges. |
| `src/fiche.py` | Fiche machine : état structuré de la box + sauvegarde/chargement. |
| `src/assistant.py` | La « colle » : charge le prompt, encadre l'entrée, met à jour mémoire et fiche. |
| `src/cli.py` | Interface interactive : boucle, commandes, affichage. |
| `prompts/system_pentest.md` | Le « cerveau » : rôle, cadre, méthodologie, format de réponse. |

### Le trajet d'une requête (état actuel)

```
Toi (terminal)
  │  colle une sortie + END      (ou une commande : help/fiche/sauver/charger/nouvelle/quit)
  ▼
cli.py            boucle, dispatch des commandes, crée mémoire + fiche
  │  analyser(entrée, mémoire, fiche)
  ▼
assistant.py      charge le prompt, encadre l'entrée (contexte "lab autorisé"),
  │               réinjecte la fiche si reprise de session, assemble historique + message
  ▼
llm_client.py     pose le cache (prompt système + dernier message), appelle l'API,
  │               gère erreurs et refus, renvoie Reponse(texte, succès)
  ▼
API Claude        (Opus 4.8, réflexion "adaptive" + effort) répond au format impose :
  │               [ANALYSE] / [PISTES] / [AVANT D'AGIR] / [FICHE MACHINE]
  ▼
retour            assistant sépare la fiche (rangée de côté) de la partie visible
                  (affichée), et mémorise l'échange complet
```

`config.py` alimente `llm_client.py` avec les réglages lus dans `.env`.

---

## V0 — Le copilote de base

**Ce que ça fait :** tu colles une sortie de commande, tu reçois des pistes
priorisées avec les commandes prêtes. Zéro mémoire, zéro autonomie.

**Comment c'est fait — les 3 briques :**
1. **Un LLM déjà entraîné** (API Claude) → `llm_client.py`.
2. **Un prompt système** = la méthodologie → `prompts/system_pentest.md`.
3. **Une boucle d'interaction** → `cli.py`.

**Détail des pièces :**
- `config.py` lit le `.env` (`python-dotenv`) et expose `MODEL`, `EFFORT`,
  `WORKSPACE_ID`, `MAX_TOKENS`. `check_config()` renvoie un message clair si la
  clé ou le modèle manquent.
- `llm_client.py` construit la requête (`model`, `system`, `messages`,
  `thinking={"type":"adaptive"}`, `output_config={"effort":...}`) et **attrape
  chaque type d'erreur** (clé, workspace, réseau, 400…) ainsi que le **refus**
  du classifieur de sûreté, au lieu de planter.
- `assistant.py` charge le prompt et **encadre** l'entrée avec un contexte
  « je m'entraîne sur un lab autorisé » → moins de refus, meilleures réponses.
- `cli.py` gère la boucle : lecture multi-lignes jusqu'à `END`, affichage.
- Le prompt impose le format **[ANALYSE] / [PISTES] / [AVANT D'AGIR]**.

**Décisions clés :**
- **Modèle Opus 4.8** : les modèles plus récents (Opus 5 / 5.5) refusent souvent
  le contenu sécurité de labs (classifieur « cyber » plus strict). Choix validé
  empiriquement (5.5 ✗, 5 ✗, 4.8 ✓).
- **Config dans `.env`** : secrets et réglages hors du code, jamais commités.
- **Un seul point d'accès à l'API** (`llm_client`) : on pourra changer de
  fournisseur (API → Ollama local) sans toucher au reste.

---

## V1 — Mémoire de session + prompt caching

**Ce que ça ajoute :** l'assistant se **souvient** de toute la session, et les
requêtes coûtent moins cher grâce au **caching**.

**La mémoire :**
- `memoire.py` : classe `Memoire` = une liste de messages
  `{"role": "user"/"assistant", "content": ...}` (le format exact de l'API).
- `llm_client.ask()` reçoit désormais **tout l'historique** au lieu d'un seul
  message, et renvoie un objet **`Reponse(texte, succès)`**.
- `assistant.analyser()` n'enregistre l'échange **que si l'appel a réussi**.
  Raison : l'API exige que les rôles **alternent** (user → assistant → user…) ;
  garder une entrée sans réponse valable casserait le tour suivant. On mémorise
  donc la paire question+réponse **ensemble, ou rien**.

**Point important à comprendre :** l'API est **sans mémoire** de son côté. C'est
nous qui renvoyons l'historique complet à chaque tour. Le coût grossit donc au
fil de la session — d'où le caching.

**Le caching :**
- Le **prompt système** (stable) et le **dernier message** portent un marqueur
  `cache_control`.
- Au tour suivant, tout le début identique de la conversation est **relu depuis
  le cache** d'Anthropic (~10 % du prix) au lieu d'être recalculé.
- On est parfaitement configurés pour ça : prompt stable + historique en **ajout
  seul** (on n'édite jamais le passé). Un helper prépare une copie des messages
  **sans jamais muter la mémoire**.
- Effet : une box passe d'environ **1,85 $ à ~1,00 $**.

---

## V2 — Fiche machine + persistance + aide

**Ce que ça ajoute :** un **état structuré** de la box, consultable, sauvegardable,
et rechargeable pour reprendre plus tard.

**La fiche :**
- Le modèle termine **chaque réponse** par un bloc `[FICHE MACHINE]` cumulatif
  (cible, ports/services, utilisateurs, identifiants, accès, à explorer).
- `fiche.py` → `separer()` **découpe** la réponse : la partie visible
  (`[ANALYSE]/[PISTES]/[AVANT D'AGIR]`) est affichée, le bloc fiche est **rangé
  de côté**. La réponse complète (fiche incluse) reste en mémoire pour que le
  modèle garde sa fiche en tête d'un tour à l'autre.
- Si le modèle oublie le bloc, on **garde la fiche précédente** (robuste).

**Choix de conception :** c'est **le modèle** qui tient la fiche (pas de parsing
fragile des sorties, pas d'appel API supplémentaire), et la fiche est **cachée
de l'affichage** par défaut (consultable via `fiche`).

**La persistance :**
- `sauver [nom]` / `charger [nom]` écrivent/lisent `sessions/<nom>.txt`.
- Le nom est **nettoyé** (lettres, chiffres, `-`, `_`) → impossible d'écrire hors
  du dossier `sessions/` (ex. `../../etc/passwd` est neutralisé).
- `sessions/` est **ignoré par git** (fiches personnelles, infos de lab).
- **Reprise :** `charger` repart proprement de l'état sauvé (mémoire remise à
  zéro) ; à la première analyse, l'état de la fiche est **réinjecté** au modèle.

**L'aide :**
- `help` affiche à quoi sert l'outil, comment envoyer un message, et la liste des
  commandes : `fiche`, `sauver`, `charger`, `nouvelle`, `help`, `quit`.

---

## Décisions techniques (résumé)

| Décision | Pourquoi |
|---|---|
| API Claude, pas de modèle entraîné | On oriente un modèle existant par du texte : rapide, pas de données ni de GPU. |
| Opus 4.8 | Les modèles plus récents refusent le contenu sécurité de labs. |
| `.env` + `python-dotenv` | Secrets et réglages hors du code. |
| Un seul `llm_client` | Isole l'API : changement de fournisseur facile. |
| Réflexion `adaptive` + `effort` | Le modèle dose sa réflexion ; on règle l'intensité. |
| Mémoire en ajout seul + stockage atomique | Rôles qui alternent, historique propre. |
| Prompt caching | Coût réduit sans rien perdre du contexte. |
| Fiche tenue par le modèle | Pas de parsing fragile, pas d'appel en plus. |
| Nom de fichier nettoyé | Pas de sortie du dossier `sessions/`. |

---

## Prochaines étapes possibles

- **Enrichir le prompt méthodo** avec des réflexes concrets (service → CVE,
  checklists de privesc) au fil des box TryHackMe. *Peu de code, gros impact.*
- **Tests automatisés (`pytest`)** : transformer les tests actuels en une vraie
  suite `tests/`. *Montre la rigueur d'ingénierie.*
- **Évaluation de la qualité (evals)** : un banc d'essai qui note les réponses du
  copilote (format respecté ? pistes pertinentes ?). *Cœur du métier de la
  qualité de l'IA.*
- **V3 — exécution assistée en lecture seule** : proposer une commande
  non-destructive et, **après validation humaine**, l'exécuter et réinjecter la
  sortie. *À cadrer soigneusement (liste blanche, lecture seule) car cela touche
  au principe « l'humain exécute ».*
