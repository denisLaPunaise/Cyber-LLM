"""Exécuteur de commandes (V3) : lance UNIQUEMENT des commandes de recon sûres,
après validation humaine, et sans shell (anti-injection).

Garde-fous (défense en couches) :
1. refus de tout caractère de chaînage shell ( ; | & > < ` $ ( ) \\ ) ;
2. le premier mot doit être dans la LISTE BLANCHE (recon lecture seule) ;
3. refus de tout motif destructif ;
4. exécution SANS shell, avec timeout, sortie capturée (et tronquée).

La validation humaine (le « o » dans la CLI) reste le garde-fou FINAL : rien ne
tourne sans l'accord explicite de l'utilisateur.
"""

import os
import re
import shlex
import subprocess

# Outils de reconnaissance en lecture seule, autorisés à l'exécution assistée.
LISTE_BLANCHE = {
    "nmap",
    "enum4linux", "enum4linux-ng", "smbmap", "nbtscan",
    "dig", "nslookup", "host",
    "whatweb", "gobuster", "ffuf", "dirb", "nikto",
    "snmpwalk", "showmount",
}

# Caractères qui permettraient d'enchaîner ou d'injecter une autre commande.
_METACARACTERES = [";", "|", "&", ">", "<", "`", "$", "(", ")", "\n", "\\"]

# Motifs destructeurs refusés même si le binaire était autorisé (ceinture + bretelles).
_MOTIFS_DESTRUCTEURS = ["rm -r", "mkfs", "dd if=", "shutdown", "reboot", "del /", "format "]

# Taille max de sortie réinjectée (évite de faire exploser le contexte et le coût).
_MAX_SORTIE = 4000


def est_autorisee(commande: str) -> tuple[bool, str]:
    """Dit si une commande peut être exécutée automatiquement, et sinon pourquoi."""
    cmd = commande.strip()
    if not cmd:
        return False, "commande vide"
    if any(m in cmd for m in _METACARACTERES):
        return False, "contient un caractère shell (chaînage interdit)"
    bas = cmd.lower()
    if any(motif in bas for motif in _MOTIFS_DESTRUCTEURS):
        return False, "motif destructif détecté"
    binaire = os.path.basename(cmd.split()[0])
    if binaire not in LISTE_BLANCHE:
        return False, f"« {binaire} » hors liste blanche"
    return True, "ok"


def commande_proposee(reponse: str) -> str | None:
    """Renvoie la 1re commande ENTRE BACKTICKS éligible à l'auto-run, ou None."""
    for bloc in re.findall(r"`([^`]+)`", reponse):
        ok, _ = est_autorisee(bloc.strip())
        if ok:
            return bloc.strip()
    return None


def executer(commande, timeout: int = 180) -> str:
    """Exécute la commande SANS shell et renvoie la sortie (tronquée).

    `commande` peut être une chaîne (découpée façon shell) ou une liste d'args.
    """
    args = commande if isinstance(commande, list) else shlex.split(commande)
    try:
        proc = subprocess.run(
            args, shell=False, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError:
        return f"[outil introuvable : « {args[0]} » n'est pas installé sur cette machine]"
    except subprocess.TimeoutExpired:
        return f"[timeout après {timeout}s — relance la commande à la main si besoin]"
    except Exception as e:  # garde-fou : on ne laisse jamais la CLI planter
        return f"[erreur d'exécution : {e}]"

    sortie = ((proc.stdout or "") + (proc.stderr or "")).strip() or "[aucune sortie]"
    if len(sortie) > _MAX_SORTIE:
        sortie = sortie[:_MAX_SORTIE] + "\n[...sortie tronquée...]"
    return sortie
