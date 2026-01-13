/**
 * Functions Firebase pour recevoir les webhooks Petzi
 * et persister les tickets dans Firestore.
 */

require("dotenv").config();

const functions = require("firebase-functions");
const admin = require("firebase-admin");
const { FieldValue } = require("firebase-admin/firestore");
const crypto = require("crypto");

// Init Firestore
if (!admin.apps.length) {
  admin.initializeApp();
}
const db = admin.firestore();

function isFiniteNumber(value) {
  if (typeof value === "number") return Number.isFinite(value);
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return false;
    const num = Number(trimmed);
    return Number.isFinite(num);
  }
  return false;
}

function toNumber(value) {
  if (typeof value === "number") return value;
  if (typeof value === "string") return Number(value.trim());
  return NaN;
}

function normalizeCurrencyList(value) {
  if (!Array.isArray(value)) return [];
  return value
    .filter((x) => x && typeof x === "object")
    .map((x) => ({
      currency: typeof x.currency === "string" ? x.currency : null,
      amount: typeof x.amount === "number" ? x.amount : Number(x.amount),
    }))
    .filter((x) => x.currency && Number.isFinite(x.amount));
}

function addToCurrencyList(list, currency, delta) {
  const normalized = normalizeCurrencyList(list);
  const cur = typeof currency === "string" ? currency.trim() : "";
  if (!cur) return normalized;

  const d = typeof delta === "number" ? delta : Number(delta);
  if (!Number.isFinite(d)) return normalized;

  const idx = normalized.findIndex((x) => x.currency === cur);
  if (idx >= 0) {
    normalized[idx] = { currency: cur, amount: normalized[idx].amount + d };
    return normalized;
  }

  return [...normalized, { currency: cur, amount: d }];
}

function normalizeSessionsArray(value) {
  if (!Array.isArray(value)) return [];
  return value
    .filter((s) => s && typeof s === "object")
    .map((s) => ({
      date: typeof s.date === "string" ? s.date : null,
      time: typeof s.time === "string" ? s.time : null,
      locationName: typeof s.locationName === "string" ? s.locationName : null,
      ticketsCount: typeof s.ticketsCount === "number" ? s.ticketsCount : Number(s.ticketsCount),
      revenueByCurrency: normalizeCurrencyList(s.revenueByCurrency),
    }))
    .map((s) => ({
      ...s,
      ticketsCount: Number.isFinite(s.ticketsCount) ? s.ticketsCount : 0,
    }));
}

function sessionsMatch(a, b) {
  const ad = a && a.date ? a.date : null;
  const at = a && a.time ? a.time : null;
  const al = a && a.locationName ? a.locationName : null;

  const bd = b && b.date ? b.date : null;
  const bt = b && b.time ? b.time : null;
  const bl = b && b.locationName ? b.locationName : null;

  return ad === bd && at === bt && al === bl;
}

/**
 * Parse l'en-tête Petzi-Signature
 * Format: "t=<unix_timestamp>,v1=<hex_hmac>"
 */
function parsePetziSignature(headerValue) {
  const parts = headerValue.split(",");
  const result = {};
  for (const part of parts) {
    const [key, value] = part.split("=");
    if (key && value) {
      result[key.trim()] = value.trim();
    }
  }
  return {
    timestamp: result["t"],
    signature: result["v1"],
  };
}

/**
 * Vérifie la signature HMAC envoyée par Petzi.
 * Algorithme d’après petzi_simulator.py :
 *   digest = HMAC_SHA256(secret, "<timestamp>.<body_json>")
 */
function verifySignature({ headerValue, rawBody, secret }) {
  if (!headerValue) {
    throw new Error("Missing Petzi-Signature header");
  }

  const { timestamp, signature } = parsePetziSignature(headerValue);
  if (!timestamp || !signature) {
    throw new Error("Invalid Petzi-Signature format");
  }

  const bodyString = rawBody.toString("utf8");
  const bodyToSign = `${timestamp}.${bodyString}`;

  const expectedDigest = crypto
    .createHmac("sha256", secret)
    .update(bodyToSign)
    .digest("hex");

  if (expectedDigest !== signature) {
    throw new Error("Invalid HMAC signature");
  }

  return { timestamp, bodyString };
}

