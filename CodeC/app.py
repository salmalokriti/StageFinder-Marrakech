import hashlib
import html
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from pypdf import PdfReader

import style
from carte import COULEURS, html_google, html_leaflet, preparer
from contacts import STATUTS, appliquer_contacts, enregistrer_contact
from cv_pdf import cv_vers_pdf
from email_sender import envoyer_email, lien_mailto, smtp_configure
from liens import liens_entreprise, liens_offres
from llm_cv import (adapter_cv, analyser_profil, competences_par_mots_cles, matcher_offres,
                    score_mots_cles, verifier_fidelite)
from omniroute_client import diagnostic, omniroute_disponible, rediger_email_candidature
from recherche_web import SITES, chercher_offres

IA = style.IA  # unique icône de l'app : fonctions propulsées par le LLM

# ============================================================
# CONFIGURATION
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = PROJECT_DIR / "01_Donnees"
SUIVI_FILE = PROJECT_DIR / "Suivi" / "StageFinder_Analyse_Suivii.xlsx"
RESULTATS_DIR = PROJECT_DIR / "Resultats"
OPPORTUNITES_FILE = DATA_DIR / "opportunites.xlsx"
LOGO = BASE_DIR / "logo.png"

load_dotenv(BASE_DIR / ".env")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

st.set_page_config(page_title="StageFinder Marrakech", page_icon=str(LOGO) if LOGO.exists() else None, layout="wide")
style.appliquer()


# ============================================================
# DONNÉES
# ============================================================
@st.cache_data
def charger_entreprises() -> pd.DataFrame:
    suivi = pd.read_excel(SUIVI_FILE, sheet_name="Suivi")
    nettoyees = pd.read_excel(DATA_DIR / "donnees_nettoyees.xlsx")
    coords = nettoyees[["Entreprise", "Place_ID", "Latitude", "Longitude"]].drop_duplicates("Entreprise")
    df = suivi.merge(coords, on="Entreprise", how="left")
    liens = df.apply(lambda r: liens_entreprise(r["Entreprise"], r["Latitude"], r["Longitude"], r["Place_ID"]), axis=1)
    return pd.concat([df, pd.DataFrame(list(liens))], axis=1)


@st.cache_data
def charger_brut_vs_nettoye() -> pd.DataFrame:
    suivi = pd.read_excel(SUIVI_FILE, sheet_name="Suivi")
    r2d = suivi.drop_duplicates("Recherche").set_index("Recherche")["Domaine"].to_dict()
    brut = pd.read_excel(DATA_DIR / "donnees_brutes.xlsx")
    net = pd.read_excel(DATA_DIR / "donnees_nettoyees.xlsx")
    out = pd.DataFrame({"Brut": brut["Recherche"].map(r2d).value_counts(),
                        "Nettoyé": net["Recherche"].map(r2d).value_counts()}).fillna(0).astype(int)
    return out.reset_index(names="Domaine")


def charger_offres() -> pd.DataFrame:
    return pd.read_excel(OPPORTUNITES_FILE)


@st.cache_data(ttl=20)
def omniroute_ok() -> bool:
    return omniroute_disponible()


try:
    entreprises = appliquer_contacts(charger_entreprises(), RESULTATS_DIR)
except FileNotFoundError as e:
    st.error(f"Fichier de données introuvable : {e.filename}")
    st.stop()
tous_secteurs = sorted(entreprises["Domaine"].dropna().unique())
COULEUR_SECTEUR = {s: COULEURS[i % len(COULEURS)] for i, s in enumerate(tous_secteurs)}
om = omniroute_ok()


def mise_en_forme(fig):
    fig.update_layout(font_family="Inter", margin=dict(t=30, b=10, l=10, r=10),
                      paper_bgcolor="white", plot_bgcolor="white", legend_title_text="")
    return fig


def ia_requise() -> bool:
    """Affiche un message d'aide si OmniRoute n'est pas joignable ; retourne True si l'IA est prête."""
    if om:
        return True
    st.warning("Le moteur IA (OmniRoute) n'est pas joignable. Lancez `omniroute` puis rechargez la page.")
    with st.expander("Diagnostic"):
        st.code(diagnostic())
    return False


