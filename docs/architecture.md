# Architecture de Cyber-LLM

Ce document explique **comment le projet est construit** et **comment chaque
version fonctionne**. Il sert de référence technique (et de support pour
présenter le projet).

---

## Philosophie

Cyber-LLM est un **copilote de pentest**, pas un outil qui attaque tout seul.
L'utilisateur colle la sortie d'une commande, l'assistant raisonne avec lui et
**propose** les étapes suivantes selon la méthodologie de pentest.
**L'humain garde toujours la décision.** (Depuis la V3, l'outil peut exécuter des
commandes de recon lecture seule, mais **uniquement après validation explicite**.)
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
| `src/executeur.py` | **(V3)** Exécution assistée : liste blanche recon, garde-fous, exécution sans shell. |
| `src/assistant.py` | La « colle » : charge le prompt, encadre l'entrée, met à jour mémoire et fiche. |
| `src/cli.py` | Interface interactive : boucle, commandes, affichage, mode `auto`. |
| `prompts/system_pentest.md` | Le « cerveau » : rôle, cadre, méthodologie, format de réponse. |
| `tests/` | Suite `pytest` (35 tests) : vérifie la tuyauterie, **sans** appeler l'API. |
| `evals/` | Évaluation de la **qualité des réponses** (cas types, critères, LLM-juge). |

### Le trajet d'une requête

```
Toi (terminal)
  │  colle une sortie + END   (ou une commande : help/fiche/sauver/charger/auto/nouvelle/quit)
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
API Claude        (Opus 4.8, réflexion "adaptive" + effort) répond au format imposé :
  │               [ANALYSE] / [PISTES] / [AVANT D'AGIR] / [FICHE MACHINE]
  ▼
retour            assistant sépare la fiche (rangée de côté) de la partie visible
  │               (affichée), et mémorise l'échange complet
  ▼  (mode `auto` seulement)
executeur.py      si une commande de recon de la LISTE BLANCHE est proposée, demande
                  ton accord (o/N), l'exécute SANS shell, réinjecte la sortie → nouvelle analyse
```

`config.py` alimente `llm_client.py` avec les réglages lus dans `.env`.

---

## V0 — Le copilote de base

**Ce que ça fait :** tu colles une sortie de commande, tu reçois des pistes
priorisées avec les commandes prêtes. Zéro mémoire, zéro autonomie.

**Les 3 briques :**
1. **Un LLM déjà entraîné** (API Claude) → `llm_client.py`.
2. **Un prompt système** = la méthodologie → `prompts/system_pentest.md`.
3. **Une boucle d'interaction** → `cli.py`.

**Détail :**
- `config.py` lit le `.env` (`python-dotenv`) et expose `MODEL`, `EFFORT`,
  `WORKSPACE_ID`, `MAX_TOKENS` ; `check_config()` renvoie un message clair si la
  clé ou le modèle manquent.
- `llm_client.py` construit la requête (`thinking={"type":"adaptive"}`,
  `output_config={"effort":...}`) et **attrape chaque type d'erreur** (clé,
  workspace, réseau, 400…) ainsi que le **refus** du classifieur, au lieu de planter.
- `assistant.py` **encadre** l'entrée avec un contexte « je m'entraîne sur un lab
  autorisé » → moins de refus, meilleures réponses.
