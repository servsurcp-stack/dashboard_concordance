import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuration de la page
st.set_page_config(page_title="Dashboard EDA Vérifications Contrôles", layout="wide")

# Chargement des données
@st.cache_data
def load_data(query="SELECT * FROM db_verification_concordance;"):
    conn = st.connection("postgresql", type="sql")
    df = conn.query(query, ttl="10m")
    # Normalisations utiles
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if "heure_de_debut" in df.columns:
        df["heure_de_debut"] = pd.to_datetime(df["heure_de_debut"], errors="coerce")
    if "heure_de_fin" in df.columns:
        df["heure_de_fin"] = pd.to_datetime(df["heure_de_fin"], errors="coerce")
    if "lieu_de_la_verification" in df.columns:
        df["lieu_de_la_verification"] = df["lieu_de_la_verification"].astype(str)
    if "appartenance_du_conducteur" in df.columns:
        df["appartenance_du_conducteur"] = df["appartenance_du_conducteur"].astype(str)
    if "tournee_pda_nom_societe" in df.columns:
        df["tournee_pda_nom_societe"] = df["tournee_pda_nom_societe"].astype(str)
    if "type_de_verification" in df.columns:
        df["type_de_verification"] = df["type_de_verification"].astype(str)
    if "region" in df.columns:
        df["region"] = df["region"].astype(str)
    if "anomalie" in df.columns:
        df["anomalie"] = df["anomalie"].astype(str)
    if "anomalie_de_chargement" in df.columns:
        df["anomalie_de_chargement"] = df["anomalie_de_chargement"].astype(str, errors="ignore")
    if "anomalie_de_vehicule" in df.columns:
        df["anomalie_de_vehicule"] = df["anomalie_de_vehicule"].astype(str, errors="ignore")
    if "anomalie_suivi_de_tournee" in df.columns:
        df["anomalie_suivi_de_tournee"] = df["anomalie_suivi_de_tournee"].astype(str, errors="ignore")
    if "agences_antennes" in df.columns:
        df["agences_antennes"] = df["agences_antennes"].astype(str)
    if "tournee" in df.columns:
        df["tournee"] = df["tournee"].astype(str, errors="ignore")
    if "pda" in df.columns:
        df["pda"] = df["pda"].astype(str, errors="ignore")
    if "nom_de_la_societe" in df.columns:
        df["nom_de_la_societe"] = df["nom_de_la_societe"].astype(str, errors="ignore")
    if "jour" in df.columns:
        df["jour"] = df["jour"].astype(str)
    if "heure_arrondie" in df.columns:
        df["heure_arrondie"] = df["heure_arrondie"].astype(str)
    return df

df = load_data()

# Sidebar pour filtres
st.sidebar.title("Filtres")

# Préparer les valeurs par défaut
default_agences = sorted(df['agences_antennes'].unique()) if 'agences_antennes' in df.columns else []
default_jours = sorted(df['jour'].unique()) if 'jour' in df.columns else []
default_type_verif = list(df['type_de_verification'].unique()) if 'type_de_verification' in df.columns else []
default_appartenance = list(df['appartenance_du_conducteur'].unique()) if 'appartenance_du_conducteur' in df.columns else []

# Initialiser session_state pour les filtres si non présents (permet le reset)
if 'selected_agences' not in st.session_state:
    st.session_state['selected_agences'] = default_agences
if 'selected_jours' not in st.session_state:
    st.session_state['selected_jours'] = default_jours
if 'selected_type_verif' not in st.session_state:
    st.session_state['selected_type_verif'] = default_type_verif
if 'selected_appartenance' not in st.session_state:
    st.session_state['selected_appartenance'] = default_appartenance

def reset_filters():
    """Remettre les filtres à leurs valeurs par défaut."""
    st.session_state['selected_agences'] = default_agences
    st.session_state['selected_jours'] = default_jours
    st.session_state['selected_type_verif'] = default_type_verif
    st.session_state['selected_appartenance'] = default_appartenance

# Bouton pour réinitialiser
if st.sidebar.button("Réinitialiser les filtres"):
    reset_filters()

