"""Tests du LLM-juge (evals/juge.py).

On teste le PARSING du verdict et la gestion d'un échec d'appel — sans jamais
contacter l'API (l'appel au juge est simulé).
"""

from evals import juge
from evals.juge import parser_verdict
from src.llm_client import Reponse


def test_verdicts_positifs():
    texte = (
        "PERTINENCE: OUI\nHALLUCINATION: NON\nPRIORISATION: OUI\n"
        "JUSTIFICATION: pistes adaptées et bien ordonnées."
    )
    v = parser_verdict(texte)
    assert v["juge_pertinence"] is True
    assert v["juge_sans_hallucination"] is True   # HALLUCINATION NON -> pas d'invention
    assert v["juge_priorisation"] is True
    assert "adaptées" in v["justification"]


def test_hallucination_detectee():
    texte = "PERTINENCE: OUI\nHALLUCINATION: OUI\nPRIORISATION: NON"
    v = parser_verdict(texte)
    assert v["juge_sans_hallucination"] is False  # a inventé -> critère raté
    assert v["juge_priorisation"] is False


def test_format_invalide_echoue_par_prudence():
    # Si le juge ne suit pas le format, aucun critère n'est validé.
    v = parser_verdict("je pense que la réponse est plutôt bonne")
    assert v["juge_pertinence"] is False
    assert v["juge_sans_hallucination"] is False
    assert v["juge_priorisation"] is False


def test_juger_succes(monkeypatch):
    texte = "PERTINENCE: OUI\nHALLUCINATION: NON\nPRIORISATION: OUI\nJUSTIFICATION: ok"
    monkeypatch.setattr(juge.llm_client, "ask", lambda s, m: Reponse(texte, True))
    v = juge.juger("sortie", "reponse")
    assert v["juge_pertinence"] and v["juge_sans_hallucination"] and v["juge_priorisation"]


def test_juger_gere_l_echec(monkeypatch):
    # Si l'appel au juge échoue, juger renvoie None (le rapport le signalera).
    monkeypatch.setattr(juge.llm_client, "ask", lambda s, m: Reponse("erreur", False))
    assert juge.juger("sortie", "reponse") is None
