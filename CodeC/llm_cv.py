"""Fonctions IA (LLM via OmniRoute) : analyse du CV, matching CV / offres, adaptation du CV.

Règle d'or : le LLM ne doit JAMAIS inventer. Il reformule, réordonne et met en avant
ce qui existe déjà dans le CV. Un contrôle automatique signale tout élément nouveau.
"""
import json
import re

import pandas as pd

from omniroute_client import generer_texte

COMPETENCES_CONNUES = [
    "python", "java", "c++", "sql", "machine learning", "deep learning", "artificial intelligence",
    "intelligence artificielle", "data analysis", "data analyst", "pandas", "numpy", "scikit-learn",
    "tensorflow", "keras", "pytorch", "opencv", "nlp", "llm", "power bi", "excel", "streamlit", "django",
    "flask", "git", "github", "html", "css", "javascript", "react", "docker", "linux", "mysql",
    "postgresql", "mongodb", "tableau", "spark", "fastapi", "php", "laravel",
]


# ------------------------------------------------------------------ utilitaires
def _json_depuis(texte: str):
    """Extrait le premier objet/tableau JSON d'une réponse de LLM (même entourée de ```)."""
    texte = re.sub(r"```(?:json)?", "", texte)
    for ouvrant, fermant in (("{", "}"), ("[", "]")):
        i, j = texte.find(ouvrant), texte.rfind(fermant)
        if i != -1 and j > i:
            try:
                return json.loads(texte[i:j + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError("Réponse IA illisible (JSON attendu).")


def competences_par_mots_cles(texte_cv: str) -> list:
    bas = texte_cv.lower()
    return [c for c in COMPETENCES_CONNUES if re.search(r"(?<![a-z0-9+#])" + re.escape(c) + r"(?![a-z0-9+#])", bas)]


# ------------------------------------------------------------------ 1. profil
def analyser_profil(texte_cv: str) -> dict:
    """Profil structuré du CV. Sans IA : simple détection de mots-clés."""
    systeme = ("Tu analyses un CV. Réponds uniquement par un objet JSON avec les clés : "
               "competences (liste de compétences techniques écrites dans le CV), "
               "domaine (domaine principal en 3 mots max), niveau (ex: étudiant, junior), "
               "langues (liste), resume (une phrase). N'invente rien : uniquement ce qui est dans le CV.")
    try:
        p = _json_depuis(generer_texte(texte_cv[:6000], systeme))
        p["competences"] = [str(c).strip() for c in p.get("competences", []) if str(c).strip()]
        return p
    except Exception:
        return {"competences": competences_par_mots_cles(texte_cv), "domaine": "", "niveau": "",
                "langues": [], "resume": ""}


# ------------------------------------------------------------------ 2. matching
def _texte_offre(ligne: pd.Series) -> str:
    champs = ["Entreprise", "Opportunité", "Type", "Domaine", "Ville"]
    return " | ".join(str(ligne[c]) for c in champs
                      if c in ligne and str(ligne[c]).strip() not in ("", "nan", "Non spécifié"))


def score_mots_cles(offres: pd.DataFrame, competences: list) -> pd.Series:
    """Score rapide (0-100) par mots-clés : sert de pré-filtre et de plan B sans IA."""
    if not competences:
        return pd.Series(0.0, index=offres.index)
    textes = offres.apply(_texte_offre, axis=1).str.lower()
    return textes.apply(lambda t: round(sum(c.lower() in t for c in competences) / len(competences) * 100, 1))


def matcher_offres(profil: dict, offres: pd.DataFrame, top: int = 12) -> pd.DataFrame:
    """Classe les offres avec le LLM. Pré-filtre par mots-clés, puis le LLM note les `top` meilleures
    en UN seul appel (rapide). Retourne les offres avec Score IA, Raison, Compétences manquantes."""
    df = offres.copy()
    df["Score mots-clés"] = score_mots_cles(df, profil.get("competences", []))
    candidates = df.sort_values("Score mots-clés", ascending=False).head(top)

    liste = "\n".join(f"{i}. {_texte_offre(r)}" for i, (_, r) in enumerate(candidates.iterrows()))
    systeme = ("Tu es un recruteur. Compare le profil du candidat à chaque offre et réponds uniquement par un "
               "tableau JSON d'objets {\"id\": numéro, \"score\": 0-100, \"raison\": une phrase en français, "
               "\"manque\": liste des compétences utiles absentes du profil}. Base-toi UNIQUEMENT sur les "
               "informations fournies ; si l'offre est trop vague, donne un score prudent. Si le résultat n'est PAS une vraie "
               "offre de stage ou d'emploi (formation, retreat, page de recherche générique, article), donne un "
               "score <= 10 et dis-le dans la raison.")
    prompt = (f"PROFIL : domaine {profil.get('domaine', '?')}, niveau {profil.get('niveau', '?')}, "
              f"compétences : {', '.join(profil.get('competences', [])) or 'non précisées'}.\n\nOFFRES :\n{liste}")
    notes = {int(n["id"]): n for n in _json_depuis(generer_texte(prompt, systeme)) if "id" in n}

    df["Score IA (%)"] = pd.NA
    df["Raison"] = ""
    df["À renforcer"] = ""
    for i, idx in enumerate(candidates.index):
        n = notes.get(i)
        if n:
            df.loc[idx, "Score IA (%)"] = max(0, min(100, float(n.get("score", 0))))
            df.loc[idx, "Raison"] = str(n.get("raison", ""))
            df.loc[idx, "À renforcer"] = ", ".join(str(m) for m in n.get("manque", []))
    df["Score IA (%)"] = pd.to_numeric(df["Score IA (%)"], errors="coerce")
    return df.sort_values(["Score IA (%)", "Score mots-clés"], ascending=False, na_position="last")


# ------------------------------------------------------------------ 3. adaptation du CV
SYSTEME_ADAPTATION = """Tu es un conseiller en recrutement. Tu RÉÉCRIS un CV pour qu'il corresponde mieux à \
la demande d'une entreprise, sans RIEN inventer.

RÈGLES ABSOLUES
1. Utilise UNIQUEMENT les informations présentes dans le CV d'origine.
2. N'ajoute aucune compétence, outil, diplôme, entreprise, date, chiffre, projet ou langue absents du CV.
3. Tu peux : réordonner les sections et les points, mettre en avant ce qui répond au besoin, reformuler avec \
les mots de l'entreprise quand c'est équivalent à ce que le CV dit, raccourcir ce qui est hors sujet.
4. Si le CV ne contient rien pour une exigence de l'entreprise, ignore-la (ne la comble pas).
5. Garde la langue du CV d'origine. Pas de commentaire, pas de markdown autre que le format ci-dessous.

FORMAT DE SORTIE
Ligne 1 : le nom du candidat (tel qu'écrit dans le CV)
Ligne 2 : coordonnées (telles qu'écrites dans le CV)
Puis des sections : une ligne « # TITRE DE SECTION » suivie de lignes normales ou de puces « - texte »."""


def adapter_cv(texte_cv: str, entreprise: str, domaine: str, description: str = "") -> str:
    besoin = description.strip() or "(aucune description fournie : déduis le besoin probable du secteur uniquement)"
    prompt = (f"ENTREPRISE : {entreprise} (secteur : {domaine})\n"
              f"DEMANDE / OFFRE :\n{besoin}\n\nCV D'ORIGINE :\n{texte_cv[:8000]}")
    return generer_texte(prompt, SYSTEME_ADAPTATION)


def verifier_fidelite(original: str, adapte: str) -> list:
    """Signale ce qui apparaît dans le CV adapté mais PAS dans l'original (risque d'invention)."""
    orig = original.lower()
    suspects = []
    # chiffres / années
    for nombre in sorted(set(re.findall(r"\d[\d.,/%]*\d|\d", adapte))):
        if nombre not in original:
            suspects.append(f"chiffre « {nombre} »")
    # compétences connues
    ada = adapte.lower()
    for c in competences_par_mots_cles(adapte):
        if c not in orig:
            suspects.append(f"compétence « {c} »")
    # noms propres (mots capitalisés absents de l'original)
    for m in sorted(set(re.findall(r"\b[A-ZÀ-Ý][\wÀ-ÿ&-]{2,}\b", adapte))):
        if m.lower() not in orig and not m.isupper():
            suspects.append(f"nom « {m} »")
    return suspects
