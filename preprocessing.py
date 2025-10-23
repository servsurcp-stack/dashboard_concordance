import pandas as pd
import numpy as np
import seaborn as sns
import openpyxl
import re

df = pd.read_excel("VERIFICATION DE CONCORDANCE DE CHARGEMENT.xlsx", engine="openpyxl", skiprows=[1,1])

def extract_vehicle_info(value):
    if pd.isna(value):
        return pd.NA, pd.NA
    
    value = str(value).upper().strip()
    immat_pattern = r'[A-Z]{1,2}-?\d{2,3}-?[A-Z]{1,2}|[A-Z]{1,2}\d{2,3}[A-Z]{1,2}'
    immat_match = re.search(immat_pattern, value.replace(" ", ""))
    
    if immat_match:
        immat = immat_match.group(0)
        immat = immat.replace("-", "")
        if len(immat) >= 5:
            immat_standard = f"{immat[:2]}-{immat[2:-2]}-{immat[-2:]}"
        else:
            immat_standard = immat
        type_vehicule = value.replace(immat_match.group(0), "").strip().replace("/", "").strip()
        if not type_vehicule:
            type_vehicule = "INCONNU"
    else:
        type_vehicule = value
        immat_standard = pd.NA
    
    return type_vehicule, immat_standard

def extract_tournee_pda_societe(value):
    if pd.isna(value):
        return pd.NA, pd.NA, pd.NA
    
    value = str(value).upper().strip()
    pattern = r'^(\d+)(?:[\s/]*([A-Z]))?(?:[\s/]*(.*))?$'
    match = re.match(pattern, value.replace("/", " ").strip())
    
    tournee = pd.NA
    pda = pd.NA
    societe = pd.NA
    
    if match:
        tournee = match.group(1)
        pda = match.group(2) if match.group(2) else pd.NA
        societe = match.group(3) if match.group(3) else pd.NA
    else:
        if re.match(r'^\d+$', value):
            tournee = value
        else:
            societe = value
    
    if pd.notna(societe):
        societe = re.sub(r'\s+', ' ', societe.strip())
        if not societe:
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

def preprocessing(df):
    # Ensure 'id' column exists; if not, you may need to generate it (e.g., df.index + 1)
    if 'id' not in df.columns and 'Id' not in df.columns:
        print("Warning: 'id' column not found in Excel. You may need to generate it manually.")
        # Example: df['id'] = df.index + 1  # Uncomment if you want to generate IDs

    # Rename 'Id' to 'id' if necessary
    if 'Id' in df.columns:
        df.rename(columns={'Id': 'id'}, inplace=True)

    # Handle AGENCES/ANTENNES based on REGION
    df["agences_antennes"] = ""
    for index, row in df.iterrows():
        if row["REGION"] == "REGION EST":
            df.at[index, "agences_antennes"] = row["AGENCES/ ANTENNES REGION EST"]
        elif row["REGION"] == "REGION NORD":
            df.at[index, "agences_antennes"] = row["AGENCES/ANTENNES REGION NORD"]
        elif row["REGION"] == "REGION OUEST":
            df.at[index, "agences_antennes"] = row["AGENCES/ANTENNES REGION OUEST"]
        elif row["REGION"] == "REGION SUD":
            df.at[index, "agences_antennes"] = row["AGENCES/ANTENNES REGION SUD"]

    # Drop unnecessary columns
    df = df.drop(columns=["AGENCES/ ANTENNES REGION EST", "AGENCES/ANTENNES REGION NORD", 
                          "AGENCES/ANTENNES REGION OUEST", "AGENCES/ANTENNES REGION SUD"], errors='ignore')

    # Extract vehicle info (though these columns are dropped as they aren't in the table)
    df[["Type de véhicule", "Immatriculation"]] = df["Type de véhicule / immatriculation"].apply(
        lambda x: pd.Series(extract_vehicle_info(x))
    )
    df = df.drop(columns=["Type de véhicule / immatriculation"], errors='ignore')

    # Extract tournée, PDA, and nom de la société
    df[["tournee", "pda", "nom_de_la_societe"]] = df["Tournée / PDA / Nom de la société si DSP"].apply(
        lambda x: pd.Series(extract_tournee_pda_societe(x))
    )

    # Rename columns to match table schema
    df.rename(columns={
        "Heure de début": "heure_de_debut",
        "Heure de fin": "heure_de_fin",
        "Date": "date",
        "Lieu de la vérification": "lieu_de_la_verification",
        "Appartenance du conducteur": "appartenance_du_conducteur",
        "Tournée / PDA / Nom de la société si DSP": "tournee_pda_nom_societe",
        "Type de vérification": "type_de_verification",
        "REGION": "region",
        "ANOMALIE": "anomalie",
        "ANOMALIE DE CHARGEMENT ": "anomalie_de_chargement",
        "ANOMALIE DE VEHICULE": "anomalie_de_vehicule",
        "ANOMALIE SUIVI DE TOURNEE": "anomalie_suivi_de_tournee",
        "AGENCES/ANTENNES": "agences_antennes",
        "Tournée": "tournee",
        "PDA": "pda",
        "Nom de la société": "nom_de_la_societe"
    }, inplace=True)

    # Drop columns not in the table schema
    df.drop(columns=["Matière dangereuse", "Adresse de messagerie", "Nom",
                     "Nom de la personne en charge de la vérification", 
                     "Commentaires ( N° de colis...)", "Commentaires", 
                     "Commentaires divers", "Type de véhicule", "Immatriculation"], 
            inplace=True, errors='ignore')

    # Convert datetime columns
    df["heure_de_debut"] = pd.to_datetime(df["heure_de_debut"], errors='coerce')
    df["heure_de_fin"] = pd.to_datetime(df["heure_de_fin"], errors='coerce')
    df["date"] = pd.to_datetime(df["date"], errors='coerce')

    # Derive jour column (in French, capitalized)
    df["jour"] = df["heure_de_debut"].dt.day_name(locale='fr_FR').str.upper()

    # Derive heure_arrondie as string (HH:MM:SS)
    df["heure_arrondie"] = df["heure_de_debut"].apply(arrondir_demi_heure).dt.strftime('%H:%M:%S')

    # Ensure all columns are uppercase where appropriate
    for col in ["lieu_de_la_verification", "appartenance_du_conducteur", 
                "tournee_pda_nom_societe", "type_de_verification", "region", 
                "anomalie", "anomalie_de_chargement", "anomalie_de_vehicule", 
                "anomalie_suivi_de_tournee", "agences_antennes", "tournee", 
                "pda", "nom_de_la_societe", "jour"]:
        if col in df.columns:
            df[col] = df[col].str.upper()

    df["appartenance_du_conducteur"] = df["appartenance_du_conducteur"].replace({"COLIS PRIVE LIVRAISON": "COLIS PRIVE"})

    return df

df = preprocessing(df)

# Save to CSV
df.to_csv("verif_concordance1.csv", index=False)