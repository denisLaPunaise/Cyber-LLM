"""Tests de la fiche machine (src/fiche.py).

On vérifie : le découpage du bloc [FICHE MACHINE], le stockage, la sauvegarde /
le rechargement, la sécurité du nom de fichier, et l'erreur si le fichier
n'existe pas.

`tmp_path` et `monkeypatch` sont des « fixtures » fournies par pytest :
 - tmp_path   : un dossier temporaire propre, unique à chaque test ;
 - monkeypatch : permet de remplacer temporairement une variable/fonction
                 (ici, le dossier des sessions) le temps d'un test.
"""

import pytest

from src import fiche as fiche_mod
from src.fiche import Fiche, separer, _chemin


def test_separer_isole_le_bloc_fiche():
    reponse = "[ANALYSE]\nok\n\n[FICHE MACHINE]\nCible : 10.10.10.50"
    visible, fiche = separer(reponse)
    assert "[FICHE MACHINE]" not in visible   # la fiche est retirée de l'affichage
    assert visible == "[ANALYSE]\nok"
    assert "10.10.10.50" in fiche             # mais bien récupérée à part


def test_separer_sans_marqueur():
    # Pas de bloc fiche -> tout est visible, la fiche est vide.
    visible, fiche = separer("[ANALYSE]\nrien de plus")
    assert visible == "[ANALYSE]\nrien de plus"
    assert fiche == ""


def test_fiche_stocke_et_se_vide():
    f = Fiche()
    assert f.est_vide()
    f.mettre_a_jour("  [FICHE MACHINE]\nCible : 1.2.3.4  ")
    assert not f.est_vide()
    assert "1.2.3.4" in f.contenu
    f.vider()
    assert f.est_vide()


def test_sauver_puis_charger(tmp_path, monkeypatch):
    # On redirige le dossier des sessions vers un dossier temporaire.
    monkeypatch.setattr(fiche_mod, "_DOSSIER", tmp_path)

    f = Fiche()
    f.mettre_a_jour("[FICHE MACHINE]\nCible : 10.10.10.50\nUtilisateurs : bob")
    chemin = f.sauver("blue")
    assert chemin.exists()

    # Une NOUVELLE fiche recharge exactement le même contenu.
    f2 = Fiche()
    f2.charger("blue")
    assert "10.10.10.50" in f2.contenu and "bob" in f2.contenu


def test_nom_de_fichier_securise(tmp_path, monkeypatch):
    monkeypatch.setattr(fiche_mod, "_DOSSIER", tmp_path)
    chemin = _chemin("../../etc/passwd")
    assert chemin.parent == tmp_path        # on reste dans le dossier des sessions
    assert chemin.name == "etcpasswd.txt"   # les caractères dangereux sont retirés


def test_charger_absent_leve_une_erreur(tmp_path, monkeypatch):
    monkeypatch.setattr(fiche_mod, "_DOSSIER", tmp_path)
    with pytest.raises(FileNotFoundError):
        Fiche().charger("nexiste_pas")
