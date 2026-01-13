# ticketing-dashboard

Dashboard d’analytics de billetterie alimenté par les webhooks **Petzi**, un backend **Firebase** (Cloud Functions + Firestore) et un frontend **Vue 3**.

> Objectif : fournir une **vue temps réel** (KPIs, graphiques, carte, recherche) + des pages “métier” (overview, agenda, détail événement) pour analyser les ventes.

---

## ✨ Fonctionnalités

### Backend (Firebase Functions + Firestore)
- Endpoint webhook HTTP : `petziWebhook`
- Vérification de signature **HMAC** via header `Petzi-Signature` avec secret partagé `PETZI_SECRET`
- Persistance dans Firestore (collection `tickets`)
- Écriture idempotente (document indexé par `ticketNumber` quand disponible, `merge: true`)
- Mapping robuste du prix (supporte `price` objet `{ amount, currency }` ou format legacy string)

### Frontend (Vue 3)
- Données **temps réel** via Firestore (`onSnapshot`)
- Pages :
  - `/` : Home (statut / onboarding / accès rapide)
  - `/overview` : KPIs (CA, billets, événements, prix moyen…), top événements (CA), dernières ventes
  - `/dashboard` : charts + carte, filtres multi-sélection (événements / catégories) synchronisés dans l’URL
  - `/tickets` : listing + recherche/tri + filtres avancés (période, buyer, event, catégories, range de prix), presets en localStorage, URL sync
  - `/agenda` : vue “agenda” (ventes par jour) + action pour afficher les tickets vendus sur une journée
  - Page “événement” : vue détail dédiée (analyse d’un event, navigation depuis les top events)

- Visualisations / outils analytiques :
  - Évolution des ventes (journalier/hebdo, cumulées et/ou par période)
  - Répartition des ventes par événement (camembert)
  - Carte géographique (Leaflet) basée sur codes postaux + drill-down (zoom au double-clic)
  - Panier moyen (tickets/transaction)
  - Comparaison mensuelle année sur année
  - Heatmap temporelle : ventes par **jour & heure**
  - Top événements cliquables (navigation rapide)

---

## 🧱 Stack
- **Frontend** : Vue 3 + Vite, Tailwind CSS, Chart.js (`vue-chartjs`), Leaflet
- **Backend** : Firebase Functions (Node 22), Firestore, Firebase Emulator Suite
- **Outils** : Firebase CLI, Python (scripts de simulation webhook)

---

## ✅ Prérequis
- Node.js
  - Frontend : `^20.19.0 || >=22.12.0`
  - Firebase Functions : Node 22
- Firebase CLI (`firebase --version`)
- Python 3 (simulateurs webhook)

---

## 🚀 Démarrage rapide (local)

### 1) Installer les dépendances
Frontend :
```bash
cd frontend
npm install
```

Functions :
```bash
cd backend/functions
npm install
```

### 2) Variables d’environnement

#### Backend (secret webhook)
Créer `backend/functions/.env` (**non versionné**) :
```bash
PETZI_SECRET=TON_SECRET_PARTAGE
```

#### Frontend (Firebase)
Créer `frontend/.env.local` :
```bash
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...

# Optionnel : connecter Firestore à l'émulateur local
VITE_USE_FIREBASE_EMULATOR=true
```

### 3) Lancer Firebase Emulator Suite
Depuis `backend/` :
```bash
cd backend
firebase emulators:start
```

UI emulators : http://127.0.0.1:4000

### 4) Lancer le frontend
```bash
cd frontend
npm run dev
```

Accès :
- http://localhost:5173/
- http://localhost:5173/overview
- http://localhost:5173/dashboard
- http://localhost:5173/tickets
- http://localhost:5173/agenda

---

## 📡 Webhook Petzi (tests locaux)

URL émulateur typique :
```
http://127.0.0.1:5001/<project-id>/us-central1/petziWebhook
```

Exemples (si scripts présents dans `backend/`) :
```bash
cd backend
python .\petzi_simulator_template.py http://127.0.0.1:5001/<project-id>/us-central1/petziWebhook TON_SECRET_PARTAGE
python .\petzi_simulator.py          http://127.0.0.1:5001/<project-id>/us-central1/petziWebhook TON_SECRET_PARTAGE
```

Si tout est OK :
- le script renvoie `OK`
- des documents apparaissent dans Firestore Emulator → collection `tickets` :
  http://127.0.0.1:4000/firestore

---

## 🗃️ Données stockées (Firestore)

Collection : `tickets`

Champs principaux (issus du mapping webhook) :
- Ticket : `ticketNumber`, `ticketType`, `ticketCategory`, `ticketTitle`, `generatedAt`
- Événement : `eventType`, `eventId`, `eventName`
- Session : `sessionName`, `sessionDate`, `sessionTime`, `venueCity`, `venuePostcode`, ...
- Acheteur : `buyerFirstName`, `buyerLastName`, `buyerPostcode`, ...
- Prix : `priceAmount`, `priceCurrency`
- Technique : `createdAt`, `rawPayload`

---

## 🌍 Déploiement (prod)

Fonctions :
```bash
cd backend/functions
npm run deploy
```

À prévoir :
- Définir `PETZI_SECRET` en environnement (prod) plutôt que via `.env` local
- Ajuster les règles Firestore (voir `backend/firestore.rules`) selon l’exposition souhaitée
