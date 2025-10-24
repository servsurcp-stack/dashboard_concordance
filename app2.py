import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuration de la page
st.set_page_config(page_title="Dashboard EDA Vérifications Chargement", layout="wide")

# Chargement des données
@st.cache_data
def load_data(query="SELECT * FROM db_verifications_chargement;"):
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
        df["lieu_de_la_verification"] = df["lieu_de_la_verification"].astype(str, errors="ignore")
    if "appartenance_du_conducteur" in df.columns:
        df["appartenance_du_conducteur"] = df["appartenance_du_conducteur"].astype(str, errors="ignore")
    if "tournee_pda_nom_societe" in df.columns:
        df["tournee_pda_nom_societe"] = df["tournee_pda_nom_societe"].astype(str, errors="ignore")
    if "type_de_verification" in df.columns:
        df["type_de_verification"] = df["type_de_verification"].astype(str, errors="ignore")
    if "region" in df.columns:
        df["region"] = df["region"].astype(str, errors="ignore")
    if "presence_licence_transport" in df.columns:
        df["presence_licence_transport"] = df["presence_licence_transport"].astype(str, errors="ignore")
    if "numero_licence" in df.columns:
        df["numero_licence"] = df["numero_licence"].astype(str, errors="ignore")
    if "presentation_permis_conduire" in df.columns:
        df["presentation_permis_conduire"] = df["presentation_permis_conduire"].astype(str, errors="ignore")
    if "verification_liste_nominative" in df.columns:
        df["verification_liste_nominative"] = df["verification_liste_nominative"].astype(str, errors="ignore")
    if "anomalie" in df.columns:
        df["anomalie"] = df["anomalie"].astype(str, errors="ignore")
    if "anomalie_de_chargement" in df.columns:
        df["anomalie_de_chargement"] = df["anomalie_de_chargement"].astype(str, errors="ignore")
    if "anomalie_de_vehicule" in df.columns:
        df["anomalie_de_vehicule"] = df["anomalie_de_vehicule"].astype(str, errors="ignore")
    if "anomalie_suivi_de_tournee" in df.columns:
        df["anomalie_suivi_de_tournee"] = df["anomalie_suivi_de_tournee"].astype(str, errors="ignore")
    if "agences_antennes" in df.columns:
        df["agences_antennes"] = df["agences_antennes"].astype(str, errors="ignore")
    if "tournee" in df.columns:
        df["tournee"] = df["tournee"].astype(str, errors="ignore")
    if "pda" in df.columns:
        df["pda"] = df["pda"].astype(str, errors="ignore")
    if "nom_de_la_societe" in df.columns:
        df["nom_de_la_societe"] = df["nom_de_la_societe"].astype(str, errors="ignore")
    if "jour" in df.columns:
        df["jour"] = df["jour"].astype(str, errors="ignore")
    if "heure_arrondie" in df.columns:
        df["heure_arrondie"] = df["heure_arrondie"].astype(str, errors="ignore")
    if "is_surete" in df.columns:
        df["is_surete"] = df["is_surete"].astype(bool, errors="ignore")
    return df

df = load_data()

# Sidebar pour filtres
st.sidebar.title("Filtres")

# Préparer les valeurs par défaut
default_agences = sorted(df['agences_antennes'].unique()) if 'agences_antennes' in df.columns else []
default_jours = sorted(df['jour'].unique()) if 'jour' in df.columns else []
default_type_verif = list(df['type_de_verification'].unique()) if 'type_de_verification' in df.columns else []
default_appartenance = list(df['appartenance_du_conducteur'].unique()) if 'appartenance_du_conducteur' in df.columns else []
default_is_surete = list(df['is_surete'].unique()) if 'is_surete' in df.columns else [True, False]

# Initialiser session_state pour les filtres si non présents
if 'selected_agences' not in st.session_state:
    st.session_state['selected_agences'] = default_agences
if 'selected_jours' not in st.session_state:
    st.session_state['selected_jours'] = default_jours
if 'selected_type_verif' not in st.session_state:
    st.session_state['selected_type_verif'] = default_type_verif
if 'selected_appartenance' not in st.session_state:
    st.session_state['selected_appartenance'] = default_appartenance
