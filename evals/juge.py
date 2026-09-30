"""LLM-juge : un 2e appel à Claude qui NOTE la réponse du copilote.

Complète les critères mécaniques (criteres.py) par un jugement plus fin, bien
plus difficile à tricher qu'un simple mot-clé.

⚠️  À utiliser en connaissant ses limites : un LLM qui juge un LLM peut être
incohérent ou biaisé (préférence pour les réponses longues/assurées, angles
morts partagés). On garde donc AUSSI les critères mécaniques, et le juge reste
facultatif (il coûte un appel de plus par cas).
"""

from src import llm_client

# On impose un format de sortie strict pour pouvoir lire le verdict de façon fiable.
_SYSTEME_JUGE = (
    "Tu es un examinateur rigoureux. On te donne la SORTIE d'une commande de "
    "pentest (sur un lab autorisé) et la RÉPONSE d'un copilote. Évalue la "
    "réponse selon exactement trois questions, puis réponds STRICTEMENT dans ce "
    "format, sans rien ajouter :\n"
    "PERTINENCE: OUI ou NON\n"
    "HALLUCINATION: OUI ou NON\n"
    "PRIORISATION: OUI ou NON\n"
    "JUSTIFICATION: une phrase.\n\n"
    "Définitions :\n"
    "- PERTINENCE : les pistes proposées sont adaptées à cette sortie.\n"
    "- HALLUCINATION : la réponse invente des infos absentes de la sortie "
    "(OUI = elle invente, c'est un défaut).\n"
    "- PRIORISATION : l'ordre des pistes est raisonnable (du moins au plus "
    "intrusif)."
)


def _verdict_oui(lignes: dict, cle: str) -> bool:
    """True seulement si la ligne existe ET commence par « O » (OUI)."""
    return cle in lignes and lignes[cle].strip().upper().startswith("O")


def parser_verdict(texte: str) -> dict:
    """Transforme le texte du juge en verdicts booléens + justification.

    Prudence : si une ligne manque, le critère correspondant est considéré
    comme RATÉ (on ne valide pas ce qu'on n'a pas pu vérifier).
    """
    lignes = {}
    for ligne in texte.splitlines():
        if ":" in ligne:
            cle, _, val = ligne.partition(":")
            lignes[cle.strip().upper()] = val

    return {
        "juge_pertinence": _verdict_oui(lignes, "PERTINENCE"),
        # « sans hallucination » réussit si le juge a explicitement dit NON.
        "juge_sans_hallucination": ("HALLUCINATION" in lignes)
        and not _verdict_oui(lignes, "HALLUCINATION"),
        "juge_priorisation": _verdict_oui(lignes, "PRIORISATION"),
        "justification": lignes.get("JUSTIFICATION", "").strip(),
    }


def juger(entree: str, reponse_copilote: str):
    """Note la réponse du copilote.

    Renvoie le dict de verdicts, ou None si l'appel au juge a échoué.
    """
    message = (
        "----- SORTIE DE COMMANDE -----\n" + entree
        + "\n\n----- RÉPONSE DU COPILOTE -----\n" + reponse_copilote
    )
    reponse = llm_client.ask(_SYSTEME_JUGE, [{"role": "user", "content": message}])
    if not reponse.succes:
        return None
    return parser_verdict(reponse.texte)
