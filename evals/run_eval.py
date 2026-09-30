"""Lance le copilote sur chaque cas type, note les réponses, affiche un rapport.

⚠️  Ce script appelle le VRAI Claude (ta clé API) → il coûte quelques centimes
    par passage. À lancer quand on change le prompt ou le modèle :

        python -m evals.run_eval

On obtient un score (ex. 14/15) : un repère chiffré pour savoir si un changement
améliore ou dégrade le copilote.
"""

import sys

from src import assistant, config
from src.memoire import Memoire
from src.fiche import Fiche

from .cas import CAS
from .criteres import evaluer

# Préfixes des messages d'erreur renvoyés par le client LLM (clé invalide, etc.).
_PREFIXES_ERREUR = ("❌", "🚫", "🔎", "⚠️", "⏳", "🌐", "🛑")


def main() -> None:
    try:
        config.check_config()
    except RuntimeError as e:
        print(f"❌ Configuration : {e}")
        return

    print("=" * 60)
    print("  Cyber-LLM — Évaluation de la qualité (evals)")
    print("=" * 60)
    print("  ⚠️  Appelle le vrai Claude (coûte quelques centimes).\n")

    total_ok = 0
    total = 0

    for cas in CAS:
        print("-" * 60)
        print(f"Cas : {cas['nom']}")

        # Session neuve pour chaque cas -> les cas sont indépendants.
        memoire, fiche = Memoire(), Fiche()
        reponse = assistant.analyser(cas["entree"], memoire, fiche)

        # Si l'appel API a échoué, on le signale et on passe au cas suivant.
        if reponse.strip().startswith(_PREFIXES_ERREUR):
            print(f"  ⚠️  Appel API échoué : {reponse.strip().splitlines()[0]}")
            print("      (vérifie ta clé / le modèle dans .env)")
            continue

        resultats = evaluer(reponse, cas)
        reussis = sum(1 for ok in resultats.values() if ok)
        for critere, ok in resultats.items():
            print(f"  {'✅' if ok else '❌'} {critere}")
        print(f"  → {reussis}/{len(resultats)}")

        total_ok += reussis
        total += len(resultats)

    print("=" * 60)
    if total == 0:
        print("  Aucun cas évalué (voir les erreurs ci-dessus).")
    else:
        pourcent = round(100 * total_ok / total)
        print(f"  SCORE GLOBAL : {total_ok}/{total}  ({pourcent} %)")
    print("=" * 60)

    # Code de sortie non nul si tout a échoué (utile en automatisation).
    if total == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
