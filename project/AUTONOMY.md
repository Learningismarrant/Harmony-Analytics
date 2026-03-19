# Règles d'autonomie — Claude dans ce projet

> Ce document définit ce que Claude peut faire **sans demander confirmation**, ce qu'il annonce brièvement avant de faire, et ce qui nécessite une **validation explicite de Quentin**. L'objectif est de maximiser la vitesse d'exécution sans surprise.

---

## Niveaux d'autonomie

### TIER 1 — Autonome (aucune confirmation requise)

Claude fait, signale en résumé après.

**Documentation & mémoire**
- Lire n'importe quel fichier du projet
- Mettre à jour `project/docs/`, `project/science/`, `project/README.md`
- Mettre à jour les fichiers mémoire (`memory/`)
- Corriger des fautes ou incohérences dans les docs

**Code — corrections & cohérence**
- Corriger les **bugs listés dans CLAUDE.md** (known bugs)
- Fixer un test en échec en utilisant le même pattern existant
- Syncer `@harmony/types` après un changement de schéma Pydantic
- Refactorer dans un pattern existant (sans nouvelle abstraction)
- Ajouter des tests co-localisés suivant le pattern existant

**Agents**
- Invoquer `debug` dès qu'un test échoue (proactif, sans demander)
- Invoquer `head-of-science` avant toute modification d'engine (non-bloquant pour Quentin)
- Invoquer `schema-sync` et `security-review` en parallèle après backend (non-bloquant)

---

### TIER 2 — Annonce puis fait (Claude prévient, attend 30s max, puis exécute)

Claude indique ce qu'il va faire dans sa réponse. Si pas d'objection de Quentin, il continue.

**Code — nouvelles fonctionnalités**
- Créer de nouveaux fichiers suivant des patterns existants
- Ajouter un endpoint suivant exactement le pattern router→service→repo
- Créer une migration Alembic non-destructive
- Invoquer `orchestrator` pour décomposer une feature (produit un plan, pas du code)

**Structure**
- Créer de nouveaux dossiers dans `project/`
- Déplacer des fichiers (en laissant une note de redirection dans l'original)

---

### TIER 3 — Confirmation requise avant d'agir

Claude **propose et attend** une réponse explicite de Quentin.

**Décisions structurantes**
- Toute modification des formules du moteur (`engine/pe_fit/`) — même mineure
- Ajout d'une nouvelle dépendance (pip, npm)
- Changement du format du `psychometric_snapshot` ou `vessel_snapshot`
- Changement du flux d'authentification
- Toute migration Alembic **destructive** (DROP, ALTER avec perte de données)
- Modification de `TESTS_AND_SECURITY.md` ou des règles de sécurité
- Modification des prompts des agents (`.claude/agents/*.md`)

**Suppressions**
- Supprimer un fichier source (code, pas doc)
- Supprimer ou archiver un agent

---

### TIER 4 — Jamais sans instruction explicite

Claude refuse même si demandé implicitement.

- `git push` vers remote
- `git push --force` / opérations destructives git
- `--no-verify` sur un commit (bypass hooks)
- DROP TABLE ou TRUNCATE sur une base non-seed
- Modifier les credentials / secrets / variables d'environnement de production
- Publier vers un service externe (npm publish, deploy, etc.)

---

## Règles contextuelles

### Sur les tests
- Si `pytest` ou `npm test` échoue après une modification → **invoquer `debug` immédiatement**, sans attendre Quentin
- Ne jamais commiter avec des tests en échec
- 0 régression est non-négociable : si un fix casse un test existant, le fix est mauvais

### Sur la science
- Toute modification d'une formule dans `engine/pe_fit/` → **`head-of-science` en premier**, même pour un changement de coefficient
- Les profils idéaux SDT (`MOTIVATION_PROFILES`) sont Temps 0 — les traiter comme indicatifs, ne pas les modifier sans validation scientifique

### Sur la communication
- Claude ne demande pas de confirmation pour des choses classées TIER 1 ou TIER 2
- Claude ne reformule pas ce qu'il vient de faire — il est concis
- Si Claude détecte une ambiguïté sur le scope d'une tâche : il pose **une seule question** ciblée, pas une liste

### Sur les priorités
- En cas de doute sur la priorité : se référer à `project/docs/ROADMAP.md`
- Les bugs connus dans `.claude/CLAUDE.md` ont priorité sur les nouvelles features

---

## Zones de flexibilité créative

Dans ces domaines, Claude peut proposer des approches alternatives sans que ce soit demandé :

- Structure de dossier ou nommage de fichier (si le choix actuel crée de la confusion)
- Formulation des messages d'erreur / libellés UI (toujours en cohérence avec le thème maritime)
- Séquençage d'un plan d'exécution (proposer de paralléliser ou réordonner)
- Détection proactive d'un risque de régression ou d'incohérence architecturale

Dans ces cas, Claude **signale sa proposition** avant d'agir (TIER 2).
