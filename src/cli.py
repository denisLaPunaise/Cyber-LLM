"""Interface en ligne de commande : la boucle interactive de Cyber-LLM.

Lancement :  python -m src.cli            (mode normal)
             python -m src.cli --auto     (exécution assistée activée au départ)
"""

import sys

from . import assistant, config, executeur
from .memoire import Memoire
from .fiche import Fiche

# S'assure que l'affichage gère accents et emojis quel que soit le terminal.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


BANNIERE = """
============================================================
  Cyber-LLM — Copilote de pentest (V3)
------------------------------------------------------------
  [!] Labs AUTORISES uniquement (TryHackMe, HackTheBox...).
  Tu gardes la decision : l'assistant PROPOSE, tu valides.
  Rien de destructif en automatique.
  [Memoire] Il se souvient de la machine en cours.
  [Auto]    'auto' (de)active l'execution assistee (recon).
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
  les etapes suivantes. Tu gardes la decision. Labs AUTORISES.

  ENVOYER UN MESSAGE
  Colle ton texte, puis tape END sur une ligne seule.

  COMMANDES (a taper seules, sans END)
  fiche            Voir la fiche machine (IP, ports, acces...).
  sauver [nom]     Sauvegarder la fiche       (ex: sauver blue).
  charger [nom]    Recharger une fiche sauvee (ex: charger blue).
  auto             (De)activer l'execution assistee (recon).
  nouvelle         Effacer memoire + fiche (nouvelle machine).
  help             Afficher cette aide.
  quit             Quitter.

  EXECUTION ASSISTEE (auto)
  Quand 'auto' est actif, l'outil propose de lancer LUI-MEME
  les commandes de recon sures (liste blanche), apres ton
  accord (o/N). Tout le reste (exploitation, destructif,
  hors liste) reste MANUEL : c'est toi qui lances.
  A utiliser sur la machine qui a les outils (ex: Kali).
============================================================
"""


def lire_entree() -> str:
    """Lit une entrée multi-lignes jusqu'à une ligne contenant seulement END.

    Renvoie un sentinel pour une commande tapée seule : '__quit__', '__help__',
    '__reset__', '__fiche__', '__auto__', ou '__sauver__' / '__charger__'
    (avec un nom optionnel après ':'). Sinon renvoie le texte collé.
    """
    print("\n" + "-" * 60)
    print("Colle ta sortie (nmap, curl, ...) ou ta question, puis END pour envoyer.")
    print("Commandes : help | fiche | sauver/charger | auto | nouvelle | quit")
    lignes = []
    while True:
        try:
            ligne = input()
        except EOFError:  # Ctrl-Z puis Entrée (Windows) / Ctrl-D (Linux)
            return "__quit__"
        commande = ligne.strip().lower()
        premier = commande.split()[0] if commande.split() else ""
        if not lignes:  # commandes reconnues seulement avant tout contenu collé
            if commande in ("quit", "exit"):
                return "__quit__"
            if commande in ("help", "aide", "?"):
                return "__help__"
            if commande in ("nouvelle", "reset", "clear"):
                return "__reset__"
            if commande in ("fiche", "etat", "état"):
                return "__fiche__"
            if commande in ("auto",):
                return "__auto__"
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


def _tenter_autorun(reponse: str) -> str | None:
    """Propose d'exécuter une commande de recon de la réponse (si éligible).

    Renvoie la sortie à réinjecter si la commande a été lancée, sinon None.
    """
    cmd = executeur.commande_proposee(reponse)
    if not cmd:
        return None
    rep = input(f"\n▶ Lancer « {cmd} » ?  [o/N] : ").strip().lower()
    if rep not in ("o", "oui"):
        return None
    print("   ⚙️  exécution en cours...\n")
    sortie = executeur.executer(cmd)
    print(sortie)
    return f"Sortie de la commande `{cmd}` :\n{sortie}"


def main(auto_initial: bool = False) -> None:
    print(BANNIERE)

    try:
        config.check_config()
    except RuntimeError as e:
        print(f"❌ Configuration : {e}")
        return

    memoire = Memoire()
    fiche = Fiche()
    auto_actif = auto_initial
    if auto_actif:
        print("🟢 Auto-run ACTIVÉ au démarrage (--auto).")

    entree_auto = None  # sortie d'une commande à réinjecter automatiquement

    while True:
        if entree_auto is not None:
            entree, entree_auto = entree_auto, None
        else:
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
        if entree == "__auto__":
            auto_actif = not auto_actif
            if auto_actif:
                print("\n🟢 Auto-run ACTIVÉ — l'outil proposera de lancer les commandes de recon (liste blanche).")
            else:
                print("\n⚪ Auto-run désactivé — tu lances les commandes toi-même.")
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
            memoire.vider()
            print(f"\n📂 Fiche chargée depuis {chemin} :\n")
            print(fiche.contenu)
            print("\n(la prochaine analyse repartira de cet état)")
            continue
        if not entree:
            print("(rien à analyser)")
            continue

        print("\n⏳ Analyse en cours...\n")
        reponse = assistant.analyser(entree, memoire, fiche)
        print(reponse)

        if auto_actif:
            suite = _tenter_autorun(reponse)
            if suite is not None:
                entree_auto = suite  # relance l'analyse avec la sortie obtenue


if __name__ == "__main__":
    main(auto_initial="--auto" in sys.argv)
