# Plan de réalisation — V0 de l'Assistant de pentest LLM

> Copilote de pentest basé sur un LLM. **V0 = CLI simple, zéro autonomie.**
> Usage strictement limité aux labs autorisés (TryHackMe, HackTheBox…), validation humaine obligatoire.

---

## 0. Périmètre de la V0

**Ce qu'on fait :** une CLI interactive. L'utilisateur colle une sortie de commande → l'assistant analyse et propose 2-3 pistes priorisées avec les commandes prêtes à copier.

**Ce qu'on ne fait pas (réservé v1/v2) :** aucune exécution automatique, aucune autonomie, aucune mémoire persistante entre sessions.

**Réduit à l'essentiel :** `1 appel API LLM + 1 prompt système méthodo + 1 boucle`.

---

## 1. Décisions techniques (figées pour la V0)

| Décision | Choix | Pourquoi |
|---|---|---|
| Fournisseur LLM | **API (Claude)** | Le plus rapide à brancher. Ollama local = plus tard (argument confidentialité). |
| Langage | **Python 3.11+** | Écosystème LLM riche, terrain connu. |
| Secrets (clé API) | **`.env` + variable d'environnement** | Jamais de clé en dur dans le code ni le repo. |
| Dépendances | Minimales (SDK LLM + `python-dotenv`) | Garder la v0 légère et lisible. |

---

## 2. Arborescence cible

```
Cyber-LLM/
├── README.md                  # présentation + garde-fous + comment lancer
├── requirements.txt           # dépendances
├── .env.example               # modèle de config (sans vraie clé)
├── .gitignore                 # ignore .env, __pycache__, etc.
├── prompts/
│   └── system_pentest.md      # LE "cerveau" méthodo (la vraie valeur)
├── src/
│   ├── __init__.py
│   ├── config.py              # charge la clé API + réglages
│   ├── llm_client.py          # wrapper autour de l'appel API
│   ├── assistant.py           # assemble prompt système + entrée → réponse
│   └── cli.py                 # boucle interactive (point d'entrée)
├── examples/
│   └── nmap_sample.txt        # sortie d'exemple pour tester sans lab
└── docs/
    └── plan-v0.md             # ce document
```

Chaque fichier a **une responsabilité** : en v1/v2, on ajoute `state.py` (mémoire) et
`runner.py` (exécution lecture seule) sans toucher au reste.

---

## 3. Le prompt système — la vraie valeur du projet

Fichier : `prompts/system_pentest.md`. Structure recommandée :

1. **Rôle & posture** — copilote de pentest ; l'humain garde toujours la décision ; propose, n'exécute pas.
2. **Cadre légal/éthique** — labs autorisés uniquement, validation humaine obligatoire, rien de destructif.
3. **Méthodologie en phases** — recon → énumération → identification de vulnérabilités → exploitation → post-exploitation/privesc → pivoting. Pour chaque phase : quoi chercher, dans quel ordre, les réflexes.
4. **Format de réponse imposé** (voir §4).
5. **Règles de raisonnement** — s'appuyer sur le connu, prioriser, ne pas répéter, expliciter ce qu'on cherche à valider.
6. **Limites explicites** — refuse ce qui sort du périmètre / toute action destructive automatique.

**Source de contenu :** les notes TryHackMe, thème par thème. En v0 on couvre d'abord
recon + énumération (les plus utilisés), puis on enrichit au fil de l'eau.

---

## 4. Format de sortie imposé

```
[ANALYSE]        ce qui ressort d'important dans la sortie
[PISTES]         2-3 options classées par priorité, avec :
                 - le raisonnement (pourquoi cette piste)
                 - la commande prête à copier
                 - ce qu'on cherche à confirmer
[AVANT D'AGIR]   rappel de validation / périmètre si l'étape est offensive
```

---

## 5. Rôle de chaque composant Python

- **`config.py`** — lit la clé API depuis l'environnement, expose les réglages (modèle, température). Erreur claire si la clé manque.
- **`llm_client.py`** — une fonction `ask(system_prompt, user_message) -> str`. Seul endroit qui parle à l'API → on pourra brancher Ollama plus tard sans rien changer ailleurs.
- **`assistant.py`** — charge `system_pentest.md`, prend l'entrée utilisateur, appelle `llm_client`, renvoie la réponse.
- **`cli.py`** — la boucle : bannière garde-fous → lit l'input multi-lignes → appelle l'assistant → affiche → recommence. Commande `quit` pour sortir.

---

## 6. Boucle d'interaction (flux V0)

```
Démarrage → bannière garde-fous
   ↓
L'utilisateur colle une sortie (nmap, curl, …), termine par un marqueur
   ↓
assistant.py construit [prompt système + sortie] → appelle le LLM
   ↓
Affichage : ANALYSE + PISTES priorisées + commandes
   ↓
L'utilisateur choisit, lance lui-même dans son terminal, recolle le résultat
   ↓ (retour au début)
```

Zéro exécution côté outil : l'humain reste aux commandes à 100 %.

---

## 7. Garde-fous « en dur »

- **Bannière au lancement** : labs autorisés uniquement, tu valides tout, rien de destructif.
- **Aucune fonction d'exécution de commande** en v0 (impossible par construction).
- **README** qui explique la posture « consultant » (démarcation vs « script kiddie »).

---

## 8. Étapes de réalisation (checklist ordonnée)

1. **Init repo** : `.gitignore`, `requirements.txt`, `.env.example`, README squelette.
2. **`config.py`** : chargement clé API + erreur claire si absente.
3. **`llm_client.py`** : le wrapper d'appel (~10-15 lignes).
4. **`prompts/system_pentest.md` v1** : rôle + garde-fous + phases recon/énum + format de sortie.
5. **`assistant.py`** : assemblage prompt + entrée → réponse.
6. **`cli.py`** : boucle interactive + bannière.
7. **`examples/nmap_sample.txt`** : sortie d'exemple pour tester sans lab.
8. **Test manuel** : lancer, coller l'exemple, vérifier la cohérence des pistes. Itérer sur le prompt.

Ordre pensé pour avoir un outil qui tourne dès l'étape 6, puis passer le plus de
temps sur le prompt (étape 4, à réenrichir en boucle).

---

## 9. Critères de « V0 terminée »

- [ ] Coller une sortie nmap → recevoir 2-3 pistes priorisées cohérentes + commandes correctes.
- [ ] La clé API n'est jamais dans le code ni le repo.
- [ ] Aucune exécution automatique possible.
- [ ] README clair + garde-fous visibles.
- [ ] Chaque fichier explicable de tête (défense en entretien).

---

## 10. Transition vers la V1

Le découpage permet d'ajouter en v1 :
- **`state.py`** : mémoire de la machine en cours (IP, ports, services, versions, creds trouvés), injectée dans le prompt à chaque tour.
- Génération de commandes prêtes à copier plus structurée.

Aucune refonte nécessaire.
