"""Mémorise l'e-mail et le statut de chaque entreprise dans Resultats/contacts.csv
(fichier séparé : le classeur Excel de suivi n'est jamais modifié)."""
from datetime import datetime
from pathlib import Path

import pandas as pd

STATUTS = ["À contacter", "CV envoyé", "Réponse reçue", "Entretien", "Refus"]
COLONNES = ["Entreprise", "E-mail", "Statut", "Date envoi"]


def _fichier(dossier) -> Path:
    return Path(dossier) / "contacts.csv"


def charger_contacts(dossier) -> pd.DataFrame:
    f = _fichier(dossier)
    if f.exists():
        try:
            return pd.read_csv(f, dtype=str, encoding="utf-8-sig").fillna("")[COLONNES]
        except Exception:
            pass
    return pd.DataFrame(columns=COLONNES)


def enregistrer_contact(dossier, entreprise, email=None, statut=None, date_envoi=None):
    """Crée ou met à jour la ligne de l'entreprise (seuls les champs fournis changent)."""
    Path(dossier).mkdir(parents=True, exist_ok=True)
    df = charger_contacts(dossier).astype(object)
    if entreprise not in set(df["Entreprise"]):
        df = pd.concat([df, pd.DataFrame([[entreprise, "", "", ""]], columns=COLONNES, dtype=object)],
                       ignore_index=True)
    masque = df["Entreprise"] == entreprise
    if email is not None:
        df.loc[masque, "E-mail"] = email.strip()
    if statut is not None:
        df.loc[masque, "Statut"] = statut
    if date_envoi is not None:
        df.loc[masque, "Date envoi"] = date_envoi
    df.to_csv(_fichier(dossier), index=False, encoding="utf-8-sig")


def appliquer_contacts(entreprises: pd.DataFrame, dossier) -> pd.DataFrame:
    """Ajoute la colonne « E-mail » et remplace le statut par celui mémorisé (s'il existe)."""
    c = charger_contacts(dossier).set_index("Entreprise")
    df = entreprises.copy()
    df["E-mail"] = df["Entreprise"].map(c["E-mail"]).fillna("")
    statut_memo = df["Entreprise"].map(c["Statut"]).fillna("")
    df["Statut du suivi"] = statut_memo.where(statut_memo != "", df["Statut du suivi"])
    return df
