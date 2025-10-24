import pandas as pd
import numpy as np
import seaborn as sns
import openpyxl
import re

# Charger les fichiers Excel
df1 = pd.read_excel("VERIFICATION DE CONCORDANCE DE CHARGEMENT VERIFICATION DOCUMENTAIRE - ETAT DES VEHICULES.xlsx", engine="openpyxl")
df2 = pd.read_excel("VERIFICATION DE CONCORDANCE DE CHARGEMENT.xlsx", engine="openpyxl", skiprows=[1, 1])

# Étape 1 : Renommer les colonnes du premier DataFrame pour correspondre au second
rename_dict = {
    'Date du contrôle': 'Date',
    'Personne en charge de la vérification': 'Nom de la personne en charge de la vérification',
    'Tournée / PDA / Nom de la société si besoin': 'Tournée / PDA / Nom de la société si DSP',
    'Type de véhicule / Immatriculation': 'Type de véhicule / immatriculation'
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

# Fonction pour extraire tournée, PDA et nom de la société
def extract_tournee_pda_societe(value):
    if pd.isna(value):
        return pd.NA, pd.NA, pd.NA
    
    # Convertir en majuscule et nettoyer les espaces inutiles
    value = str(value).upper().strip()
    
    # Expression régulière pour capturer :
    # - Tournée : séquence de chiffres
    # - PDA : une seule lettre juste après la tournée (éventuellement séparée par un espace ou "/")
    # - Société : tout ce qui suit après la tournée et le PDA
    pattern = r'^(\d+)(?:[\s/]*([A-Z]))?(?:[\s/]*(.*))?$'
    match = re.match(pattern, value.replace("/", " ").strip())
    
    tournee = pd.NA
    pda = pd.NA
    societe = pd.NA
    
    if match:
        tournee = match.group(1)  # Numéro de tournée
        pda = match.group(2) if match.group(2) else pd.NA  # PDA (une seule lettre)
        societe = match.group(3) if match.group(3) else pd.NA  # Nom de la société
    else:
        # Si pas de match, considérer la valeur entière comme société ou tournée
        if re.match(r'^\d+$', value):
            tournee = value
        else:
            societe = value
    
    # Nettoyer la société (supprimer espaces multiples et barres obliques)
    if pd.notna(societe):
        societe = re.sub(r'\s+', ' ', societe.strip())
        if not societe:  # Si vide après nettoyage
            societe = pd.NA
    
    return tournee, pda, societe

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

import pandas as pd
import re

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
        'Tournée / PDA / Nom de la société si DSP': 'tournee_pda_nom_societe',
        'Type de vérification': 'type_de_verification',
        'REGION': 'region',
        'Présence dans le véhicule de la copie numérotée de la licence de transport.\xa0\nHypothèse de la non présentation : Contactez le\xa0gérant de l\'entreprise de Transport afin de l\'en informer.\xa0\nC\'est à lui de ': 'presence_licence_transport',
        'Numéro de la licence': 'numero_licence',
        'Présentation du Permis de Conduire\nHypothèse de la non présentation du permis de conduire :\xa0 Contactez le\xa0gérant de l\'entreprise de Transport\xa0\xa0afin de l\'en informer.\nC\'est à lui de gérer\xa0la situation.': 'presentation_permis_conduire',
        'Vérification Liste nominative des salariés affectés à la prestation\nLa personne en charge du contrôle à quai doit se munir de la liste nominative fournie par le gérant de l\'entreprise de Transport et ': 'verification_liste_nominative',
        'ANOMALIE': 'anomalie',
        'ANOMALIE DE CHARGEMENT': 'anomalie_de_chargement',
        'ANOMALIE DE VEHICULE': 'anomalie_de_vehicule',
        'ANOMALIE SUIVI DE TOURNEE': 'anomalie_suivi_de_tournee',
        'AGENCES/ANTENNES': 'agences_antennes',
        'Tournée': 'tournee',
        'PDA': 'pda',
        'Nom de la société': 'nom_de_la_societe',
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
        'appartenance_du_conducteur', 'tournee_pda_nom_societe', 'type_de_verification',
        'region', 'presence_licence_transport', 'numero_licence', 'presentation_permis_conduire',
        'verification_liste_nominative', 'anomalie', 'anomalie_de_chargement',
        'anomalie_de_vehicule', 'is_surete', 'anomalie_suivi_de_tournee',
        'agences_antennes', 'tournee', 'pda', 'nom_de_la_societe', 'jour', 'heure_arrondie'
    ]
    for col in target_columns:
        if col not in df.columns:
            df[col] = pd.NA
            print(f"Colonne '{col}' ajoutée avec des valeurs NULL car absente du DataFrame.")

    # Réorganiser les colonnes pour correspondre à l'ordre de la table SQL
    df = df[target_columns]

    return df

def preprocessing(df):
    df["AGENCES/ANTENNES"] = ""
    for index, row in df.iterrows():
        if row["REGION"] == "REGION EST":
            df.at[index, "AGENCES/ANTENNES"] = row["AGENCES/ ANTENNES REGION EST"]
        elif row["REGION"] == "REGION NORD":
            df.at[index, "AGENCES/ANTENNES"] = row["AGENCES/ANTENNES REGION NORD"]
        elif row["REGION"] == "REGION OUEST":
            df.at[index, "AGENCES/ANTENNES"] = row["AGENCES/ANTENNES REGION OUEST"]
        elif row["REGION"] == "REGION SUD":
            df.at[index, "AGENCES/ANTENNES"] = row["AGENCES/ANTENNES REGION SUD"]
    
    # Supprimer les colonnes inutiles
    df = df.drop(columns=["AGENCES/ ANTENNES REGION EST", "AGENCES/ANTENNES REGION NORD", 
                          "AGENCES/ANTENNES REGION OUEST", "AGENCES/ANTENNES REGION SUD"])

    df["Nom"] = df["Nom"].str.upper()
    df["Nom"] = df["Nom"].str.replace("-", " ", regex=False)

    # Appliquer la fonction pour créer deux nouvelles colonnes
    df[["Type de véhicule", "Immatriculation"]] = df["Type de véhicule / immatriculation"].apply(
        lambda x: pd.Series(extract_vehicle_info(x))
    )
    
    # Supprimer la colonne originale
    df = df.drop(columns=["Type de véhicule / immatriculation"])
    
    # Mettre les colonnes en majuscule pour homogénéité
    df["Type de véhicule"] = df["Type de véhicule"].str.upper()
    df["Immatriculation"] = df["Immatriculation"].str.upper()

    
    # Appliquer la fonction pour créer trois nouvelles colonnes
    df[["Tournée", "PDA", "Nom de la société"]] = df["Tournée / PDA / Nom de la société si DSP"].apply(
        lambda x: pd.Series(extract_tournee_pda_societe(x))
    )
    
    # Standardiser : tout en majuscule
    df["PDA"] = df["PDA"].str.upper()
    df["Nom de la société"] = df["Nom de la société"].str.upper()
    
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


# Appliquer le preprocessing
df = preprocessing(df_combined)

# Sauvegarder le DataFrame dans un CSV
df.to_csv("verif_concordance2.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
print("Fichier 'verif_concordance2.csv' généré avec succès.")