# ============================================================
# BARRE LATÉRALE : filtres + état des services
# ============================================================
with st.sidebar:
    if LOGO.exists():
        st.image(str(LOGO), width=84)
    st.markdown('<div class="brand"><div><div class="nom">StageFinder</div>'
                '<div class="sous">Marrakech · Stages &amp; Emplois</div></div></div>', unsafe_allow_html=True)

    st.markdown("### Filtres")
    secteurs = st.multiselect("Secteurs", tous_secteurs, default=tous_secteurs)
    recherche_nom = st.text_input("Nom d'entreprise", placeholder="Ex : Monark")
    filtre = entreprises[entreprises["Domaine"].isin(secteurs)]
    if recherche_nom:
        filtre = filtre[filtre["Entreprise"].str.contains(recherche_nom, case=False, na=False)]
    st.caption(f"**{len(filtre)}** entreprise(s) sélectionnée(s)")

    st.divider()

    def pastille(ok, nom):
        couleur = "#4ADE80" if ok else "#F87171"
        return f'<span><span style="color:{couleur}">●</span> {nom}</span>'

    st.markdown('<div class="statut">' + pastille(om, "IA") + pastille(smtp_configure(), "E-mail")
                + pastille(bool(GOOGLE_MAPS_API_KEY), "Google Maps") + "</div>", unsafe_allow_html=True)

# ============================================================
# ÉTAT PARTAGÉ (CV)
# ============================================================
profil = st.session_state.get("profil", {"competences": []})
offres_df = charger_offres() if OPPORTUNITES_FILE.exists() else pd.DataFrame()

style.hero("Marrakech · Recherche de stage", "Tableau de bord StageFinder",
           "Entreprises, offres, CV, matching et candidatures : tout au même endroit.")

t_vue, t_ent, t_opp, t_cv, t_match, t_adapt, t_mail = st.tabs([
    "Vue d'ensemble", "Entreprises", "Opportunités", "Mon CV",
    f"Matching {IA}", f"Adapter mon CV {IA}", "Candidature"])

# ============================================================
# VUE D'ENSEMBLE
# ============================================================
with t_vue:
    c1, c2, c3, c4 = st.columns(4)
    with c1: style.kpi("Entreprises", len(filtre))
    with c2: style.kpi("Secteurs", len(secteurs))
    with c3: style.kpi("Offres collectées", len(offres_df), rouge=True)
    with c4: style.kpi("À contacter", int((filtre["Statut du suivi"] == "À contacter").sum()), rouge=True)
    st.write("")

    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Avant / après nettoyage")
        bn = charger_brut_vs_nettoye()
        bn = bn[bn["Domaine"].isin(secteurs)]
        fig = go.Figure()
        fig.add_bar(x=bn["Domaine"], y=bn["Brut"], name="Brut", marker_color=style.ROUGE)
        fig.add_bar(x=bn["Domaine"], y=bn["Nettoyé"], name="Nettoyé", marker_color=style.BLEU)
        fig.update_layout(barmode="group", yaxis_title="Entreprises")
        st.plotly_chart(mise_en_forme(fig), use_container_width=True)
    with g2:
        st.subheader("Répartition par secteur")
        rep = filtre["Domaine"].value_counts().reset_index()
        rep.columns = ["Domaine", "Entreprises"]
        st.plotly_chart(mise_en_forme(px.pie(rep, names="Domaine", values="Entreprises", hole=0.5,
                                             color="Domaine", color_discrete_map=COULEUR_SECTEUR)),
                        use_container_width=True)
    if not offres_df.empty:
        g3, g4 = st.columns(2)
        with g3:
            st.subheader("Offres par domaine")
            o1 = offres_df["Domaine"].value_counts().reset_index()
            o1.columns = ["Domaine", "Offres"]
            st.plotly_chart(mise_en_forme(px.bar(o1, x="Offres", y="Domaine", orientation="h",
                                                 color_discrete_sequence=[style.BLEU])), use_container_width=True)
        with g4:
            st.subheader("Offres par source")
            o2 = offres_df["Source"].value_counts().reset_index()
            o2.columns = ["Source", "Offres"]
            st.plotly_chart(mise_en_forme(px.bar(o2, x="Source", y="Offres",
                                                 color_discrete_sequence=[style.ROUGE])), use_container_width=True)

