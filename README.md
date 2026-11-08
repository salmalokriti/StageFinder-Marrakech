# StageFinder Marrakech

Plateforme web qui aide un étudiant à **trouver, analyser et suivre des stages à Marrakech** : collecte des entreprises (Google Places), nettoyage des données avec Python, tableau de bord interactif, carte, recherche d'offres, analyse du CV, **matching CV ↔ offres par IA**, adaptation du CV et envoi des candidatures par e-mail.

> Projet de stage réalisé par **Salma Lokriti** (OFPPT), encadré par **Mme Nadia Idlahaj**.

- 🔗 **Plateforme en ligne** : _à compléter avec l'URL de votre application déployée_
- 💻 **Code source** : ce dépôt

---

## 1. Fonctionnalités

| Onglet de l'application | Ce qu'il fait |
|---|---|
| Vue d'ensemble | Indicateurs (entreprises, secteurs, offres, à contacter), graphiques avant/après nettoyage, répartition par secteur, offres par domaine et par source |
| Entreprises | Liste avec liens utiles et carte interactive de Marrakech (marqueurs colorés par secteur) |
| Opportunités | Offres collectées, recherche automatique (Indeed, LinkedIn, Stagiaires.ma, web), export CSV |
| Mon CV | Import du CV (PDF), extraction du texte et détection des compétences |
| Matching ✨ | Score de compatibilité CV ↔ offres par IA (LLM), avec la raison du score |
| Adapter mon CV ✨ | Reformulation du CV selon l'offre, **sans inventer d'informations** (contrôle de fidélité) |
| Candidature | Rédaction de l'e-mail (modèle ou IA), envoi avec le CV, statut de suivi et historique |

## 2. Architecture

```
Sources externes                Backend Python (CodeC/)                 Données               Frontend
-----------------               ------------------------                -------               --------
Google Places API  ───────────► collecte_google_places.py ─┐
Recherche web (ddgs) ─────────► recherche_*.py             ├─► Excel / CSV ───► app.py (Streamlit)
CV (PDF) ─────────────────────► llm_cv.py + cv_pdf.py      │   01_Donnees/      7 onglets, Plotly,
LLM (OmniRoute, API OpenAI) ──► omniroute_client.py        │   Resultats/       carte, filtres
Serveur SMTP ─────────────────► email_sender.py, contacts.py┘   Suivi/
```

L'interface Streamlit appelle **directement** les modules Python (pas de serveur REST intermédiaire). Les API utilisées sont externes : Google Places, passerelle LLM compatible OpenAI et serveur SMTP.

## 3. Stack technique

- **Langage** : Python
- **Données** : Pandas, openpyxl (fichiers Excel et CSV, pas de base SQL)
- **Interface et visualisation** : Streamlit, Plotly, carte Leaflet / Google Maps
- **API et services** : Google Places API (`requests`), recherche web (`ddgs`), LLM via OmniRoute, e-mails (`smtplib`)
- **Documents** : `pypdf` (lecture du CV), `reportlab` (export du CV adapté en PDF)
- **Configuration** : `python-dotenv` (clés dans un fichier `.env`)

## 4. Structure du dépôt

```
.
├── CodeC/
│   ├── app.py                      # Application Streamlit (frontend)
│   ├── collecte_google_places.py   # Collecte des entreprises (Google Places)
│   ├── nettoyage_donnees.py        # Nettoyage avec Pandas
│   ├── recherche_web.py            # Recherche d'offres sur le web
│   ├── recherche_opportunites.py   # Extraction du nom d'entreprise, filtre Marrakech
│   ├── llm_cv.py                   # Analyse du profil, matching, adaptation du CV
│   ├── omniroute_client.py         # Client du LLM (API compatible OpenAI)
│   ├── email_sender.py, contacts.py, cv_pdf.py, carte.py, liens.py, style.py
│   ├── .env.example                # Modèle de configuration (à copier en .env)
│   └── .streamlit/config.toml      # Thème de l'application
├── 01_Donnees/                     # donnees_brutes.xlsx, donnees_nettoyees.xlsx, opportunites.xlsx
├── Suivi/                          # Fichier Excel de suivi des candidatures
├── Resultats/                      # CSV générés (contacts, historique d'e-mails, matching)
├── requirements.txt
└── README.md
```

## 5. Prérequis

- **Python 3.10 ou plus récent**
- **Git**
- (optionnel) **Node.js** pour lancer la passerelle IA OmniRoute en local
- (optionnel) une clé **Google Maps / Places**, un compte e-mail avec « mot de passe d'application »

## 6. Installation

