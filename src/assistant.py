"""Logique de l'assistant : charge le prompt méthodo et interroge le LLM."""

from pathlib import Path

from . import llm_client

# Chemin vers le prompt système (le « cerveau » méthodo), à la racine du projet.
_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_pentest.md"

# Contexte rappelé à CHAQUE requête. Il cadre le message comme une demande
# d'aide pédagogique sur un lab autorisé. Double effet :
#  1) de meilleures réponses (le modèle sait ce qu'on attend) ;
#  2) beaucoup moins de refus du classifieur de sûreté sur des sorties brutes,
#     car l'intention légitime est explicite.
_CONTEXTE = (
    "Contexte : je m'entraîne sur une machine de lab AUTORISÉE "
    "(TryHackMe / HackTheBox / CTF), dans un but pédagogique et de préparation "
    "à la certification eJPT. Je garde la main sur chaque action et j'exécute "
    "les commandes moi-même.\n\n"
    "Voici la sortie de ma dernière commande (ou ma question). Aide-moi à "
    "décider la suite selon la méthodologie de pentest :\n\n"
    "----- DÉBUT DE LA SORTIE -----\n"
)


def load_system_prompt() -> str:
    """Charge le prompt système depuis prompts/system_pentest.md."""
    return _PROMPT_PATH.read_text(encoding="utf-8")


def analyser(entree_utilisateur: str) -> str:
    """Envoie l'entrée de l'utilisateur au LLM, guidé par le prompt méthodo.

    On recharge le prompt à chaque appel : tu peux l'éditer et voir l'effet
    immédiatement, sans relancer le programme.
    """
    system_prompt = load_system_prompt()
    message = _CONTEXTE + entree_utilisateur + "\n----- FIN DE LA SORTIE -----"
    return llm_client.ask(system_prompt, message)