# ============================================================
# ENTREPRISES
# ============================================================
with t_ent:
    sous_liste, sous_carte = st.tabs(["Liste et liens", "Carte de Marrakech"])

    with sous_liste:
        st.dataframe(
            filtre[["Entreprise", "Domaine", "Adresse", "Statut du suivi", "E-mail", "Google", "Google Maps",
                    "LinkedIn (entreprise)", "Offres Indeed", "Offres Google"]],
            use_container_width=True, height=480, hide_index=True,
            column_config={
                "Google": st.column_config.LinkColumn("Google", display_text="Ouvrir"),
                "Google Maps": st.column_config.LinkColumn("Maps", display_text="Localiser"),
                "LinkedIn (entreprise)": st.column_config.LinkColumn("LinkedIn", display_text="Profil"),
                "Offres Indeed": st.column_config.LinkColumn("Indeed", display_text="Offres"),
                "Offres Google": st.column_config.LinkColumn("Offres Google", display_text="Offres"),
            })
        st.download_button("Télécharger la sélection (CSV)", filtre.to_csv(index=False).encode("utf-8"),
                           "entreprises_selection.csv", "text/csv")

    with sous_carte:
        if filtre.empty:
            st.warning("Aucune entreprise : élargissez la sélection de secteurs.")
        else:
            col1, col2 = st.columns([2, 3])
            with col1:
                moteur = st.radio("Fond de carte", ["Plan coloré / Satellite", "Google Maps"], horizontal=True)
            with col2:
                noms = filtre["Entreprise"].tolist()
                choix = st.selectbox("Zoomer sur une entreprise", ["Vue d'ensemble"] + noms)
            focus = None if choix == "Vue d'ensemble" else noms.index(choix)

            marqueurs = preparer(filtre, COULEUR_SECTEUR)
            if moteur == "Google Maps" and GOOGLE_MAPS_API_KEY:
                components.html(html_google(marqueurs, GOOGLE_MAPS_API_KEY, focus), height=640)
            else:
                if moteur == "Google Maps":
                    st.warning("Clé GOOGLE_MAPS_API_KEY absente de .env : affichage du plan coloré.")
                components.html(html_leaflet(marqueurs, focus), height=640)
            st.caption("Cliquez sur un pin pour la fiche, l'itinéraire et les offres.")

            if focus is not None:
                ent = filtre.iloc[focus]
                st.markdown(
                    f'<div class="fiche"><span class="badge">{html.escape(str(ent["Domaine"]))}</span>'
                    f'<h3>{html.escape(ent["Entreprise"])}</h3><p>{html.escape(str(ent["Adresse"]))}<br>'
                    f'GPS : {ent["Latitude"]:.6f}, {ent["Longitude"]:.6f}</p>'
                    + style.chips({"Google Maps": ent["Google Maps"], "Itinéraire": ent["Itinéraire"]},
                                  {"Itinéraire": "vert"}) + '</div>', unsafe_allow_html=True)

