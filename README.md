# Cyber-LLM — Copilote de pentest assisté par LLM

Assistant en ligne de commande qui aide à progresser sur une machine de lab :
tu lui donnes la sortie de tes commandes, il raisonne avec toi et te propose
les étapes suivantes en s'appuyant sur la méthodologie de pentest.

**Ce n'est pas un outil qui attaque tout seul.** C'est un copilote : tu gardes
toujours la décision et tu exécutes toi-même les commandes.

> 🚧 **Statut : V0 en construction.** Les fondations sont posées ; la CLI arrive.

---

## ⚠️ Cadre d'usage (à lire)

Cet outil est destiné **uniquement** à :

- des machines et labs sur lesquels on est **explicitement autorisé**
  (TryHackMe, HackTheBox, environnements de test personnels…) ;
- un usage **pédagogique** et de préparation à la certification.

Règles intégrées au projet :

- ✅ **Validation humaine obligatoire** avant toute action offensive.
- ✅ **Rien de destructif** en automatique.
- ✅ L'assistant **propose**, il **n'exécute pas** à ta place (en V0).

L'utilisation contre des systèmes sans autorisation est illégale et sort
totalement du cadre de ce projet.

---

## Comment ça marche

Trois briques :

1. **Un LLM déjà entraîné** (API Claude d'Anthropic) — aucun modèle n'est
   entraîné ; on oriente un modèle existant par du texte.
2. **Un prompt système** = la méthodologie de pentest (le « cerveau »).
3. **Une boucle d'interaction** : tu colles une sortie → l'assistant analyse
   et propose des pistes priorisées avec les commandes.

Le modèle Claude utilisé est **configurable** dans `.env`
(variable `CYBER_LLM_MODEL`).

---

## Prérequis

- **Python 3.11+**
- Une **clé API Anthropic** (console.anthropic.com)

---

## Installation

```bash
# 1. Créer et activer un environnement virtuel
python3 -m venv .venv
source .venv/bin/activate         # Windows : .venv\Scripts\activate

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer la clé API
cp .env.example .env
# puis édite .env et colle ta vraie clé (le .env n'est jamais commité)
```

---

## Utilisation

> 🚧 Disponible à la prochaine étape de la V0.

```bash
python -m src.cli
```

Puis colle une sortie de commande (ex. un scan `nmap`) et laisse l'assistant
te proposer les étapes suivantes.

---

## Roadmap

- **V0** *(en cours)* — CLI : coller une sortie → recevoir des pistes. Zéro autonomie.
- **V1** — mémoire de session (état de la machine en cours).
- **V2** — exécution assistée de commandes en lecture seule, avec validation humaine.

Plan détaillé de la V0 : [`docs/plan-v0.md`](docs/plan-v0.md).

---

## Note

Projet personnel d'apprentissage (reconversion vers la cybersécurité offensive,
angle IA × sécurité). Construit progressivement, chaque brique comprise et
documentée.
