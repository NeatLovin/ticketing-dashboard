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
        {"date": "2025-09-13", "title": "ABSTRACTION II"}
    ]

    first_names = ["Jean", "Marie", "Pierre", "Sophie", "Lucas", "Emma", "Thomas", "Lea", "Nicolas", "Julie", "David", "Sarah", "Paul", "Anna", "Julien", "Laura", "Kevin", "Celine", "Maxime", "Audrey"]
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