# ============================================================
# OPPORTUNITÉS
# ============================================================
with t_opp:
    sous_off, sous_rech, sous_xl = st.tabs(["Offres collectées", "Rechercher des offres", "Fichiers Excel"])

    with sous_off:
        if offres_df.empty:
            st.info("Aucune offre collectée pour le moment.")
        else:
            q = st.text_input("Rechercher dans les offres", placeholder="Entreprise, stage, Python, Data...", key="q_offres")
            aff = offres_df
            if q:
                masque = aff.astype(str).apply(lambda col: col.str.contains(q, case=False, na=False)).any(axis=1)
                aff = aff[masque]
            st.dataframe(aff, use_container_width=True, height=480, hide_index=True,
                         column_config={"Lien": st.column_config.LinkColumn("Lien", display_text="Ouvrir l'offre")})
            st.download_button("Télécharger (CSV)", aff.to_csv(index=False).encode("utf-8"),
                               "offres.csv", "text/csv")

    with sous_rech:
        suggestions = ["intelligence artificielle", "data science", "machine learning", "NLP", "LLM",
                       "data analyst", "data engineer", "computer vision", "développement web",
                       "marketing digital", "développeur python"]
        c1, c2 = st.columns([2, 3])
        with c1:
            base = st.selectbox("Secteur / compétence", suggestions + ["(autre mot-clé)"])
        with c2:
            mot_cle = st.text_input("Mot-clé", value="" if base == "(autre mot-clé)" else base)
        mot_cle = mot_cle.strip()

        if mot_cle:
            style.titre("1 · Ouvrir directement la recherche", f"Stage « {mot_cle} » à Marrakech")
            liens = liens_offres(mot_cle)
            for col, (nom, url) in zip(st.columns(4), liens.items()):
                with col:
                    st.link_button(nom, url, use_container_width=True)

            st.write("")
            style.titre("2 · Recherche automatique", "Les résultats s'affichent ici avec un lien cliquable.")
            plateformes = st.multiselect("Plateformes", list(SITES), default=["Indeed", "LinkedIn", "Stagiaires.ma"])
            if st.button("Lancer la recherche", type="primary"):
                with st.spinner("Recherche en cours sur le web…"):
                    try:
                        st.session_state["resultats_web"] = chercher_offres(mot_cle, plateformes)
                        st.session_state["mot_cle_web"] = mot_cle
                    except ImportError:
                        st.error("La bibliothèque « ddgs » manque : lancez  pip install ddgs")
                    except Exception as e:
                        st.error(f"Recherche impossible : {e}")

            res = st.session_state.get("resultats_web")
            if res is not None:
                if res.empty:
                    st.info("Aucun résultat. Essayez un autre mot-clé ou utilisez les boutons ci-dessus.")
                else:
                    st.success(f"{len(res)} résultat(s) pour « {st.session_state['mot_cle_web']} »")
                    st.dataframe(res, use_container_width=True, hide_index=True, height=420,
                                 column_config={"Lien": st.column_config.LinkColumn("Lien", display_text="Ouvrir")})
                    b1, b2 = st.columns(2)
                    with b1:
                        st.download_button("Télécharger (CSV)", res.to_csv(index=False).encode("utf-8"),
                                           "offres_web.csv", "text/csv", use_container_width=True)
                    with b2:
                        if st.button("Ajouter à opportunites.xlsx", use_container_width=True):
                            try:
                                ancien = charger_offres()
                                nouveau = pd.DataFrame({
                                    "Entreprise": "Non spécifié", "Opportunité": res["Titre"], "Type": "Stage",
                                    "Domaine": st.session_state["mot_cle_web"], "Ville": "Marrakech",
                                    "Source": res["Plateforme"], "Lien": res["Lien"],
                                    "Date collecte": datetime.now().strftime("%Y-%m-%d"),
                                    "Statut de l'offre": "À vérifier"})
                                nouveau = nouveau[nouveau["Lien"].astype(bool)]
                                tout = pd.concat([ancien, nouveau]).drop_duplicates("Lien")
                                tout.to_excel(OPPORTUNITES_FILE, index=False)
                                st.success(f"{len(tout) - len(ancien)} nouvelle(s) offre(s) ajoutée(s).")
                            except PermissionError:
                                st.error("Fermez opportunites.xlsx dans Excel puis réessayez.")
            st.caption("LinkedIn et Indeed interdisent le scraping direct : l'outil passe par un moteur de "
                       "recherche. Pour des résultats complets et à jour, utilisez les boutons de l'étape 1.")

        st.divider()
        style.titre("3 · Offres d'une entreprise précise", "Dans la liste filtrée par vos secteurs.")
        if filtre.empty:
            st.info("Aucune entreprise dans la sélection.")
        else:
            nom_o = st.selectbox("Entreprise", filtre["Entreprise"].tolist(), key="ent_offres")
            e = filtre[filtre["Entreprise"] == nom_o].iloc[0]
            st.markdown(style.chips({"Google": e["Google"], "Offres Google": e["Offres Google"],
                                     "Offres Indeed": e["Offres Indeed"], "LinkedIn": e["LinkedIn (entreprise)"],
                                     "Google Maps": e["Google Maps"]},
                                    {"Offres Google": "rouge", "Offres Indeed": "gris", "LinkedIn": "linkedin"}),
                        unsafe_allow_html=True)

    with sous_xl:
        fichiers_excel = list(DATA_DIR.glob("*.xlsx"))
        if not fichiers_excel:
            st.warning("Aucun fichier Excel trouvé dans le dossier 01_Donnees.")
        else:
            fichier = st.selectbox("Fichier Excel", [f.name for f in fichiers_excel])
            try:
                chemin = DATA_DIR / fichier
                feuille = st.selectbox("Feuille", pd.ExcelFile(chemin).sheet_names)
                df_x = pd.read_excel(chemin, sheet_name=feuille)
                k1, k2 = st.columns(2)
                with k1: style.kpi("Lignes", len(df_x))
                with k2: style.kpi("Colonnes", len(df_x.columns), rouge=True)
                st.write("")
                cfg = {"Lien": st.column_config.LinkColumn("Lien", display_text="Ouvrir")} if "Lien" in df_x.columns else {}
                st.dataframe(df_x, use_container_width=True, height=440, column_config=cfg)
            except Exception as e:
                st.error(f"Erreur lors de la lecture du fichier : {e}")

