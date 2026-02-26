# Référentiel de Tests et de Sécurité

Ce document définit les standards stricts de qualité (tests) et de sécurité à appliquer sur l'ensemble de la stack (Backend, Web Frontend, Mobile Frontend). 
**Instruction pour l'IA (Claude Code) :** Tu dois systématiquement te référer à ces règles avant de générer, modifier ou valider du code. Aucune PR ou feature ne doit omettre ces aspects.

---

## 1. Typologie et Stratégie de Tests

Toute nouvelle fonctionnalité doit être accompagnée de ses tests. Nous appliquons la pyramide des tests :

### A. Tests Unitaires (Logique métier isolée)
* **Outils :** Jest / Vitest.
* **Périmètre :** Fonctions utilitaires, calculs, reducers, hooks custom (Frontend), et services métier (Backend).
* **Règle :** Chaque fonction complexe doit avoir au moins un test passant (cas nominal) et un test d'échec (cas d'erreur ou limites).
* **Couverture visée :** > 80% sur la logique métier.

### B. Tests d'Intégration (Communication entre composants)
* **Outils :** Supertest (Backend API), React Testing Library (Web/Mobile).
* **Périmètre :** * *Backend :* Routes API avec une base de données de test (ou mockée intelligemment). Vérifier que le contrôleur, le service et le repository communiquent bien.
    * *Frontend :* Intégration entre un composant UI et un état global (Zustand/Redux) ou un mock d'API (MSW - Mock Service Worker).

### C. Tests End-to-End (E2E) (Parcours utilisateur critique)
* **Outils :** Playwright / Cypress (Web), Detox / Maestro (Mobile).
* **Périmètre :** Parcours vitaux (Inscription, Connexion, Paiement, Création d'une ressource principale).
* **Règle :** Ne pas surcharger les E2E. Se concentrer uniquement sur les "Happy Paths" et les blocages majeurs.

---

## 2. Règles de Sécurité (Backend & API)

La sécurité est "Secure by Design". Les règles suivantes doivent être implémentées sur tous les endpoints exposés.

### A. Protection contre les abus (Rate Limiting)
* **Rate Limiter Global :** Limiter les requêtes par IP (ex: 100 requêtes / 15 minutes) pour éviter le DDoS.
* **Rate Limiter Sensible :** Limiter de façon très stricte les routes d'authentification (`/login`, `/reset-password`) pour prévenir le Brute Force (ex: 5 essais / 15 minutes).
* **Quotas Utilisateurs :** Si des endpoints font appel à des API tierces coûteuses, implémenter un "Token Bucket" ou une limitation par ID Utilisateur pour éviter l'explosion des coûts.

### B. Validation des Entrées (Input Sanitization)
* **Outil :** Utilisation obligatoire de `Zod` ou `Yup` pour valider TOUS les payloads (Body, Query params, URL params).
* **Règle :** Ne jamais faire confiance au Frontend. Rejeter toute requête ne correspondant pas strictement au schéma avec une erreur HTTP 400 (Bad Request).
* **Prévention XSS & SQLi :** Échapper les caractères dangereux. Utiliser un ORM/Query Builder (ex: Prisma, Drizzle) qui gère nativement la prévention des injections SQL.

### C. Sécurité de l'Authentification et des Sessions
* **JWT :** Si utilisation de JSON Web Tokens, durée de vie courte (ex: 15 mins) avec un système de Refresh Token sécurisé.
* **Stockage Web :** Stocker les tokens d'accès dans des cookies `HttpOnly`, `Secure` et `SameSite=Strict`. Ne **jamais** les stocker dans le `localStorage`.
* **Stockage Mobile :** Utiliser le Secure Storage natif (ex: `expo-secure-store`, `react-native-keychain`).

### D. Sécurité Spécifique aux LLMs (Prompt Injections)
* Ne jamais concaténer directement les inputs utilisateurs dans les prompts envoyés à l'IA sans les encadrer correctement (ex: utilisation de délimiteurs comme `"""` ou `<user_input>`).
* Filtrer les PII (Personal Identifiable Information) avant de les envoyer à des services tiers si non strictement nécessaires.

### E. Configuration Serveur
* **Headers de sécurité :** Utiliser `Helmet.js` (si Express/Node) pour définir les headers HSTS, X-Content-Type-Options, etc.
* **CORS :** Configuration stricte. Seuls les domaines du frontend Web et de l'application mobile sont autorisés. Pas de wildcard `*` en production.

---

## 3. Bonnes Pratiques de Maintenance

### A. Gestion des Secrets
* Les clés API (`CLAUDE_API_KEY`, `DATABASE_URL`, etc.) ne doivent **jamais** être écrites en dur dans le code.
* Passer exclusivement par des variables d'environnement (`process.env`).
* Valider la présence de ces variables au démarrage de l'application (ex: avec `T3 Env` ou Zod).

### B. Gestion des Erreurs et Logs
* Ne jamais renvoyer la stack trace (détails techniques de l'erreur) au client en production.
* Utiliser un format d'erreur standardisé pour le Frontend : `{ "error": true, "message": "Description lisible", "code": "ERR_CODE" }`.
* Logguer les erreurs critiques côté serveur (utilisation de Sentry, Winston ou Pino).

### C. Qualité du Code
* **Linting & Formatage :** ESLint et Prettier sont obligatoires. Aucune erreur de linter n'est tolérée.
* **Typage Strict :** TypeScript en mode `strict: true`. L'utilisation de `any` est formellement interdite. Si le type est inconnu, utiliser `unknown` et faire du type narrowing.