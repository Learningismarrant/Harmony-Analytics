# Q2 — GCA Matrices Abstraites — Spécifications Items

**Version :** 1.0 — Mars 2026
**Construct :** Intelligence fluide (Gf) — raisonnement inductif sur patterns visuels (Carroll 1993)
**Format :** Grille 3×3 de symboles — la case R3C3 est manquante — candidat choisit parmi 4 options
**Nature :** Spécifications pour implémentation graphique — pas d'items graphiques dans ce fichier
**Difficulté :** Progressive — items 01–14 : Facile | 15–27 : Moyen | 28–40 : Difficile
**Droits :** Items custom originaux — non dérivés de Raven SPM/APM ni de ICAR ni de MaRs-IB.

---

## Format de spécification

```
Item M-XX | Difficulté: [Facile/Moyen/Difficile]
Règle: [description de la transformation logique]
Symbole: [type de forme géométrique à utiliser]
Grille: [description ligne par ligne R1/R2/R3]
Réponse: [contenu de la case R3C3]
Distractor trap: [erreurs fréquentes à proposer comme distracteurs]
```

---

## Niveau Facile (Items 01–14)

**Item M-01** | Difficulté: Facile
Règle: Rotation 90° horaire — chaque ligne présente la même forme pivotée
Symbole: Flèche directionnelle simple
Grille: R1: →, ↓, ← | R2: →, ↓, ← | R3: →, ↓, [?]
Réponse: ← (flèche gauche)
Distractor trap: → (aucune rotation perçue), ↑ (rotation inverse), ↓ (répétition)

**Item M-02** | Difficulté: Facile
Règle: Progression de taille croissante gauche → droite (petit, moyen, grand) — identique sur chaque ligne
Symbole: Cercle plein
Grille: R1: petit, moyen, grand | R2: petit, moyen, grand | R3: petit, moyen, [?]
Réponse: grand cercle
Distractor trap: cercle moyen (confusion position centrale), très grand cercle (extrapolation)

**Item M-03** | Difficulté: Facile
Règle: Progression du remplissage gauche → droite (vide → rayé → plein) — constante par ligne
Symbole: Carré
Grille: R1: vide, rayé, plein | R2: vide, rayé, plein | R3: vide, rayé, [?]
Réponse: carré plein
Distractor trap: carré vide (retour début de cycle), carré partiellement rempli

**Item M-04** | Difficulté: Facile
Règle: Nombre d'éléments croissant colonne par colonne (col1=1, col2=2, col3=3) — constant sur toutes les lignes
Symbole: Petit triangle
Grille: R1: 1, 2, 3 | R2: 1, 2, 3 | R3: 1, 2, [?]
Réponse: 3 triangles
Distractor trap: 4 triangles (extrapolation incorrecte)

**Item M-05** | Difficulté: Facile
Règle: Réflexion axe vertical — pattern vide/rayé/vide sur chaque ligne
Symbole: Forme en "L"
Grille: R1: L normal, L reflété, L normal | R2: idem | R3: L normal, L reflété, [?]
Réponse: L normal
Distractor trap: L reflété, L pivoté 90°

