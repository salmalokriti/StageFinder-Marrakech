"""Construit tous les liens de recherche (entreprises + offres) pour Marrakech."""
from urllib.parse import quote_plus

VILLE = "Marrakech"


def lien_google(requete: str) -> str:
    return f"https://www.google.com/search?q={quote_plus(requete)}"


def liens_entreprise(nom, lat=None, lng=None, place_id=None) -> dict:
    """Liens utiles pour UNE entreprise (clés = noms des colonnes du tableau)."""
    a_coords = lat is not None and lng is not None and lat == lat and lng == lng  # lat == lat : exclut NaN
    maps = "https://www.google.com/maps/search/?api=1&query=" + (
        f"{lat},{lng}" if a_coords else quote_plus(f"{nom} {VILLE}"))
    if place_id and place_id == place_id:
        maps += f"&query_place_id={place_id}"
    itineraire = (f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}" if a_coords else maps)
    return {
        "Google": lien_google(f'"{nom}" {VILLE}'),
        "Google Maps": maps,
        "Itinéraire": itineraire,
        "LinkedIn (entreprise)": "https://www.linkedin.com/search/results/companies/?keywords="
                                 + quote_plus(f"{nom} {VILLE}"),
        "Trouver e-mail": lien_google(f'"{nom}" {VILLE} contact email'),
        "Offres Google": lien_google(f'"{nom}" stage OR emploi OR recrutement {VILLE}'),
        "Offres Indeed": f"https://ma.indeed.com/jobs?q={quote_plus(nom)}&l={VILLE}",
    }


def liens_offres(mot_cle: str) -> dict:
    """Liens de recherche d'offres de stage pour un mot-clé (secteur, compétence...)."""
    q = f"stage {mot_cle}".strip()
    return {
        "Google": lien_google(f"{q} {VILLE}"),
        "Indeed": f"https://ma.indeed.com/jobs?q={quote_plus(q)}&l={VILLE}",
        "LinkedIn": "https://www.linkedin.com/jobs/search/?keywords="
                    f"{quote_plus(q)}&location={quote_plus(VILLE + ', Maroc')}",
        "Stagiaires.ma": lien_google(f"site:stagiaires.ma {q} {VILLE}"),
    }
