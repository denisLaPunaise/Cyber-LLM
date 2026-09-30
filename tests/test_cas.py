"""Tests de cohérence du jeu de cas (evals/cas.py).

On ne teste pas la qualité de l'IA ici, mais que les DONNÉES sont bien formées :
chaque cas a les bons champs, un split valide, et ne référence que des critères
qui existent. Ça évite qu'une faute de frappe casse l'eval silencieusement.
"""

from evals.cas import CAS
from evals.criteres import CRITERES


def test_chaque_cas_est_bien_forme():
    for cas in CAS:
        assert cas["nom"], "un cas sans nom"
        assert cas["entree"].strip(), f"entrée vide pour {cas['nom']}"
        assert cas["split"] in ("dev", "test"), f"split invalide pour {cas['nom']}"
        assert cas["criteres"], f"aucun critère pour {cas['nom']}"
        for critere in cas["criteres"]:
            assert critere in CRITERES, f"critère inconnu '{critere}' dans {cas['nom']}"


def test_noms_uniques():
    noms = [cas["nom"] for cas in CAS]
    assert len(noms) == len(set(noms)), "deux cas portent le même nom"


def test_les_deux_splits_sont_presents():
    splits = {cas["split"] for cas in CAS}
    assert splits == {"dev", "test"}, f"splits attendus dev+test, trouvés : {splits}"
