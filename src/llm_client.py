"""Client LLM : le seul endroit du projet qui parle à l'API Claude.

Isoler l'appel ici permet de changer de fournisseur plus tard
(API → local via Ollama) sans toucher au reste du code.
"""

import anthropic

from . import config

# Le client n'est créé qu'au premier appel (initialisation « paresseuse ») :
# ça évite de planter au simple import si la clé n'est pas encore configurée.
_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        headers = {}
        # Si un workspace est précisé dans .env, on l'ajoute en en-tête.
        # Nécessaire quand la clé API n'est pas déjà rattachée à un workspace.
        if config.WORKSPACE_ID:
            headers["anthropic-workspace-id"] = config.WORKSPACE_ID
        # Anthropic() lit automatiquement ANTHROPIC_API_KEY dans l'environnement
        # (variable chargée depuis .env par config.py).
        _client = anthropic.Anthropic(default_headers=headers)
    return _client


def ask(system_prompt: str, user_message: str) -> str:
    """Envoie une requête à Claude et renvoie la réponse en texte.

    - system_prompt : les instructions permanentes (le « cerveau » méthodo).
    - user_message  : ce que colle l'utilisateur (sortie de commande, question).
    """
    config.check_config()  # message clair si la clé / le modèle manquent
    client = _get_client()

    try:
        response = client.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=system_prompt,
            # Réflexion interne « adaptive » : le modèle décide quand/combien
            # réfléchir. Sur Opus 4.8 elle est désactivée par défaut ; on
            # l'active ici pour de meilleures pistes (non affichée à l'écran).
            thinking={"type": "adaptive"},
            # Niveau d'effort (profondeur de raisonnement / dépense de tokens).
            output_config={"effort": config.EFFORT},
            messages=[{"role": "user", "content": user_message}],
        )
    except anthropic.AuthenticationError:
        return "❌ Clé API invalide. Vérifie ANTHROPIC_API_KEY dans ton fichier .env."
    except anthropic.PermissionDeniedError:
        return (
            "🚫 Ta clé n'a pas accès à cette ressource — le modèle "
            f"« {config.MODEL} » n'est peut-être pas activé sur ton compte."
        )
    except anthropic.NotFoundError:
        return (
            f"🔎 Modèle introuvable : « {config.MODEL} ». "
            "Vérifie et corrige CYBER_LLM_MODEL dans ton .env."
        )
    except anthropic.BadRequestError as e:
        # 400 = la requête elle-même pose problème (modèle, workspace, effort...).
        # On affiche le message exact renvoyé par l'API pour pouvoir diagnostiquer.
        return f"⚠️ Requête refusée par l'API (400) : {e.message}"
    except anthropic.RateLimitError:
        return "⏳ Trop de requêtes d'un coup. Patiente quelques secondes et réessaie."
    except anthropic.APIConnectionError:
        return "🌐 Problème de connexion. Vérifie ta connexion internet."
    except anthropic.APIStatusError as e:
        if e.status_code >= 500:
            return f"⚠️ Erreur serveur de l'API (code {e.status_code}). Réessaie dans un moment."
        return f"⚠️ Erreur de l'API (code {e.status_code}) : {e.message}"

    # Le modèle peut décliner une requête (classifieur de sûreté, ex. « cyber »).
    # On le gère proprement au lieu de renvoyer une réponse vide.
    if response.stop_reason == "refusal":
        categorie = ""
        if response.stop_details is not None:
            categorie = f" (catégorie : {response.stop_details.category})"
        return (
            "🛑 Le modèle a préféré ne pas répondre à cette requête"
            + categorie
            + ".\nRappel : cet assistant est prévu pour des labs autorisés. "
            "Reformule en précisant le contexte (machine de lab / CTF), "
            "ou passe à une autre étape."
        )

    # Cas normal : response.content est une liste de blocs (réflexion + texte).
    # On assemble uniquement le texte des blocs de type « text ».
    morceaux = [bloc.text for bloc in response.content if bloc.type == "text"]
    return "\n".join(morceaux).strip()
