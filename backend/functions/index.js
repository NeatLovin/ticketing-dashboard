/**
 * Functions Firebase pour recevoir les webhooks Petzi
 * et persister les tickets dans Firestore.
 */

require("dotenv").config();

const functions = require("firebase-functions");
const admin = require("firebase-admin");
const crypto = require("crypto");

// Init Firestore
if (!admin.apps.length) {
  admin.initializeApp();
}
const db = admin.firestore();

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

  const price = ticket.price || {};
  const amountNumber = price.amount ? parseFloat(price.amount) : null;

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
    priceAmountRaw: price.amount ?? null, // string d’origine "24.00"
    priceCurrency: price.currency ?? null,

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

    // 8) Réponse rapide à Petzi
    return res.status(200).send("OK");
  } catch (err) {
    console.error("petziWebhook error", err);
    return res.status(500).send("Server error");
  }
});
