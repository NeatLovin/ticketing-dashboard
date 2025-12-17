# Description: This script simulates a petzi webhook request.
#   ____                    _       ____ _
#  / ___|__ _ ___  ___     / \     / ___| |__   ___   ___ ___
# | |   / _` / __|/ _ \   / _ \   | |   | '_ \ / _ \ / __/ __|
# | |__| (_| \__ \  __/  / ___ \  | |___| | | | (_) | (__\__ \
#  \____\__,_|___/\___| /_/   \_\  \____|_| |_|\___/ \___|___/

import argparse
import datetime
import hmac
import requests
import random
import string
import json

def generate_random_string(length=12):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))


def make_header(body, secret):
    unix_timestamp = str(datetime.datetime.timestamp(datetime.datetime.now())).split('.')[0]
    body_to_sign = f'{unix_timestamp}.{body}'.encode()
    digest = hmac.new(secret.encode(), body_to_sign, "sha256").hexdigest()
    # Set the headers for the POST request
    headers = {'Petzi-Signature': f't={unix_timestamp},v1={digest}', 'Petzi-Version': '2',
               'Content-Type': 'application/json', 'User-Agent': 'PETZI webhook'}
    return headers


def make_post_request(url, data, secret):
    try:
        # Make the POST request
        response = requests.post(url, data=data.encode('utf-8'), headers=make_header(data, secret))

        if response.status_code == 200:
            print(f"Request successful. Response: {response.text}")
        else:
            print(f"Request failed with status code {response.status_code}.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Create a command line argument parser
    parser = argparse.ArgumentParser(description="HTTP POST Request with JSON Body")
    parser.add_argument("url", type=str, help="URL to send the POST request to")
    parser.add_argument("secret", nargs='?', type=str, help="secret shared between your server and petzi simulator",
                        default="AEeyJhbGciOiJIUzUxMiIsImlzcyI6")

    # Parse the command line arguments
    args = parser.parse_args()

    events = [
        {"date": "2025-12-13", "title": "BSA : TEKNO REBELLION"},
        {"date": "2025-12-12", "title": "DOUBLE VERNISSAGE : PRUNE CARMEN DIAZ + ILAJAN"},
        {"date": "2025-12-06", "title": "BLACK DISCO W/ JIL-C & FRANZ VON G"},
        {"date": "2025-12-05", "title": "SUBLIMINAL X SOLEM"},
        {"date": "2025-11-29", "title": "Ô BAL MASQUÉ : CLAQUETTES, CHAUSSETTES, PAILLETTES"},
        {"date": "2025-11-29", "title": "BBM 74"},
        {"date": "2025-11-28", "title": "SUBLIMINAL X DETRACK’HER"},
        {"date": "2025-11-22", "title": "MÉDINE"},
        {"date": "2025-11-21", "title": "MORGAN + ANTES & MADZES"},
        {"date": "2025-11-20", "title": "PROJECTION – GRAND DEBATS APRÈS LA TEMPÊTE... COMMENT GÉRER LA FORÊT À L’ÈRE CLIMATIQUE ?"},
        {"date": "2025-11-15", "title": "SUBLIMINAL X GARDEN OF SOUND"},
        {"date": "2025-11-15", "title": "MAIRO + AL-WALID + SMOKY"},
        {"date": "2025-11-14", "title": "KT GORIQUE + BADNAIY + TYLER"},
        {"date": "2025-11-08", "title": "BATBAIT + MOICTANI"},
        {"date": "2025-11-07", "title": "ARRABIATA : JUSTE SHANI + URUMI + LA COLLECTIVE"},
        {"date": "2025-11-01", "title": "FIESTA DE LOS MUERTOS"},
        {"date": "2025-10-31", "title": "PARANOISE W/ JEREMY J + PHO3 + SOLOSMOSE"},
        {"date": "2025-10-30", "title": "DEUX CLAQUES ET AU LIT ! : INFINITY KNIVES & BRIAN ENNALS + TALIABLE"},
        {"date": "2025-10-25", "title": "SOLD - OUT ! FÉLIX RABIN - LIVE SHOW RECORDING @ QKC"},
        {"date": "2025-10-25", "title": "MARCO D. TOURNÉE D’ADIEUX… SAISON 1 !"},
        {"date": "2025-10-24", "title": "DEUX CLAQUES ET AU LIT! MARIE KLOCK + ALICE"},
        {"date": "2025-10-18", "title": "SUBLIMINAL X DISSOLUTION & INTROSPECTIVE RECORDS"},
        {"date": "2025-10-17", "title": "INTERLOPE - Dj’ résident.e.x.s w/ Mouchaille"},
        {"date": "2025-10-11", "title": "Ô BAL MASQUÉ : Y2K / ANNÉES 2000"},
        {"date": "2025-10-10", "title": "BLIZZARD AUDIO CLUB FÊTE SES 5 ANS : AUST + J.NUNN + OWELLE"},
        {"date": "2025-10-04", "title": "TECH WITH US"},
        {"date": "2025-10-03", "title": "KICK OFF DJS RÉSIDENT·E·X·S 2025"},
        {"date": "2025-10-03", "title": "GRAND REOPENING : MONTE MAI + MEL D + MARY MIDDLEFIELD"},
        {"date": "2025-09-21", "title": "DOUBLÉ #3"},
        {"date": "2025-09-19", "title": "KICK BILL: VERNISSAGE DE L’ALBUM « KISS MY LIPS »"},
        {"date": "2025-09-13", "title": "ABSTRACTION II"},
        {"date": "2025-07-02", "title": "GYMNAZ’OUT"},
        {"date": "2025-06-06", "title": "TECH WITH US"},
        {"date": "2025-05-28", "title": "CHOCOLATE REMIX + LA TERRORISTA DEL SABOR // CLÔTURE DE SAISON"},
        {"date": "2025-05-28", "title": "CLOSING PARTY DES DJS RÉSIDENT·E·X·S 2024"},
        {"date": "2025-05-21", "title": "Rendez-Vous - Mediatraining : Comment Préparer Ses Interviews"},
        {"date": "2025-05-17", "title": "LOCAL FEST"},
        {"date": "2025-05-09", "title": "INTERLOPE - Dj’ résident.e.x.s : Mozka & Ghetto BVST"},
        {"date": "2025-05-03", "title": "VERNISSAGE OSMOSE TV + 24 KIARA"},
        {"date": "2025-05-02", "title": "IDEM SHOW : YOUSSEF SWATT’S + SCRED CONNEXION + LA BOUCLE"},
        {"date": "2025-05-02", "title": "DEUX CLAQUES ET AU LIT! LOVATARAXX + PARKER LEFTLOVER"},
        {"date": "2025-04-30", "title": "TECHNOWAR PRÉSENTE : TNW CLUB"},
        {"date": "2025-04-30", "title": "PUG IMPACT: VERNISSAGE EP AVEC GASOIL + SECRET GUEST"},
        {"date": "2025-04-26", "title": "ARRABIATA : CAMION BIP BIP + TENDINITES"},
        {"date": "2025-04-26", "title": "SOLD OUT - THEODORA"},
        {"date": "2025-04-25", "title": "PARADISCO"},
        {"date": "2025-04-25", "title": "WACKEN OPEN AIR : METAL BATTLE SWITZERLAND"},
        {"date": "2025-04-13", "title": "LOTO ALTERNO - 4 ÈME ÉDITION - DIMANCHE"},
        {"date": "2025-04-12", "title": "BLACK DISCO"},
        {"date": "2025-04-12", "title": "LOTO ALTERNO - SOLD OUT"},
        {"date": "2025-04-11", "title": "UBRE BLANCA + LETTEN 94"},
        {"date": "2025-04-05", "title": "GIULIA DABALA (VERNISSAGE) + MAFALDA HIGH"},
        {"date": "2025-04-04", "title": "STREET-ADDICT: DEMI PORTION + FANNY POLLY"},
        {"date": "2025-04-04", "title": "STREET-ADDICT: DEMI PORTION + FANNY POLLY"},
        {"date": "2025-03-29", "title": "BUNKR RELEASE PARTY + BEATRICE GRAF"},
        {"date": "2025-03-29", "title": "ZINÉE + ARøNE + AMIRAL"},
        {"date": "2025-03-28", "title": "DOMBRANCE + IL EST VILAINE + LADY GOBELET"},
        {"date": "2025-03-27", "title": "SACR - LES JEUNES CHANTENT LES DROITS HUMAINS"},
        {"date": "2025-03-22", "title": "ARRABIATA : MALVINA + BARBICOP"},
        {"date": "2025-03-21", "title": "SUBLIMINAL X RAVOLUTION"},
        {"date": "2025-03-21", "title": "STREET-ADDICT: SINIK + DOUBLE L"},
        {"date": "2025-03-15", "title": "ASIAN DUB FOUNDATION + TORCHON & GANJ FT. FREEKY"},
        {"date": "2025-03-14", "title": "PIERRE HUGUES JOSE + OSCAR LES VACANCES"},
        {"date": "2025-03-08", "title": "MANU LE MALIN + SWOOH LIVE AV + CUFTEN + HOELLYPOP POUR LES 10 ANS DU LABEL ASTROPOLIS"},
        {"date": "2025-03-07", "title": "A TABLE"},
        {"date": "2025-03-01", "title": "CIGARETTE CITY ALLSTARZ"},
        {"date": "2025-02-22", "title": "SOLD OUT - BSA SOUNDSYSTEM: INVASION TEKNO"},
        {"date": "2025-02-21", "title": "RUE OBERKAMPF + POTOCHKINE"},
        {"date": "2025-02-21", "title": "A.K.A IDIOTS FIRST SHOW"},
        {"date": "2025-02-15", "title": "SUBLIMINAL X BODY DANCE SYNTH MUSIC"},
        {"date": "2025-02-15", "title": "WALTER ASTRAL + FOREST LAW"},
        {"date": "2025-02-14", "title": "SAINT VALENTIN W/ VALENTINO VIVACE + LOLA BASTARD"},
        {"date": "2025-02-08", "title": "HAVING A BALL"},
        {"date": "2025-02-07", "title": "KHIDI X CASE A CHOCS : ANCIENT METHODS + UNHUMAN + 00RT + MAR/NE"},
        {"date": "2025-02-01", "title": "Ô BAL MASQUÉ : HANTÉ"},
        {"date": "2025-01-31", "title": "SUBLIMINAL X RETROBLAST"},
        {"date": "2025-01-25", "title": "TECH WITH US"},
        {"date": "2025-01-24", "title": "DEUX CLAQUES ET AU LIT! GORZ + ECKHART"},
        {"date": "2025-01-04", "title": "PETIT NOUVEL AN"},
        {"date": "2024-12-31", "title": "NOUVEL AN : PAILLETTES PARTOUT, JUSTICE NULLE PART"},
        {"date": "2024-12-22", "title": "DOUBLÉ #2"},
        {"date": "2024-12-21", "title": "FLECHE LOVE + ISIA"},
        {"date": "2024-12-21", "title": "ORSO + NEVBORN"},
        {"date": "2024-12-06", "title": "BLACK DISCO"},
        {"date": "2024-11-30", "title": "SOURCE : DASHA RUSH + NNAMAEL + PH03 B2B RAMON"},
        {"date": "2024-11-30", "title": "DASHA RUSH LIVE + KRIS MESS"},
        {"date": "2024-11-29", "title": "BAGARRE + EGGS AND TIARAS"},
        {"date": "2024-11-23", "title": "SAFETY TRANCE (CARDOPUSHER) + TOCCORORO + YURACHAIM"},
        {"date": "2024-11-23", "title": "LUCY KRUGER AND THE LOST BOYS + JONNY + LEA MARTINEZ"},
        {"date": "2024-11-22", "title": "SUBLIMINAL X LE ZOO : (E-)FAZ"},
        {"date": "2024-11-16", "title": "Ô BAL MASQUÉ : Y2K / ANNÉE 2000"},
        {"date": "2024-11-15", "title": "REPORTE AU 29.03.25 : ZINÉE + SEAN + AMIRAL"},
        {"date": "2024-11-15", "title": "SOIRÉE DES MAJORANT·E·X·S : FOREVER YOUNG"},
        {"date": "2024-11-10", "title": "FESTIVAL DE MARIONNETTES - LA GRENOUILLE QUI AVAIT BU TOUTE L’EAU"},
        {"date": "2024-11-09", "title": "SUBLIMINAL X ATMSPHR VOL. 2"},
        {"date": "2024-11-09", "title": "FESTIVAL DE MARIONNETTES - LA GRENOUILLE QUI AVAIT BU TOUTE L’EAU"},
        {"date": "2024-11-08", "title": "A TABLE"},
        {"date": "2024-11-06", "title": "FESTIVAL DE MARIONNETTES : VIVA !"},
        {"date": "2024-11-05", "title": "FESTIVAL DE MARIONNETTES : VIVA !"},
        {"date": "2024-11-02", "title": "FIESTA DE LOS MUERTOS"},
        {"date": "2024-11-01", "title": "ARRABIATA : AKIRA & LE SABBAT + THÉA + CREME SOLAIRE"},
        {"date": "2024-10-25", "title": "LUCIE ANTUNES + LA COLÈRE"},
        {"date": "2024-10-19", "title": "NAVA X CASE A CHOCS : ZOOMY, VILHELM, LILI CASTIGLIONI, WASTING SHIT + TYLERTIMO"},
        {"date": "2024-10-18", "title": "TECH WITH US"},
        {"date": "2024-10-05", "title": "KABA & HYAS + CLARO QUE SI + MANU KANN"},
        {"date": "2024-10-04", "title": "KICK OFF PARTY DES DJS RÉSIDENT·E·X·S 2024"},
        {"date": "2024-09-26", "title": "BOXING NOISE"},
        {"date": "2024-05-08", "title": "TATAKI WAVE PARTY"},
        {"date": "2024-05-04", "title": "PARANOISE W/ JULIA MARIA, .WAV_909, PH03"},
        {"date": "2024-05-04", "title": "BONNIE BANANE + L’ÉCLAIR + BUVETTE"},
        {"date": "2024-04-06", "title": "Rendez-Vous - Comprendre Et Évoluer Dans Le Milieu Des Musiques Actuelles"},
        {"date": "2024-04-05", "title": "SUBLIMINAL W/ LA BICHE, SLEVY, KROWL"},
        {"date": "2024-04-05", "title": "RAVOLUTION 2"},
        {"date": "2024-04-04", "title": "IDRIS ACKAMOOR AND THE PYRAMIDS + L’EFFET PHILÉMON"},
        {"date": "2024-03-28", "title": "MARIE DAVIDSON (DJSET) + DJ GIGOLA + BOUND BY ENDOGAMY + ORPHIA"},
        {"date": "2024-03-23", "title": "ABSTRACTION"},
        {"date": "2024-03-15", "title": "RELEASE PARTY PSYCHO WEAZEL (LIVE) + DINA SUMMER (LIVE) + CURSES (DJSET) + CAMPINGPONG (DJSET)"},
        {"date": "2024-03-14", "title": "JAM PLAISIRS COUPABLES"},
        {"date": "2024-03-09", "title": "DETRACK’NIGHT IX X MSKT"},
        {"date": "2024-02-24", "title": "TECH WITH US W/PHLOXO, EXIL DER SCHATTEN, FLATBEAT, DEBENJIY"},
        {"date": "2024-02-24", "title": "COCANHA"},
        {"date": "2024-02-23", "title": "SUBLIMINAL W/ JEUNEBOB, GËRXHALITA, YURACHAIM"},
        {"date": "2024-02-02", "title": "SUBLIMINAL X ATMSPHR"},
        {"date": "2024-02-01", "title": "Rendez-Vous - Table Ronde Sur L’Identité Artistique Avec Baby Volcano, Fulmine, My Name Is Fuzzy"},
        {"date": "2024-01-26", "title": "VERNISSAGE FIRE CULT + THE COME’N’GO"}
    ]

    first_names = ["Jean", "Marie", "Pierre", "Sophie", "Lucas", "Emma", "Thomas", "Lea", "Nicolas", "Julie", "David", "Sarah", "Paul", "Anna", "Julien", "Laura", "Kevin", "Celine", "Maxime", "Audrey", "Valentin"]
    last_names = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier"]

    for event in events:
        event_id = random.randint(10000, 99999)
        num_tickets = random.randint(10, 50)
        print(f"Generating {num_tickets} tickets for event: {event['title']}")

        for _ in range(num_tickets):
            prelocation_price = random.randint(10, 35)
            on_place_price = random.randint(20, 50)
            
            if on_place_price < prelocation_price:
                on_place_price = prelocation_price

            category = random.choice(["Prélocation", "Sur place"])
            price_amount = f"{prelocation_price:.2f}" if category == "Prélocation" else f"{on_place_price:.2f}"
            price = {
                "amount": price_amount,
                "currency": "CHF"
            }

            # Calculate random generatedAt between 6 months and 1 hour before event
            event_datetime = datetime.datetime.strptime(f"{event['date']} 21:00:00", "%Y-%m-%d %H:%M:%S")
            start_window = event_datetime - datetime.timedelta(days=180)
            end_window = event_datetime - datetime.timedelta(hours=1)
            time_diff = end_window - start_window
            random_seconds = random.randint(0, int(time_diff.total_seconds()))
            generated_at = start_window + datetime.timedelta(seconds=random_seconds)

            data = {
                "event": "ticket_created",
                "details": {
                    "ticket": {
                        "number": generate_random_string(),
                        "type": "online_presale",
                        "title": event["title"],
                        "category": category,
                        "eventId": event_id,
                        "event": event["title"],
                        "cancellationReason": "",
                        "generatedAt": generated_at.isoformat(),
                        "sessions": [
                            {
                                "name": event["title"],
                                "date": event["date"],
                                "time": "21:00:00",
                                "doors": "21:00:00",
                                "location": {
                                    "name": "Case à Chocs",
                                    "street": "Quai Philipe Godet 20",
                                    "city": "Neuchatel",
                                    "postcode": "2000"
                                }
                            }
                        ],
                        "promoter": "Case à Chocs",
                        "price": price
                    },
                    "buyer": {
                        "role": "customer",
                        "firstName": random.choice(first_names),
                        "lastName": random.choice(last_names),
                        "postcode": str(random.randint(1000, 9999))
                    }
                }
            }

            make_post_request(args.url, json.dumps(data), args.secret)