# ============================================================
# MON CV
# ============================================================
with t_cv:
    cv = st.file_uploader("Importer votre CV (PDF)", type=["pdf"], key="cv_upload")
    if cv is not None:
        octets = cv.getvalue()
        empreinte = hashlib.md5(octets).hexdigest()
        if st.session_state.get("cv_hash") != empreinte:  # nouveau fichier : on (re)lit et on réinitialise
            try:
                lecteur = PdfReader(cv)
                texte = "\n".join(p.extract_text() or "" for p in lecteur.pages)
            except Exception as e:
                st.error(f"Impossible de lire le CV : {e}")
                texte = ""
            if texte.strip():
                st.session_state.update(cv_hash=empreinte, cv_original_bytes=octets, cv_bytes=octets,
                                        cv_nom=cv.name, cv_nom_original=cv.name, cv_est_adapte=False,
                                        texte_cv=texte, nb_pages=len(lecteur.pages),
                                        profil={"competences": competences_par_mots_cles(texte), "domaine": "",
                                                "niveau": "", "langues": [], "resume": ""})
                st.session_state.pop("matching", None)
                st.session_state.pop("cv_adapte", None)
            else:
                st.warning("Aucun texte extractible : le PDF est peut-être une image scannée.")

    if "texte_cv" in st.session_state:
        profil = st.session_state["profil"]
        c1, c2, c3 = st.columns(3)
        with c1: style.kpi("Pages", st.session_state["nb_pages"])
        with c2: style.kpi("Caractères", len(st.session_state["texte_cv"]), rouge=True)
        with c3: style.kpi("Compétences détectées", len(profil["competences"]))
        st.write("")

        st.subheader("Compétences")
        if profil["competences"]:
            st.markdown(style.tags(profil["competences"]), unsafe_allow_html=True)
        else:
            st.warning("Aucune compétence connue n'a été détectée.")
        if profil.get("resume") or profil.get("domaine"):
            st.caption(f"{profil.get('domaine', '')} · {profil.get('niveau', '')} · {profil.get('resume', '')}")

        if st.button(f"{IA} Analyser mon profil avec l'IA"):
            if ia_requise():
                with st.spinner("Analyse du CV…"):
                    st.session_state["profil"] = analyser_profil(st.session_state["texte_cv"])
                    st.session_state.pop("matching", None)
                st.rerun()

        with st.expander("Texte extrait du CV"):
            st.text_area("Texte", st.session_state["texte_cv"], height=300, label_visibility="collapsed")
    else:
        st.info("Importez votre CV pour activer le matching, l'adaptation et la candidature.")

