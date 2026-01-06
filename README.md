# ticketing-dashboard

Dashboard d’analytics de billetterie alimenté par les webhooks Petzi, un backend Firebase (Functions + Firestore) et un frontend Vue 3.

---

## Objectif

- Recevoir les événements Petzi (ex: `ticket_created`, `ticket_updated`) via un endpoint HTTP.
- Normaliser et persister les données dans Firestore (collection `tickets`).
- Explorer les ventes en temps réel via une UI Vue (KPIs, graphiques, carte, recherche avancée).

---

## Fonctionnalités

### Backend

- Endpoint webhook HTTP Firebase Function `petziWebhook`.
- Vérification de signature HMAC (`Petzi-Signature`) avec un secret partagé (`PETZI_SECRET`).
- Écriture idempotente dans Firestore : le document est indexé par `ticketNumber` quand disponible (`set(..., { merge: true })`).
- Mapping robuste du prix (supporte `price` en objet `{ amount, currency }` ou en string legacy).

### Frontend

- Données en temps réel via Firestore (listeners `onSnapshot`).
- Pages :
  - `/overview` : KPIs (CA, billets, événements, prix moyen…), top événements (CA), dernières ventes.
  - `/dashboard` : charts + carte, avec filtres multi-sélection (événements / catégories), synchronisés dans l’URL.
  - `/tickets` : listing + recherche/tri, filtres avancés (période, buyer, event, catégories, range de prix), presets de filtres en localStorage, synchronisés dans l’URL.
- Visualisations :
  - Évolution des ventes (journalier/hebdomadaire, cumulées et/ou par période)
  - Répartition des ventes par événement (camembert)
  - Carte géographique (Leaflet) basée sur les codes postaux
  - Panier moyen (tickets/transaction)
  - Comparaison mensuelle année sur année

---

## Stack

- Frontend: Vue 3 + Vite, Tailwind CSS, Chart.js (`vue-chartjs`), Leaflet.
- Backend: Firebase Functions (Node 22), Firestore, Firebase Emulator Suite.
- Outils: Node.js (voir versions ci-dessous), Firebase CLI, Python (scripts de simulation webhook).

---

## Prérequis

- Node.js
  - Frontend: `^20.19.0 || >=22.12.0`
  - Firebase Functions: Node 22
- Firebase CLI installé (`firebase --version`)
- Python 3 (pour les scripts `backend/petzi_simulator*.py`)

---

## Démarrage rapide (local)

### 1) Installer les dépendances

Frontend:

```bash
cd frontend
npm install
```

Functions:

```bash
cd backend/functions
npm install
```

### 2) Configurer les variables d’environnement

#### Backend (secret webhook)

Créer `backend/functions/.env` (non versionné) :

```env
PETZI_SECRET=TON_SECRET_PARTAGE
```

#### Frontend (Firebase)

Le frontend a besoin d’une config Firebase (même en mode emulator) : créer `frontend/.env.local` :

```env
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...

# Optionnel: connecter Firestore à l'émulateur local
VITE_USE_FIREBASE_EMULATOR=true
```

Notes:

- `VITE_USE_FIREBASE_EMULATOR` (ou `VITE_USE_FIREBASE_EMULATORS`) accepte `true|1|yes|y`.
- En dev, le frontend logge un diagnostic si la config est absente.

### 3) Lancer Firebase Emulator Suite

Depuis `backend/`:

```bash
cd backend
firebase emulators:start
```

UI emulators: http://127.0.0.1:4000

### 4) Lancer le frontend

```bash
cd frontend
npm run dev
```

Accès:

- Home: http://localhost:5173/
- Overview: http://localhost:5173/overview
- Dashboard: http://localhost:5173/dashboard
- Tickets: http://localhost:5173/tickets

---

## Tester le webhook Petzi en local (simulateur)

Le backend attend un header `Petzi-Signature` de la forme `t=<unix>,v1=<hex_hmac>` où la signature est calculée comme:

`HMAC_SHA256(PETZI_SECRET, "<timestamp>.<body_json>")`

### Pré-requis Python

Les scripts utilisent `requests`. Si besoin:

```bash
pip install requests
```

### Endpoint local

URL émulateur typique:

`http://127.0.0.1:5001/<project-id>/us-central1/petziWebhook`

`<project-id>` correspond au project id Firebase (voir la sortie de `firebase emulators:start`).

### Exemples

Envoyer 1 ticket (template):

```bash
cd backend
python .\petzi_simulator_template.py http://127.0.0.1:5001/<project-id>/us-central1/petziWebhook TON_SECRET_PARTAGE
```

Générer un lot de tickets (simulateur):

```bash
cd backend
python .\petzi_simulator.py http://127.0.0.1:5001/<project-id>/us-central1/petziWebhook TON_SECRET_PARTAGE
```

Si tout est OK:

- le script renvoie `OK`
- des documents apparaissent dans Firestore Emulator, collection `tickets`:
  http://127.0.0.1:4000/firestore

---

## Données stockées (Firestore)

Collection: `tickets`

Champs principaux (issus du mapping du webhook):

- Ticket: `ticketNumber`, `ticketType`, `ticketCategory`, `ticketTitle`, `generatedAt`
- Événement: `eventType`, `eventId`, `eventName`
- Session (première session): `sessionName`, `sessionDate`, `sessionTime`, `venueCity`, `venuePostcode`, ...
- Acheteur: `buyerFirstName`, `buyerLastName`, `buyerPostcode`, ...
- Prix: `priceAmount`, `priceCurrency`
- Technique: `createdAt` (ISO), `rawPayload`

---

## Déploiement (prod)

Fonctions:

```bash
cd backend/functions
npm run deploy
```

À prévoir côté infra:

- Définir `PETZI_SECRET` en environnement (prod) plutôt que via `.env` local.
- Ajuster les règles Firestore ([backend/firestore.rules](backend/firestore.rules)) selon l’exposition souhaitée.
- **Liste des tickets** : `http://localhost:5173/tickets`

---

## 🔧 Configuration Frontend

### Variables d'environnement

Créez un fichier `.env.local` dans `frontend/` avec :

```env
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

Ces valeurs sont disponibles dans la console Firebase de votre projet.

### Dépendances Frontend

Les dépendances suivantes ont été ajoutées :
- `chart.js` et `vue-chartjs` : pour les graphiques
- `leaflet` : pour les cartes géographiques
- `tailwindcss`, `postcss`, `autoprefixer` : pour le styling

---

Le front Vue se connecte à Firestore en temps réel pour lire la collection `tickets` et construire ces vues.
