from pathlib import Path
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 28)

# Le fichier est dans ../01_Donnees (le dossier à côté de CodeC)
chemin = Path(__file__).resolve().parent.parent / "01_Donnees" / "donnees_brutes.xlsx"
df = pd.read_excel(chemin)

print("Aperçu des 5 premières lignes :")
print(df.head())

print("\nDimensions (lignes, colonnes) :", df.shape)

print("\nInformations sur les colonnes :")
df.info()

print("\nValeurs manquantes par colonne :")
print(df.isna().sum())

print("\nDoublons sur Place_ID :", df["Place_ID"].duplicated().sum())