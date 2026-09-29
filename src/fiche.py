"""Fiche machine : l'état structuré de la box en cours (V2).

Le modèle tient cette fiche à jour à la fin de chaque réponse (bloc
[FICHE MACHINE]). On l'extrait, on garde la dernière version, et l'utilisateur
la consulte quand il veut avec la commande `fiche`.

Elle peut aussi être sauvegardée puis rechargée (dossier `sessions/`) pour
reprendre une box un autre jour.
"""

from pathlib import Path

MARQUEUR = "[FICHE MACHINE]"

# Dossier où l'on range les fiches sauvegardées (une par box). Ignoré par git.
_DOSSIER = Path(__file__).resolve().parent.parent / "sessions"


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


def _chemin(nom: str) -> Path:
    """Construit un chemin de sauvegarde sûr à partir d'un nom libre.

    On ne garde que des caractères simples (lettres, chiffres, - et _) : ça
    évite qu'un nom comme « ../secret » ne sorte du dossier des sessions.
    """
    propre = "".join(c for c in (nom or "") if c.isalnum() or c in "-_")
    if not propre:
        propre = "derniere"
    return _DOSSIER / (propre + ".txt")


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

    def sauver(self, nom: str = "derniere") -> Path:
        """Écrit la fiche dans sessions/<nom>.txt et renvoie le chemin."""
        chemin = _chemin(nom)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(self.contenu, encoding="utf-8")
        return chemin

    def charger(self, nom: str = "derniere") -> Path:
        """Recharge la fiche depuis sessions/<nom>.txt.

        Lève FileNotFoundError si le fichier n'existe pas (géré par la CLI).
        """
        chemin = _chemin(nom)
        self.contenu = chemin.read_text(encoding="utf-8").strip()
        return chemin