if 'selected_is_surete' not in st.session_state:
    st.session_state['selected_is_surete'] = default_is_surete

def reset_filters():
    """Remettre les filtres à leurs valeurs par défaut."""
    st.session_state['selected_agences'] = default_agences
    st.session_state['selected_jours'] = default_jours
    st.session_state['selected_type_verif'] = default_type_verif
    st.session_state['selected_appartenance'] = default_appartenance
    st.session_state['selected_is_surete'] = default_is_surete

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

selected_is_surete = st.sidebar.multiselect(
    "Vérifications par la Sûreté",
    options=default_is_surete,
    default=st.session_state.get('selected_is_surete', default_is_surete),
    key='selected_is_surete'
)

# Filtrer les données
filtered_df = df[
    (df['agences_antennes'].isin(selected_agences)) &
    (df['jour'].isin(selected_jours)) &
    (df['type_de_verification'].isin(selected_type_verif)) &
    (df['appartenance_du_conducteur'].isin(selected_appartenance)) &
    (df['is_surete'].isin(selected_is_surete))
]

# Titre principal
st.title("Dashboard EDA - Vérifications de Chargement")

# Section 1: Métriques Globales
st.header("Métriques Globales")
col1, col2, col3, col4 = st.columns(4)
total_controles = len(filtered_df)
total_anomalies = len(filtered_df[filtered_df['anomalie'] == 'Oui'])
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
anomalies_par_site = filtered_df[filtered_df['anomalie'] == 'Oui']['agences_antennes'].value_counts().reset_index()
anomalies_par_site.columns = ['Site', 'Nombre d\'Anomalies']
fig_anomalies_site = px.bar(anomalies_par_site, x='Site', y='Nombre d\'Anomalies', title="Classement Sites par Anomalies")
st.plotly_chart(fig_anomalies_site, use_container_width=True)

# % Anomalies vs Nb Contrôles
pourcent_anomalies_site = filtered_df.groupby('agences_antennes').apply(
    lambda x: (len(x[x['anomalie'] == 'Oui']) / len(x) * 100) if len(x) > 0 else 0
).reset_index()
pourcent_anomalies_site.columns = ['Site', '% Anomalies']
pourcent_anomalies_site = pourcent_anomalies_site.sort_values('% Anomalies', ascending=False).reset_index(drop=True)
fig_pourcent = px.bar(pourcent_anomalies_site, x='Site', y='% Anomalies', title="% Anomalies par Site")
st.plotly_chart(fig_pourcent, use_container_width=True)

# % d'Anomalies par Jour de la semaine
if 'jour' in filtered_df.columns:
    anomalies_par_jour = filtered_df.groupby('jour').apply(
        lambda x: (len(x[x['anomalie'] == 'Oui']) / len(x) * 100) if len(x) > 0 else 0
    ).reset_index(name="% Anomalies")
    jours_fr = ['LUNDI', 'MARDI', 'MERCREDI', 'JEUDI', 'VENDREDI', 'SAMEDI', 'DIMANCHE']
    jours_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    anomalies_par_jour['jour'] = anomalies_par_jour['jour'].astype(str)

    def compute_sort_key(val):
        v = val.strip().upper()
        if v in jours_fr:
            return jours_fr.index(v)
        if v in jours_en:
            return jours_en.index(v)
        v_cap = v.capitalize()
        if v_cap in jours_fr:
            return jours_fr.index(v_cap)
        try:
            dt = pd.to_datetime(v, dayfirst=True, errors='coerce')
            if not pd.isna(dt):
                return dt.weekday()
        except Exception:
            pass
        return 999

    anomalies_par_jour['jour_sort'] = anomalies_par_jour['jour'].apply(compute_sort_key)
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

# Nouvelle Section: Visualisation Temporelle des Anomalies
st.header("Visualisation Temporelle des Anomalies")