/**
 * Transforme le payload Petzi en document Firestore "tickets".
 *
 * Exemple de JSON (simplifié) d’après petzi_simulator.py :
 * {
 *   "event": "ticket_created",
 *   "details": {
 *     "ticket": {
 *       "number": "XXXX2941J6SABA",
 *       "type": "online_presale",
 *       "title": "Test To Delete",
 *       "category": "Prélocation",
 *       "eventId": 54694,
 *       "event": "Test To Delete",
 *       "cancellationReason": "",
 *       "generatedAt": "2024-09-04T10:21:21.925529+00:00",
 *       "sessions": [
 *         {
 *           "name": "Test To Delete",
 *           "date": "2024-01-27",
 *           "time": "21:00:00",
 *           "doors": "21:00:00",
 *           "location": {
 *             "name": "Case à Chocs",
 *             "street": "Quai Philipe Godet 20",
 *             "city": "Neuchatel",
 *             "postcode": "2000"
 *           }
 *         }
 *       ],
 *       "promoter": "...",
 *       "price": {
 *         "amount": "24.00",
 *         "currency": "CHF"
 *       }
 *     },
 *     "buyer": {
 *       "role": "customer",
 *       "firstName": "Jane",
 *       "lastName": "Doe",
 *       "email": null,
 *       "postcode": "1234"
 *     }
 *   }
 * }
 */
function buildTicketDoc(payload) {
  const eventType = payload.event; // "ticket_created" | "ticket_updated"
  const details = payload.details || {};
  const ticket = details.ticket || {};
  const buyer = details.buyer || {};

  const sessions = Array.isArray(ticket.sessions) ? ticket.sessions : [];
  const mainSession = sessions.length > 0 ? sessions[0] : null;

  // Gestion robuste du prix (objet ou string)
  const priceObj = ticket.price;
  let amountNumber = null;
  let priceCurrency = null;
  let priceAmountRaw = null;

  if (typeof priceObj === "object" && priceObj !== null) {
    // Format standard: { amount: "25.00", currency: "CHF" }
    if (priceObj.amount) {
      amountNumber = parseFloat(priceObj.amount);
      priceAmountRaw = priceObj.amount;
    }
    priceCurrency = priceObj.currency || null;
  } else if (typeof priceObj === "string") {
    // Format legacy/simple: "25.00"
    const match = priceObj.match(/([\d.]+)/);
    if (match) {
      amountNumber = parseFloat(match[1]);
      priceAmountRaw = priceObj;
    }
    priceCurrency = "CHF"; // Devise par défaut si string
  }

  // On utilise le numéro de ticket comme identifiant métier principal
  const ticketNumber = ticket.number;

  const doc = {
    // Info event
    eventType: eventType, // ticket_created / ticket_updated
    eventId: ticket.eventId ?? null,
    eventName: ticket.event ?? null,

    // Info ticket
    ticketNumber: ticketNumber,
    ticketType: ticket.type ?? null,
    ticketCategory: ticket.category ?? null,
    ticketTitle: ticket.title ?? null,
    cancellationReason: ticket.cancellationReason || null,
    generatedAt: ticket.generatedAt || null, // date/heure génération ticket

    // Session principale (première de la liste)
    sessionName: mainSession ? mainSession.name : null,
    sessionDate: mainSession ? mainSession.date : null, // "YYYY-MM-DD"
    sessionTime: mainSession ? mainSession.time : null, // "HH:MM:SS"
    sessionDoors: mainSession ? mainSession.doors : null,
    venueName: mainSession && mainSession.location ? mainSession.location.name : null,
    venueStreet: mainSession && mainSession.location ? mainSession.location.street : null,
    venueCity: mainSession && mainSession.location ? mainSession.location.city : null,
    venuePostcode: mainSession && mainSession.location ? mainSession.location.postcode : null,

    // Prix
    priceAmount: amountNumber,
    priceAmountRaw: priceAmountRaw,
    priceCurrency: priceCurrency,

    // Acheteur
    buyerRole: buyer.role ?? null,
    buyerFirstName: buyer.firstName ?? null,
    buyerLastName: buyer.lastName ?? null,
    buyerEmail: buyer.email ?? null,
    buyerPostcode: buyer.postcode ?? null,

    // Technique
    rawPayload: payload, // pour debug / audit
    createdAt: new Date().toISOString(), // date/heure de création du doc
  };

  return {
    doc,
    id: ticketNumber || undefined, // si pas de number, Firestore générera un ID auto
  };
}

/**
 * Function HTTP appelée par Petzi (ou le simulateur).
 * URL émulateur typique :
 *   http://127.0.0.1:5001/<project-id>/us-central1/petziWebhook
 */
