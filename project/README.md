# Radiant Analytics — Espace de collaboration

> Ce dossier `project/` est le **centre de gravité** du projet. Tout ce qui concerne la direction produit, l'architecture, la science, et les règles de collaboration se trouve ici.

---

## Par où commencer ?

| Tu veux... | Lis... |
|-----------|--------|
| Comprendre ce qu'on construit et pourquoi | [docs/VISION.md](docs/VISION.md) |
| Savoir où on en est et quoi faire ensuite | [docs/ROADMAP.md](docs/ROADMAP.md) |
| Comprendre comment c'est construit | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Savoir quelles données le moteur attend | [docs/DATA_REQUIREMENTS.md](docs/DATA_REQUIREMENTS.md) |
| Valider/modifier le fondement scientifique | [science/pe_fit_reference.md](science/pe_fit_reference.md) |
| Voir les specs techniques des instruments | [science/pe_fit_technical.md](science/pe_fit_technical.md) |
| Comprendre les règles d'autonomie de Claude | [AUTONOMY.md](AUTONOMY.md) |

---

## Organisation du dossier

```
project/
├── README.md               ← Ce fichier — point d'entrée
├── AUTONOMY.md             ← Ce que Claude peut faire seul vs ce qui requiert validation
│
├── docs/                   ← Vérité produit & architecture
│   ├── VISION.md           ← Les 7 questions, use cases, north star (SOURCE UNIQUE)
│   ├── ROADMAP.md          ← État actuel, Temps 1/2/3, backlog priorisé
│   ├── ARCHITECTURE.md     ← Système, flux, patterns, contraintes
│   └── DATA_REQUIREMENTS.md← Format snapshots, instruments, statut seed
│
└── science/                ← Fondement scientifique
    ├── pe_fit_reference.md ← Référentiel théorique P-E Fit (Kristof-Brown 2005)
    └── pe_fit_technical.md ← Specs techniques : formules, instruments, pondérations
```

---

## Règle d'or

**Chaque information a un seul endroit canonique.** Les autres fichiers (CLAUDE.md, backend/README, frontend/README) font référence à ces docs — ils ne dupliquent pas.

Quand une décision est prise ici, elle fait autorité sur tout le reste.
