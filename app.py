import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuration de la page
st.set_page_config(page_title="Dashboard EDA Vérifications Contrôles", layout="wide")

# Chargement des données
@st.cache_data
def load_data():
    df = pd.read_csv("verif_concordance1.csv")
    # Nettoyage similaire au notebook
    df['Date'] = pd.to_datetime(df['Date'])
    df['jour'] = df['Date'].dt.day_name()  # En français si besoin: mapper à Jeudi, etc.
    jour_map = {
        'Monday': 'Lundi',
        'Tuesday': 'Mardi',
        'Wednesday': 'Mercredi',
        'Thursday': 'Jeudi',
        'Friday': 'Vendredi',
        'Saturday': 'Samedi',
        'Sunday': 'Dimanche'
    }
    df['jour'] = df['jour'].map(jour_map)
    df['heure_arrondie'] = pd.to_datetime(df['Heure de début']).dt.round('30min').dt.time
    return df

df = load_data()

# Sidebar pour filtres
st.sidebar.title("Filtres")
selected_agences = st.sidebar.multiselect("Sélectionner les Agences/Antennes", options=sorted(df['AGENCES/ANTENNES'].unique()), default=sorted(df['AGENCES/ANTENNES'].unique()))
selected_jours = st.sidebar.multiselect("Sélectionner les Jours", options=sorted(df['jour'].unique()), default=sorted(df['jour'].unique()))
selected_type_verif = st.sidebar.multiselect("Type de Vérification", options=df['Type de vérification'].unique(), default=df['Type de vérification'].unique())
selected_appartenance = st.sidebar.multiselect("Appartenance du Conducteur", options=df['Appartenance du conducteur'].unique(), default=df['Appartenance du conducteur'].unique())

# Filtrer les données
filtered_df = df[
    (df['AGENCES/ANTENNES'].isin(selected_agences)) &
    (df['jour'].isin(selected_jours)) &
    (df['Type de vérification'].isin(selected_type_verif)) &
    (df['Appartenance du conducteur'].isin(selected_appartenance))
]

# Titre principal
st.title("Dashboard EDA - Vérifications de Contrôles")

# Section 1: Métriques Globales
st.header("Métriques Globales")
col1, col2, col3, col4 = st.columns(4)
total_controles = len(filtered_df)
total_anomalies = len(filtered_df[filtered_df['ANOMALIE'] == 'Oui'])
pourcent_anomalies = (total_anomalies / total_controles * 100) if total_controles > 0 else 0
nb_cp = len(filtered_df[(filtered_df['Appartenance du conducteur'] == 'COLIS PRIVE') | (filtered_df['Appartenance du conducteur'] == 'COLIS PRIVE')])
nb_dsp = len(filtered_df[filtered_df['Appartenance du conducteur'] == 'DSP'])

col1.metric("Total Contrôles", total_controles)
col2.metric("Total Anomalies", total_anomalies)
col3.metric("% Anomalies", f"{pourcent_anomalies:.2f}%")
col4.metric("CP vs DSP", f"{nb_cp} CP / {nb_dsp} DSP")

# Section 2: Nombre de Contrôles par Site
st.header("Nombre de Contrôles par Site")
controles_par_site = filtered_df['AGENCES/ANTENNES'].value_counts().reset_index()
controles_par_site.columns = ['Site', 'Nombre de Contrôles']
fig_controles_site = px.bar(controles_par_site, x='Site', y='Nombre de Contrôles', title="Contrôles par Site")
st.plotly_chart(fig_controles_site, use_container_width=True)

# Section 3: Jours et Heures de Contrôles par Site
st.header("Jours et Heures de Contrôles par Site")
col_jour, col_heure = st.columns(2)

# Par Jour
with col_jour:
    controles_par_jour_site = filtered_df.groupby(['AGENCES/ANTENNES', 'jour']).size().unstack().fillna(0)
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
    controles_par_heure_site = filtered_df.groupby(['AGENCES/ANTENNES', 'heure_arrondie']).size().unstack().fillna(0)
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
anomalies_par_site = filtered_df[filtered_df['ANOMALIE'] == 'Oui']['AGENCES/ANTENNES'].value_counts().reset_index()
anomalies_par_site.columns = ['Site', 'Nombre d\'Anomalies']
fig_anomalies_site = px.bar(anomalies_par_site, x='Site', y='Nombre d\'Anomalies', title="Classement Sites par Anomalies")
st.plotly_chart(fig_anomalies_site, use_container_width=True)

