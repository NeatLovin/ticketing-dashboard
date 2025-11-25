# ticketing-dashboard

Dashboard d’analytics de tickets basé sur les webhooks Petzi, un backend Firebase et un frontend Vue.js pour des insights en temps réel.

## 🔍 Objectif du projet

- Centraliser les événements provenant de Petzi (tickets, ventes, événements, etc.)
- Les stocker et/ou transformer via un backend serverless (Firebase)
- Les afficher dans un dashboard en temps réel (Vue.js)
- Permettre d’analyser les performances (ventes, fréquentation, répartition par événement, etc.)

## 🧱 Stack technique (prévue)

- **Frontend**
  - [Vue.js 3](https://vuejs.org/) (Composition API)
  - Vite / Vue CLI (à confirmer)
  - UI kit (ex : TailwindCSS, Vuetify ou autre – à définir)
  - Authentification (Firebase Auth ou autre – à définir)

- **Backend**
  - **Firebase**
    - Cloud Firestore ou Realtime Database (à choisir)
    - Cloud Functions pour recevoir et traiter les webhooks Petzi
    - Firebase Hosting pour servir le frontend (optionnel)
  - Webhooks Petzi (endpoint HTTP exposé via Firebase Functions)

- **Outils**
  - Node.js (LTS)
  - npm / pnpm / yarn (à définir)
  - Git + GitHub

## 🚧 État actuel

> Début de projet, structure en cours de mise en place.

- [ ] Initialiser le projet Vue
- [ ] Configurer Firebase (projet, services nécessaires)
- [ ] Créer une fonction webhook pour Petzi
- [ ] Définir le modèle de données pour les analytics
- [ ] Mettre en place un premier dashboard minimal (ex : total des tickets vendus)

## ⚙️ Installation (prévisionnel)

1. **Cloner le dépôt**

   ```bash
   git clone https://github.com/<ton-compte>/ticketing-dashboard.git
   cd ticketing-dashboard
   ```

2. **Installer les dépendances**

   ```bash
   npm install
   # ou
   pnpm install
   ```

3. **Configurer l’environnement**

   Créer un fichier `.env.local` (ou équivalent) à la racine du frontend :

   ```bash
   cp .env.example .env.local
   ```

   Puis renseigner :

   ```bash
   VITE_FIREBASE_API_KEY=...
   VITE_FIREBASE_AUTH_DOMAIN=...
   VITE_FIREBASE_PROJECT_ID=...
   # etc.
   ```

   Et les secrets nécessaires côté Firebase Functions (via `firebase functions:config:set`).

## ▶️ Lancement du projet en développement

**Frontend (Vue)**

```bash
npm run dev
# ou
pnpm dev
```

**Backend (Firebase)**

```bash
firebase emulators:start
```

> À adapter une fois la structure du repo figée (dossiers `functions`, `hosting`, `src`, etc.).

## 📡 Webhooks Petzi (brouillon de design)

- Exposer une route `POST /webhooks/petzi` via Firebase Functions.
- Valider la signature Petzi (si disponible).
- Normaliser les événements reçus (ex : `ticket.created`, `ticket.refunded`, etc.).
- Persister les données nécessaires dans Firestore (ex : collection `tickets`, `events`, `venues`).
- Déclencher éventuellement des agrégations (Cloud Functions, collections dédiées aux stats).

## 📊 Dashboard (brouillon de design)

Quelques idées de widgets :

- Nombre total de tickets vendus (période donnée)
- CA total / par événement
- Top événements par ventes
- Répartition des ventes dans le temps (courbe)
- Répartition par type de billet / tarif

## 🗺️ Roadmap (indicative)

- **Phase 1** : Setup technique (Firebase + Vue + CI simple)
- **Phase 2** : Réception et stockage des webhooks Petzi
- **Phase 3** : Premier dashboard temps réel basique
- **Phase 4** : Filtres avancés / export / multi-utilisateur
- **Phase 5** : Optimisations perf, sécurité, UX

## 🤝 Contribution

Pour l’instant, le projet est en phase de bootstrap.  
Notes rapides :

- Utiliser des branches thématiques (`feature/...`, `fix/...`)
- Ouvrir une PR avec description courte et claire
- Ajouter au minimum des tests unitaires de base sur les fonctions critiques

## 📄 Licence

À définir (MIT, Apache-2.0, etc.).
