# Feuille de route — prochaines étapes

**Ordre convenu :** B → C → D — **tous faits ✅**. Seul **A** reste, volontairement reporté.
**A est reporté** : les réflexes de méthodologie seront ajoutés au prompt une
fois le cours TryHackMe / eJPT terminé (quand les notes seront prêtes).

---

## ✅ Déjà fait
- **V0** — copilote de base : coller une sortie → pistes priorisées.
- **V1** — mémoire de session + prompt caching.
- **V2** — fiche machine + sauvegarde/chargement + commande `help`.
- **B (tests)** — suite `pytest` (35 tests) : mémoire, fiche, assistant, notation, données, juge, exécuteur.
- **C (evals)** — banc d'évaluation robuste : 8 cas (dev + test cachés), critères
  mécaniques **+ LLM-juge** (pertinence, hallucination, priorisation), et rapport
  détaillé sauvegardé pour relecture humaine.
- **D (V3)** — exécution assistée : mode `auto`, liste blanche recon, validation
  humaine (`o/N`), exécution sans shell + timeout. Tout le reste reste manuel.

---

## ⏳ À faire

Toutes les étapes prévues (B, C, D) sont faites. Il ne reste que **A**, reporté
volontairement (ci-dessous). Pistes d'évolution libres : étoffer le jeu de cas
des evals, ajouter des commandes à la liste blanche, soigner la présentation
pour le portfolio.

---

## 🅰️ Reporté

### A — Enrichir le prompt méthodo
Ajouter des réflexes concrets (service → CVE, checklists de privesc Linux/Windows,
identifiants par défaut…) dans `prompts/system_pentest.md`, au fil de
l'apprentissage.
- **Déclencheur :** quand le cours TryHackMe / eJPT est prêt et que les notes
  sont disponibles.
- Peu de code, gros impact sur la qualité des pistes.
