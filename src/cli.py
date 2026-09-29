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
  [Memoire] Il se souvient de la machine en cours.
  Tape 'help' pour l'aide et la liste des commandes.
============================================================
"""


AIDE = """
============================================================
  Cyber-LLM — aide
------------------------------------------------------------
  A QUOI CA SERT
  Copilote de pentest : tu colles la sortie d'une commande
  (nmap, curl, enum4linux...), l'assistant analyse et propose
  les etapes suivantes. Tu gardes la decision et tu executes
  toi-meme. Labs AUTORISES uniquement.

  ENVOYER UN MESSAGE
  Colle ton texte, puis tape END sur une ligne seule.

  COMMANDES (a taper seules, sans END)
  fiche            Voir la fiche machine (IP, ports, acces...).
  sauver [nom]     Sauvegarder la fiche       (ex: sauver blue).
  charger [nom]    Recharger une fiche sauvee (ex: charger blue).
  nouvelle         Effacer memoire + fiche (nouvelle machine).
  help             Afficher cette aide.
  quit             Quitter.

  MEMOIRE & FICHE
  L'assistant se souvient de la session et tient une fiche
  machine a jour. 'sauver'/'charger' servent a reprendre une
  box un autre jour (fichiers dans le dossier sessions/).
============================================================
"""


def lire_entree() -> str:
    """Lit une entrée multi-lignes jusqu'à une ligne contenant seulement END.

    Renvoie un sentinel pour une commande tapée seule : '__quit__', '__help__',
    '__reset__', '__fiche__', ou '__sauver__' / '__charger__' (avec un nom
    optionnel après ':'). Sinon renvoie le texte collé.
    """
    print("\n" + "-" * 60)
    print("Colle ta sortie (nmap, curl, ...) ou ta question, puis END pour envoyer.")
    print("Commandes : help | fiche | sauver/charger | nouvelle | quit")
    lignes = []
    while True:
        try:
            ligne = input()
        except EOFError:  # Ctrl-Z puis Entrée (Windows) / Ctrl-D (Linux)
            return "__quit__"
        commande = ligne.strip().lower()
        premier = commande.split()[0] if commande.split() else ""
        # Les commandes ne valent que tapées seules, avant tout contenu collé.
        if not lignes:
            if commande in ("quit", "exit"):
                return "__quit__"
            if commande in ("help", "aide", "?"):
                return "__help__"
            if commande in ("nouvelle", "reset", "clear"):
                return "__reset__"
            if commande in ("fiche", "etat", "état"):
                return "__fiche__"
            # sauver / charger acceptent un nom optionnel : « sauver blue »
            if premier in ("sauver", "save"):
                parts = ligne.strip().split(maxsplit=1)
                return "__sauver__" + (":" + parts[1].strip() if len(parts) > 1 else "")
            if premier in ("charger", "load"):
                parts = ligne.strip().split(maxsplit=1)
                return "__charger__" + (":" + parts[1].strip() if len(parts) > 1 else "")
        if ligne.strip() == "END":
            break
        lignes.append(ligne)
    return "\n".join(lignes).strip()


def _nom_depuis_sentinel(entree: str) -> str:
    """Extrait le nom passé après ':' dans un sentinel sauver/charger."""
    return entree.split(":", 1)[1] if ":" in entree else "derniere"


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
        if entree == "__help__":
            print(AIDE)
            continue
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
        if entree.startswith("__sauver__"):
            if fiche.est_vide():
                print("\n(fiche vide — rien à sauvegarder pour l'instant)")
            else:
                chemin = fiche.sauver(_nom_depuis_sentinel(entree))
                print(f"\n💾 Fiche sauvegardée dans {chemin}")
            continue
        if entree.startswith("__charger__"):
            nom = _nom_depuis_sentinel(entree)
            try:
                chemin = fiche.charger(nom)
            except FileNotFoundError:
                print(f"\n🔎 Aucune sauvegarde trouvée (nom : {nom}).")
                continue
            # On repart proprement de l'état chargé (la prochaine analyse le rappellera).
            memoire.vider()
            print(f"\n📂 Fiche chargée depuis {chemin} :\n")
            print(fiche.contenu)
            print("\n(la prochaine analyse repartira de cet état)")
            continue
        if not entree:
            print("(rien à analyser)")
            continue

        print("\n⏳ Analyse en cours...\n")
        print(assistant.analyser(entree, memoire, fiche))


if __name__ == "__main__":
    main()