# % Anomalies vs Nb Contrôles
pourcent_anomalies_site = filtered_df.groupby('AGENCES/ANTENNES').apply(
    lambda x: (len(x[x['ANOMALIE'] == 'Oui']) / len(x) * 100) if len(x) > 0 else 0
).reset_index()
pourcent_anomalies_site.columns = ['Site', '% Anomalies']
fig_pourcent = px.bar(pourcent_anomalies_site, x='Site', y='% Anomalies', title="% Anomalies par Site")
st.plotly_chart(fig_pourcent, use_container_width=True)

# Section 5: Types de Vérifications et Anomalies Spécifiques
st.header("Types de Vérifications et Anomalies")
col_verif, col_anomalie = st.columns(2)

# Nb Contrôles Avant/Après Chargement
with col_verif:
    verif_type = filtered_df['Type de vérification'].value_counts().reset_index()
    verif_type.columns = ['Type', 'Nombre']
    fig_verif = px.pie(verif_type, values='Nombre', names='Type', title="Répartition Types de Vérifications")
    st.plotly_chart(fig_verif, use_container_width=True)

# Anomalies par Type (Chargement, Véhicule, Suivi)
with col_anomalie:
    # Sous-figures pour les 3 types d'anomalies
    fig_anom = make_subplots(rows=1, cols=3, subplot_titles=('Anomalies Chargement', 'Anomalies Véhicule', 'Anomalies Suivi'))

    # Anomalies Chargement
    anom_charg = filtered_df['ANOMALIE DE CHARGEMENT'].value_counts().head(5)
    fig_anom.add_trace(go.Bar(x=anom_charg.index, y=anom_charg.values), row=1, col=1)

    # Anomalies Véhicule
    anom_veh = filtered_df['ANOMALIE DE VEHICULE'].value_counts().head(5)
    fig_anom.add_trace(go.Bar(x=anom_veh.index, y=anom_veh.values), row=1, col=2)

    # Anomalies Suivi
    anom_suivi = filtered_df['ANOMALIE SUIVI DE TOURNEE'].value_counts().head(5)
    fig_anom.add_trace(go.Bar(x=anom_suivi.index, y=anom_suivi.values), row=1, col=3)

    fig_anom.update_layout(height=400, title_text="Top Anomalies par Catégorie")
    st.plotly_chart(fig_anom, use_container_width=True)

# Section 6: Anomalies CP vs DSP (Délocalisé?)
st.header("Anomalies par Appartenance (CP / DSP)")
anom_cp_dsp = filtered_df.groupby(['Appartenance du conducteur', 'ANOMALIE']).size().unstack().fillna(0)
fig_cp_dsp = px.bar(anom_cp_dsp.reset_index(), x='Appartenance du conducteur', y=['Oui', 'Non'], barmode='stack', title="Anomalies CP vs DSP")
st.plotly_chart(fig_cp_dsp, use_container_width=True)

# Nouvelle Section 7: Analyse du Top 20 des Tournées avec le plus d'Anomalies Positives
st.header("Analyse du Top 20 des Tournées avec le plus d'Anomalies Positives")

# Calcul du top 20
top_tournees_anomalies = filtered_df[filtered_df['ANOMALIE'] == 'Oui'].groupby('Tournée').size().reset_index(name='Nb Anomalies')
top_tournees_anomalies = top_tournees_anomalies.sort_values('Nb Anomalies', ascending=False).head(20)
top_tournees_anomalies['Tournée'] = top_tournees_anomalies['Tournée'].astype(str)  # Pour affichage

# Table des données
st.subheader("Détails du Top 20")
st.dataframe(top_tournees_anomalies)

# Petite analyse textuelle
if not top_tournees_anomalies.empty:
    max_anom = top_tournees_anomalies.iloc[0]
    st.write(f"La tournée avec le plus d'anomalies est la {max_anom['Tournée']} avec {max_anom['Nb Anomalies']} anomalies.")
    st.write("Ces tournées représentent les zones prioritaires pour des investigations supplémentaires ou des améliorations.")
else:
    st.write("Aucune anomalie détectée dans les données filtrées.")

# Affichage des données brutes (optionnel)
if st.checkbox("Afficher les Données Filtrées"):
    st.dataframe(filtered_df)