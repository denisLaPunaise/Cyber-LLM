"""Logique de l'assistant : charge le prompt méthodo et interroge le LLM."""

from pathlib import Path

from . import llm_client

# Chemin vers le prompt système (le « cerveau » méthodo), à la racine du projet.
_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_pentest.md"


def load_system_prompt() -> str:
    """Charge le prompt système depuis prompts/system_pentest.md."""
    return _PROMPT_PATH.read_text(encoding="utf-8")


def analyser(entree_utilisateur: str) -> str:
    """Envoie l'entrée de l'utilisateur au LLM, guidé par le prompt méthodo.

    On recharge le prompt à chaque appel : tu peux l'éditer et voir l'effet
    immédiatement, sans relancer le programme.
    """
    system_prompt = load_system_prompt()
    return llm_client.ask(system_prompt, entree_utilisateur)