**Item M-06** | Difficulté: Facile
Règle: Remplissage suit un cycle en diagonale principale (vide→rayé→plein, décalé d'une case par ligne)
Symbole: Pentagone régulier
Grille: R1: vide, rayé, plein | R2: rayé, plein, vide | R3: plein, vide, [?]
Réponse: rayé
Distractor trap: plein (continuation incorrecte), vide

**Item M-07** | Difficulté: Facile
Règle: Colonne 1 = pointe en haut, colonne 3 = rotation 180° (pointe en bas), colonne 2 = identique colonne 1
Symbole: Triangle isocèle
Grille: R1: △, △, ▽ | R2: △, △, ▽ | R3: △, △, [?]
Réponse: ▽ (pointe en bas)
Distractor trap: △ (pas de transformation), △ incliné 90°

**Item M-08** | Difficulté: Facile
Règle: Nombre d'éléments identique sur toute la ligne (R1=1 partout, R2=2 partout, R3=3 partout)
Symbole: Étoile à 5 branches
Grille: R1: 1, 1, 1 | R2: 2, 2, 2 | R3: 3, 3, [?]
Réponse: 3 étoiles
Distractor trap: 4 étoiles, 2 étoiles

**Item M-09** | Difficulté: Facile
Règle: Forme déterminée par la colonne (col1=cercle, col2=carré, col3=triangle) — taille constante
Symbole: Formes géométriques simples
Grille: R1: ○, □, △ | R2: ○, □, △ | R3: ○, □, [?]
Réponse: triangle moyen
Distractor trap: cercle (confusion colonnes), triangle grand (confusion taille)

**Item M-10** | Difficulté: Facile
Règle: Alternance demi-cercle ouvert en bas / ouvert en haut — symétrie ligne à ligne
Symbole: Demi-cercle
Grille: R1: ⌢, ⌢, ⌢ | R2: ⌣, ⌣, ⌣ | R3: ⌢, ⌢, [?]
Réponse: ⌢ (ouvert en bas)
Distractor trap: ⌣ (ouvert en haut), cercle complet

**Item M-11** | Difficulté: Facile
Règle: Taille décroissante de gauche à droite (grand, moyen, petit) — constante par ligne
Symbole: Losange
Grille: R1: grand, moyen, petit | R2: grand, moyen, petit | R3: grand, moyen, [?]
Réponse: petit losange
Distractor trap: très petit (extrapolation), moyen

**Item M-12** | Difficulté: Facile
Règle: Alternance rectangle horizontal / vertical — pattern H, V, H sur chaque ligne
Symbole: Rectangle
Grille: R1: H, V, H | R2: H, V, H | R3: H, V, [?]
Réponse: rectangle horizontal
Distractor trap: rectangle vertical, carré

**Item M-13** | Difficulté: Facile
Règle: Nombre d'éléments suit col1=1, col2=2, col3=3 — constant sur toutes les lignes
Symbole: Croix (+)
Grille: R1: 1, 2, 3 | R2: 1, 2, 3 | R3: 1, 2, [?]
Réponse: 3 croix
Distractor trap: 4 croix, 2 croix

**Item M-14** | Difficulté: Facile
Règle: Pattern vide/plein/vide identique sur chaque ligne (positions impaires = vide, paires = plein)
Symbole: Hexagone
Grille: R1: vide, plein, vide | R2: vide, plein, vide | R3: vide, plein, [?]
Réponse: hexagone vide
Distractor trap: hexagone plein, hexagone rayé

---

## Niveau Moyen (Items 15–27)

**Item M-15** | Difficulté: Moyen
Règle: Rotation 90° horaire ET progression remplissage (vide→rayé→plein) simultanément en ligne
Symbole: Flèche courbe
Grille: R1: →vide, ↓rayé, ←plein | R2: ↓vide, ←rayé, ↑plein | R3: ←vide, ↑rayé, [?]
Réponse: →plein (rotation 90° depuis ↑, remplissage = plein car 3e position)
Distractor trap: →rayé (remplissage oublié), ↓plein (mauvaise rotation)

**Item M-16** | Difficulté: Moyen
Règle: Intersection logique — cellule = éléments présents dans la même ligne ET la même colonne
Symbole: Formes simples (carré, cercle, triangle)
Grille: R1: {○,□}, {□,△}, {□} | R2: {○,△}, {△,□}, {△} | R3: {○}, {□}, [?]
Réponse: {} (ensemble vide — pas d'intersection entre {○} et {□})
Distractor trap: {○} ou {□} (union au lieu d'intersection)

**Item M-17** | Difficulté: Moyen
Règle: Taille croissante en diagonale secondaire + forme constante sur chaque ligne
Symbole: Pentagone
Grille: R1: grand, grand, grand | R2: moyen, grand, grand | R3: petit, moyen, [?]
Réponse: grand pentagone
Distractor trap: moyen (continuation erreur diagonale), très grand

**Item M-18** | Difficulté: Moyen
Règle: Latin square 3×3 sur le remplissage — chaque ligne ET chaque colonne contient vide, rayé, plein une fois
Symbole: Étoile à 6 branches
Grille: R1: vide, rayé, plein | R2: rayé, plein, vide | R3: plein, vide, [?]
Réponse: rayé
Distractor trap: plein (répétition colonne), vide (répétition ligne)

**Item M-19** | Difficulté: Moyen
Règle: Latin square 3×3 sur les formes — chaque ligne ET chaque colonne contient ○, □, △ une fois
Symbole: Formes géométriques simples, même taille
Grille: R1: ○, □, △ | R2: △, ○, □ | R3: □, △, [?]
Réponse: ○ (cercle)
Distractor trap: □ (répétition ligne R3), △ (répétition colonne C3)

**Item M-20** | Difficulté: Moyen
Règle: Nombre d'éléments = R + C − 1 (position dans la grille, R et C à partir de 1)
Symbole: Point/disque
Grille: R1: 1, 2, 3 | R2: 2, 3, 4 | R3: 3, 4, [?]
Réponse: 5 points
Distractor trap: 6 (extrapolation), 7 ou 4

**Item M-21** | Difficulté: Moyen
Règle: Rotation 45° horaire + taille croissante (petit→moyen→grand) sur chaque ligne
Symbole: Flèche simple
Grille: R1: →petit, ↘moyen, ↓grand | R2: ↘petit, ↓moyen, ↙grand | R3: ↓petit, ↙moyen, [?]
Réponse: ←grand (rotation 45° depuis ↙, taille grand)
Distractor trap: ↙grand (pas de rotation), ←moyen (mauvaise taille)

**Item M-22** | Difficulté: Moyen
Règle: Union de formes — R3 de chaque colonne = superposition de R1 et R2
Symbole: Figures composées
Grille: R1: ○, □, △ | R2: □, △, ○ | R3: ○+□, □+△, [?]
Réponse: △+○ (superposition)
Distractor trap: △ seul, ○+□ (mauvaise colonne)

**Item M-23** | Difficulté: Moyen
Règle: Symétrie réflexive par rapport à la diagonale principale — grille[i][j] = grille[j][i]
Symbole: Croix asymétrique (un bras plus long)
Grille: R1: A, B, C | R2: D, A, E | R3: F, G, [?]
Réponse: A (élément diagonal, invariant par réflexion diagonale)
Distractor trap: B ou D (confusion ligne/colonne), miroir de A

**Item M-24** | Difficulté: Moyen
Règle: Arrangement des formes dans chaque cellule pivote d'une position à droite entre chaque ligne
Symbole: Mix ○□△ dans chaque cellule (3 formes par cellule)
Grille: R1: ○□△ | ○□△ | ○□△ | R2: △○□ | △○□ | △○□ | R3: □△○ | □△○ | [?]
Réponse: □△○ (même arrangement que R3C1 et R3C2)
Distractor trap: ○□△ (retour R1), △○□ (retour R2)

**Item M-25** | Difficulté: Moyen
Règle: Suppression progressive — R1 = 3 formes, R2 = 2 formes, R3 = 1 forme (la forme absente de R1C dans chaque colonne)
Symbole: ○, □, △
Grille: R1: {○,□,△} | {○,□,△} | {○,□,△} | R2: {○,□} | {□,△} | {○,△} | R3: {△} | {○} | [?]
Réponse: {□} (forme manquante dans la colonne 3)
Distractor trap: {○} ou {△} (déjà présents en R3), {□,△}

**Item M-26** | Difficulté: Moyen
Règle: Rotation 90° + inversion remplissage (plein↔vide) simultanément
Symbole: Demi-disque orientable
Grille: R1: D→plein, D↓vide, D←plein | R2: D↓plein, D←vide, D↑plein | R3: D←plein, D↑vide, [?]
Réponse: D→plein (rotation 90° depuis D↑, inversion vide→plein)
Distractor trap: D→vide (inversion manquée), D↓plein (mauvaise rotation)

**Item M-27** | Difficulté: Moyen
Règle: Latin square triple — 3 attributs simultanés (forme, taille, remplissage), chacun apparaît une fois par ligne ET par colonne
Symbole: Combinaisons forme (○□△) × taille (S,M,L) × remplissage (vide,rayé,plein)
Grille: R1: ○-S-vide, □-M-rayé, △-L-plein | R2: △-M-vide, ○-L-rayé, □-S-plein | R3: □-L-vide, △-S-rayé, [?]
Réponse: ○-M-plein (seule combinaison complétant les 3 Latin squares simultanément)
Distractor trap: ○-L-plein (taille déjà en R3), □-M-plein (forme déjà en R3)

---

## Niveau Difficile (Items 28–40)

**Item M-28** | Difficulté: Difficile
Règle: Nombre d'éléments = R + C − 1 où R,C ∈ {1,2,3}
Symbole: Petit carré
Grille: R1: 1, 2, 3 | R2: 2, 3, 4 | R3: 3, 4, [?]
Réponse: 5 carrés
Distractor trap: 4 (continuation R3), 6 (extrapolation)

**Item M-29** | Difficulté: Difficile
Règle: Rotation 90° appliquée au groupe de symboles + progression de taille du groupe
Symbole: Groupe de 3 points formant un triangle orienté
Grille: Chaque case = groupe de points tournant de 90° et augmentant en taille case après case
Réponse: Groupe de 3 points, grande taille, orientation = rotation 90° depuis la case précédente
Distractor trap: Rotation correcte mauvaise taille, taille correcte rotation inverse

**Item M-30** | Difficulté: Difficile
Règle: XOR logique — R3 = éléments présents dans R1 OU R2 mais pas les deux (différence symétrique)
Symbole: Lignes (H = horizontale, V = verticale, D = diagonale)
Grille: R1C3: {H,D} | R2C3: {V,D} | (utiliser même logique pour toutes colonnes) R3: [?]
Réponse: {H} pour la colonne 3 (H∆V : H présent dans R1 seulement ; V présent dans R2 seulement ; D présent dans les deux → exclu)
Distractor trap: {V} ou {H,V} (confusion XOR/OR/AND), {} (confusion avec AND)

**Item M-31** | Difficulté: Difficile
Règle: Chaque ligne est une rotation de 120° de la précédente (rotation positionnelle des cellules dans la grille)
Symbole: Étoile asymétrique (une branche plus longue — permet de distinguer l'orientation)
Grille: La position de la branche longue tourne de 120° entre chaque ligne
Réponse: Orientation après deux rotations de 120° depuis R1
Distractor trap: Rotation 90° (erreur d'angle), rotation 180°, rotation de l'étoile seule sans rotation positionnelle

**Item M-32** | Difficulté: Difficile
Règle: Double règle — remplissage : (R1+R2) mod 3 = R3 avec vide=0, rayé=1, plein=2 ; taille : max(R1,R2) = R3
Symbole: Hexagone régulier (3 tailles × 3 remplissages)
Grille: R1: vide-S, rayé-M, plein-L | R2: rayé-M, plein-L, vide-S | R3: rayé-M, (1+2)mod3=0→vide-L, [?]
Réponse: (2+0)mod3=2→plein, max(L,S)=L → plein-L
Distractor trap: vide-L (mauvais calcul remplissage), plein-S (mauvaise règle taille)

**Item M-33** | Difficulté: Difficile
Règle: Un point cible unique se déplace en spirale case après case (R1C1→R1C2→R1C3→R2C3→R2C2→R2C1→R3C1→R3C2→R3C3)
Symbole: Point noir unique sur fond blanc, 3×3 = grille 3D temps (3 états successifs représentent 3 moments)
Grille: Moment 1: point en R1C1 | Moment 2: point en R1C2 | Moment 3: point en [?]
Réponse: Point en R1C3 (étape suivante de la spirale)
Distractor trap: Déplacement linéaire simple (ne pas reconnaître la spirale)

**Item M-34** | Difficulté: Difficile
Règle: Incrément d'angle de rotation de 45° à chaque case lu de gauche à droite, haut en bas (0°, 45°, 90°, ..., 315°, 360°=0°)
Symbole: Flèche fine
Grille: R1: → (0°), ↗ (45°), ↑ (90°) | R2: ↖ (135°), ← (180°), ↙ (225°) | R3: ↓ (270°), ↘ (315°), [?]
Réponse: → (360°=0°, retour au cycle)
Distractor trap: ↗ (continuation sans cycle), ↑, ↘ (valeur adjacente)

**Item M-35** | Difficulté: Difficile
Règle: Chaque ligne "annule" un attribut de la précédente (ligne 1→2 : transformation forme ; ligne 2→3 : transformation taille ; ligne 3 : transformation remplissage)
Symbole: Triangle scalène (3 tailles, 3 remplissages)
Grille: Définir 3 transformations dans cet ordre : forme change en R2, taille change en R3, remplissage change dans la case cible
Réponse: Résultat des 3 transformations appliquées séquentiellement
Distractor trap: Ne pas identifier l'ordre des attributs transformés

**Item M-36** | Difficulté: Difficile
Règle: Parité du nombre total d'éléments (R1C + R2C) détermine la taille de R3C : pair → grand, impair → petit
Symbole: Croix (éléments comptables)
Grille: R1: 1, 2, 3 | R2: 3, 2, 1 | R3: grand(1+3=4 pair), grand(2+2=4 pair), [?]
Réponse: grand (3+1=4, pair → grand)
Distractor trap: petit (confusion parité), 4 éléments (confusion comptage avec taille)

**Item M-37** | Difficulté: Difficile
Règle: Rotation 45° + ajout d'un bras à l'étoile (+1 branche à chaque pas) + progression remplissage (vide→rayé→plein) — 3 règles simultanées
Symbole: Étoile polygonale (nombre de branches variable : 3, 4, 5)
Grille: R1: 3br-0°-vide, 4br-45°-rayé, 5br-90°-plein | R2: 3br-45°-rayé, 4br-90°-plein, 5br-135°-vide | R3: 3br-90°-plein, 4br-135°-vide, [?]
Réponse: 5br-180°-rayé
Distractor trap: 5br-90°-plein (mauvais angle), 4br-180°-rayé (mauvais nombre de branches)

**Item M-38** | Difficulté: Difficile
Règle: Contenant/contenu — forme extérieure suit règle A (rotation), forme intérieure suit règle B indépendante (taille croissante). Les deux règles doivent être identifiées séparément.
Symbole: Forme extérieure (cercle/carré/triangle) contenant un triangle intérieur orientable
Grille: R1: ○+△↑S, ○+△→M, ○+△↓L | R2: □+△→S, □+△↓M, □+△←L | R3: △+△↓S, △+△←M, [?]
Réponse: △(ext)+△↑(int)-taille L
Distractor trap: △+△↓L (mauvaise rotation intérieure), □+△↑L (mauvaise forme extérieure)

**Item M-39** | Difficulté: Difficile
Règle: Symétrie rotationnelle d'ordre 3 — la grille entière a une symétrie de rotation de 120°. La case cible = rotation de 120° d'une case symétrique connue.
Symbole: Arrangement de 2 formes dans chaque cellule (cercle + carré à positions relatives différentes)
Grille: Définir 8 cases avec symétrie rotationnelle — la 9e (R3C3) est déductible par rotation de 120° depuis R1C1 ou R2C2
Réponse: Rotation de 120° de la cellule symétrique équivalente
Distractor trap: Symétrie réflexive (miroir) confondue avec symétrie rotationnelle

**Item M-40** | Difficulté: Difficile
Règle: Chaque colonne encode une opération logique différente (AND, OR, XOR) appliquée aux attributs binaires de R1 et R2 pour produire R3
Symbole: Hexagone divisé en 3 zones, chaque zone = attribut binaire (plein/vide)
Grille: Col1 (AND): R1={1,0,1}, R2={1,1,0} → R3={1,0,0} | Col2 (OR): R1={0,1,0}, R2={1,0,1} → R3={1,1,1} | Col3 (XOR): R1={1,1,0}, R2={0,1,1} → R3={1,0,1} → [?] = hexagone avec zones 1 et 3 pleines, zone 2 vide
Réponse: Hexagone avec pattern {1,0,1} (zones 1 et 3 pleines, zone 2 vide)
Distractor trap: Appliquer la même opération (AND uniquement) à toutes les colonnes

---

## Notes psychométriques — Étalonnage Q2 Matrices

- **α Cronbach cible :** ≥ 0.80 sur les 40 items. Surveiller les items complexes (M-32 à M-40) — retrait si discrimination < 0.20.
- **Originalité des items :** tenir un registre de création documentant l'indépendance vis-à-vis de Raven SPM/APM et ICAR (consultation juridique recommandée avant commercialisation).
- **Implémentation graphique :** utiliser SVG ou canvas — les symboles doivent être reproductibles programmatiquement. Définir une bibliothèque de formes de base (cercle, carré, triangle, losange, étoile, flèche, hexagone, demi-cercle) avec attributs taille et remplissage.
- **Référence :** Carroll, J.B. (1993). *Human cognitive abilities*. Cambridge University Press.
