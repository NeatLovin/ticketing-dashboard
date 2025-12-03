# ticketing-dashboard

Dashboard d’analytics de tickets basé sur les webhooks Petzi, un backend Firebase et un frontend Vue.js pour des insights en temps réel.

---

## 🔍 Objectif du projet

- Centraliser les événements provenant de Petzi (tickets, ventes, événements, etc.)
- Les stocker et/ou transformer via un backend serverless (Firebase)
- Les afficher dans un dashboard en temps réel (Vue.js)
- Permettre d’analyser les performances (ventes, fréquentation, répartition par événement, etc.)

---

## 🧱 Stack technique

- **Frontend**
  - Vue.js 3 (Vite)
  - (à définir plus tard : Tailwind / autre UI kit, Auth, etc.)

- **Backend**
  - **Firebase**
    - Cloud Functions (HTTP) pour recevoir les webhooks Petzi (`petziWebhook`)
    - Cloud Firestore pour stocker les tickets (`tickets`, etc.)
    - Firebase Emulator Suite pour le développement local
  - Webhooks Petzi (endpoint HTTP exposé via Firebase Functions)

- **Outils**
  - Node.js (version 22+ recommandée)
  - npm / pnpm / yarn
  - Git + GitHub
  - Python (pour le script `petzi_simulator.py` de test des webhooks)

---

## 🚧 État actuel

> Début de projet, mise en place du backend et du frontend.

- [x] Initialiser le projet Vue
- [x] Configurer Firebase (projet, emulators)
- [x] Créer une fonction webhook pour Petzi (`petziWebhook`)
- [ ] Définir le modèle de données final pour les analytics
- [ ] Mettre en place un premier dashboard minimal (ex : total des tickets vendus)

---

## ⚙️ Installation & setup

### 1. Cloner le dépôt

```bash
git clone https://github.com/<ton-compte>/ticketing-dashboard.git
cd ticketing-dashboard
```

### 2. Frontend (Vue)

Dans `frontend/` :

```bash
cd frontend
npm install
```

Lancement du serveur de dev :

```bash
npm run dev
```

> ⚠️ Plus tard, il faudra ajouter un fichier `.env.local` pour configurer la connexion Firebase côté front (`VITE_FIREBASE_API_KEY`, etc.). Pour l’instant, le front peut tourner sans connexion réelle.

### 3. Backend (Firebase Functions + Firestore)

Dans `backend/functions/` :

```bash
cd ../backend/functions
npm install
```

#### 3.1. Fichier `.env` obligatoire (secret Petzi)

Chaque développeur doit créer **son propre** fichier `.env` dans `backend/functions` :

```bash
# dans backend/functions
echo PETZI_SECRET=ton_secret_petzi_ici > .env
```

Contenu attendu du fichier `backend/functions/.env` :

```env
PETZI_SECRET=TON_SECRET_PARTAGE_AVEC_PETZI
```

- `PETZI_SECRET` = secret partagé entre Petzi (ou le simulateur) et la fonction Firebase.
- **Ne pas committer** ce fichier (`.env` est ignoré par Git).

Le simulateur Petzi doit utiliser **le même secret** que celui défini dans ce `.env`.

#### 3.2. Lancer les emulators Firebase en local

Depuis `backend/` :

```bash
cd ..
firebase emulators:start
```

Cela démarre :

- l’émulateur **Functions** (incluant `petziWebhook`)
- l’émulateur **Firestore**
- l’interface web des emulators : http://127.0.0.1:4000

---

## 🧪 Tester le webhook avec `petzi_simulator.py`

Un script Python permet de simuler les appels de Petzi vers l’endpoint Firebase.

### 1. Pré-requis

- Python installé
- `PETZI_SECRET` dans `backend/functions/.env` **identique** au secret utilisé par le simulateur.

### 2. Commande de test

Depuis `backend/` :

```bash
cd backend
python .\petzi_simulator.py http://127.0.0.1:5001/<project-id>/us-central1/petziWebhook TON_SECRET_PARTAGE
```

Si tout est correct :

- le script affiche une réponse `OK`,
- une collection `tickets` (ou `tickets_test` selon la config) apparaît dans l’UI Firestore de l’émulateur :  
  http://127.0.0.1:4000/firestore

---

## 📡 Webhooks Petzi (design actuel)

- Endpoint HTTP Firebase Function : `petziWebhook`
  - méthode : `POST`
  - vérification de la signature HMAC basée sur `PETZI_SECRET`
  - parsing du JSON envoyé par Petzi
  - mapping des champs utiles vers un document Firestore (collection `tickets`)
- Les événements de type `ticket_created` / `ticket_updated` sont persistés avec :
  - infos event (id, nom, date…)
  - infos ticket (numéro, type, catégorie, prix…)
  - infos session (date, heure, salle…)
  - infos acheteur (nom, CP, etc.)
  - payload brut pour debug (`rawPayload`)

---

Le front Vue se connectera à Firestore pour lire la collection `tickets` et construire ces vues.
