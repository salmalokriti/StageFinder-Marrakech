
"""Client OmniRoute (passerelle IA compatible OpenAI).

Installation locale :
npm install -g omniroute
omniroute

API : http://localhost:20128/v1
"""

import os
import requests

# Session HTTP
_session = requests.Session()
_session.trust_env = False


def _configuration(nom: str, defaut: str = "") -> str:
    """Lit une configuration depuis Streamlit Secrets ou les variables d'environnement."""
    valeur = ""

    try:
        import streamlit as st
        valeur = str(st.secrets.get(nom, "")).strip()
    except Exception:
        pass

    if not valeur:
        valeur = os.getenv(nom, defaut).strip()

    return valeur.strip('"').strip("'")


def _bases() -> list:
    """Récupère l'adresse OmniRoute depuis Streamlit Secrets ou .env."""

    base = _configuration(
        "OMNIROUTE_BASE_URL",
        "http://localhost:20128/v1"
    )

    base = base.rstrip("/")

    if "localhost" in base:
        return [base, base.replace("localhost", "127.0.0.1")]

    return [base]


def _headers() -> dict:
    """Récupère la clé API."""

    cle = _configuration("OMNIROUTE_API_KEY")

    return {"Authorization": f"Bearer {cle}"} if cle else {}


def omniroute_disponible() -> bool:
    """Vérifie si le serveur OmniRoute est accessible."""

    for base in _bases():
        try:
            r = _session.get(
                f"{base}/models",
                timeout=10,
                headers=_headers()
            )

            if r.status_code in (200, 401, 403):
                return True

        except requests.RequestException:
            continue

    return False


def diagnostic() -> str:
    """Affiche un diagnostic de connexion."""

    lignes = [
        f"Clé API configurée : {'oui' if _headers() else 'NON'}"
    ]

    for base in _bases():
        try:
            r = _session.get(
                f"{base}/models",
                timeout=10,
                headers=_headers()
            )

            lignes.append(f"{base}/models -> HTTP {r.status_code}")

        except requests.RequestException as e:
            lignes.append(
                f"{base}/models -> injoignable ({type(e).__name__})"
            )

    return "\n".join(lignes)


def generer_texte(prompt: str, systeme: str = "") -> str:
    """Envoie une demande au modèle IA via OmniRoute."""

    messages = (
        [{"role": "system", "content": systeme}]
        if systeme else []
    ) + [
        {"role": "user", "content": prompt}
    ]

    derniere = None

    for base in _bases():
        try:
            r = _session.post(
                f"{base}/chat/completions",
                headers={
                    **_headers(),
                    "Content-Type": "application/json"
                },
                json={
                    "model": _configuration("OMNIROUTE_MODEL", "auto"),
                    "messages": messages,
                    "temperature": 0.7
                },
                timeout=90
            )

        except requests.RequestException as e:
            derniere = e
            continue

        if r.status_code != 200:
            raise RuntimeError(
                f"HTTP {r.status_code} : {r.text[:300]}"
            )

        try:
            contenu = r.json()["choices"][0]["message"]["content"]
            return contenu.strip()

        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise RuntimeError(
                f"Réponse OmniRoute invalide : {e}"
            ) from e

    raise RuntimeError(f"OmniRoute injoignable ({derniere})")


def rediger_email_candidature(
    entreprise,
    domaine,
    adresse,
    competences,
    nom_candidat,
    offre=""
) -> str:

    systeme = (
        "Tu rédiges des e-mails de candidature spontanée pour un stage, "
        "en français, avec un ton professionnel et chaleureux, "
        "de 120 à 160 mots, sans inventer de faits. "
        "Réponds uniquement avec le corps de l'e-mail, sans objet."
    )

    prompt = (
        f"Candidat : {nom_candidat}\n"
        f"Compétences du CV : "
        f"{', '.join(competences) if competences else 'non précisées'}\n"
        f"Entreprise visée : {entreprise} "
        f"(secteur : {domaine}, adresse : {adresse}, Marrakech)\n"
        + (
            f"Offre visée : {offre}. "
            "Mentionne ce poste/stage précisément.\n"
            if offre else ""
        )
        + "Le CV est en pièce jointe. Termine par une demande d'entretien."
    )

    return generer_texte(prompt, systeme)
