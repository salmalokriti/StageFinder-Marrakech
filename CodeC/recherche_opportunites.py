import os
import pandas as pd
from datetime import datetime
from ddgs import DDGS


# =====================================================
# 1. CHEMINS
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "01_Donnees")

FICHIER_EXCEL = os.path.join(
    DATA_DIR,
    "opportunites.xlsx"
)

ville = "Marrakech"


# =====================================================
# 2. MOTS-CLES
# =====================================================

mots_cles = [
    "intelligence artificielle",
    "data science",
    "machine learning",
    "NLP",
    "LLM",
    "automatisation IA",
    "data analyst",
    "data engineer",
    "computer vision"
]


# =====================================================
# 3. EXTRAIRE ENTREPRISE
# =====================================================

def extraire_entreprise(titre, lien):

    entreprise = ""

    titre = titre.strip()
    lien = lien.strip()


    # -------------------------------------------------
    # LINKEDIN
    # Exemple:
    # I-TRACING recrute pour des postes de Stage...
    # -------------------------------------------------

    if " recrute pour des postes " in titre.lower():

        entreprise = titre.split(
            " recrute pour des postes ",
            1
        )[0].strip()


    # -------------------------------------------------
    # LINKEDIN
    # Exemple URL:
    # ...-at-tietalent-4079986435
    # -------------------------------------------------

    elif "linkedin.com/jobs/view" in lien.lower():

        partie = lien.lower().split("-at-")

        if len(partie) > 1:

            entreprise = partie[-1]

            entreprise = entreprise.rsplit(
                "-",
                1
            )[0]

            entreprise = entreprise.replace(
                "-",
                " "
            )


    # -------------------------------------------------
    # STAGIAIRES.MA
    # Exemple:
    # Stage IA / Machine Learning - Marrakech
    # chez Orchid Island Real Estate
    # -------------------------------------------------

    elif " chez " in titre.lower():

        entreprise = titre.split(
            " chez ",
            1
        )[1]

        entreprise = entreprise.split(
            "|",
            1
        )[0].strip()


    # -------------------------------------------------
    # NETTOYAGE
    # -------------------------------------------------

    entreprises_invalides = [
        "",
        "indeed",
        "indeed.com",
        "linkedin",
        "linkedin.com",
        "stagiaires.ma",
        "marrakech",
        "casablanca",
        "france"
    ]

    if entreprise.lower() in entreprises_invalides:

        entreprise = ""


    return entreprise.strip(" -|")


# =====================================================
# 4. VERIFIER SI C'EST MARRAKECH
# =====================================================

def concerne_marrakech(titre, description):

    texte = (
        titre + " " + description
    ).lower()

    return (
        "marrakech" in texte
        or
        "marrakesh" in texte
    )


# =====================================================
# 5. LISTE FINALE
# =====================================================

opportunites = []


# =====================================================
# 6. RECHERCHE
# =====================================================

with DDGS() as ddgs:

    for mot in mots_cles:

        recherche = f"stage {mot} Marrakech"

        print("\n======================================")
        print("Recherche :", recherche)
        print("======================================")


        try:

            resultats = list(
                ddgs.text(
                    recherche,
                    max_results=8
                )
            )

            print(
                "Résultats trouvés :",
                len(resultats)
            )


        except Exception as e:

            print(
                "Erreur recherche :",
                e
            )

            continue


        # =================================================
        # 7. TRAITER LES RESULTATS
        # =================================================

        for resultat in resultats:

            titre = resultat.get(
                "title",
                ""
            ).strip()

            lien = resultat.get(
                "href",
                ""
            ).strip()

            description = resultat.get(
                "body",
                ""
            ).strip()


            # -------------------------------------------------
            # Ignorer résultat vide
            # -------------------------------------------------

            if not titre or not lien:

                continue


            # -------------------------------------------------
            # SOURCE
            # -------------------------------------------------

            if "linkedin.com" in lien.lower():

                source = "LinkedIn"

            elif "indeed.com" in lien.lower():

                source = "Indeed"

            elif "stagiaires.ma" in lien.lower():

                source = "Stagiaires.ma"

            else:

                source = "Autre"


            # -------------------------------------------------
            # Vérifier Marrakech
            # -------------------------------------------------

            if not concerne_marrakech(
                titre,
                description
            ):

                print(
                    "Ignorée (pas Marrakech) :",
                    titre[:70]
                )

                continue


            # -------------------------------------------------
            # ENTREPRISE
            # -------------------------------------------------

            entreprise = extraire_entreprise(
                titre,
                lien
            )


            # -------------------------------------------------
            # AJOUT
            # -------------------------------------------------

            opportunites.append({

                "Entreprise": entreprise,

                "Opportunité": titre,

                "Type": "Stage",

                "Domaine": mot,

                "Ville": "Marrakech",

                "Source": source,

                "Lien": lien,

                "Date collecte":
                    datetime.now().strftime(
                        "%Y-%m-%d"
                    ),

                "Statut de l'offre":
                    "À vérifier"
            })


            # -------------------------------------------------
            # AFFICHAGE
            # -------------------------------------------------

            print("\n✅ OFFRE")

            print(
                "Entreprise :",
                entreprise if entreprise else "À identifier"
            )

            print(
                "Opportunité :",
                titre
            )

            print(
                "Source :",
                source
            )

            print(
                "Lien :",
                lien
            )


# =====================================================
# 8. CREER DATAFRAME
# =====================================================

df = pd.DataFrame(
    opportunites
)
# -----------------------------------------------------
# AJOUT : Remplacer les valeurs vides par "Non spécifié"
# -----------------------------------------------------
if not df.empty and "Entreprise" in df.columns:
    df["Entreprise"] = df["Entreprise"].replace(r"^\s*$", "Non spécifié", regex=True)

# =====================================================
# 9. SUPPRIMER DOUBLONS
# =====================================================

if not df.empty:

    df = df.drop_duplicates(
        subset=["Lien"],
        keep="first"
    )


# =====================================================
# 10. ORDRE DES COLONNES
# =====================================================

colonnes = [
    "Entreprise",
    "Opportunité",
    "Type",
    "Domaine",
    "Ville",
    "Source",
    "Lien",
    "Date collecte",
    "Statut de l'offre"
]


if df.empty:

    df = pd.DataFrame(
        columns=colonnes
    )

else:

    df = df[colonnes]


# =====================================================
# 11. ECRASER L'ANCIEN EXCEL
# =====================================================

df.to_excel(
    FICHIER_EXCEL,
    index=False
)


# =====================================================
# 12. RESULTAT FINAL
# =====================================================

print("\n")
print("======================================")
print("RECHERCHE TERMINÉE")
print("======================================")

print(
    "Nombre d'offres :",
    len(df)
)

print(
    "Fichier :",
    FICHIER_EXCEL
)

print("\nAperçu :")

print(df.to_string(index=False))