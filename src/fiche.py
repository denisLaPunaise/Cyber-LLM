"""Fiche machine : l'état structuré de la box en cours (V2).

Le modèle tient cette fiche à jour à la fin de chaque réponse (bloc
[FICHE MACHINE]). On l'extrait, on garde la dernière version, et l'utilisateur
la consulte quand il veut avec la commande `fiche`.

Intérêt : une vue d'ensemble claire (IP, ports, services, identifiants, accès)
et, à l'étape 2, la reprise d'une box plus tard.
"""

MARQUEUR = "[FICHE MACHINE]"


def separer(reponse_complete: str) -> tuple[str, str]:
    """Sépare une réponse du modèle en (partie visible, fiche).

    La fiche est le bloc qui commence au marqueur [FICHE MACHINE] (que le modèle
    place en dernier). Sans marqueur, la fiche est vide et toute la réponse est
    considérée comme la partie visible.
    """
    if MARQUEUR in reponse_complete:
        avant, apres = reponse_complete.split(MARQUEUR, 1)
        visible = avant.rstrip()
        fiche = (MARQUEUR + apres).strip()
        return visible, fiche
    return reponse_complete, ""


class Fiche:
    """Garde la dernière version de la fiche machine de la session."""

    def __init__(self) -> None:
        self.contenu = ""

    def mettre_a_jour(self, texte: str) -> None:
        """Remplace la fiche par la dernière version produite par le modèle."""
        self.contenu = texte.strip()

    def est_vide(self) -> bool:
        """Vrai tant qu'aucune fiche n'a été produite."""
        return not self.contenu

    def vider(self) -> None:
        """Nouvelle machine : on repart d'une fiche vierge."""
        self.contenu = ""