# Widgets liés à session_state
selected_agences = st.sidebar.multiselect(
    "Sélectionner les Agences/Antennes",
    options=default_agences,
    default=st.session_state.get('selected_agences', default_agences),
    key='selected_agences'
)

selected_jours = st.sidebar.multiselect(
    "Sélectionner les Jours",
    options=default_jours,
    default=st.session_state.get('selected_jours', default_jours),
    key='selected_jours'
)

selected_type_verif = st.sidebar.multiselect(
    "Type de Vérification",
    options=default_type_verif,
    default=st.session_state.get('selected_type_verif', default_type_verif),
    key='selected_type_verif'
)

selected_appartenance = st.sidebar.multiselect(
    "Appartenance du Conducteur",
    options=default_appartenance,
    default=st.session_state.get('selected_appartenance', default_appartenance),
    key='selected_appartenance'
)

# Filtrer les données
filtered_df = df[
    (df['agences_antennes'].isin(selected_agences)) &
    (df['jour'].isin(selected_jours)) &
    (df['type_de_verification'].isin(selected_type_verif)) &
    (df['appartenance_du_conducteur'].isin(selected_appartenance))
]

# Titre principal
st.title("Dashboard EDA - Vérifications de Contrôles")

# Section 1: Métriques Globales
st.header("Métriques Globales")
col1, col2, col3, col4 = st.columns(4)
total_controles = len(filtered_df)
total_anomalies = len(filtered_df[filtered_df['anomalie'] == 'OUI'])
pourcent_anomalies = (total_anomalies / total_controles * 100) if total_controles > 0 else 0
nb_cp = len(filtered_df[(filtered_df['appartenance_du_conducteur'] == 'COLIS PRIVE') | (filtered_df['appartenance_du_conducteur'] == 'COLIS PRIVE')])
nb_dsp = len(filtered_df[filtered_df['appartenance_du_conducteur'] == 'DSP'])

col1.metric("Total Contrôles", total_controles)
col2.metric("Total Anomalies", total_anomalies)
col3.metric("% Anomalies", f"{pourcent_anomalies:.2f}%")
col4.metric("CP vs DSP", f"{nb_cp} CP / {nb_dsp} DSP")

# Section 2: Nombre de Contrôles par Site
st.header("Nombre de Contrôles par Site")
controles_par_site = filtered_df['agences_antennes'].value_counts().reset_index()
controles_par_site.columns = ['Site', 'Nombre de Contrôles']
fig_controles_site = px.bar(controles_par_site, x='Site', y='Nombre de Contrôles', title="Contrôles par Site")
st.plotly_chart(fig_controles_site, use_container_width=True)

# Section 3: Jours et Heures de Contrôles par Site
st.header("Jours et Heures de Contrôles par Site")
col_jour, col_heure = st.columns(2)

# Par Jour
with col_jour:
    controles_par_jour_site = filtered_df.groupby(['agences_antennes', 'jour']).size().unstack().fillna(0)
    fig_jour = go.Figure(data=go.Heatmap(
        z=controles_par_jour_site.values,
        x=controles_par_jour_site.columns,
        y=controles_par_jour_site.index,
        colorscale='Viridis'
    ))
    fig_jour.update_layout(title="Heatmap Contrôles par Jour et Site")
    st.plotly_chart(fig_jour, use_container_width=True)

# Par Heure
with col_heure:
    controles_par_heure_site = filtered_df.groupby(['agences_antennes', 'heure_arrondie']).size().unstack().fillna(0)
    fig_heure = go.Figure(data=go.Heatmap(
        z=controles_par_heure_site.values,
        x=controles_par_heure_site.columns,
        y=controles_par_heure_site.index,
        colorscale='Viridis'
    ))
    fig_heure.update_layout(title="Heatmap Contrôles par Heure et Site")
    st.plotly_chart(fig_heure, use_container_width=True)

# Section 4: Anomalies
st.header("Analyse des Anomalies")

# Classement Sites par Anomalies
anomalies_par_site = filtered_df[filtered_df['anomalie'] == 'OUI']['agences_antennes'].value_counts().reset_index()
anomalies_par_site.columns = ['Site', 'Nombre d\'Anomalies']
fig_anomalies_site = px.bar(anomalies_par_site, x='Site', y='Nombre d\'Anomalies', title="Classement Sites par Anomalies")
st.plotly_chart(fig_anomalies_site, use_container_width=True)

