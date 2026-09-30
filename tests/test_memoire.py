"""Tests de la mémoire de session (src/memoire.py).

On vérifie que l'historique se remplit correctement, que les rôles alternent
bien (user / assistant), et que « vider » remet tout à zéro.
"""

from src.memoire import Memoire


def test_memoire_vide_au_depart():
    m = Memoire()
    assert m.est_vide()
    assert m.historique() == []


def test_ajout_et_alternance_des_roles():
    m = Memoire()
    m.ajouter_utilisateur("sortie nmap")
    m.ajouter_assistant("des pistes")
    m.ajouter_utilisateur("enum SMB")
    m.ajouter_assistant("d'autres pistes")

    roles = [msg["role"] for msg in m.historique()]
    assert roles == ["user", "assistant", "user", "assistant"]


def test_contenu_memorise():
    m = Memoire()
    m.ajouter_utilisateur("bonjour")
    assert m.historique()[0] == {"role": "user", "content": "bonjour"}


def test_vider_remet_a_zero():
    m = Memoire()
    m.ajouter_utilisateur("x")
    m.ajouter_assistant("y")
    m.vider()
    assert m.est_vide()
    assert m.historique() == []