```bash
# 1. Récupérer le code
git clone https://github.com/<votre-compte>/stagefinder-marrakech.git
cd stagefinder-marrakech

# 2. Créer et activer un environnement virtuel
python -m venv .venv
# Windows (PowerShell) :
.venv\Scripts\Activate.ps1
# macOS / Linux :
source .venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt
```

## 7. Configuration

Copiez le modèle puis renseignez vos valeurs :

```bash
# Windows :  copy CodeC\.env.example CodeC\.env
# macOS / Linux :
cp CodeC/.env.example CodeC/.env
```

| Variable | Rôle | Obligatoire pour |
|---|---|---|
| `GOOGLE_MAPS_API_KEY` | Collecte Google Places et fond de carte Google Maps | Collecte des données, carte Google Maps |
| `SMTP_HOST`, `SMTP_PORT` | Serveur d'envoi (Gmail : `smtp.gmail.com`, `587`) | Envoi d'e-mails |
| `SMTP_USER`, `SMTP_PASSWORD` | Compte e-mail et **mot de passe d'application** (validation en 2 étapes requise sur Gmail) | Envoi d'e-mails |
| `NOM_CANDIDAT` | Nom signé dans les e-mails | Envoi d'e-mails |
| `OMNIROUTE_BASE_URL` | Adresse de l'API LLM (par défaut `http://localhost:20128/v1`) | Fonctions IA |
| `OMNIROUTE_API_KEY`, `OMNIROUTE_MODEL` | Clé et modèle du LLM (modèle par défaut : `auto`) | Fonctions IA |

Les données du projet sont déjà fournies : **aucune clé n'est nécessaire** pour consulter le tableau de bord, les entreprises, les offres et pour importer un CV. Les clés ne servent que pour les fonctions décrites ci-dessus.

> ⚠️ Le fichier `.env` contient des secrets : il est exclu du dépôt par `.gitignore`. Ne le publiez jamais.

## 8. Exécution

**Lancer l'application** (depuis la racine du dépôt) :

```bash
streamlit run CodeC/app.py
```

Ouvrez ensuite http://localhost:8501.

**Activer l'IA en local** (optionnel) :

```bash
npm install -g omniroute
omniroute            # expose l'API sur http://localhost:20128/v1
```

**Refaire le pipeline de données** (optionnel, les fichiers sont déjà fournis) :

```bash
python CodeC/collecte_google_places.py   # collecte Google Places -> 01_Donnees/donnees_brutes.xlsx
python CodeC/nettoyage_donnees.py        # nettoyage Pandas  -> 01_Donnees/donnees_nettoyees.xlsx
```

⚠️ La collecte consomme le quota de votre clé Google et **remplace** `donnees_brutes.xlsx`.

## 9. Résultats obtenus

- **102** entreprises collectées, **77** après nettoyage (**25 doublons** supprimés, soit 24,5 %), réparties sur **6 secteurs**
- **42** offres collectées sur **4 sources** (Indeed, Stagiaires.ma, LinkedIn, autres sites) et **9** mots-clés
- Matching IA avec score expliqué, adaptation du CV sans invention d'informations, envoi des candidatures par e-mail avec historique

## 10. Limites connues

- 38 offres sur 42 n'ont pas de nom d'entreprise (collecte par recherche web)
- Certaines « offres » collectées sont des pages de résultats plutôt que des annonces individuelles
- Google Places limite chaque requête à 20 résultats
- Les fichiers Excel et CSV servent de stockage : en ligne, les modifications (statuts, contacts) ne sont pas conservées d'une session à l'autre

## 11. Déploiement en ligne (Streamlit Community Cloud)

1. Poussez le dépôt sur GitHub (public).
2. Sur https://share.streamlit.io, cliquez sur **Create app**, choisissez le dépôt et la branche `main`.
3. **Main file path** : `CodeC/app.py`.
4. Dans **Advanced settings → Secrets**, collez le contenu de `CodeC/.streamlit/secrets.toml.example` avec vos vraies valeurs.
5. Cliquez sur **Deploy**, puis reportez l'URL obtenue en haut de ce README.

Remarque : la passerelle OmniRoute locale (`localhost`) n'est pas accessible depuis un serveur en ligne. Pour activer l'IA en ligne, renseignez dans les secrets l'adresse d'un fournisseur LLM compatible OpenAI (`OMNIROUTE_BASE_URL`, `OMNIROUTE_API_KEY`, `OMNIROUTE_MODEL`).

## 12. Sécurité

- Ne publiez jamais `.env`, `passe.txt` ni de clé API.
- Si une clé a été partagée par erreur, **régénérez-la** immédiatement.
- Restreignez la clé Google Maps aux adresses autorisées (`http://localhost:8501/*` et l'URL de la plateforme en ligne).
