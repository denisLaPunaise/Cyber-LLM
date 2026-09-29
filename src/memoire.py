"""Mémoire de session.

En V0, chaque requête était indépendante : l'assistant oubliait tout entre
deux messages. Ce module garde l'historique de la conversation (tes sorties de
commandes + les réponses de l'assistant) pendant toute une session.

Résultat : l'assistant se souvient de la machine en cours (IP, ports, services,
identifiants déjà trouvés) et raisonne de façon cumulative, sans se répéter.
"""


class Memoire:
    """Retient l'historique des échanges, au format attendu par l'API Claude."""

    def __init__(self) -> None:
        # Liste de messages { "role": "user"/"assistant", "content": "..." }.
        # C'est EXACTEMENT le format que l'API Claude attend dans `messages`.
        self._messages: list[dict] = []

    def ajouter_utilisateur(self, texte: str) -> None:
        """Mémorise un message de l'utilisateur (sortie de commande, question)."""
        self._messages.append({"role": "user", "content": texte})

    def ajouter_assistant(self, texte: str) -> None:
        """Mémorise la réponse de l'assistant."""
        self._messages.append({"role": "assistant", "content": texte})

    def historique(self) -> list[dict]:
        """Renvoie tout l'historique, à envoyer à l'API à chaque tour."""
        return self._messages

    def vider(self) -> None:
        """Efface la mémoire : on repart de zéro (nouvelle machine)."""
        self._messages = []

    def est_vide(self) -> bool:
        """Vrai tant qu'aucun échange n'a eu lieu."""
        return len(self._messages) == 0
