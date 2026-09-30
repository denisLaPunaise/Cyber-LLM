"""Lance le copilote sur chaque cas type, note les réponses, affiche un rapport.

⚠️  Ce script appelle le VRAI Claude (ta clé API) → il coûte quelques centimes
    par passage. Lancement :

        python -m evals.run_eval                 # tous les cas (dev + test)
        python -m evals.run_eval dev             # seulement les cas de réglage
        python -m evals.run_eval all --juge      # + LLM-juge (2e appel par cas)

DEV  = cas sur lesquels on RÈGLE le prompt.
TEST = cas CACHÉS, pour vérifier que le prompt généralise (pas juste mémorisé).
Un progrès qui monte sur DEV mais pas sur TEST = surapprentissage.

Un rapport détaillé (avec les réponses complètes) est écrit dans
evals/resultats/ pour la relecture humaine.
"""

import sys
from datetime import datetime
from pathlib import Path

from src import assistant, config
from src.memoire import Memoire
from src.fiche import Fiche

from .cas import CAS
from .criteres import evaluer
from . import juge as juge_mod

# Préfixes des messages d'erreur renvoyés par le client LLM (clé invalide, etc.).
_PREFIXES_ERREUR = ("❌", "🚫", "🔎", "⚠️", "⏳", "🌐", "🛑")

_DOSSIER_RESULTATS = Path(__file__).resolve().parent / "resultats"


def _ligne_resume(par_split: dict) -> str:
    """Construit le bloc de résumé (scores dev / test / total)."""
    lignes = ["=" * 60]
    for nom_split in ("dev", "test"):
        ok, tot = par_split[nom_split]
        if tot:
            lignes.append(f"  {nom_split.upper():4} : {ok}/{tot}  ({round(100 * ok / tot)} %)")
    ok_tot = par_split["dev"][0] + par_split["test"][0]
    tot_tot = par_split["dev"][1] + par_split["test"][1]
    if tot_tot:
        lignes.append(f"  {'TOTAL':4} : {ok_tot}/{tot_tot}  ({round(100 * ok_tot / tot_tot)} %)")
    else:
        lignes.append("  Aucun cas évalué (voir les erreurs ci-dessus).")
    lignes.append("=" * 60)
    return "\n".join(lignes)


def _sauver_rapport(contenu: str) -> Path:
    """Écrit le rapport détaillé (réponses complètes) pour relecture."""
    _DOSSIER_RESULTATS.mkdir(parents=True, exist_ok=True)
    chemin = _DOSSIER_RESULTATS / "dernier_rapport.txt"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


def main(split: str = "all", avec_juge: bool = False) -> None:
    try:
        config.check_config()
    except RuntimeError as e:
        print(f"❌ Configuration : {e}")
        return

    print("=" * 60)
    print("  Cyber-LLM — Évaluation de la qualité (evals)")
    print("=" * 60)
    print("  ⚠️  Appelle le vrai Claude (coûte quelques centimes).")
    print(f"  DEV = régler le prompt · TEST = cas cachés · juge : {'ON' if avec_juge else 'off'}\n")

    cas_choisis = [c for c in CAS if split in ("all", c["split"])]
    par_split = {"dev": [0, 0], "test": [0, 0]}
    detail = [f"Rapport d'évaluation — {datetime.now():%Y-%m-%d %H:%M}", ""]

    for cas in cas_choisis:
        print("-" * 60)
        print(f"Cas : {cas['nom']}  [{cas['split']}]")

        memoire, fiche = Memoire(), Fiche()
        reponse = assistant.analyser(cas["entree"], memoire, fiche)

        detail.append(f"===== {cas['nom']}  [{cas['split']}] =====")
        detail.append("--- ENTRÉE ---\n" + cas["entree"])
        detail.append("--- RÉPONSE ---\n" + reponse)

        if reponse.strip().startswith(_PREFIXES_ERREUR):
            print(f"  ⚠️  Appel API échoué : {reponse.strip().splitlines()[0]}")
            print("      (vérifie ta clé / le modèle dans .env)")
            detail.append("(appel API échoué)\n")
            continue

        resultats = dict(evaluer(reponse, cas))

        justification = ""
        if avec_juge:
            verdicts = juge_mod.juger(cas["entree"], reponse)
            if verdicts is None:
                print("  ⚠️  juge indisponible (appel échoué)")
                detail.append("(juge indisponible)")
            else:
                justification = verdicts.pop("justification", "")
                resultats.update(verdicts)

        reussis = sum(1 for ok in resultats.values() if ok)
        for critere, ok in resultats.items():
            print(f"  {'✅' if ok else '❌'} {critere}")
            detail.append(f"  {'OK' if ok else 'X '} {critere}")
        if justification:
            print(f"  🧑‍⚖️  {justification}")
            detail.append(f"  juge : {justification}")
        print(f"  → {reussis}/{len(resultats)}")
        detail.append(f"  score : {reussis}/{len(resultats)}\n")

        par_split[cas["split"]][0] += reussis
        par_split[cas["split"]][1] += len(resultats)

    resume = _ligne_resume(par_split)
    print(resume)
    detail.append(resume)

    chemin = _sauver_rapport("\n".join(detail))
    print(f"\n📄 Rapport détaillé (avec les réponses) : {chemin}")

    if par_split["dev"][1] + par_split["test"][1] == 0:
        sys.exit(1)  # rien n'a tourné (utile en automatisation)


if __name__ == "__main__":
    args = sys.argv[1:]
    avec_juge = "--juge" in args
    positionnels = [a for a in args if not a.startswith("--")]
    choix = positionnels[0] if positionnels else "all"
    if choix not in ("all", "dev", "test"):
        print("Usage : python -m evals.run_eval [all|dev|test] [--juge]")
        sys.exit(2)
    main(choix, avec_juge)
