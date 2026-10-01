"""Tests de l'exécuteur (src/executeur.py).

On vérifie surtout les GARDE-FOUS (ce qui est autorisé / refusé) — c'est la
partie critique pour la sécurité. L'exécution réelle est testée sur une commande
anodine et portable (l'interpréteur Python), jamais sur un outil dangereux.
"""

import sys

from src.executeur import est_autorisee, commande_proposee, executer


def test_autorise_commandes_recon():
    assert est_autorisee("nmap -sV 10.10.10.50")[0]
    assert est_autorisee("enum4linux -a 10.10.10.50")[0]
    assert est_autorisee("/usr/bin/gobuster dir -u http://10.10.10.50")[0]  # chemin complet


def test_refuse_hors_liste_blanche():
    assert not est_autorisee("cat /etc/passwd")[0]
    assert not est_autorisee("curl http://10.10.10.50")[0]   # curl exclu par prudence
    assert not est_autorisee("sudo nmap 10.10.10.50")[0]     # sudo n'est pas la liste


def test_refuse_chainage_shell():
    assert not est_autorisee("nmap 10.10.10.50; rm -rf /")[0]   # ';'
    assert not est_autorisee("nmap 10.10.10.50 | tee out.txt")[0]  # '|'
    assert not est_autorisee("nmap 10.10.10.50 > out.txt")[0]      # '>'
    assert not est_autorisee("echo $(whoami)")[0]                   # '$(' et hors liste


def test_refuse_motif_destructif():
    assert not est_autorisee("rm -rf /")[0]
    assert not est_autorisee("mkfs.ext4 /dev/sda")[0]


def test_commande_proposee_prend_la_premiere_eligible():
    # La 1re piste (curl) est exclue -> on doit retomber sur enum4linux.
    reponse = (
        "[PISTES]\n1. `curl http://10.10.10.50`\n"
        "2. `enum4linux -a 10.10.10.50` pour lister les partages"
    )
    assert commande_proposee(reponse) == "enum4linux -a 10.10.10.50"


def test_commande_proposee_aucune():
    assert commande_proposee("Aucune commande ici.") is None
    assert commande_proposee("essaie `cat /etc/passwd`") is None  # hors liste


def test_executer_capture_la_sortie():
    # Commande portable et inoffensive : l'interpréteur Python lui-même.
    sortie = executer([sys.executable, "-c", "print('cyber-ok')"])
    assert "cyber-ok" in sortie


def test_executer_outil_introuvable():
    sortie = executer(["binaire_qui_nexiste_pas_12345"])
    assert "introuvable" in sortie.lower()