# Préparer les données pour la visualisation temporelle
# Par heure
filtered_df['heure'] = filtered_df['heure_de_debut'].dt.hour
anomalies_par_heure = filtered_df[filtered_df['anomalie'] == 'Oui'].groupby('heure').size().reset_index(name='Nb Anomalies')
controles_par_heure = filtered_df.groupby('heure').size().reset_index(name='Nb Contrôles')
df_heure = pd.merge(controles_par_heure, anomalies_par_heure, on='heure', how='left').fillna(0)
df_heure['% Anomalies'] = (df_heure['Nb Anomalies'] / df_heure['Nb Contrôles'] * 100).round(2)

# Par semaine
filtered_df['date'] = pd.to_datetime(filtered_df['date'])
filtered_df['annee_semaine'] = filtered_df['date'].dt.strftime('%Y-W%W')
anomalies_par_semaine = filtered_df[filtered_df['anomalie'] == 'Oui'].groupby('annee_semaine').size().reset_index(name='Nb Anomalies')
controles_par_semaine = filtered_df.groupby('annee_semaine').size().reset_index(name='Nb Contrôles')
df_semaine = pd.merge(controles_par_semaine, anomalies_par_semaine, on='annee_semaine', how='left').fillna(0)
df_semaine['% Anomalies'] = (df_semaine['Nb Anomalies'] / df_semaine['Nb Contrôles'] * 100).round(2)

# Graphique par heure
st.subheader("Évolution par Heure")
fig_heure = make_subplots(specs=[[{"secondary_y": True}]])
fig_heure.add_trace(
    go.Scatter(x=df_heure['heure'], y=df_heure['Nb Contrôles'], name="Nb Contrôles", line=dict(color='blue')),
    secondary_y=False
)
fig_heure.add_trace(
    go.Scatter(x=df_heure['heure'], y=df_heure['Nb Anomalies'], name="Nb Anomalies", line=dict(color='red')),
    secondary_y=False
)
fig_heure.add_trace(
    go.Scatter(x=df_heure['heure'], y=df_heure['% Anomalies'], name="% Anomalies", line=dict(color='green', dash='dash')),
    secondary_y=True
)
fig_heure.update_layout(
    title="Évolution des Contrôles et Anomalies par Heure",
    xaxis_title="Heure de la Journée",
    yaxis_title="Nombre de Contrôles/Anomalies",
    legend=dict(x=0, y=1.1, orientation="h", font=dict(size=12)),
    font=dict(size=14),
    margin=dict(l=50, r=50, t=100, b=50),
    xaxis=dict(tickfont=dict(size=12)),
    yaxis=dict(tickfont=dict(size=12))
)
fig_heure.update_yaxes(title_text="% Anomalies", secondary_y=True, tickfont=dict(size=12))
if not df_heure['Nb Anomalies'].empty:
    max_anom_heure = df_heure.loc[df_heure['Nb Anomalies'].idxmax()]
    fig_heure.add_annotation(
        x=max_anom_heure['heure'], y=max_anom_heure['Nb Anomalies'],
        text=f"Pic: {int(max_anom_heure['Nb Anomalies'])} anomalies",
        showarrow=True, arrowhead=1, ax=20, ay=-30, font=dict(size=12)
    )
st.plotly_chart(fig_heure, use_container_width=True)
st.dataframe(df_heure)

# Graphique par semaine
st.subheader("Évolution par Semaine")
fig_semaine = make_subplots(specs=[[{"secondary_y": True}]])
fig_semaine.add_trace(
    go.Scatter(x=df_semaine['annee_semaine'], y=df_semaine['Nb Contrôles'], name="Nb Contrôles", line=dict(color='blue')),
    secondary_y=False
)
fig_semaine.add_trace(
    go.Scatter(x=df_semaine['annee_semaine'], y=df_semaine['Nb Anomalies'], name="Nb Anomalies", line=dict(color='red')),
    secondary_y=False
)
fig_semaine.add_trace(
    go.Scatter(x=df_semaine['annee_semaine'], y=df_semaine['% Anomalies'], name="% Anomalies", line=dict(color='green', dash='dash')),
    secondary_y=True
)
fig_semaine.update_layout(
    title="Évolution des Contrôles et Anomalies par Semaine",
    xaxis_title="Semaine (Année-Semaine)",
    yaxis_title="Nombre de Contrôles/Anomalies",
    legend=dict(x=0, y=1.1, orientation="h", font=dict(size=12)),
    font=dict(size=14),
    margin=dict(l=50, r=50, t=100, b=50),
    xaxis=dict(tickfont=dict(size=12), tickangle=45),
    yaxis=dict(tickfont=dict(size=12))
)
fig_semaine.update_yaxes(title_text="% Anomalies", secondary_y=True, tickfont=dict(size=12))
if not df_semaine['Nb Anomalies'].empty:
    max_anom_semaine = df_semaine.loc[df_semaine['Nb Anomalies'].idxmax()]
    fig_semaine.add_annotation(
        x=max_anom_semaine['annee_semaine'], y=max_anom_semaine['Nb Anomalies'],
        text=f"Pic: {int(max_anom_semaine['Nb Anomalies'])} anomalies",
        showarrow=True, arrowhead=1, ax=20, ay=-30, font=dict(size=12)
    )
