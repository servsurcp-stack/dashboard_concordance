import pandas as pd
import re

# Charger les fichiers Excel
df1 = pd.read_excel("./data/VERIFICATION DE CONCORDANCE DE CHARGEMENT VERIFICATION DOCUMENTAIRE - ETAT DES VEHICULES.xlsx", engine="openpyxl")
df2 = pd.read_excel("./data/SURETE - VERIFICATION DE CONCORDANCE DE CHARGEMENT 2026.xlsx", engine="openpyxl", skiprows=[1, 1])

# Étape 1 : Renommer les colonnes du premier DataFrame pour correspondre au second
rename_dict = {
    'Date du contrôle': 'Date',
    'Personne en charge de la vérification': 'Nom de la personne en charge de la vérification',
    'Tournée / PDA / Nom de la société si besoin': 'Tournée / PDA / Nom de la société si DSP',
    'Type de véhicule / Immatriculation': 'Type de véhicule / immatriculation',
    'N° TOURNEE' : 'NUMERO DE TOURNEE'
}
df1 = df1.rename(columns=rename_dict)

# Étape 2 : Ajouter la colonne 'is_surete'
df1['is_surete'] = False
df2['is_surete'] = True


# Étape 3 : Supprimer la colonne 'id' ou 'Id' des deux DataFrames pour éviter les doublons
for df in [df1, df2]:
    if 'Id' in df.columns:
        df.drop(columns=['Id'], inplace=True)
    if 'id' in df.columns:
        df.drop(columns=['id'], inplace=True)

# Étape 4 : Concaténer les deux DataFrames
df_combined = pd.concat([df1, df2], ignore_index=True)

# Étape 5 : Générer une nouvelle colonne 'id' avec des valeurs uniques
df_combined['id'] = range(1, len(df_combined) + 1)

def extract_vehicle_info(value):
    if pd.isna(value):
        return pd.NA, pd.NA
    
    # Convertir en majuscule pour homogénéité
    value = str(value).upper().strip()
    
    # Expression régulière pour détecter les immatriculations (format XX-123-YY ou similaire)
    immat_pattern = r'[A-Z]{1,2}-?\d{2,3}-?[A-Z]{1,2}|[A-Z]{1,2}\d{2,3}[A-Z]{1,2}'
    
    # Chercher l'immatriculation dans la valeur
    immat_match = re.search(immat_pattern, value.replace(" ", ""))
    
    if immat_match:
        immat = immat_match.group(0)
        # Standardiser le format de l'immatriculation (ajouter des tirets si nécessaire)
        immat = immat.replace("-", "")  # Supprimer les tirets existants
        if len(immat) >= 5:  # Vérifier que l'immatriculation a assez de caractères
            immat_standard = f"{immat[:2]}-{immat[2:-2]}-{immat[-2:]}"
        else:
            immat_standard = immat
        
        # Extraire le type de véhicule (tout ce qui est avant l'immatriculation)
        type_vehicule = value.replace(immat_match.group(0), "").strip().replace("/", "").strip()
        if not type_vehicule:  # Si vide, assigner "INCONNU"
            type_vehicule = "INCONNU"
    else:
        # Si aucune immatriculation n'est trouvée, toute la valeur est le type de véhicule
        type_vehicule = value
        immat_standard = pd.NA
    
    return type_vehicule, immat_standard


def arrondir_demi_heure(dt):
    minute = dt.minute
    if minute < 15:
        minute = 0
    elif minute < 45:
        minute = 30
    else:
        dt += pd.Timedelta(hours=1)
        minute = 0
    return dt.replace(minute=minute, second=0, microsecond=0)


