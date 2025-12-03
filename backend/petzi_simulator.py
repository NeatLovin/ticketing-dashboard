import argparse
import datetime
import hmac
import requests
import random
import string
import json
import math
 
# Liste d'artistes et événements
artists = [
    {"name": "LA NUIT D'AFRIQUE","date": "2024-10-20","id": 1},
    {"name": "Concert Rock Stars","date": "2024-09-29","id": 2},
    {"name": "Jazz Night","date": "2025-01-05","id": 3},
    {"name": "Pop Music Extravaganza","date": "2024-05-25","id": 4},
    {"name": "Bruno Mars","date": "2024-12-25","id": 5}
]
 
# Liste des catégories possibles pour le ticket
ticket_categories = ["Prélocation", "ticketproof", "self_ticket"]
 
# Location fixe "Case à Chocs"
location = {
    "name": "Case à Chocs",
    "street": "Quai Philipe Godet 20",
    "city": "Neuchatel",
    "postcode": "2000"
}
 
def generate_random_string(length=12):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))
 
def make_header(body, secret):
    unix_timestamp = str(datetime.datetime.timestamp(datetime.datetime.now())).split('.')[0]
    body_to_sign = f'{unix_timestamp}.{body}'.encode()
    digest = hmac.new(secret.encode(), body_to_sign, "sha256").hexdigest()
    headers = {'Petzi-Signature': f't={unix_timestamp},v1={digest}', 'Petzi-Version': '2',
               'Content-Type': 'application/json', 'User-Agent': 'PETZI webhook'}
    return headers
 
def make_post_request(url, data, secret):
    try:
        response = requests.post(url, data=data.encode('utf-8'), headers=make_header(data, secret))
        if response.status_code == 200:
            print(f"Request successful. Response: {response.text}")
        else:
            print(f"Request failed with status code {response.status_code}.")
    except Exception as e:
        print(f"An error occurred: {e}")
 
def generate_ticket_dates(event_date_str, num_tickets=50):
    # Convertir la date de l'événement en datetime
    event_date = datetime.datetime.strptime(event_date_str, "%Y-%m-%d")
   
    # Calculer la plage de dates pour la génération des tickets
    # Début: entre 100 et 30 jours avant l'événement
    start_days = random.randint(30, 100)
    start_date = event_date - datetime.timedelta(days=start_days)
   
    # Calculer le nombre de jours avant l'événement
    total_days = (event_date - start_date).days
   
    # Créer une liste de dates avec une courbe exponentielle d'augmentation des ventes
    ticket_dates = []
   
    # Diviser la période en 3 phases
    early_phase_days = total_days // 3
    mid_phase_days = total_days // 3
    final_phase_days = total_days - early_phase_days - mid_phase_days
   
    # Phase 1 : Ventes lentes et constantes
    for day in range(early_phase_days):
        current_date = start_date + datetime.timedelta(days=day)
        tickets_this_day = random.randint(1, 3)
        ticket_dates.extend([current_date.isoformat()] * tickets_this_day)
   
    # Phase 2 : Augmentation progressive des ventes
    for day in range(early_phase_days, early_phase_days + mid_phase_days):
        current_date = start_date + datetime.timedelta(days=day)
        # Augmentation progressive
        tickets_this_day = int(5 * (1 + math.sin(math.pi * (day - early_phase_days) / mid_phase_days)))
        ticket_dates.extend([current_date.isoformat()] * tickets_this_day)
   
    # Phase 3 : Augmentation rapide des ventes sur les derniers jours
    for day in range(early_phase_days + mid_phase_days, total_days):
        current_date = start_date + datetime.timedelta(days=day)
        # Augmentation exponentielle sur les derniers jours
        progress = (day - (early_phase_days + mid_phase_days)) / final_phase_days
        tickets_this_day = int(10 * (1 + progress * 10))  # De 10 à 100 tickets par jour
        ticket_dates.extend([current_date.isoformat()] * tickets_this_day)
   
    # Ajuster si nécessaire pour atteindre le nombre total de tickets souhaité
    if len(ticket_dates) > num_tickets:
        ticket_dates = random.sample(ticket_dates, num_tickets)
    elif len(ticket_dates) < num_tickets:
        # Compléter avec des dates des derniers jours si besoin
        last_few_days = ticket_dates[-final_phase_days:]
        while len(ticket_dates) < num_tickets:
            ticket_dates.append(random.choice(last_few_days))
   
    return ticket_dates
 