st.plotly_chart(fig_semaine, use_container_width=True)
st.dataframe(df_semaine)

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
    fig_anom = make_subplots(rows=1, cols=3, subplot_titles=('Anomalies Chargement', 'Anomalies Véhicule', 'Anomalies Suivi'))
    if 'anomalie_de_chargement' in filtered_df.columns:
        anom_charg = filtered_df['anomalie_de_chargement'].dropna().astype(str)
        anom_charg = anom_charg[anom_charg.str.strip().str.lower() != 'none']
        anom_charg = anom_charg[anom_charg.str.strip() != '']
        anom_charg = anom_charg.value_counts().head(5)
    else:
        anom_charg = pd.Series(dtype=int)
    fig_anom.add_trace(go.Bar(x=anom_charg.index, y=anom_charg.values), row=1, col=1)

    if 'anomalie_de_vehicule' in filtered_df.columns:
        anom_veh = filtered_df['anomalie_de_vehicule'].dropna().astype(str)
        anom_veh = anom_veh[anom_veh.str.strip().str.lower() != 'none']
        anom_veh = anom_veh[anom_veh.str.strip() != '']
        anom_veh = anom_veh.value_counts().head(5)
    else:
        anom_veh = pd.Series(dtype=int)
    fig_anom.add_trace(go.Bar(x=anom_veh.index, y=anom_veh.values), row=1, col=2)

    if 'anomalie_suivi_de_tournee' in filtered_df.columns:
        anom_suivi = filtered_df['anomalie_suivi_de_tournee'].dropna().astype(str)
        anom_suivi = anom_suivi[anom_suivi.str.strip().str.lower() != 'none']
        anom_suivi = anom_suivi[anom_suivi.str.strip() != '']
        anom_suivi = anom_suivi.value_counts().head(5)
    else:
        anom_suivi = pd.Series(dtype=int)
    fig_anom.add_trace(go.Bar(x=anom_suivi.index, y=anom_suivi.values), row=1, col=3)
    fig_anom.update_layout(height=400, title_text="Top Anomalies par Catégorie")
    st.plotly_chart(fig_anom, use_container_width=True)

# Nouvelle Section: Analyse des Vérifications Documentaires
st.header("Analyse des Vérifications Documentaires")
col_licence, col_permis, col_liste = st.columns(3)

# Présence de la licence de transport
with col_licence:
    if 'presence_licence_transport' in filtered_df.columns:
        licence_counts = filtered_df['presence_licence_transport'].value_counts().reset_index()
        licence_counts.columns = ['Présence Licence', 'Nombre']
        fig_licence = px.pie(licence_counts, values='Nombre', names='Présence Licence', 
                             title="Présence de la Licence de Transport")
        st.plotly_chart(fig_licence, use_container_width=True)

# Présentation du permis de conduire
with col_permis:
    if 'presentation_permis_conduire' in filtered_df.columns:
        permis_counts = filtered_df['presentation_permis_conduire'].value_counts().reset_index()
        permis_counts.columns = ['Permis Présenté', 'Nombre']
        fig_permis = px.pie(permis_counts, values='Nombre', names='Permis Présenté', 
                            title="Présentation du Permis de Conduire")
        st.plotly_chart(fig_permis, use_container_width=True)