def rename_columns(df):
    """
    Renomme les colonnes d'un DataFrame pour correspondre à la table SQL verifications_chargement.
    Les noms sont convertis en snake_case et les colonnes longues sont raccourcies.
    
    Args:
        df (pd.DataFrame): DataFrame contenant les données brutes (par exemple, issues d'un fichier Excel).
    
    Returns:
        pd.DataFrame: DataFrame avec les colonnes renommées.
    """
    # Dictionnaire de mappage des noms de colonnes originaux vers les noms cibles
    column_mapping = {
        'Id': 'id',
        'Heure de début': 'heure_de_debut',
        'Heure de fin': 'heure_de_fin',
        'Date': 'date',
        'Lieu de la vérification': 'lieu_de_la_verification',
        'Appartenance du conducteur': 'appartenance_du_conducteur',
        'Type de vérification': 'type_de_verification',
        'REGION': 'region',
        "Présence dans le véhicule de la copie numérotée de la licence de transport.\xa0\nHypothèse de la non présentation : Contactez le\xa0gérant de l'entreprise de Transport afin de l'en informer.\xa0\nC'est à lui..." : 'presence_licence_transport',
        'Numéro de la licence': 'numero_licence',
        "Présentation du Permis de Conduire\nHypothèse de la non présentation du permis de conduire :\xa0 Contactez le\xa0gérant de l'entreprise de Transport\xa0\xa0afin de l'en informer.\nC'est à lui de gérer\xa0la situat..." : 'presentation_permis_conduire',
        "Vérification Liste nominative des salariés affectés à la prestation\nLa personne en charge du contrôle à quai doit se munir de la liste nominative fournie par le gérant de l'entreprise de Transport..." : 'verification_liste_nominative',
        'ANOMALIE': 'anomalie',
        'ANOMALIE DE CHARGEMENT': 'anomalie_de_chargement',
        'ANOMALIE DE VEHICULE': 'anomalie_de_vehicule',
        'ANOMALIE SUIVI DE TOURNEE': 'anomalie_suivi_de_tournee',
        'AGENCES/ANTENNES': 'agences_antennes',
        'NUMERO DE TOURNEE': 'tournee',
        'LETTRE DE PDA': 'pda',
        'jour': 'jour',
        'heure_arrondie': 'heure_arrondie',
        'is_surete': 'is_surete'
    }

    # Nettoyer les noms de colonnes du DataFrame (supprimer \xa0, \n, espaces multiples)
    df.columns = [re.sub(r'\s+', ' ', col.replace('\xa0', ' ').replace('\n', ' ').strip()) for col in df.columns]

    # Créer un dictionnaire de mappage actualisé en tenant compte des colonnes nettoyées
    cleaned_mapping = {}
    for original_col, new_col in column_mapping.items():
        cleaned_col = re.sub(r'\s+', ' ', original_col.replace('\xa0', ' ').replace('\n', ' ').strip())
        cleaned_mapping[cleaned_col] = new_col

    # Vérifier les colonnes manquantes
    missing_cols = [col for col in cleaned_mapping.values() if col not in df.columns]
    if missing_cols:
        print(f"Avertissement : Les colonnes suivantes sont attendues mais absentes dans le DataFrame : {missing_cols}")

    # Renommer les colonnes
    df = df.rename(columns=cleaned_mapping)

    # Vérifier que toutes les colonnes cibles sont présentes, sinon ajouter des colonnes vides
    target_columns = [
        'id', 'heure_de_debut', 'heure_de_fin', 'date', 'lieu_de_la_verification',
        'appartenance_du_conducteur', 'type_de_verification',
        'region', 'presence_licence_transport', 'numero_licence', 'presentation_permis_conduire',
        'verification_liste_nominative', 'anomalie', 'anomalie_de_chargement',
        'anomalie_de_vehicule', 'is_surete', 'anomalie_suivi_de_tournee',
        'agences_antennes', 'tournee', 'pda', 'jour', 'heure_arrondie'
    ]
    for col in target_columns:
        if col not in df.columns:
            df[col] = pd.NA
            print(f"Colonne '{col}' ajoutée avec des valeurs NULL car absente du DataFrame.")

    # Réorganiser les colonnes pour correspondre à l'ordre de la table SQL
    df = df[target_columns]

    return df

def preprocessing(df):
    cols = [
        "AGENCES/ ANTENNES REGION SUD EST",
        "AGENCES/ANTENNES REGION NORD EST",
        "AGENCES/ANTENNES REGION NORD OUEST",
        "AGENCES/ANTENNES REGION SUD OUEST",
        "AGENCES/ANTENNES REGION IDF",
    ]
    # on prend la première valeur non-NaN parmi les 4
    df["AGENCES/ANTENNES"] = df[cols].bfill(axis=1).iloc[:, 0]

    
    # Supprimer les colonnes inutiles
    df = df.drop(columns=["AGENCES/ ANTENNES REGION SUD EST",
        "AGENCES/ANTENNES REGION NORD EST",
        "AGENCES/ANTENNES REGION NORD OUEST",
        "AGENCES/ANTENNES REGION SUD OUEST",
        "AGENCES/ANTENNES REGION IDF"])

    df["Nom"] = df["Nom"].str.upper()
    df["Nom"] = df["Nom"].str.replace("-", " ", regex=False)

    # Appliquer la fonction pour créer deux nouvelles colonnes
    df[["Type de véhicule", "Immatriculation"]] = df["Immatriculation"].apply(
        lambda x: pd.Series(extract_vehicle_info(x))
    )
    
    # Mettre les colonnes en majuscule pour homogénéité
    df["Type de véhicule"] = df["Type de véhicule"].str.upper()
    df["Immatriculation"] = df["Immatriculation"].str.upper()

    
    
    # Standardiser : tout en majuscule
    df["PDA"] = df["LETTRE DE PDA"].str.upper()
    
    df.drop(columns=["Matière dangereuse"],inplace=True)
    df.rename(columns={"ANOMALIE DE CHARGEMENT\xa0":"ANOMALIE DE CHARGEMENT"},inplace = True)
    df.rename(columns={"Commentaires divers\xa0":"Commentaires divers"},inplace = True)

    df.drop(columns =["Adresse de messagerie", "Nom", "Nom de la personne en charge de la vérification", "Commentaires ( N° de colis...)", "Commentaires", "Commentaires divers", "Type de véhicule", "Immatriculation" ],inplace=True)

    df["Heure de début"] = pd.to_datetime(df["Heure de début"])
    df["Heure de fin"] = pd.to_datetime(df["Heure de fin"])
    df["Date"] = pd.to_datetime(df["Date"])

    df["jour"] = df["Heure de début"].dt.day_name(locale='fr_FR')

    df["heure_arrondie"] = df["Heure de début"].apply(arrondir_demi_heure).dt.time

    df = rename_columns(df)

    df["appartenance_du_conducteur"] = df["appartenance_du_conducteur"].replace({"COLIS PRIVE LIVRAISON": "COLIS PRIVE"})
    

    return df

