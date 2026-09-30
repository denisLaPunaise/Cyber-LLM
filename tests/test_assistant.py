"""Tests du branchement de l'assistant (src/assistant.py).

Point clé : on NE contacte JAMAIS l'API. On remplace `llm_client.ask` par une
fausse version (via monkeypatch) qui renvoie une réponse toute prête. Les tests
sont donc gratuits, instantanés et déterministes — ils testent NOTRE code, pas
l'intelligence du modèle.
"""

from src import assistant
from src.llm_client import Reponse
from src.memoire import Memoire
from src.fiche import Fiche


def _faux_ask(reponse_texte, succes=True):
    """Fabrique une fausse fonction `ask` qui renvoie toujours la même réponse."""
    def ask(system_prompt, messages):
        return Reponse(reponse_texte, succes)
    return ask


def test_fiche_cachee_de_l_affichage(monkeypatch):
    reply = "[ANALYSE]\nok\n\n[FICHE MACHINE]\nCible : 10.10.10.50"
    monkeypatch.setattr(assistant.llm_client, "ask", _faux_ask(reply))

    mem, fic = Memoire(), Fiche()
    visible = assistant.analyser("nmap ...", mem, fic)

    assert "[FICHE MACHINE]" not in visible   # la fiche n'apparaît pas à l'écran
    assert visible == "[ANALYSE]\nok"


def test_echange_memorise_et_fiche_mise_a_jour(monkeypatch):
    reply = "[ANALYSE]\nok\n\n[FICHE MACHINE]\nCible : 10.10.10.50"
    monkeypatch.setattr(assistant.llm_client, "ask", _faux_ask(reply))

    mem, fic = Memoire(), Fiche()
    assistant.analyser("nmap ...", mem, fic)

    # L'échange complet est mémorisé (question + réponse), bloc fiche inclus.
    assert len(mem.historique()) == 2
    assert "[FICHE MACHINE]" in mem.historique()[1]["content"]
    # Et la fiche est à jour.
    assert "10.10.10.50" in fic.contenu


def test_echec_ne_memorise_rien(monkeypatch):
    monkeypatch.setattr(assistant.llm_client, "ask", _faux_ask("erreur", succes=False))

    mem, fic = Memoire(), Fiche()
    visible = assistant.analyser("x", mem, fic)

    assert visible == "erreur"
    assert mem.est_vide()   # un échec ne mémorise rien...
    assert fic.est_vide()   # ...et ne touche pas la fiche


def test_reprise_injecte_l_etat(monkeypatch):
    # On capture les messages réellement envoyés à l'API simulée.
    captured = {}

    def ask(system_prompt, messages):
        captured["messages"] = messages
        return Reponse("[ANALYSE]\nok", True)

    monkeypatch.setattr(assistant.llm_client, "ask", ask)

    mem, fic = Memoire(), Fiche()
    fic.mettre_a_jour("[FICHE MACHINE]\nAcces : user bob")  # comme après un 'charger'
    assistant.analyser("je reprends", mem, fic)            # mémoire vide + fiche pleine

    premier_message = captured["messages"][0]["content"]
    assert "Reprise de session" in premier_message
    assert "user bob" in premier_message
