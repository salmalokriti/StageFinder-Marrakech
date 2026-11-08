"""Client OmniRoute (passerelle IA locale compatible OpenAI).
Installation : npm install -g omniroute  puis  omniroute   (API : http://localhost:20128/v1)
"""
import os
import requests

# On ignore les proxys Windows/entreprise : OmniRoute est sur CE PC.
_session = requests.Session()
_session.trust_env = False


def _bases() -> list:
    """Adresses à essayer (localhost, puis 127.0.0.1 si localhost pose problème)."""
    base = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128/v1").rstrip("/")
    return [base, base.replace("localhost", "127.0.0.1")] if "localhost" in base else [base]


def _headers() -> dict:
    cle = os.getenv("OMNIROUTE_API_KEY", "").strip().strip('"').strip("'")
    return {"Authorization": f"Bearer {cle}"} if cle else {}


def omniroute_disponible() -> bool:
    """Vrai si le serveur OmniRoute répond (même si la clé est refusée : l'erreur exacte
    s'affichera alors au moment de rédiger)."""
    for base in _bases():
        try:
            r = _session.get(f"{base}/models", timeout=4, headers=_headers())
            if r.status_code in (200, 401, 403):
                return True
        except requests.RequestException:
            continue
    return False


def diagnostic() -> str:
    """Texte lisible expliquant pourquoi ça ne marche pas."""
    lignes = [f"Clé API lue dans .env : {'oui' if _headers() else 'NON (OMNIROUTE_API_KEY vide)'}"]
    for base in _bases():
        try:
            r = _session.get(f"{base}/models", timeout=4, headers=_headers())
            lignes.append(f"{base}/models -> HTTP {r.status_code}")
        except requests.RequestException as e:
            lignes.append(f"{base}/models -> injoignable ({type(e).__name__})")
    return "\n".join(lignes)


def generer_texte(prompt: str, systeme: str = "") -> str:
    messages = ([{"role": "system", "content": systeme}] if systeme else []) + [{"role": "user", "content": prompt}]
    derniere = None
    for base in _bases():
        try:
            r = _session.post(f"{base}/chat/completions",
                              headers={**_headers(), "Content-Type": "application/json"},
                              json={"model": os.getenv("OMNIROUTE_MODEL", "auto"),
                                    "messages": messages, "temperature": 0.7},
                              timeout=90)
        except requests.RequestException as e:
            derniere = e
            continue
        if r.status_code != 200:
            raise RuntimeError(f"HTTP {r.status_code} : {r.text[:300]}")
        return r.json()["choices"][0]["message"]["content"].strip()
    raise RuntimeError(f"OmniRoute injoignable ({derniere})")


def rediger_email_candidature(entreprise, domaine, adresse, competences, nom_candidat, offre="") -> str:
    systeme = ("Tu rédiges des e-mails de candidature spontanée pour un stage, en français, ton professionnel "
               "et chaleureux, 120 à 160 mots, sans inventer de faits. Réponds uniquement avec le corps de "
               "l'e-mail, sans objet.")
    prompt = (f"Candidat : {nom_candidat}\n"
              f"Compétences du CV : {', '.join(competences) if competences else 'non précisées'}\n"
              f"Entreprise visée : {entreprise} (secteur : {domaine}, adresse : {adresse}, Marrakech)\n"
              + (f"Offre visée : {offre}. Mentionne ce poste/stage précisément.\n" if offre else "")
              + "Le CV est en pièce jointe. Termine par une demande d'entretien.")
    return generer_texte(prompt, systeme)
