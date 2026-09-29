"""Interface en ligne de commande : la boucle interactive de Cyber-LLM.

Lancement :  python -m src.cli
"""

import sys

from . import assistant, config
from .memoire import Memoire
from .fiche import Fiche

# S'assure que l'affichage gère accents et emojis quel que soit le terminal.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


BANNIERE = """
============================================================
  Cyber-LLM — Copilote de pentest (V2)
------------------------------------------------------------
  [!] Labs AUTORISES uniquement (TryHackMe, HackTheBox...).
  Tu gardes la decision : l'assistant PROPOSE, tu executes.
  Rien de destructif en automatique.
  [Memoire]  Il se souvient de la machine en cours.
  [Fiche]    'fiche' -> etat de la box (IP, ports, acces...).
             'nouvelle' -> repartir de zero.
============================================================
"""


def lire_entree() -> str:
    """Lit une entrée multi-lignes jusqu'à une ligne contenant seulement END.

    Renvoie '__quit__' (quitter), '__reset__' (nouvelle machine),
    '__fiche__' (afficher la fiche).
    """
    print("\n" + "-" * 60)
    print("Colle ta sortie (nmap, curl, ...) ou ta question.")
    print("Puis tape END sur une ligne seule pour envoyer.")
    print("('quit' quitter  |  'nouvelle' changer de machine  |  'fiche' voir l'etat)")
    lignes = []
    while True:
        try:
            ligne = input()
        except EOFError:  # Ctrl-Z puis Entrée (Windows) / Ctrl-D (Linux)
            return "__quit__"
        commande = ligne.strip().lower()
        # Ces commandes ne valent que tapées seules, avant tout contenu collé.
        if commande in ("quit", "exit") and not lignes:
            return "__quit__"
        if commande in ("nouvelle", "reset", "clear") and not lignes:
            return "__reset__"
        if commande in ("fiche", "etat", "état") and not lignes:
            return "__fiche__"
        if ligne.strip() == "END":
            break
        lignes.append(ligne)
    return "\n".join(lignes).strip()


def main() -> None:
    print(BANNIERE)

    # Vérifie la configuration tôt, avec un message clair si besoin.
    try:
        config.check_config()
    except RuntimeError as e:
        print(f"❌ Configuration : {e}")
        return

    # Un état par session : la mémoire (historique) et la fiche machine.
    memoire = Memoire()
    fiche = Fiche()

    while True:
        entree = lire_entree()
        if entree == "__quit__":
            print("\nÀ bientôt, et bon hack (légal) ! 👋")
            return
        if entree == "__reset__":
            memoire.vider()
            fiche.vider()
            print("\n🧹 Mémoire et fiche effacées — nouvelle machine, on repart de zéro.")
            continue
        if entree == "__fiche__":
            if fiche.est_vide():
                print("\n📋 Fiche machine : (vide — lance une première analyse pour la remplir)")
            else:
                print("\n📋 Fiche machine :\n")
                print(fiche.contenu)
            continue
        if not entree:
            print("(rien à analyser)")
            continue
        print("\n⏳ Analyse en cours...\n")
        print(assistant.analyser(entree, memoire, fiche))


if __name__ == "__main__":
    main()
