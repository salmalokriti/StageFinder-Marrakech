```python
"""Client OmniRoute : passerelle IA compatible OpenAI."""

import os
import requests
import streamlit as st


# Session HTTP
_session = requests.Session()


def _configuration(nom: str, defaut: str = "") -> str:
    """Lire la configuration depuis Streamlit Secrets ou .env."""

    valeur = ""

    try:
        valeur = str(st.secrets.get(nom, "")).strip()
    except Exception:
        pass

    if not valeur:
        valeur = os.getenv(nom, defaut).strip()

    return valeur.strip('"').strip("'")


def _bases() -> list:
    """Récupérer l'adresse de l'API OmniRoute."""

    base = _configuration("OMNIROUTE_BASE_URL")

    if not base:
        return []

    base = base.rstrip("/")

    # Éviter localhost sur Streamlit Cloud
    if "localhost" in base or "127.0.0.1" in base:
        return []

    return [base]


def _headers() -> dict:
    """Récupérer la clé API."""

    cle = _configuration("OMNIROUTE_API_KEY")

    headers = {
        "Content-Type": "application/json"
    }

    if cle:
        headers["Authorization"] = f"Bearer {cle}"

    return headers


def omniroute_disponible() -> bool:
    """Vérifier si l'API OmniRoute est accessible."""

    for base in _bases():
        try:
            r = _session.get(
                f"{base}/models",
                headers=_headers(),
                timeout=10
            )

            if r.status_code == 200:
                return True

        except requests.RequestException:
            continue

    return False


def diagnostic() -> str:
    """Afficher un diagnostic de connexion."""

    bases = _bases()

    lignes = [
        f"Clé API configurée : {'oui' if _configuration('OMNIROUTE_API_KEY') else 'NON'}"
    ]

    if not bases:
        lignes.append(
            "Adresse API absente ou invalide : configure OMNIROUTE_BASE_URL."
        )
        return "\n".join(lignes)

    for base in bases:
        try:
            r = _session.get(
                f"{base}/models",
                headers=_headers(),
                timeout=10
            )

            lignes.append(
                f"Connexion API : HTTP {r.status_code}"
            )

        except requests.RequestException as e:
            lignes.append(
                f"Connexion impossible : {type(e).__name__}"
            )

    return "\n".join(lignes)


def generer_texte(prompt: str, systeme: str = "") -> str:
    """Envoyer une demande au modèle IA."""

    bases = _bases()

    if not bases:
        raise RuntimeError(
            "OMNIROUTE_BASE_URL n'est pas configurée. "
            "Une adresse API accessible depuis Internet est nécessaire."
        )

    messages = []

    if systeme:
        messages.append({
            "role": "system",
            "content": systeme
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    derniere_erreur = None

    for base in bases:
        try:
            r = _session.post(
                f"{base}/chat/completions",
                headers=_headers(),
                json={
                    "model": _configuration("OMNIROUTE_MODEL", "auto"),
                    "messages": messages,
                    "temperature": 0.7
                },
                timeout=90
            )

            if r.status_code != 200:
                raise RuntimeError(
                    f"HTTP {r.status_code} : {r.text[:300]}"
                )

            contenu = r.json()["choices"][0]["message"]["content"]

            if not isinstance(contenu, str):
                raise RuntimeError(
                    "Le contenu retourné par l'IA est invalide."
                )

            return contenu.strip()

        except requests.RequestException as e:
            derniere_erreur = e
            continue

        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise RuntimeError(
                f"Réponse IA invalide : {e}"
            ) from e

    raise RuntimeError(
        f"Impossible de contacter l'API IA : {derniere_erreur}"
    )


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
```