# % Anomalies vs Nb Contrôles
pourcent_anomalies_site = filtered_df.groupby('agences_antennes').apply(
    lambda x: (len(x[x['anomalie'] == 'OUI']) / len(x) * 100) if len(x) > 0 else 0
).reset_index()
pourcent_anomalies_site.columns = ['Site', '% Anomalies']
# Trier par pourcentage d'anomalies décroissant pour afficher du plus élevé à gauche
pourcent_anomalies_site = pourcent_anomalies_site.sort_values('% Anomalies', ascending=False).reset_index(drop=True)
fig_pourcent = px.bar(pourcent_anomalies_site, x='Site', y='% Anomalies', title="% Anomalies par Site")
st.plotly_chart(fig_pourcent, use_container_width=True)

# % d'Anomalies par Jour de la semaine
if 'jour' in filtered_df.columns:
    anomalies_par_jour = filtered_df.groupby('jour').apply(
        lambda x: (len(x[x['anomalie'] == 'OUI']) / len(x) * 100) if len(x) > 0 else 0
    ).reset_index(name="% Anomalies")
    # S'assurer du tri chronologique des jours.
    # Cas 1: noms de jours en français
    jours_fr = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    jours_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    anomalies_par_jour['jour'] = anomalies_par_jour['jour'].astype(str)

    def compute_sort_key(val):
        v = val.strip()
        # FR exact match
        if v in jours_fr:
            return jours_fr.index(v)
        # EN exact match
        if v in jours_en:
            return jours_en.index(v)
        # FR lower-case variants
        v_cap = v.capitalize()
        if v_cap in jours_fr:
            return jours_fr.index(v_cap)
        # Try parse as date
        try:
            dt = pd.to_datetime(v, dayfirst=True, errors='coerce')
            if not pd.isna(dt):
                # use weekday (Monday=0)
                return dt.weekday()
        except Exception:
            pass
        # fallback: large number to send to end, but keep stable order via original index
        return 999

    anomalies_par_jour['jour_sort'] = anomalies_par_jour['jour'].apply(compute_sort_key)
    # Conserver ordre stable: on trie par jour_sort puis par jour
    anomalies_par_jour = anomalies_par_jour.sort_values(['jour_sort', 'jour'])
    anomalies_par_jour = anomalies_par_jour.drop(columns=['jour_sort']).reset_index(drop=True)

    st.subheader("% d'Anomalies par Jour")
    fig_anom_jour = px.bar(
        anomalies_par_jour,
        x='jour',
        y='% Anomalies',
        title="% d'Anomalies par Jour",
        labels={'jour': 'Jour', '% Anomalies': 'Pourcentage d\'Anomalies'},
        text='% Anomalies'
    )
    fig_anom_jour.update_traces(texttemplate='%{text:.2f}%', textposition='auto')
    st.plotly_chart(fig_anom_jour, use_container_width=True)
    st.dataframe(anomalies_par_jour)

# Section 5: Types de Vérifications et Anomalies Spécifiques
st.header("Types de Vérifications et Anomalies")
col_verif, col_anomalie = st.columns(2)

# Nb Contrôles Avant/Après Chargement
with col_verif:
    verif_type = filtered_df['type_de_verification'].value_counts().reset_index()
    verif_type.columns = ['Type', 'Nombre']
    fig_verif = px.pie(verif_type, values='Nombre', names='Type', title="Répartition Types de Vérifications")
    st.plotly_chart(fig_verif, use_container_width=True)

