<script setup>
import { ref, onMounted } from "vue";
import { collection, getDocs, query, orderBy } from "firebase/firestore";
import { db } from "../firebase";

// états
const tickets = ref([]);
const loading = ref(true);
const error = ref(null);
const slowLoad = ref(false);

// helper format prix
function formatPrice(amount, currency) {
  // affiche comme "24.00 CHF"
  const fixed = Number(amount).toFixed(2);
  return currency ? `${fixed} ${currency}` : `${fixed}`;
}

onMounted(async () => {
  loading.value = true;
  error.value = null;

  // Indicateur "lent" ultra court sans interrompre la requête (1s)
  const TIMEOUT_MS = 1000;
  const TIMEOUT_SECONDS = Math.ceil(TIMEOUT_MS / 1000);
  const timeoutId = setTimeout(() => {
    if (loading.value) {
      console.warn(`⏱️ Chargement plus long que prévu (> ${TIMEOUT_SECONDS}s), on continue d'attendre…`);
      slowLoad.value = true; // on n'arrête PAS la requête et on n'affiche PAS d'erreur
    }
  }, TIMEOUT_MS);

  try {
    if (!db) {
      throw new Error("Firestore (db) non initialisé — vérifie frontend/src/firebase.js et .env.local");
    }

    console.log("🔍 Début de la récupération des tickets depuis Firestore...");
    console.log("📊 Collection: 'tickets'");
    console.log(`⏱️ Indicateur lenteur après: ${TIMEOUT_SECONDS} seconde(s)`);
    console.log("🔗 Configuration Firebase:", {
      projectId: db.app.options.projectId,
      databaseId: db._delegate?.databaseId || "default",
    });
    
    const startTime = Date.now();
    
    // Essayer d'abord une requête simple sans orderBy pour éviter les problèmes d'index
    let q;
    let snap;
    let docs;
    
    try {
      console.log("📝 Tentative 1: Requête simple sans orderBy...");
      q = query(collection(db, "tickets"));
      snap = await getDocs(q);
      docs = snap.docs;
      const elapsed = Date.now() - startTime;
      console.log(`✅ Requête réussie en ${elapsed}ms. ${docs.length} document(s) trouvé(s)`);
      
      // Si on a des résultats, essayer de les trier par createdAt si disponible
      if (docs.length > 0) {
        console.log("🔄 Tri manuel des résultats par createdAt...");
        docs = docs.sort((a, b) => {
          const dateA = a.data().createdAt;
          const dateB = b.data().createdAt;
          if (!dateA || !dateB) return 0;
          try {
            const timeA = dateA.toDate ? dateA.toDate().getTime() : new Date(dateA).getTime();
            const timeB = dateB.toDate ? dateB.toDate().getTime() : new Date(dateB).getTime();
            return timeB - timeA; // Plus récent en premier
          } catch {
            return 0;
          }
        });
        console.log("✅ Tri terminé");
      }
    } catch (simpleError) {
      const elapsed = Date.now() - startTime;
      console.error(`❌ Erreur avec requête simple après ${elapsed}ms:`, simpleError);
      console.error("Détails:", {
        code: simpleError?.code,
        message: simpleError?.message,
      });
      
      // Si la requête simple échoue, essayer avec orderBy (peut-être qu'un index existe)
      try {
        console.log("📝 Tentative 2: Requête avec orderBy('createdAt', 'desc')...");
        q = query(collection(db, "tickets"), orderBy("createdAt", "desc"));
        snap = await getDocs(q);
        docs = snap.docs;
        const elapsed2 = Date.now() - startTime;
        console.log(`✅ Requête avec orderBy réussie en ${elapsed2}ms. ${docs.length} document(s) trouvé(s)`);
      } catch (orderByError) {
        const elapsed2 = Date.now() - startTime;
        console.error(`❌ Erreur avec orderBy après ${elapsed2}ms:`, orderByError);
        throw orderByError; // Relancer l'erreur pour qu'elle soit gérée par le catch principal
      }
    }

    // transformer en objets JS simples
    tickets.value = docs.map((doc) => {
      const data = doc.data();

      // createdAt peut être un Timestamp Firestore, une ISO string, ou autre.
      let createdAtRaw = data.createdAt;
      try {
        // si c'est un objet avec toDate (Firestore Timestamp), convertir en ISO string pour affichage brut lisible
        if (createdAtRaw && typeof createdAtRaw.toDate === "function") {
          createdAtRaw = createdAtRaw.toDate().toISOString();
        } else if (typeof createdAtRaw === "object" && createdAtRaw !== null) {
          // si c'est un objet quelconque, stringify minimal
          createdAtRaw = JSON.stringify(createdAtRaw);
        }
      } catch (e) {
        // leave as-is si erreur
      }

      return {
        id: doc.id,
        eventName: data.eventName ?? null,
        sessionDate: data.sessionDate ?? null,
        sessionTime: data.sessionTime ?? null,
        ticketNumber: data.ticketNumber ?? null,
        priceAmount: typeof data.priceAmount === "number" ? data.priceAmount : (data.priceAmount ? Number(data.priceAmount) : undefined),
        priceCurrency: data.priceCurrency ?? null,
        createdAtRaw,
        // conserver payload si utile plus tard
        // raw: data.rawPayload ?? null,
      };
    });

    console.debug(`Tickets chargés: ${tickets.value.length}`);
    
    if (tickets.value.length === 0) {
      console.warn("⚠️ Aucun ticket trouvé dans la collection 'tickets'");
      console.info("💡 Pour ajouter des tickets, utilisez le simulateur Petzi ou envoyez des webhooks");
      console.info("🔍 Vérifications à faire:");
      console.info("   1. Vérifiez que vous êtes connecté au bon projet Firebase (émulateur vs cloud)");
      console.info("   2. Ouvrez la console Firebase/émulateur et vérifiez que la collection 'tickets' contient des documents");
      console.info("   3. Si vous utilisez l'émulateur, ajoutez VITE_USE_FIREBASE_EMULATOR=true dans .env.local");
      console.info("   4. Vérifiez les règles de sécurité Firestore dans backend/firestore.rules");
    } else {
      console.log(`✅ ${tickets.value.length} ticket(s) chargé(s) avec succès!`);
    }
  } catch (err) {
    console.error("❌ Erreur lecture tickets:", err);
    console.error("Détails de l'erreur:", {
      code: err?.code,
      message: err?.message,
      stack: err?.stack,
    });
    
    // Messages d'erreur plus explicites
    let errorMessage = err?.message || String(err);
    if (err?.code === "unavailable" || err?.code === "deadline-exceeded") {
      errorMessage = "Impossible de se connecter à Firestore. Vérifiez votre connexion internet et que Firebase est accessible.";
      if (import.meta.env.DEV) {
        errorMessage += " Si vous utilisez l'émulateur, assurez-vous qu'il est démarré et ajoutez VITE_USE_FIREBASE_EMULATOR=true dans .env.local";
      }
    } else if (err?.code === "permission-denied") {
      errorMessage = "Permission refusée. Vérifiez les règles de sécurité Firestore.";
    } else if (err?.code === "failed-precondition") {
      errorMessage = "Index manquant. Créez l'index requis dans la console Firebase ou utilisez l'émulateur.";
    }
    
    error.value = errorMessage;
  } finally {
    clearTimeout(timeoutId);
    loading.value = false;
  }
});
</script>

