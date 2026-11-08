import os
import pandas as pd


# ============================================================
# 1. CHEMINS DES FICHIERS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PROJECT_DIR = os.path.dirname(BASE_DIR)

DATA_DIR = os.path.join(PROJECT_DIR, "01_Donnees")

FICHIER_BRUT = os.path.join(
    DATA_DIR,
    "donnees_brutes.xlsx"
)

FICHIER_NETTOYE = os.path.join(
    DATA_DIR,
    "donnees_nettoyees.xlsx"
)


# ============================================================
# 2. CHARGER LES DONNÉES BRUTES
# ============================================================

df = pd.read_excel(FICHIER_BRUT)

print("Nombre de lignes avant nettoyage :", len(df))


# ============================================================
# 3. SUPPRIMER LES ESPACES INUTILES
# ============================================================

colonnes_texte = [
    "Entreprise",
    "Adresse",
    "Source",
    "Recherche"
]

for colonne in colonnes_texte:
    df[colonne] = df[colonne].astype(str).str.strip()


# ============================================================
# 4. SUPPRIMER LES ENTREPRISES SANS NOM
# ============================================================

df = df[
    (df["Entreprise"] != "") &
    (df["Entreprise"] != "nan")
]


# ============================================================
# 5. SUPPRIMER LES DOUBLONS
# ============================================================

df = df.drop_duplicates(
    subset=["Place_ID"]
)


# ============================================================
# 6. SUPPRIMER LES COORDONNÉES MANQUANTES
# ============================================================

df = df.dropna(
    subset=["Latitude", "Longitude"]
)


# ============================================================
# 7. RÉINITIALISER LES ID
# ============================================================

df = df.reset_index(drop=True)

df["ID"] = range(1, len(df) + 1)


# ============================================================
# 8. SAUVEGARDER LES DONNÉES NETTOYÉES
# ============================================================

df.to_excel(
    FICHIER_NETTOYE,
    index=False
)


# ============================================================
# 9. AFFICHER LE RÉSULTAT
# ============================================================

print("\n======================================")
print("NETTOYAGE TERMINÉ")
print("======================================")

print("Nombre de lignes après nettoyage :", len(df))

print("\nFichier créé :")
print(FICHIER_NETTOYE)

print("\nAperçu :")
print(df.head())