import os
import time
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv


# ============================================================
# 1. CHARGER LA CLÉ API DEPUIS LE FICHIER .env
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


if not API_KEY:
    print("ERREUR : la clé Google Maps n'a pas été trouvée dans .env")
    exit()


# ============================================================
# 2. CONFIGURATION DE GOOGLE PLACES API
# ============================================================

URL = "https://places.googleapis.com/v1/places:searchText"

HEADERS = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask":
        "places.id,"
        "places.displayName,"
        "places.formattedAddress,"
        "places.location"
}


# ============================================================
# 3. RECHERCHES À EFFECTUER
# ============================================================

recherches = [
    "entreprises informatiques à Marrakech",
    "entreprises développement web à Marrakech",
    "entreprises intelligence artificielle à Marrakech",
    "entreprises data à Marrakech",
    "entreprises digitales à Marrakech",
    "entreprises software à Marrakech"
]


# ============================================================
# 4. LISTE POUR STOCKER LES RÉSULTATS
# ============================================================

donnees = []

id_ligne = 1

date_collecte = datetime.now().strftime("%Y-%m-%d")


# ============================================================
# 5. EFFECTUER LES RECHERCHES
# ============================================================

for recherche in recherches:

    print("\nRecherche :", recherche)

    data = {
        "textQuery": recherche,
        "languageCode": "fr"
    }

    response = requests.post(
        URL,
        headers=HEADERS,
        json=data
    )

    print("Code HTTP :", response.status_code)

    if response.status_code != 200:
        print("Erreur :", response.text)
        continue

    resultats = response.json().get("places", [])

    print("Nombre de résultats :", len(resultats))


    # ========================================================
    # 6. EXTRAIRE LES INFORMATIONS
    # ========================================================

    for place in resultats:

        nom = place.get("displayName", {}).get("text", "")

        adresse = place.get("formattedAddress", "")

        location = place.get("location", {})

        latitude = location.get("latitude", "")

        longitude = location.get("longitude", "")

        place_id = place.get("id", "")


        donnees.append({
            "ID": id_ligne,
            "Place_ID": place_id,
            "Entreprise": nom,
            "Adresse": adresse,
            "Latitude": latitude,
            "Longitude": longitude,
            "Source": "Google Places",
            "Recherche": recherche,
            "Date collecte": date_collecte
        })

        id_ligne += 1


    # Petite pause entre les recherches
    time.sleep(1)


# ============================================================
# 7. CRÉER LE DATAFRAME
# ============================================================

df = pd.DataFrame(donnees)


# ============================================================
# 8. CRÉER LE DOSSIER 01_Donnees
# ============================================================

PROJECT_DIR = os.path.dirname(BASE_DIR)

DATA_DIR = os.path.join(
    PROJECT_DIR,
    "01_Donnees"
)

os.makedirs(DATA_DIR, exist_ok=True)


# ============================================================
# 9. SAUVEGARDER DANS EXCEL
# ============================================================

OUTPUT_FILE = os.path.join(
    DATA_DIR,
    "donnees_brutes.xlsx"
)

df.to_excel(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 10. AFFICHER LE RÉSULTAT
# ============================================================

print("\n======================================")
print("COLLECTE TERMINÉE")
print("======================================")

print("Nombre total de lignes :", len(df))

print("Fichier Excel créé :")
print(OUTPUT_FILE)

print("\nAperçu des données :")
print(df.head())