def uniform_anomalies(df) :
    # Remplacer NaN
    df["anomalie_de_chargement"] = df["anomalie_de_chargement"].fillna("Aucune anomalie")
    
    # Split et nettoyage
    df["anomalie_list"] = df["anomalie_de_chargement"].apply(
        lambda x: [item.strip().rstrip(";") for item in x.split(";") if item.strip()]
    )
    
    # Mapping pour uniformiser
    mapping = {
        "Autre": "Autre",
        "Colis en cabine": "Colis en cabine",
        "Colis non scanné (prévu pour ce chauffeur-livreur)": "Colis non scanné",
        "Colis non prévu pour ce chauffeur-livreur": "Colis non prévu",
        "Colis non prévu pour ce chauffeur-livreur (prévenir sans délai le service sûreté)": "Colis non prévu",
        "Adhésif Colis Privé dans le véhicule": "Adhésif Colis Privé"
    }
    
    df["anomalie_de_chargement"] = df["anomalie_list"].apply(
        lambda lst: [mapping.get(item, item) for item in lst]
    )
    
    # Remplacer NaN
    df["anomalie_de_vehicule"] = df["anomalie_de_vehicule"].fillna("Aucune anomalie")
    
    # Split et nettoyage
    df["anomalie_vehicule_list"] = df["anomalie_de_vehicule"].apply(
        lambda x: [item.strip().rstrip(";") for item in x.split(";") if item.strip()]
    )

    # Mapping pour uniformiser
    mapping_vehicule = {
        "Clef laissé sur le contact": "Clef laissée sur le contact",
        "Clef laissée sur le contact": "Clef laissée sur le contact",
        "Défaut de verrouillage": "Défaut de verrouillage",
        "Etat général": "Etat général",
        "Manque séparation cabine/caisse": "Manque séparation cabine/caisse",
        "Passager non autorisé": "Passager non autorisé",
        "Véhicule vitré": "Véhicule vitré"
    }
    
    df["anomalie_de_vehicule"] = df["anomalie_vehicule_list"].apply(
        lambda lst: [mapping_vehicule.get(item, item) for item in lst]
    )
    
    # Remplacer NaN
    df["anomalie_suivi_de_tournee"] = df["anomalie_suivi_de_tournee"].fillna("Aucune anomalie")
    
    # Split et nettoyage
    df["anomalie_tournee_list"] = df["anomalie_suivi_de_tournee"].apply(
        lambda x: [item.strip().rstrip(";") for item in x.split(";") if item.strip()]
    )
    
    # Mapping pour uniformiser
    mapping_tournee = {
        "Colis en cabine": "Colis en cabine",
        "Colis non autorisé": "Colis non autorisé",
        "Défaut de verrouillage": "Défaut de verrouillage",
        "Moteur tournant ou clef sur le contact": "Moteur tournant ou clef sur le contact"
    }
    
    df["anomalie_suivi_de_tournee"] = df["anomalie_tournee_list"].apply(
        lambda lst: [mapping_tournee.get(item, item) for item in lst]
    )

    return df


# Appliquer le preprocessing
df = preprocessing(df_combined)

df = uniform_anomalies(df)

# Sauvegarder le DataFrame dans un CSV
df.to_csv("./data/controles_surete.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
print("Fichier 'controles_surete.csv' généré avec succès.")