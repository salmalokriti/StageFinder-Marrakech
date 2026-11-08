"""Design de l'application : CSS + petits composants HTML."""
import html
import streamlit as st

BLEU = "#123B66"
NAVY = "#0B2545"
ROUGE = "#d03b3b"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background: radial-gradient(1200px 500px at 85% -10%, #E3ECF8 0%, transparent 60%), #F3F6FB; }}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.4rem; max-width: 1350px; }}

/* ---------- SIDEBAR ---------- */
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, {NAVY} 0%, {BLEU} 100%); }}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"], [data-testid="stSidebar"] .stCaption {{ color: #EAF1FB !important; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{ padding: 9px 12px; border-radius: 10px; margin-bottom: 2px;
  transition: background .15s; }}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background: rgba(255,255,255,.12); }}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background: rgba(255,255,255,.2);
  box-shadow: inset 4px 0 0 {ROUGE}; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.18); }}
.brand {{ display:flex; align-items:center; gap:12px; margin: 4px 0 14px; }}
.brand .nom {{ color:#fff; font-weight:800; font-size:19px; line-height:1.1; }}
.brand .sous {{ color:#9FB7D6; font-size:12px; }}
.statut {{ display:flex; gap:6px; flex-wrap:wrap; margin-top:6px; }}
.statut span {{ font-size:11px; padding:3px 9px; border-radius:999px; background:rgba(255,255,255,.14); color:#fff; }}

/* ---------- HERO ---------- */
.hero {{ position:relative; overflow:hidden; border-radius:22px; padding:34px 38px; margin-bottom:22px; color:#fff;
  background: linear-gradient(120deg, {NAVY} 0%, {BLEU} 55%, #1F5FA3 100%);
  box-shadow: 0 14px 34px rgba(18,59,102,.28); }}
.hero::before {{ content:''; position:absolute; right:-70px; top:-70px; width:300px; height:300px; border-radius:50%;
  background: radial-gradient(circle, rgba(208,59,59,.75), rgba(208,59,59,0) 70%); }}
.hero::after {{ content:''; position:absolute; right:140px; bottom:-90px; width:240px; height:240px; border-radius:50%;
  background: radial-gradient(circle, rgba(255,255,255,.14), rgba(255,255,255,0) 70%); }}
.hero .tag {{ display:inline-block; font-size:12px; font-weight:700; letter-spacing:.12em; text-transform:uppercase;
  background:rgba(255,255,255,.16); padding:5px 12px; border-radius:999px; margin-bottom:12px; }}
.hero h1 {{ margin:0; font-size:38px; font-weight:800; letter-spacing:-.02em; color:#fff; }}
.hero p {{ margin:8px 0 0; color:#D5E3F6; font-size:16px; max-width:720px; position:relative; z-index:1; }}
.hero > * {{ position:relative; z-index:1; }}

/* ---------- TITRES ---------- */
.titre {{ font-size:24px; font-weight:800; color:{NAVY}; margin:6px 0 4px; display:flex; align-items:center; gap:10px; }}
.titre::before {{ content:''; width:6px; height:26px; border-radius:4px; background:linear-gradient({ROUGE}, {BLEU}); }}
.soustitre {{ color:#6B7A90; margin-bottom:14px; }}

/* ---------- KPI ---------- */
.kpi {{ background:#fff; border-radius:16px; padding:18px 20px; position:relative; overflow:hidden;
  box-shadow:0 4px 16px rgba(20,33,61,.07); border:1px solid #E6ECF5; transition: transform .15s, box-shadow .15s; }}
.kpi:hover {{ transform: translateY(-3px); box-shadow:0 10px 24px rgba(20,33,61,.12); }}
.kpi::after {{ content:''; position:absolute; left:0; top:0; height:4px; width:100%; background:linear-gradient(90deg,{BLEU},#4F7CAC); }}
.kpi.rouge::after {{ background:linear-gradient(90deg,{ROUGE},#F08A8A); }}
.kpi .valeur {{ font-size:34px; font-weight:800; color:{NAVY}; line-height:1.1; margin-top:6px; }}
.kpi .label {{ font-size:12px; color:#6B7A90; text-transform:uppercase; letter-spacing:.06em; font-weight:600; }}

/* ---------- CARTES / FICHE ---------- */
.fiche {{ background:#fff; border-radius:18px; padding:22px 26px; border:1px solid #E6ECF5;
  box-shadow:0 6px 20px rgba(20,33,61,.08); border-left:6px solid {ROUGE}; }}
.fiche .badge {{ display:inline-block; background:{BLEU}; color:#fff; border-radius:999px; padding:3px 13px;
  font-size:12px; font-weight:600; }}
.fiche h3 {{ margin:8px 0 6px; color:{NAVY}; font-size:26px; font-weight:800; }}
.fiche p {{ margin:4px 0 10px; color:#44546A; }}
.chips {{ display:flex; flex-wrap:wrap; gap:8px; }}
.chip {{ display:inline-block; padding:7px 14px; border-radius:10px; font-size:13px; font-weight:600;
  text-decoration:none !important; color:#fff !important; background:{BLEU}; transition: transform .12s, filter .12s; }}
.chip:hover {{ transform:translateY(-2px); filter:brightness(1.12); }}
.chip.rouge {{ background:{ROUGE}; }} .chip.vert {{ background:#1F9D6B; }} .chip.linkedin {{ background:#0A66C2; }}
.chip.gris {{ background:#4B5B73; }}

.plateforme {{ background:#fff; border:1px solid #E6ECF5; border-radius:16px; padding:16px 18px; text-align:center;
  box-shadow:0 4px 14px rgba(20,33,61,.06); }}

.ia-note {{ background:linear-gradient(90deg,#FFF4F4,#EEF4FC); border:1px solid #F0CFCF; border-radius:12px;
  padding:10px 14px; color:{NAVY}; font-size:14px; margin:6px 0 14px; }}
.ia-note b {{ color:{ROUGE}; }}
.bloc {{ background:#fff; border:1px solid #E6ECF5; border-radius:16px; padding:18px 22px;
  box-shadow:0 4px 14px rgba(20,33,61,.06); }}

/* ---------- WIDGETS ---------- */
.stButton > button, .stDownloadButton > button, [data-testid="stLinkButton"] a {{
  border-radius:12px; font-weight:600; border:1px solid #D5DEEB; transition: all .15s; }}
.stButton > button:hover, [data-testid="stLinkButton"] a:hover {{ border-color:{ROUGE}; color:{ROUGE}; transform:translateY(-1px); }}
.stButton > button[kind="primary"] {{ background:linear-gradient(135deg,{ROUGE},#e25b5b); color:#fff; border:none;
  box-shadow:0 6px 16px rgba(208,59,59,.35); }}
.stButton > button[kind="primary"]:hover {{ color:#fff; filter:brightness(1.08); }}
.stTabs [data-baseweb="tab-list"] {{ gap:6px; }}
.stTabs [data-baseweb="tab"] {{ background:#fff; border-radius:12px 12px 0 0; padding:10px 18px; font-weight:600; }}
[data-testid="stDataFrame"] {{ border-radius:14px; overflow:hidden; box-shadow:0 4px 14px rgba(20,33,61,.07); }}
div[data-testid="stPlotlyChart"] {{ background:#fff; border-radius:16px; padding:8px; border:1px solid #E6ECF5;
  box-shadow:0 4px 14px rgba(20,33,61,.06); }}
</style>
"""


def appliquer():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(tag, titre, texte):
    st.markdown(
        f'<div class="hero"><span class="tag">{html.escape(tag)}</span>'
        f'<h1>{html.escape(titre)}</h1><p>{html.escape(texte)}</p></div>',
        unsafe_allow_html=True)


def titre(texte, sous=""):
    st.markdown(f'<div class="titre">{html.escape(texte)}</div>', unsafe_allow_html=True)
    if sous:
        st.markdown(f'<div class="soustitre">{html.escape(sous)}</div>', unsafe_allow_html=True)


def kpi(label, valeur, rouge=False):
    st.markdown(
        f'<div class="kpi {"rouge" if rouge else ""}">'
        f'<div class="label">{html.escape(label)}</div><div class="valeur">{valeur}</div></div>',
        unsafe_allow_html=True)


IA = "✨"  # l'UNIQUE icône de l'application : elle signale les fonctions propulsées par le LLM


def ia_note(texte):
    st.markdown(f'<div class="ia-note"><b>{IA} IA</b> · {html.escape(texte)}</div>', unsafe_allow_html=True)


def chips(liens: dict, styles: dict | None = None) -> str:
    """Boutons-liens HTML. styles = {nom_du_lien: 'rouge'|'vert'|'linkedin'|'gris'}"""
    styles = styles or {}
    return '<div class="chips">' + "".join(
        f'<a class="chip {styles.get(nom, "")}" href="{html.escape(url, quote=True)}" target="_blank">{html.escape(nom)}</a>'
        for nom, url in liens.items()) + "</div>"


def tags(noms) -> str:
    """Petites pastilles non cliquables (ex : compétences détectées)."""
    return '<div class="chips">' + "".join(
        f'<span class="chip" style="cursor:default">{html.escape(n)}</span>' for n in noms) + "</div>"