<template>
  <main class="p-4">
    <h1 class="text-2xl font-bold mb-4">Tickets</h1>

    <router-link to="/" class="underline text-blue-600 mb-4 inline-block">
      Retour à l’accueil
    </router-link>

    <div v-if="loading" class="mt-4">
      Chargement des tickets…
      <span v-if="slowLoad" class="ml-2 text-sm text-gray-500">c'est un peu long, merci de patienter</span>
    </div>

    <div v-else-if="error" class="mt-4 text-red-600">Erreur : {{ error }}</div>

    <table v-else class="mt-4 border-collapse w-full">
      <thead>
        <tr>
          <th class="border px-2 py-1 text-left">Event</th>
          <th class="border px-2 py-1 text-left">Date</th>
          <th class="border px-2 py-1 text-left">Heure</th>
          <th class="border px-2 py-1 text-left">Ticket #</th>
          <th class="border px-2 py-1 text-left">Prix</th>
          <th class="border px-2 py-1 text-left">Créé le</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="t in tickets" :key="t.id">
          <td class="border px-2 py-1">{{ t.eventName ?? "—" }}</td>
          <td class="border px-2 py-1">{{ t.sessionDate ?? "—" }}</td>
          <td class="border px-2 py-1">{{ t.sessionTime ?? "—" }}</td>
          <td class="border px-2 py-1">{{ t.ticketNumber ?? "—" }}</td>
          <td class="border px-2 py-1">
            <span v-if="typeof t.priceAmount === 'number'">
              {{ formatPrice(t.priceAmount, t.priceCurrency) }}
            </span>
            <span v-else>—</span>
          </td>
          <td class="border px-2 py-1">
            <span v-if="t.createdAtRaw !== undefined">{{ t.createdAtRaw }}</span>
            <span v-else>—</span>
          </td>
        </tr>
        <tr v-if="tickets.length === 0 && !loading">
          <td class="border px-2 py-1" colspan="6">Aucun ticket trouvé.</td>
        </tr>
      </tbody>
    </table>
  </main>
</template>

<style scoped>
/* Pas de CSS compliqué — utilitaires légers déjà fournis inline */
</style>
