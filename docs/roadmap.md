# Feuille de route — prochaines étapes

**Ordre convenu :** B → C → D. **B et C faits ✅** — prochaine étape : **D**.
**A est reporté** : les réflexes de méthodologie seront ajoutés au prompt une
fois le cours TryHackMe / eJPT terminé (quand les notes seront prêtes).

---

## ✅ Déjà fait
- **V0** — copilote de base : coller une sortie → pistes priorisées.
- **V1** — mémoire de session + prompt caching.
- **V2** — fiche machine + sauvegarde/chargement + commande `help`.
- **B (tests)** — suite `pytest` (22 tests) : mémoire, fiche, assistant, notation, données.
- **C (evals)** — banc d'évaluation de la qualité : 8 cas types (dev/test),
  critères (format, ancrage, sécurité, actionnable), scores dev/test séparés.
  *En cours de renforcement : LLM-juge + sauvegarde des réponses.*

---

## ⏳ À faire, dans l'ordre

### 1) D — V3 : exécution assistée en lecture seule
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