def generate_buyer_info():
    # Liste de prénoms et noms français/suisses
    first_names = ["Jean", "Marie", "Pierre", "Sophie", "Laurent", "Céline", "Marc", "Isabelle",
                   "David", "Anne", "Thomas", "Claire", "Nicolas", "Lucie", "Julien", "Emma"]
    last_names = ["Dupont", "Martin", "Durand", "Leroy", "Moreau", "Dubois", "Bernard", "Schmidt",
                  "Laurent", "Michel", "Garcia", "Roux", "Petit", "Fontaine", "Mercier", "Blanc"]
   
    postCode ={
        '1000': 'Lausanne',
  '1004': 'Lausanne',
  '1005': 'Lausanne',
  '1006': 'Lausanne',
  '1007': 'Lausanne',
  '1008': 'Lausanne',
  '1009': 'Lausanne',
  '1010': 'Lausanne',
  '1011': 'Lausanne',
  '1012': 'Lausanne',
  '1018': 'Lausanne',
 
  '1003': 'Lausanne-Sébeillon',
  '1002': 'Lausanne-Flon',
 
  '1110': 'Morges',
  '1131': 'Tolochenaz',
  '1124': 'Gollion',
 
  '1009': 'Pully',
  '1090': 'La Croix-sur-Lutry',
 
  '1260': 'Nyon',
  '1262': 'Eysins',
 
  '1004': 'Chauderon',
 
  '1007': 'Rumine',
  '1005': 'Bourdonette',
 
  '1010': 'Secteur Riponne',
  '1011': 'Secteur Montbenon',
 
  '2000': 'Neuchâtel',
  '2002': 'Neuchâtel',
 
  '1200': 'Genève',
  '1202': 'Genève',
  '1203': 'Genève',
  '1204': 'Genève',
  '1205': 'Genève',
  '1206': 'Genève',
  '1207': 'Genève',
  '1208': 'Genève',
 
  '1800': 'Vevey',
  '1820': 'Montreux',
 
    }
    return {
        "role": "customer",
        "firstName": random.choice(first_names),
        "lastName": random.choice(last_names),
        "postcode": random.choice(list(postCode.keys()))
    }
 
if __name__ == "__main__":
    # Create a command line argument parser
    parser = argparse.ArgumentParser(description="HTTP POST Request with JSON Body")
    parser.add_argument("url", type=str, help="URL to send the POST request to")
    parser.add_argument("secret", nargs='?', type=str, help="secret shared between your server and petzi simulator",
                        default="AEeyJhbGciOiJIUzUxMiIsImlzcyI6")
    parser.add_argument("--tickets", type=int, default=50, help="Number of tickets to generate")
 
    # Parse the command line arguments
    args = parser.parse_args()
 
    # Sélectionner un artiste aléatoire
    selected_artist = random.choice(artists)
 
    # Générer les dates des tickets
    ticket_dates = generate_ticket_dates(selected_artist["date"], args.tickets)
 
    # Générer les tickets
    for ticket_date in ticket_dates:
        # Sélectionner une catégorie de ticket aléatoire
        selected_category = random.choice(ticket_categories)
 
        # Créer un ticket avec des informations aléatoires
        data = {
            "event": "ticket_created",
            "details": {
                "ticket": {
                    "number": generate_random_string(),
                    "type": selected_category,
                    "title": selected_artist["name"],
                    "category": selected_category,
                    "eventId": selected_artist["id"],
                    "event": selected_artist["name"],
                    "cancellationReason": "",
                    "generatedAt": ticket_date,
                    "sessions": [
                        {
                            "name": selected_artist["name"],
                            "date": selected_artist["date"],
                            "time": "21:00:00",
                            "doors": "20:00:00",
                            "location": location
                        }
                    ],
                    "promoter": "Case à Chocs",
                    "price": {
                        "amount": str(random.randint(30, 100)),
                        "currency": "CHF"
                    }
                },
                "buyer": generate_buyer_info()
            }
        }
 
        # Convertir les données en JSON
        data_json = json.dumps(data, indent=4)
 
        # Faire la requête POST
        make_post_request(args.url, data_json, args.secret)