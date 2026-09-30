# Feuille de route — prochaines étapes

**Ordre convenu :** B → C → D. **B est fait ✅** — prochaine étape : **C**, puis **D**.
**A est reporté** : les réflexes de méthodologie seront ajoutés au prompt une
fois le cours TryHackMe / eJPT terminé (quand les notes seront prêtes).

---

## ✅ Déjà fait
- **V0** — copilote de base : coller une sortie → pistes priorisées.
- **V1** — mémoire de session + prompt caching.
- **V2** — fiche machine + sauvegarde/chargement + commande `help`.
- **B (tests)** — suite `pytest` (14 tests) : mémoire, fiche, assistant.

---

## ⏳ À faire, dans l'ordre

### 1) C — Évaluation de la qualité des réponses (evals)
Un petit banc d'essai qui **note** les réponses du copilote sur des cas types.
- Vérifie : format respecté (`[ANALYSE]` / `[PISTES]` / `[AVANT D'AGIR]` /
  `[FICHE MACHINE]`), pistes pertinentes, aucune invention de résultat.
- But : **mesurer la qualité de l'IA** — compétence clé pour l'axe IA × sécurité.

### 2) D — V3 : exécution assistée en lecture seule
Proposer une commande **non-destructive** puis, **après validation humaine
explicite**, l'exécuter et réinjecter la sortie automatiquement.
- À cadrer avec soin : liste blanche de commandes en lecture seule, validation à
  chaque fois, rien de destructif.
- Point d'attention : cela touche au principe « l'humain exécute » → design
  prudent, on garde l'humain aux commandes.

---

## 🅰️ Reporté

### A — Enrichir le prompt méthodo
Ajouter des réflexes concrets (service → CVE, checklists de privesc Linux/Windows,
identifiants par défaut…) dans `prompts/system_pentest.md`, au fil de
l'apprentissage.
- **Déclencheur :** quand le cours TryHackMe / eJPT est prêt et que les notes
  sont disponibles.
- Peu de code, gros impact sur la qualité des pistes.