exports.petziWebhook = functions.https.onRequest(async (req, res) => {
  try {
    // 1) Méthode HTTP
    if (req.method !== "POST") {
      return res.status(405).send("Method Not Allowed");
    }

    // 2) Secret partagé (en prod: variable d'environnement)
    const secret = process.env.PETZI_SECRET || "dev-secret-change-me";

    // 3) Récupération de la signature
    const signatureHeader = req.get("Petzi-Signature");
    if (!signatureHeader) {
      console.error("Missing Petzi-Signature header");
      return res.status(400).send("Missing signature");
    }

    // 4) Vérification HMAC (utilise le body brut)
    const rawBody = req.rawBody || Buffer.from(JSON.stringify(req.body));
    const { bodyString } = verifySignature({
      headerValue: signatureHeader,
      rawBody,
      secret,
    });

    // 5) Parsing JSON
    let payload;
    try {
      payload = JSON.parse(bodyString);
    } catch (e) {
      console.error("Invalid JSON body", e);
      return res.status(400).send("Invalid JSON");
    }

    // 👉 Ici tu pourrais ajouter une vraie validation JSON Schema
    //    avec le fichier webhooks_json_schema.413902fc487f.json (ajv, etc.)

    // 6) Mapping vers un document Firestore
    const { doc, id } = buildTicketDoc(payload);

    // 7) Persist dans la collection "tickets"
    if (id) {
      // idempotent: même ticketNumber -> même doc
      await db.collection("tickets").doc(id).set(doc, { merge: true });
    } else {
      await db.collection("tickets").add(doc);
    }

    // 7bis) Mise à jour de l'agrégat "events" (par eventId)
    // Le payload ticket contient: eventId, eventName, sessionDate/time/location, price.amount/currency.
    // Si eventId absent: on ne peut pas agréger.
    if (doc.eventId !== null && doc.eventId !== undefined && doc.eventId !== "") {
      const eventId = String(doc.eventId);
      const eventName = doc.eventName ?? null;

      const sessionDate = doc.sessionDate ?? null;
      const sessionTime = doc.sessionTime ?? null;
      const venueName = doc.venueName ?? null;

      const amountValid = isFiniteNumber(doc.priceAmount);
      const amount = amountValid ? toNumber(doc.priceAmount) : NaN;
      const currency = (typeof doc.priceCurrency === "string" && doc.priceCurrency.trim()) ? doc.priceCurrency.trim() : null;

      const eventRef = db.collection("events").doc(eventId);

      await db.runTransaction(async (tx) => {
        const snap = await tx.get(eventRef);
        const existing = snap.exists ? (snap.data() || {}) : {};

        // Base (sans inventer) + compteur global
        const base = {
          eventId,
          ticketsCount: FieldValue.increment(1),
        };
        if (eventName) base.eventName = eventName;

        // Revenus au niveau event (liste, pas de champs dynamiques revenue.CHF)
        if (amountValid && currency) {
          const currentRevenue = existing.revenueByCurrency;
          base.revenueByCurrency = addToCurrencyList(currentRevenue, currency, amount);
        }

        // Sessions au niveau event: tableau d'objets, pas de clés dynamiques "sessions.<...>"
        const hasSessionIdentity = !!(sessionDate || sessionTime || venueName);
        if (hasSessionIdentity) {
          const currentSessions = normalizeSessionsArray(existing.sessions);
          const nextSessions = [...currentSessions];

          const sessionIdentity = {
            date: sessionDate,
            time: sessionTime,
            locationName: venueName,
          };

          const idx = nextSessions.findIndex((s) => sessionsMatch(s, sessionIdentity));
          if (idx >= 0) {
            const prev = nextSessions[idx];
            const updated = {
              ...prev,
              // On conserve les champs existants si null côté webhook
              date: prev.date ?? sessionDate,
              time: prev.time ?? sessionTime,
              locationName: prev.locationName ?? venueName,
              ticketsCount: (Number.isFinite(prev.ticketsCount) ? prev.ticketsCount : 0) + 1,
              revenueByCurrency: (amountValid && currency) ? addToCurrencyList(prev.revenueByCurrency, currency, amount) : normalizeCurrencyList(prev.revenueByCurrency),
            };
            nextSessions[idx] = updated;
          } else {
            nextSessions.push({
              date: sessionDate,
              time: sessionTime,
              locationName: venueName,
              ticketsCount: 1,
              revenueByCurrency: amountValid && currency ? addToCurrencyList([], currency, amount) : [],
            });
          }

          base.sessions = nextSessions;
        }

        tx.set(eventRef, base, { merge: true });
      });
    }

    // 8) Réponse rapide à Petzi
    return res.status(200).send("OK");
  } catch (err) {
    console.error("petziWebhook error", err);
    return res.status(500).send("Server error");
  }
});
