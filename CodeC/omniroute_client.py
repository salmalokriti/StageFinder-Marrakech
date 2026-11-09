"""Client IA Gemini compatible avec l'API OpenAI."""

import os
import requests

# Session HTTP
_session = requests.Session()
_session.trust_env = False

# Configuration Gemini
BASE_URL_DEFAUT = "https://generativelanguage.googleapis.com/v1beta/openai"


def _configuration(nom: str, defaut: str = "") -> str:
    """Lit la configuration depuis Streamlit Secrets ou les variables d'environnement."""

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
    """Récupère l'adresse de l'API Gemini."""

    base = _configuration("OMNIROUTE_BASE_URL", BASE_URL_DEFAUT)

    return [base.rstrip("/")]


def _headers() -> dict:
    """Récupère la clé API Gemini."""

    cle = _configuration("OMNIROUTE_API_KEY")

    return {
        "Authorization": f"Bearer {cle}",
        "Content-Type": "application/json"
    } if cle else {}


def omniroute_disponible() -> bool:
    """Vérifie si l'API Gemini est accessible."""

    if not _headers():
        return False

    for base in _bases():
        try:
            r = _session.get(
                f"{base}/models",
                timeout=15,
                headers=_headers()
            )

            if r.status_code == 200:
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
                timeout=15,
                headers=_headers()
            )

            lignes.append(
                f"API Gemini -> HTTP {r.status_code}"
            )

            if r.status_code != 200:
                lignes.append(r.text[:300])

        except requests.RequestException as e:
            lignes.append(
                f"API inaccessible : {type(e).__name__}"
            )

    return "\n".join(lignes)


def generer_texte(prompt: str, systeme: str = "") -> str:
    """Envoie une demande à Gemini et retourne le texte généré."""

    if not _headers():
        raise RuntimeError("Clé API Gemini non configurée.")

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
                headers=_headers(),
                json={
                    "model": _configuration(
                        "OMNIROUTE_MODEL",
                        "gemini-3.8-flash"
                    ),
                    "messages": messages,
                    "temperature": 0.7
                },
                timeout=90
            )

            if r.status_code != 200:
                raise RuntimeError(
                    f"Erreur Gemini HTTP {r.status_code} : "
                    f"{r.text[:500]}"
                )

            contenu = r.json()["choices"][0]["message"]["content"]

            if not isinstance(contenu, str) or not contenu.strip():
                raise RuntimeError("Gemini a retourné une réponse vide.")

            return contenu.strip()

        except requests.RequestException as e:
            derniere = e

    raise RuntimeError(f"Connexion Gemini impossible : {derniere}")


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
