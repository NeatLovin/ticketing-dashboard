// frontend/src/firebase.js
import { initializeApp } from "firebase/app";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";
// Analytics est optionnel
// import { getAnalytics } from "firebase/analytics";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  // measurementId optionnel
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
};

// Vérifier si les variables d'environnement sont définies
// Vérifier que les valeurs ne sont pas "undefined" (string) ni undefined
const isConfigValid = 
  firebaseConfig.apiKey && 
  firebaseConfig.apiKey !== "undefined" &&
  firebaseConfig.projectId && 
  firebaseConfig.projectId !== "undefined";

// Debug : afficher les variables chargées (sans les valeurs complètes pour la sécurité)
if (import.meta.env.DEV) {
  const envCheck = {
    hasApiKey: !!firebaseConfig.apiKey && firebaseConfig.apiKey !== "undefined",
    hasProjectId: !!firebaseConfig.projectId && firebaseConfig.projectId !== "undefined",
    hasAuthDomain: !!firebaseConfig.authDomain && firebaseConfig.authDomain !== "undefined",
    apiKeyValue: firebaseConfig.apiKey ? (firebaseConfig.apiKey.substring(0, 10) + "...") : "non défini",
    projectId: firebaseConfig.projectId || "non défini",
  };
  console.log("🔍 Variables Firebase chargées:", envCheck);
  
  if (!isConfigValid) {
    console.error(
      "❌ Configuration Firebase manquante ou incorrecte.\n" +
      "📝 Vérifiez que votre fichier .env.local dans frontend/ contient :\n" +
      "   - VITE_FIREBASE_API_KEY=...\n" +
      "   - VITE_FIREBASE_PROJECT_ID=...\n" +
      "   - VITE_FIREBASE_AUTH_DOMAIN=...\n" +
      "   - etc.\n" +
      "⚠️  IMPORTANT : Redémarrez le serveur de développement (Ctrl+C puis npm run dev) après avoir créé/modifié .env.local"
    );
  }
}

let app;
let db;

try {
  if (isConfigValid) {
    app = initializeApp(firebaseConfig);
    db = getFirestore(app);
    
    // Se connecter à l'émulateur Firebase en développement si demandé
    // Pour utiliser l'émulateur, ajoutez VITE_USE_FIREBASE_EMULATOR=true dans .env.local
    const useEmulator = import.meta.env.VITE_USE_FIREBASE_EMULATOR === "true";
    
    if (useEmulator) {
      try {
        // Vérifier si on n'est pas déjà connecté à l'émulateur
        connectFirestoreEmulator(db, "127.0.0.1", 8080);
        console.log("🔌 Connecté à l'émulateur Firestore local (127.0.0.1:8080)");
        console.log("💡 Assurez-vous que l'émulateur est démarré: cd backend && firebase emulators:start");
      } catch (emulatorError) {
        // L'émulateur est peut-être déjà connecté
        if (emulatorError.message && !emulatorError.message.includes("already been called")) {
          console.warn("⚠️ Impossible de se connecter à l'émulateur Firestore:", emulatorError.message);
          console.log("💡 Assurez-vous que l'émulateur est démarré avec: firebase emulators:start");
        }
      }
    } else {
      console.log("🌐 Connexion à Firestore en production/cloud");
    }
    
    console.log("✅ Firebase initialisé avec succès");
  } else {
    console.error("❌ Configuration Firebase incomplète");
    db = null;
  }
} catch (error) {
  console.error("❌ Erreur d'initialisation Firebase:", error);
  db = null;
}

export { db };
// Si un jour tu veux Analytics :
// export const analytics = getAnalytics(app);
