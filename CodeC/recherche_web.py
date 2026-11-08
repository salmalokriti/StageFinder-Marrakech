"""Recherche d'offres sur le web (via DuckDuckGo) limitée à Indeed / LinkedIn / Stagiaires.ma."""
import pandas as pd

SITES = {
    "Indeed": "site:ma.indeed.com",
    "LinkedIn": "site:linkedin.com/jobs",
    "Stagiaires.ma": "site:stagiaires.ma",
    "Web (tous sites)": "",
}


def chercher_offres(mot_cle: str, plateformes: list, max_par_site: int = 8) -> pd.DataFrame:
    from ddgs import DDGS  # importé ici : l'app démarre même si ddgs manque

    lignes = []
    with DDGS() as ddgs:
        for nom in plateformes:
            requete = f"{SITES[nom]} stage {mot_cle} Marrakech".strip()
            try:
                for r in ddgs.text(requete, max_results=max_par_site):
                    lignes.append({"Plateforme": nom, "Titre": r.get("title", ""),
                                   "Extrait": (r.get("body", "") or "")[:200], "Lien": r.get("href", "")})
            except Exception as e:  # une plateforme qui échoue ne bloque pas les autres
                lignes.append({"Plateforme": nom, "Titre": f"⚠️ Recherche indisponible ({type(e).__name__})",
                               "Extrait": "", "Lien": ""})
    df = pd.DataFrame(lignes, columns=["Plateforme", "Titre", "Extrait", "Lien"])
    return df.drop_duplicates("Lien") if not df.empty else df