# ============================================================
# MATCHING IA
# ============================================================
with t_match:
    style.ia_note("Le LLM compare votre profil à chaque offre et explique le score. "
                  "Il se base uniquement sur ce qui est écrit dans votre CV et dans l'offre.")
    if "texte_cv" not in st.session_state:
        st.warning("Importez d'abord votre CV dans l'onglet « Mon CV ».")
    elif offres_df.empty:
        st.warning("Aucune offre à comparer : ajoutez des offres dans « Opportunités ».")
    else:
        profil = st.session_state["profil"]
        st.markdown(style.tags(profil["competences"]), unsafe_allow_html=True)
        st.write("")
        if st.button(f"{IA} Lancer le matching IA", type="primary"):
            if ia_requise():
                with st.spinner("Le LLM analyse les offres…"):
                    try:
                        st.session_state["matching"] = matcher_offres(profil, offres_df)
                        st.session_state["matching_ia"] = True
                    except Exception as e:
                        st.error(f"Matching IA impossible ({e}). Affichage du score par mots-clés.")
                        d = offres_df.copy()
                        d["Score mots-clés"] = score_mots_cles(d, profil["competences"])
                        st.session_state["matching"] = d.sort_values("Score mots-clés", ascending=False)
                        st.session_state["matching_ia"] = False

        dfm = st.session_state.get("matching")
        if dfm is None:
            st.caption("Cliquez sur le bouton pour classer les offres selon votre CV.")
        else:
            ia = st.session_state.get("matching_ia", False)
            cle = "Score IA (%)" if ia else "Score mots-clés"
            cfg = {cle: st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.0f%%")}
            if "Lien" in dfm.columns:
                cfg["Lien"] = st.column_config.LinkColumn("Lien", display_text="Ouvrir l'offre")
            colonnes = [c for c in ["Entreprise", "Opportunité", "Domaine", cle, "Raison", "À renforcer", "Lien"]
                        if c in dfm.columns]
            st.subheader("Meilleures correspondances")
            st.dataframe(dfm[colonnes].head(8), use_container_width=True, column_config=cfg, hide_index=True)
            with st.expander("Toutes les offres"):
                st.dataframe(dfm[colonnes], use_container_width=True, height=420, column_config=cfg, hide_index=True)
            st.download_button("Télécharger le matching", dfm.to_csv(index=False).encode("utf-8"),
                               "matching_cv_offres.csv", "text/csv")

# ============================================================
# ADAPTER MON CV (IA)
# ============================================================
with t_adapt:
    style.ia_note("Le LLM reformule et réordonne votre CV pour qu'il réponde mieux à la demande de l'entreprise. "
                  "Il n'ajoute rien : seules les informations déjà présentes dans votre CV sont utilisées.")
    if "texte_cv" not in st.session_state:
        st.warning("Importez d'abord votre CV dans l'onglet « Mon CV ».")
    else:
        mode = st.radio("Adapter pour", ["Une entreprise", "Une offre collectée"], horizontal=True)
        if mode == "Une entreprise":
            if filtre.empty:
                st.warning("Aucune entreprise dans la sélection.")
                cible = None
            else:
                nom_c = st.selectbox("Entreprise", filtre["Entreprise"].tolist(), key="adapt_ent")
                domaine_c = str(filtre.loc[filtre["Entreprise"] == nom_c, "Domaine"].iloc[0])
                cible = (nom_c, domaine_c, "")
        else:
            if offres_df.empty:
                st.warning("Aucune offre collectée.")
                cible = None
            else:
                libelles = (offres_df["Entreprise"].astype(str) + " — " + offres_df["Opportunité"].astype(str)).tolist()
                i = st.selectbox("Offre", range(len(libelles)), format_func=lambda k: libelles[k][:110], key="adapt_off")
                o = offres_df.iloc[i]
                nom_off = str(o["Entreprise"])
                if nom_off.strip() in ("", "nan", "Non spécifié"):
                    nom_off = str(o["Opportunité"])[:60]  # entreprise inconnue : on nomme la cible par l'offre
                cible = (nom_off, str(o.get("Domaine", "")), str(o["Opportunité"]))

        description = st.text_area("Description de l'offre / ce que demande l'entreprise (recommandé)",
                                   placeholder="Collez ici le texte de l'annonce : missions, profil recherché, "
                                               "compétences demandées…", height=150)

        if cible and st.button(f"{IA} Adapter mon CV", type="primary"):
            if ia_requise():
                with st.spinner("Adaptation du CV…"):
                    try:
                        besoin = (cible[2] + "\n" + description).strip()
                        texte_adapte = adapter_cv(st.session_state["texte_cv"], cible[0], cible[1], besoin)
                        st.session_state["cv_adapte"] = {"cible": cible[0], "texte": texte_adapte}
                        st.session_state["adapt_editeur"] = texte_adapte
                    except Exception as e:
                        st.error(f"Adaptation impossible : {e}")

        adapte = st.session_state.get("cv_adapte")
        if adapte:
            st.subheader(f"CV adapté pour {adapte['cible']}")
            texte_final = st.text_area("Vous pouvez corriger le texte avant de l'exporter", key="adapt_editeur", height=420)

            suspects = verifier_fidelite(st.session_state["texte_cv"], texte_final)
            if suspects:
                st.warning("Éléments absents de votre CV d'origine, à vérifier ou supprimer : "
                           + ", ".join(suspects[:15]))
            else:
                st.success("Contrôle de fidélité : aucun élément nouveau détecté par rapport à votre CV.")

            pdf = cv_vers_pdf(texte_final)
            b1, b2 = st.columns(2)
            with b1:
                st.download_button("Télécharger le CV adapté (PDF)", pdf,
                                   f"CV_{adapte['cible'].replace(' ', '_')}.pdf", "application/pdf",
                                   use_container_width=True)
            with b2:
                if st.button("Utiliser ce CV pour la candidature", use_container_width=True):
                    st.session_state["cv_bytes"] = pdf
                    st.session_state["cv_nom"] = f"CV_{adapte['cible'].replace(' ', '_')}.pdf"
                    st.session_state["cv_est_adapte"] = True
                    st.success("Ce CV sera joint dans l'onglet « Candidature ».")

# ============================================================
# CANDIDATURE (E-MAIL)
# ============================================================
with t_mail:
    mode_mail = st.radio("Postuler à", ["Une entreprise", "Une offre collectée"], horizontal=True, key="mail_mode")
    cible_ok, offre_titre, statut_actuel = False, "", STATUTS[0]

    if mode_mail == "Une entreprise":
        if filtre.empty:
            st.warning("Aucune entreprise : élargissez la sélection de secteurs.")
        else:
            nom = st.selectbox("Entreprise", filtre["Entreprise"].tolist(), key="mail_ent")
            ent = filtre[filtre["Entreprise"] == nom].iloc[0]
            domaine, adresse, email_connu = str(ent["Domaine"]), str(ent["Adresse"]), str(ent["E-mail"])
            statut_actuel = ent["Statut du suivi"]
            st.markdown(
                f'<div class="fiche"><span class="badge">{html.escape(domaine)}</span>'
                f'<h3>{html.escape(ent["Entreprise"])}</h3><p>{html.escape(adresse)} · '
                f'Statut : {html.escape(str(statut_actuel))}</p>'
                + style.chips({"Trouver l'e-mail": ent["Trouver e-mail"], "Google": ent["Google"],
                               "Google Maps": ent["Google Maps"], "Itinéraire": ent["Itinéraire"],
                               "LinkedIn": ent["LinkedIn (entreprise)"], "Offres Indeed": ent["Offres Indeed"],
                               "Offres Google": ent["Offres Google"]},
                              {"Trouver l'e-mail": "rouge", "Itinéraire": "vert", "LinkedIn": "linkedin",
                               "Offres Indeed": "gris"})
                + '</div>', unsafe_allow_html=True)
            cible_ok = True
    else:
        if offres_df.empty:
            st.warning("Aucune offre collectée : ajoutez-en dans « Opportunités ».")
        else:
            libelles = (offres_df["Entreprise"].astype(str) + " — " + offres_df["Opportunité"].astype(str)).tolist()
            k = st.selectbox("Offre", range(len(libelles)), format_func=lambda n: libelles[n][:110], key="mail_off")
            o = offres_df.iloc[k]
            offre_titre = str(o["Opportunité"])
            nom = str(o["Entreprise"])
            if nom.strip() in ("", "nan", "Non spécifié"):
                nom = offre_titre[:60]  # entreprise inconnue : la cible est nommée par l'offre
            domaine, adresse = str(o.get("Domaine", "")), "Marrakech"
            c_mem = pd.read_csv(RESULTATS_DIR / "contacts.csv", dtype=str, encoding="utf-8-sig").fillna("") \
                if (RESULTATS_DIR / "contacts.csv").exists() else pd.DataFrame(columns=["Entreprise", "E-mail", "Statut"])
            ligne = c_mem[c_mem["Entreprise"] == nom]
            email_connu = ligne["E-mail"].iloc[0] if len(ligne) else ""
            statut_actuel = ligne["Statut"].iloc[0] if len(ligne) and ligne["Statut"].iloc[0] else STATUTS[0]
            lien_o = str(o.get("Lien", ""))
            st.markdown(
                f'<div class="fiche"><span class="badge">{html.escape(domaine)}</span>'
                f'<h3>{html.escape(offre_titre)}</h3><p>Source : {html.escape(str(o.get("Source", "")))} · '
                f'Entreprise : {html.escape(str(o["Entreprise"]))}</p>'
                + (style.chips({"Ouvrir l'offre": lien_o}, {"Ouvrir l'offre": "rouge"}) if lien_o.startswith("http") else "")
                + '</div>', unsafe_allow_html=True)
            st.caption("L'e-mail de contact n'est pas dans le fichier : copiez-le depuis l'annonce ou cherchez-le sur le site de l'entreprise.")
            cible_ok = True

    if cible_ok:
        st.write("")
        col_a, col_b = st.columns(2)
        with col_a:
            destinataire = st.text_input("E-mail du destinataire", value=email_connu,
                                         placeholder="rh@entreprise.ma", key=f"email_{mode_mail}_{nom}")
            nom_candidat = st.text_input("Votre nom", value=os.getenv("NOM_CANDIDAT", ""))
            nouveau_statut = st.selectbox("Statut", STATUTS, key=f"statut_{mode_mail}_{nom}",
                                          index=STATUTS.index(statut_actuel) if statut_actuel in STATUTS else 0)
            if st.button("Mémoriser l'e-mail et le statut"):
                enregistrer_contact(RESULTATS_DIR, nom, email=destinataire, statut=nouveau_statut)
                st.success("Enregistré dans Resultats/contacts.csv")
        with col_b:
            st.markdown("**CV joint**")
            if "cv_bytes" in st.session_state:
                adapte_actif = st.session_state.get("cv_est_adapte", False)
                st.success(f"{st.session_state['cv_nom']}" + (" (version adaptée)" if adapte_actif else " (original)"))
                if adapte_actif and st.button("Revenir au CV original"):
                    st.session_state["cv_bytes"] = st.session_state["cv_original_bytes"]
                    st.session_state["cv_nom"] = st.session_state.get("cv_nom_original", st.session_state["cv_nom"])
                    st.session_state["cv_est_adapte"] = False
                    st.rerun()
            else:
                st.info("Importez votre CV dans l'onglet « Mon CV ».")

        if offre_titre:
            sujet = st.text_input("Objet", value=f"Candidature – {offre_titre[:80]}")
            cible_txt = f"l'offre « {offre_titre} »" + (f" au sein de {nom}" if nom != offre_titre[:60] else "")
            modele = (f"Madame, Monsieur,\n\nActuellement à la recherche d'un stage, je me permets de vous adresser "
                      f"ma candidature pour {cible_txt}.\n\nVous trouverez mon CV en pièce jointe. Je serais "
                      f"ravi(e) d'échanger avec vous lors d'un entretien.\n\nCordialement,\n{nom_candidat}")
        else:
            sujet = st.text_input("Objet", value=f"Candidature spontanée – Stage – {nom}")
            modele = (f"Madame, Monsieur,\n\nActuellement à la recherche d'un stage, je me permets de vous adresser "
                      f"ma candidature spontanée au sein de {nom}, entreprise du secteur {domaine} à Marrakech.\n\n"
                      f"Vous trouverez mon CV en pièce jointe. Je serais ravi(e) d'échanger avec vous lors d'un "
                      f"entretien.\n\nCordialement,\n{nom_candidat}")
        cle_cible = f"{mode_mail}|{nom}"
        if st.session_state.get("corps_pour") != cle_cible:
            st.session_state["corps"] = modele
            st.session_state["corps_pour"] = cle_cible

        b1, b2 = st.columns(2)
        with b1:
            if st.button(f"{IA} Rédiger avec l'IA", use_container_width=True):
                if ia_requise():
                    with st.spinner("Rédaction en cours…"):
                        try:
                            st.session_state["corps"] = rediger_email_candidature(
                                nom, domaine, adresse, st.session_state.get("profil", {}).get("competences", []),
                                nom_candidat, offre=offre_titre)
                        except Exception as e:
                            st.error(f"Erreur IA : {e} — vérifiez OMNIROUTE_API_KEY et OMNIROUTE_MODEL dans .env")
        with b2:
            if st.button("Remettre le modèle simple", use_container_width=True):
                st.session_state["corps"] = modele

        corps = st.text_area("Message", key="corps", height=260)
        st.divider()
        cv_bytes = st.session_state.get("cv_bytes")
        pret = bool(destinataire and cv_bytes)

        if st.button("Envoyer l'e-mail avec le CV", type="primary", disabled=not pret):
            if not smtp_configure():
                st.error("SMTP non configuré dans .env.")
            else:
                try:
                    envoyer_email(destinataire, sujet, corps, cv_bytes, st.session_state["cv_nom"])
                    st.success(f"E-mail envoyé à {destinataire}")
                    RESULTATS_DIR.mkdir(exist_ok=True)
                    journal = RESULTATS_DIR / "emails_envoyes.csv"
                    ligne_j = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d %H:%M"), "Entreprise": nom,
                                             "Destinataire": destinataire, "Objet": sujet}])
                    ligne_j.to_csv(journal, mode="a", header=not journal.exists(), index=False, encoding="utf-8")
                    enregistrer_contact(RESULTATS_DIR, nom, email=destinataire, statut="CV envoyé",
                                        date_envoi=datetime.now().strftime("%Y-%m-%d %H:%M"))
                except Exception as e:
                    st.error(f"Échec de l'envoi : {e}")
        if not pret:
            st.caption("Renseignez l'e-mail du destinataire et chargez le CV pour activer l'envoi.")
        if destinataire:
            st.link_button("Ou ouvrir dans ma messagerie (sans pièce jointe)", lien_mailto(destinataire, sujet, corps))

    with st.expander("Comment activer l'IA (OmniRoute)", expanded=not om):
        st.markdown("""
1. Installez **Node.js** (nodejs.org), puis dans un terminal : `npm install -g omniroute` et `omniroute`.
2. Ouvrez http://localhost:20128, connectez un fournisseur, copiez la **clé d'API** dans `.env`.
Sans IA, le **modèle de message simple** fonctionne quand même.
        """)
    journal = RESULTATS_DIR / "emails_envoyes.csv"
    if journal.exists():
        with st.expander("Historique des envois"):
            st.dataframe(pd.read_csv(journal), use_container_width=True, hide_index=True)
