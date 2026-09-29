# Cyber-LLM — Copilote de pentest assisté par LLM

Assistant en ligne de commande qui aide à progresser sur une machine de lab :
tu lui donnes la sortie de tes commandes, il raisonne avec toi et te propose
les étapes suivantes en s'appuyant sur la méthodologie de pentest.

**Ce n'est pas un outil qui attaque tout seul.** C'est un copilote : tu gardes
toujours la décision et tu exécutes toi-même les commandes.

> ✅ **Statut : V1 fonctionnelle.** Colle une sortie de commande → reçois des
> pistes priorisées avec les commandes. L'assistant **se souvient** de la
> machine en cours pendant toute la session.

---

## ⚠️ Cadre d'usage (à lire)

Cet outil est destiné **uniquement** à :

- des machines et labs sur lesquels on est **explicitement autorisé**
  (TryHackMe, HackTheBox, environnements de test personnels…) ;
- un usage **pédagogique** et de préparation à la certification.

Règles intégrées au projet :

- ✅ **Validation humaine obligatoire** avant toute action offensive.
- ✅ **Rien de destructif** en automatique.
- ✅ L'assistant **propose**, il **n'exécute pas** à ta place (pour l'instant).

L'utilisation contre des systèmes sans autorisation est illégale et sort
totalement du cadre de ce projet.

---

## Comment ça marche

Trois briques :

1. **Un LLM déjà entraîné** (API Claude d'Anthropic) — aucun modèle n'est
   entraîné ; on oriente un modèle existant par du texte.
2. **Un prompt système** = la méthodologie de pentest (le « cerveau »,
   dans `prompts/system_pentest.md`).
3. **Une boucle d'interaction** : tu colles une sortie → l'assistant analyse
   et propose des pistes priorisées avec les commandes.

Depuis la **V1**, l'assistant garde en mémoire l'historique de la session :
il se souvient des ports, services et identifiants déjà trouvés, et raisonne
de façon cumulative au lieu de repartir de zéro à chaque message.

---

## Prérequis

- **Python 3.11+**
- Une **clé API Anthropic** (console.anthropic.com)

---

## Installation

### Windows (PowerShell)

```powershell
# 1. Créer et activer un environnement virtuel
py -m venv .venv
.venv\Scripts\Activate.ps1
# Si l'activation est bloquée (« l'exécution de scripts est désactivée »),
# lance UNE fois la commande suivante, puis réessaie l'activation :
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer la clé API
copy .env.example .env
# puis édite .env et colle ta vraie clé (le .env n'est jamais commité)
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Quand l'environnement est actif, l'invite affiche `(.venv)` au début de la ligne.

---

## Configuration (`.env`)

| Variable | Rôle | Défaut |
|---|---|---|
| `ANTHROPIC_API_KEY` | Ta clé API Anthropic | — (obligatoire) |
| `CYBER_LLM_MODEL` | Modèle Claude utilisé | `claude-opus-4-8` |
| `CYBER_LLM_EFFORT` | Effort de raisonnement (`low`→`max`) | `high` |
| `ANTHROPIC_WORKSPACE_ID` | Workspace (si la clé n'y est pas rattachée) | *(vide)* |

> Note : Opus 4.8 est recommandé — Opus 5 / 5.5 refusent souvent le contenu
> sécurité de labs (classifieur de sûreté « cyber » plus strict).

---

## Utilisation

```bash
python -m src.cli
```

Colle une sortie de commande (ex. un scan `nmap`), tape `END` sur une ligne
seule, et l'assistant te propose les étapes suivantes.

L'assistant **se souvient** de tout ce que tu as collé pendant la session :
pas besoin de tout recoller à chaque message. Il tient aussi une **fiche
machine** à jour (IP, ports, services, identifiants, accès).

- `fiche` — affiche l'état structuré de la machine à tout moment.
- `sauver [nom]` — sauvegarde la fiche (ex. `sauver blue`).
- `charger [nom]` — recharge une fiche sauvegardée pour reprendre une box.
- `nouvelle` — efface la mémoire et la fiche pour repartir de zéro.
- `help` — affiche l'aide et la liste des commandes.
- `quit` — quitter.

Les fiches sauvegardées vont dans le dossier `sessions/` (ignoré par git).

---

## Roadmap

- **V0** ✅ *(terminée)* — CLI : coller une sortie → recevoir des pistes. Zéro autonomie.
- **V1** ✅ *(terminée)* — mémoire de session : l'assistant retient l'historique
  de la machine en cours et raisonne de façon cumulative. Les requêtes utilisent
  le *prompt caching* d'Anthropic pour réduire les coûts (début de conversation
  relu depuis le cache, facturé ~10 %).
- **V2** ✅ *(terminée)* — fiche machine : état structuré de la box (IP, ports,
  services, identifiants, accès).
  - ✅ Étape 1 : l'assistant tient la fiche à jour, consultable via `fiche`.
  - ✅ Étape 2 : `sauver` / `charger` pour reprendre une box plus tard.
- **V3** — exécution assistée de commandes en lecture seule, avec validation humaine.

Plan détaillé de la V0 : [`docs/plan-v0.md`](docs/plan-v0.md).

---

## Note

Projet personnel d'apprentissage (reconversion vers la cybersécurité offensive,
angle IA × sécurité). Construit progressivement, chaque brique comprise et
documentée.