# Anomalies par Type (Chargement, Véhicule, Suivi)
with col_anomalie:
    # Sous-figures pour les 3 types d'anomalies
    fig_anom = make_subplots(rows=1, cols=3, subplot_titles=('Anomalies Chargement', 'Anomalies Véhicule', 'Anomalies Suivi'))

    # Anomalies Chargement
    anom_charg = filtered_df['anomalie_de_chargement'].value_counts().head(5)
    fig_anom.add_trace(go.Bar(x=anom_charg.index, y=anom_charg.values), row=1, col=1)

    # Anomalies Véhicule
    anom_veh = filtered_df['anomalie_de_vehicule'].value_counts().head(5)
    fig_anom.add_trace(go.Bar(x=anom_veh.index, y=anom_veh.values), row=1, col=2)

    # Anomalies Suivi
    anom_suivi = filtered_df['anomalie_suivi_de_tournee'].value_counts().head(5)
    fig_anom.add_trace(go.Bar(x=anom_suivi.index, y=anom_suivi.values), row=1, col=3)

    fig_anom.update_layout(height=400, title_text="Top Anomalies par Catégorie")
    st.plotly_chart(fig_anom, use_container_width=True)

# Section 6: Anomalies CP vs DSP
st.header("Anomalies par Appartenance (CP / DSP)")

# Effectuer le groupby et unstack pour le volume des anomalies
anom_cp_dsp = filtered_df.groupby(['appartenance_du_conducteur', 'anomalie']).size().unstack(fill_value=0)
# S'assurer que les colonnes 'OUI' et 'NON' existent
for col in ['OUI', 'NON']:
    if col not in anom_cp_dsp.columns:
        anom_cp_dsp[col] = 0

# Calculer les pourcentages d'anomalies par appartenance
pourcent_anomalies = filtered_df.groupby('appartenance_du_conducteur').apply(
    lambda x: (len(x[x['anomalie'] == 'OUI']) / len(x) * 100) if len(x) > 0 else 0
).reset_index(name='% Anomalies')

# Créer le graphique pour le volume (barre empilée)
fig_cp_dsp = px.bar(
    anom_cp_dsp.reset_index(),
    x='appartenance_du_conducteur',
    y=['OUI', 'NON'],
    barmode='stack',
    title="Anomalies CP vs DSP (Volume)",
    labels={'value': 'Nombre de Contrôles', 'appartenance_du_conducteur': 'Appartenance'}
)

# Afficher le graphique du volume
st.plotly_chart(fig_cp_dsp, use_container_width=True)

# Afficher les pourcentages d'anomalies
st.subheader("Pourcentage d'Anomalies par Appartenance")
# Créer un graphique en barres pour les pourcentages
fig_pourcent_anomalies = px.bar(
    pourcent_anomalies,
    x='appartenance_du_conducteur',
    y='% Anomalies',
    title="% d'Anomalies par Appartenance",
    labels={'appartenance_du_conducteur': 'Appartenance', '% Anomalies': 'Pourcentage d\'Anomalies'},
    text='% Anomalies'  # Afficher les valeurs sur les barres
)
fig_pourcent_anomalies.update_traces(texttemplate='%{text:.2f}%', textposition='auto')
st.plotly_chart(fig_pourcent_anomalies, use_container_width=True)

# Afficher un tableau récapitulatif des pourcentages
st.dataframe(pourcent_anomalies)

# Nouvelle Section 7: Analyse du Top 20 des Tournées avec le plus d'Anomalies Positives
st.header("Analyse du Top 20 des Tournées avec le plus d'Anomalies Positives")

# Calcul du top 20
top_tournees_anomalies = filtered_df[filtered_df['anomalie'] == 'OUI'].groupby('tournee').size().reset_index(name='Nb Anomalies')
top_tournees_anomalies = top_tournees_anomalies.sort_values('Nb Anomalies', ascending=False).head(20)
top_tournees_anomalies['tournee'] = top_tournees_anomalies['tournee'].astype(str)  # Pour affichage

# Table des données
st.subheader("Détails du Top 20")
st.dataframe(top_tournees_anomalies)

# Petite analyse textuelle
if not top_tournees_anomalies.empty:
    max_anom = top_tournees_anomalies.iloc[0]
    st.write(f"La tournée avec le plus d'anomalies est la {max_anom['tournee']} avec {max_anom['Nb Anomalies']} anomalies.")
    st.write("Ces tournées représentent les zones prioritaires pour des investigations supplémentaires ou des améliorations.")
else:
    st.write("Aucune anomalie détectée dans les données filtrées.")

# Affichage des données brutes (optionnel)
if st.checkbox("Afficher les Données Filtrées"):
    st.dataframe(filtered_df)