- Le prompt impose le format **[ANALYSE] / [PISTES] / [AVANT D'AGIR]**.

**Décisions clés :** Opus 4.8 (les modèles plus récents refusent souvent le
contenu sécurité de labs — validé empiriquement 5.5 ✗, 5 ✗, 4.8 ✓) ; config dans
`.env` ; un seul point d'accès à l'API (`llm_client`) → fournisseur changeable.

---

## V1 — Mémoire de session + prompt caching

**Ce que ça ajoute :** l'assistant se **souvient** de toute la session, et les
requêtes coûtent moins cher grâce au **caching**.

- `memoire.py` : classe `Memoire` = une liste de messages
  `{"role": ..., "content": ...}` (le format exact de l'API).
- `llm_client.ask()` reçoit **tout l'historique** et renvoie **`Reponse(texte, succès)`**.
- `assistant.analyser()` n'enregistre l'échange **que si l'appel a réussi** : l'API
  exige que les rôles **alternent** (user → assistant → …), donc on mémorise la
  paire question+réponse **ensemble, ou rien**.
- **Caching :** le prompt système (stable) et le dernier message portent un
  `cache_control` → le début identique est **relu depuis le cache** (~10 % du prix).
  On est parfaits pour ça : prompt stable + historique en **ajout seul**. Effet :
  une box passe d'environ **1,85 $ à ~1,00 $**.

> À comprendre : l'API est **sans mémoire** côté serveur. C'est nous qui renvoyons
> l'historique à chaque tour → le coût grossit → d'où le caching.

---

## V2 — Fiche machine + persistance + aide

**Ce que ça ajoute :** un **état structuré** de la box, consultable, sauvegardable.

- Le modèle termine chaque réponse par un bloc `[FICHE MACHINE]` cumulatif
  (cible, ports/services, utilisateurs, identifiants, accès, à explorer).
- `fiche.py` → `separer()` **découpe** la réponse : la partie visible est affichée,
  le bloc fiche est **rangé de côté** (consultable via `fiche`). La réponse complète
  reste en mémoire pour que le modèle garde sa fiche en tête.
- **Persistance :** `sauver [nom]` / `charger [nom]` → `sessions/<nom>.txt`. Le nom
  est **nettoyé** (impossible d'écrire hors du dossier) ; `sessions/` est ignoré par git.
- **Reprise :** `charger` repart de l'état sauvé (mémoire vidée) et l'état est
  **réinjecté** au modèle à la 1re analyse.
- `help` affiche l'aide et la liste des commandes.

**Choix :** c'est **le modèle** qui tient la fiche (pas de parsing fragile, pas
d'appel API en plus), et elle est cachée de l'affichage par défaut.

---

## V3 — Exécution assistée (mode `auto`)

**Ce que ça ajoute :** en mode `auto`, l'outil propose de lancer **lui-même** les
commandes de recon, après ta validation — fini le copier-coller entre deux fenêtres.

**Le flux :** après une réponse, `executeur.commande_proposee()` repère la 1re
commande éligible ; la CLI demande `▶ Lancer « … » ? [o/N]` ; puis exécute et
**réinjecte la sortie** pour enchaîner l'analyse.

**Garde-fous (défense en couches), dans `executeur.py` :**
1. refus de tout caractère de chaînage shell (`;` `|` `>` `` ` `` `$` …) ;
2. le binaire doit être dans la **liste blanche** recon (nmap, enum4linux, smbmap,
   dig, whatweb, gobuster, ffuf, nikto…) — on **ne fait pas confiance** au LLM pour
   s'auto-autoriser ;
3. refus des motifs destructifs ;
4. exécution **sans shell** (anti-injection), avec timeout et sortie tronquée ;
5. **ta validation `o` reste le garde-fou final.**

**Le risque traité — la prompt injection :** la sortie réinjectée vient d'une cible
potentiellement hostile (une box CTF peut contenir du texte piégé). Même si elle
tentait de faire proposer une commande malveillante, celle-ci serait **recalée par
la liste blanche** et **visible dans le `o/N`**. Mode **opt-in** (`auto` / `--auto`),
désactivé par défaut. À utiliser sur la machine qui a les outils (ex. Kali).

---

## Qualité : tests + évaluations

Deux filets **complémentaires**, essentiels pour un projet sérieux.

**Tests (`pytest`, `tests/`)** — vérifient la **tuyauterie** (mémoire, fiche,
découpage, sauvegarde, garde-fous d'exécution). Ils **ne contactent jamais l'API**
(l'appel LLM est simulé via `monkeypatch`) : gratuits, instantanés, déterministes.
**35 tests.**

**Évaluations (`evals/`)** — mesurent la **qualité des réponses de l'IA** sur des
cas types, sur deux niveaux :
- **critères mécaniques** (format, ancrage, sécurité, actionnable) ;
- **LLM-juge** : un 2ᵉ appel Claude note pertinence / hallucination / priorisation.

Les cas sont séparés en **dev** (réglage) et **test** (cachés, pour mesurer la
**généralisation** et éviter le surapprentissage). On connaît aussi les **limites**
(un juge reste faillible, un petit jeu de cas se surapprend) → on garde l'humain
dans la boucle et on fait grossir le jeu. Démarche : **mesurer plutôt que deviner.**

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
| Exécution sans shell + liste blanche | Anti-injection ; on ne lance que de la recon connue, après validation. |
| Tests qui simulent l'API | Rapides, gratuits, déterministes, décorrélés du LLM. |
| Split dev/test dans les evals | Mesurer la généralisation, pas le par-cœur. |

---

## Ce qui reste

- **Enrichir le prompt méthodo** (étape « A ») avec des réflexes concrets
  (service → CVE, checklists de privesc Linux/Windows, identifiants par défaut…),
  au fil de l'apprentissage. **Reporté** jusqu'à ce que le cours TryHackMe / eJPT
  soit prêt. L'eval dira si chaque ajout améliore vraiment le copilote.
- Évolutions libres : plus de cas d'eval, journal des sessions, packaging `pip`,
  interface web légère.
