"""Lance le copilote sur chaque cas type, note les réponses, affiche un rapport.

⚠️  Ce script appelle le VRAI Claude (ta clé API) → il coûte quelques centimes
    par passage. Lancement :

        python -m evals.run_eval           # tous les cas (dev + test)
        python -m evals.run_eval dev       # seulement les cas de réglage
        python -m evals.run_eval test      # seulement les cas cachés

DEV  = cas sur lesquels on RÈGLE le prompt.
TEST = cas CACHÉS, pour vérifier que le prompt généralise (pas juste mémorisé).
Un progrès qui monte sur DEV mais pas sur TEST = surapprentissage.
"""

import sys

from src import assistant, config
from src.memoire import Memoire
from src.fiche import Fiche

from .cas import CAS
from .criteres import evaluer

# Préfixes des messages d'erreur renvoyés par le client LLM (clé invalide, etc.).
_PREFIXES_ERREUR = ("❌", "🚫", "🔎", "⚠️", "⏳", "🌐", "🛑")


def _noter_cas(cas: dict):
    """Lance le copilote sur un cas et renvoie (résultats, message_d_erreur)."""
    memoire, fiche = Memoire(), Fiche()
    reponse = assistant.analyser(cas["entree"], memoire, fiche)
    if reponse.strip().startswith(_PREFIXES_ERREUR):
        return None, reponse.strip().splitlines()[0]
    return evaluer(reponse, cas), None


def main(split: str = "all") -> None:
    try:
        config.check_config()
    except RuntimeError as e:
        print(f"❌ Configuration : {e}")
        return

    print("=" * 60)
    print("  Cyber-LLM — Évaluation de la qualité (evals)")
    print("=" * 60)
    print("  ⚠️  Appelle le vrai Claude (coûte quelques centimes).")
    print("  DEV = régler le prompt · TEST = cas cachés (généralisation).\n")

    cas_choisis = [c for c in CAS if split in ("all", c["split"])]
    # Pour chaque split : [critères réussis, critères totaux].
    par_split = {"dev": [0, 0], "test": [0, 0]}

    for cas in cas_choisis:
        print("-" * 60)
        print(f"Cas : {cas['nom']}  [{cas['split']}]")

        resultats, erreur = _noter_cas(cas)
        if erreur:
            print(f"  ⚠️  Appel API échoué : {erreur}")
            print("      (vérifie ta clé / le modèle dans .env)")
            continue

        reussis = sum(1 for ok in resultats.values() if ok)
        for critere, ok in resultats.items():
            print(f"  {'✅' if ok else '❌'} {critere}")
        print(f"  → {reussis}/{len(resultats)}")

        par_split[cas["split"]][0] += reussis
        par_split[cas["split"]][1] += len(resultats)

    print("=" * 60)
    for nom_split in ("dev", "test"):
        ok, tot = par_split[nom_split]
        if tot:
            print(f"  {nom_split.upper():4} : {ok}/{tot}  ({round(100 * ok / tot)} %)")
    ok_tot = par_split["dev"][0] + par_split["test"][0]
    tot_tot = par_split["dev"][1] + par_split["test"][1]
    if tot_tot:
        print(f"  {'TOTAL':4} : {ok_tot}/{tot_tot}  ({round(100 * ok_tot / tot_tot)} %)")
    else:
        print("  Aucun cas évalué (voir les erreurs ci-dessus).")
    print("=" * 60)

    if tot_tot == 0:
        sys.exit(1)  # utile en automatisation : signale que rien n'a tourné


if __name__ == "__main__":
    choix = sys.argv[1] if len(sys.argv) > 1 else "all"
    if choix not in ("all", "dev", "test"):
        print("Usage : python -m evals.run_eval [all|dev|test]")
        sys.exit(2)
    main(choix)