# Vérification de la liste nominative
with col_liste:
    if 'verification_liste_nominative' in filtered_df.columns:
        liste_counts = filtered_df['verification_liste_nominative'].value_counts().reset_index()
        liste_counts.columns = ['Liste Nominative Vérifiée', 'Nombre']
        fig_liste = px.pie(liste_counts, values='Nombre', names='Liste Nominative Vérifiée', 
                           title="Vérification Liste Nominative")
        st.plotly_chart(fig_liste, use_container_width=True)

# Section 6: Anomalies CP vs DSP
st.header("Anomalies par Appartenance (CP / DSP)")
anom_cp_dsp = filtered_df.groupby(['appartenance_du_conducteur', 'anomalie']).size().unstack(fill_value=0)
for col in ['Oui', 'Non']:
    if col not in anom_cp_dsp.columns:
        anom_cp_dsp[col] = 0
pourcent_anomalies = filtered_df.groupby('appartenance_du_conducteur').apply(
    lambda x: (len(x[x['anomalie'] == 'Oui']) / len(x) * 100) if len(x) > 0 else 0
).reset_index(name='% Anomalies')
fig_cp_dsp = px.bar(
    anom_cp_dsp.reset_index(),
    x='appartenance_du_conducteur',
    y=['Oui', 'Non'],
    barmode='stack',
    title="Anomalies CP vs DSP (Volume)",
    labels={'value': 'Nombre de Contrôles', 'appartenance_du_conducteur': 'Appartenance'}
)
st.plotly_chart(fig_cp_dsp, use_container_width=True)
st.subheader("Pourcentage d'Anomalies par Appartenance")
fig_pourcent_anomalies = px.bar(
    pourcent_anomalies,
    x='appartenance_du_conducteur',
    y='% Anomalies',
    title="% d'Anomalies par Appartenance",
    labels={'appartenance_du_conducteur': 'Appartenance', '% Anomalies': 'Pourcentage d\'Anomalies'},
    text='% Anomalies'
)
fig_pourcent_anomalies.update_traces(texttemplate='%{text:.2f}%', textposition='auto')
st.plotly_chart(fig_pourcent_anomalies, use_container_width=True)
st.dataframe(pourcent_anomalies)

# Section 7: Analyse du Top 20 des Tournées avec le plus d'Anomalies Positives
st.header("Analyse du Top 20 des Tournées avec le plus d'Anomalies Positives")
top_tournees_anomalies = filtered_df[filtered_df['anomalie'] == 'Oui'].groupby('tournee').size().reset_index(name='Nb Anomalies')
total_par_tournee = filtered_df.groupby('tournee').size().reset_index(name='Nb Contrôles')
top_tournees = pd.merge(top_tournees_anomalies, total_par_tournee, on='tournee', how='left')
top_tournees['% Anomalies'] = (top_tournees['Nb Anomalies'] / top_tournees['Nb Contrôles'] * 100).round(2)
top_tournees = top_tournees.sort_values('Nb Anomalies', ascending=False).head(20)
top_tournees['tournee'] = top_tournees['tournee'].astype(str)
agences_par_tournee = filtered_df.groupby('tournee')['agences_antennes'].unique().reset_index()
def join_agences(arr):
    try:
        lst = [str(x) for x in arr if pd.notna(x)]
        return '; '.join(sorted(set(lst)))
    except Exception:
        return ''
agences_par_tournee['Agences'] = agences_par_tournee['agences_antennes'].apply(join_agences)
agences_par_tournee = agences_par_tournee.drop(columns=['agences_antennes'])
top_tournees = pd.merge(top_tournees, agences_par_tournee, on='tournee', how='left')

st.subheader("Détails du Top 20")
st.dataframe(top_tournees)
if not top_tournees_anomalies.empty:
    max_anom = top_tournees_anomalies.iloc[0]
    st.write(f"La tournée avec le plus d'anomalies est la {max_anom['tournee']} avec {max_anom['Nb Anomalies']} anomalies.")
    st.write("Ces tournées représentent les zones prioritaires pour des investigations supplémentaires ou des améliorations.")
else:
    st.write("Aucune anomalie détectée dans les données filtrées.")

# Affichage des données brutes (optionnel)
if st.checkbox("Afficher les Données Filtrées"):
    st.dataframe(filtered_df)