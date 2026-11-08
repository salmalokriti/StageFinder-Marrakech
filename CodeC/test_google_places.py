import os
import requests
from dotenv import load_dotenv

# Charger la clé depuis .env
load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
print("Clé chargée :", API_KEY is not None)
print("Longueur :", len(API_KEY) if API_KEY else 0)

# URL de Google Places API
url = "https://places.googleapis.com/v1/places:searchText"

# Recherche
data = {
    "textQuery": "entreprises informatiques à Marrakech"
}

# En-têtes
headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location"
}

# Envoyer la requête
response = requests.post(
    url,
    headers=headers,
    json=data
)

# Afficher le résultat
print("Code HTTP :", response.status_code)
print(response.text)