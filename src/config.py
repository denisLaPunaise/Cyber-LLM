"""Configuration de Cyber-LLM.

Charge les variables du fichier .env et expose les réglages du projet
(modèle, effort de raisonnement, workspace, longueur max) au reste du code.
"""

import os

from dotenv import load_dotenv

# Lit le fichier .env (à la racine du projet) et met ses variables à
# disposition via os.getenv(...). À faire une seule fois, au chargement.
load_dotenv()

# Modèle Claude à utiliser. On le lit depuis le .env — bonne pratique :
# la configuration vit dans .env, pas « en dur » dans le code.
MODEL = os.getenv("CYBER_LLM_MODEL", "").strip()

# (Optionnel) ID du workspace Anthropic (format wrkspc_...).
# Utile UNIQUEMENT si ta clé API n'est pas déjà rattachée à un workspace.
WORKSPACE_ID = os.getenv("ANTHROPIC_WORKSPACE_ID", "").strip()

# Effort de raisonnement : "low", "medium", "high", "xhigh", "max".
# Plus élevé = réflexion plus poussée (meilleure qualité) mais plus de tokens.
# "high" est un bon compromis par défaut.
EFFORT = os.getenv("CYBER_LLM_EFFORT", "high").strip()

# Plafond de longueur de la réponse (la réflexion interne + le texte final
# comptent dedans). Généreux pour ne pas couper une réponse ; on ne paie que
# les tokens réellement générés.
MAX_TOKENS = 16000


def check_config() -> None:
    """Vérifie que la configuration nécessaire est présente.

    Lève une erreur claire (au lieu d'un plantage cryptique) si la clé API
    ou le modèle manquent.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "Clé API introuvable. Crée un fichier .env (copie de .env.example) "
            "contenant :  ANTHROPIC_API_KEY=sk-ant-..."
        )
    if not MODEL:
        raise RuntimeError(
            "Modèle non défini. Vérifie que ton .env contient la ligne "
            "CYBER_LLM_MODEL=...  (voir .env.example)."
        )
