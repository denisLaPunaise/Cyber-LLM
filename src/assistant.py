"""Logique de l'assistant : charge le prompt méthodo et interroge le LLM."""

from pathlib import Path

from . import llm_client
from .memoire import Memoire

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


def analyser(entree_utilisateur: str, memoire: Memoire) -> str:
    """Interroge le LLM en tenant compte de toute la session (V1).

    On recharge le prompt à chaque appel : tu peux l'éditer et voir l'effet
    immédiatement, sans relancer le programme.
    """
    system_prompt = load_system_prompt()
    message = _CONTEXTE + entree_utilisateur + "\n----- FIN DE LA SORTIE -----"

    # On prépare la liste à envoyer = tout l'historique + le nouveau message,
    # SANS toucher encore à la mémoire (concaténation = nouvelle liste).
    messages = memoire.historique() + [{"role": "user", "content": message}]
    reponse = llm_client.ask(system_prompt, messages)

    # On ne mémorise QUE si l'échange a réussi. Pourquoi ? L'API exige que les
    # rôles ALTERNENT (user → assistant → user...). Si on gardait un message
    # utilisateur sans réponse valable (erreur / refus), le tour suivant ferait
    # deux « user » de suite → l'API planterait. Donc : on enregistre la paire
    # (question + réponse) ensemble, ou rien.
    if reponse.succes:
        memoire.ajouter_utilisateur(message)
        memoire.ajouter_assistant(reponse.texte)

    return reponse.texte
