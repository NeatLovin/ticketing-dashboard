// frontend/src/services/ticketsService.js
import { collection, query, orderBy, onSnapshot, where, limit } from "firebase/firestore";
import { db } from "../firebase";

/**
 * Service pour récupérer et écouter les tickets en temps réel depuis Firestore
 */
export class TicketsService {
  /**
   * Écoute en temps réel tous les tickets
   * @param {Function} callback - Fonction appelée à chaque mise à jour
   * @returns {Function} Fonction pour désabonner
   */
  static subscribeToAllTickets(callback) {
    if (!db) {
      const error = new Error("Firebase n'est pas initialisé. Vérifiez votre fichier .env.local");
      console.error(error);
      callback([], error);
      return () => {}; // Retourner une fonction no-op pour le cleanup
    }
    
    try {
      const q = query(collection(db, "tickets"), orderBy("createdAt", "desc"));
      
      return onSnapshot(
        q,
        (snapshot) => {
          const tickets = snapshot.docs.map((doc) => ({
            id: doc.id,
            ...doc.data(),
          }));
          callback(tickets);
        },
        (error) => {
          console.error("Erreur lors de l'écoute des tickets:", error);
          callback([], error);
        }
      );
    } catch (error) {
      console.error("Erreur lors de la création de la requête:", error);
      callback([], error);
      return () => {};
    }
  }

  /**
   * Écoute en temps réel les tickets d'un événement spécifique
   * @param {number|string} eventId - ID de l'événement
   * @param {Function} callback - Fonction appelée à chaque mise à jour
   * @returns {Function} Fonction pour désabonner
   */
  static subscribeToEventTickets(eventId, callback) {
    if (!db) {
      const error = new Error("Firebase n'est pas initialisé. Vérifiez votre fichier .env.local");
      console.error(error);
      callback([], error);
      return () => {};
    }
    
    try {
      const q = query(
        collection(db, "tickets"),
        where("eventId", "==", eventId),
        orderBy("createdAt", "asc")
      );

      return onSnapshot(
        q,
        (snapshot) => {
          const tickets = snapshot.docs.map((doc) => ({
            id: doc.id,
            ...doc.data(),
          }));
          callback(tickets);
        },
        (error) => {
          console.error("Erreur lors de l'écoute des tickets de l'événement:", error);
          callback([], error);
        }
      );
    } catch (error) {
      console.error("Erreur lors de la création de la requête:", error);
      callback([], error);
      return () => {};
    }
  }

  /**
   * Écoute en temps réel les tickets d'une date de session spécifique
   * @param {string} sessionDate - Date au format "YYYY-MM-DD"
   * @param {Function} callback - Fonction appelée à chaque mise à jour
   * @returns {Function} Fonction pour désabonner
   */
  static subscribeToSessionTickets(sessionDate, callback) {
    if (!db) {
      const error = new Error("Firebase n'est pas initialisé. Vérifiez votre fichier .env.local");
      console.error(error);
      callback([], error);
      return () => {};
    }
    
    try {
      const q = query(
        collection(db, "tickets"),
        where("sessionDate", "==", sessionDate),
        orderBy("createdAt", "asc")
      );

      return onSnapshot(
        q,
        (snapshot) => {
          const tickets = snapshot.docs.map((doc) => ({
            id: doc.id,
            ...doc.data(),
          }));
          callback(tickets);
        },
        (error) => {
          console.error("Erreur lors de l'écoute des tickets de la session:", error);
          callback([], error);
        }
      );
    } catch (error) {
      console.error("Erreur lors de la création de la requête:", error);
      callback([], error);
      return () => {};
    }
  }

  /**
   * Écoute en temps réel les nouvelles ventes (nouveaux tickets ajoutés) et déclenche un callback.
   * Important: n'émet pas les tickets existants au moment de l'abonnement (snapshot initial ignoré).
   *
   * @param {(ticket: any) => void} onSale - Appelé pour chaque nouveau ticket ajouté.
   * @param {{ initialLimit?: number }} [options]
   * @returns {Function} Fonction pour désabonner
   */
  static subscribeToNewTicketSales(onSale, options = {}) {
    if (!db) {
      const error = new Error("Firebase n'est pas initialisé. Vérifiez votre fichier .env.local");
      console.error(error);
      return () => {};
    }

    const initialLimit = Number.isFinite(options.initialLimit) ? options.initialLimit : 25;

    try {
      const q = query(
        collection(db, "tickets"),
        orderBy("createdAt", "desc"),
        limit(Math.max(1, initialLimit))
      );

      let hasSeenInitial = false;
      let latestCreatedAtMs = 0;
      const notifiedIds = new Set();

      return onSnapshot(
        q,
        (snapshot) => {
          if (!hasSeenInitial) {
            snapshot.docs.forEach((doc) => {
              const data = doc.data();
              const date = TicketsService.toDate(data?.createdAt);
              const ms = date ? date.getTime() : 0;
              if (ms > latestCreatedAtMs) latestCreatedAtMs = ms;
              notifiedIds.add(doc.id);
            });
            hasSeenInitial = true;
            return;
          }

          const changes = snapshot.docChanges();
          changes.forEach((change) => {
            if (change.type !== "added") return;

            const doc = change.doc;
            if (notifiedIds.has(doc.id)) return;

            const data = doc.data();
            const createdAt = data?.createdAt;
            const date = TicketsService.toDate(createdAt);
            const ms = date ? date.getTime() : 0;

            // Filtrer les ajouts provenant d'un rattrapage ancien / re-sync.
            if (ms && ms <= latestCreatedAtMs) {
              notifiedIds.add(doc.id);
              return;
            }

            if (ms > latestCreatedAtMs) latestCreatedAtMs = ms;
            notifiedIds.add(doc.id);

            try {
              onSale({ id: doc.id, ...data });
            } catch (e) {
              console.error("Erreur dans callback onSale:", e);
            }
          });
        },
        (error) => {
          console.error("Erreur lors de l'écoute des nouvelles ventes:", error);
        }
      );
    } catch (error) {
      console.error("Erreur lors de la création de la requête (nouvelles ventes):", error);
      return () => {};
    }
  }

  /**
   * Convertit un timestamp Firestore en Date JavaScript
   * @param {any} timestamp - Timestamp Firestore ou string ISO
   * @returns {Date|null}
   */
  static toDate(timestamp) {
    if (!timestamp) return null;
    if (timestamp instanceof Date) return timestamp;
    if (typeof timestamp === "string") return new Date(timestamp);
    if (typeof timestamp === "number") return new Date(timestamp);
    if (timestamp && typeof timestamp.toDate === "function") {
      return timestamp.toDate();
    }
    return null;
  }

  /**
   * Groupe les tickets par date de session
   * @param {Array} tickets - Liste des tickets
   * @returns {Object} Objet avec dates comme clés
   */
  static groupBySessionDate(tickets) {
    const grouped = {};
    tickets.forEach((ticket) => {
      const date = ticket.sessionDate;
      if (date) {
        if (!grouped[date]) {
          grouped[date] = [];
        }
        grouped[date].push(ticket);
      }
    });
    return grouped;
  }

  /**
   * Groupe les tickets par mois
   * @param {Array} tickets - Liste des tickets
   * @returns {Object} Objet avec "YYYY-MM" comme clés
   */
  static groupByMonth(tickets) {
    const grouped = {};
    tickets.forEach((ticket) => {
      const date = this.toDate(ticket.createdAt);
      if (date) {
        const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
        if (!grouped[monthKey]) {
          grouped[monthKey] = [];
        }
        grouped[monthKey].push(ticket);
      }
    });
    return grouped;
  }

  /**
   * Calcule le panier moyen (nombre moyen de tickets par transaction)
   * Les transactions sont identifiées par le même ticketNumber ou createdAt très proche
   * Pour simplifier, on considère qu'un ticket = une transaction
   * @param {Array} tickets - Liste des tickets
   * @returns {number} Panier moyen
   */
  static calculateAverageBasket(tickets) {
    if (tickets.length === 0) return 0;
    
    // Grouper par ticketNumber pour identifier les transactions multiples
    const transactions = new Map();
    tickets.forEach((ticket) => {
      const key = ticket.ticketNumber || ticket.id;
      if (!transactions.has(key)) {
        transactions.set(key, []);
      }
      transactions.get(key).push(ticket);
    });

    // Calculer le nombre moyen de tickets par transaction
    const totalTickets = tickets.length;
    const totalTransactions = transactions.size;
    
    return totalTransactions > 0 ? totalTickets / totalTransactions : 0;
  }
}

