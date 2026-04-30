import pandas as pd
import psycopg2
import toml
from dotenv import load_dotenv
import os

# Fonction pour charger les paramètres de connexion
def load_db_config():
    secrets_file = os.path.join(".streamlit", "secrets.toml")
    if os.path.exists(secrets_file):
        secrets = toml.load(secrets_file)
        if "connections" in secrets and "postgresql" in secrets["connections"]:
            db_config = secrets["connections"]["postgresql"]
            return {
                "DB_USER": db_config.get("username"),
                "DB_PASSWORD": db_config.get("password"),
                "DB_HOST": db_config.get("host"),
                "DB_PORT": db_config.get("port", "5432"),
                "DB_NAME": db_config.get("database", "postgres")
            }
        else:
            print("Aucun bloc [connections.postgresql] trouvé dans secrets.toml, tentative avec .env...")
    
    load_dotenv()
    return {
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_PORT": os.getenv("DB_PORT", "5432"),
        "DB_NAME": db_config.get("database", "postgres")
    }

# Charger les paramètres de connexion
db_config = load_db_config()
DB_USER = db_config["DB_USER"]
DB_PASSWORD = db_config["DB_PASSWORD"]
DB_HOST = db_config["DB_HOST"]
DB_PORT = db_config["DB_PORT"]
DB_NAME = db_config["DB_NAME"]

# Vérifier que toutes les variables nécessaires sont définies
if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    raise ValueError("Certaines variables de connexion (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME) sont manquantes.")

# URL de connexion pour psycopg2
DATABASE_URL = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"

# Nom de la table
TABLE_NAME = 'db_verifications_chargement'

# Lire le fichier CSV
csv_path = './data/controles_surete.csv'
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"Le fichier {csv_path} n'existe pas.")

df = pd.read_csv(csv_path)

# Renommer la colonne 'Id' en 'id' si nécessaire pour correspondre à la table
if 'Id' in df.columns and 'id' not in df.columns:
    df.rename(columns={'Id': 'id'}, inplace=True)

# Assurer les types de données corrects
if 'heure_de_debut' in df.columns:
    df['heure_de_debut'] = pd.to_datetime(df['heure_de_debut'], errors='coerce')
if 'heure_de_fin' in df.columns:
    df['heure_de_fin'] = pd.to_datetime(df['heure_de_fin'], errors='coerce')
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
if 'is_surete' in df.columns:
    df['is_surete'] = df['is_surete'].astype(bool, errors='ignore')

# Établir la connexion à Supabase
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
except Exception as e:
    raise Exception(f"Erreur de connexion à la base de données Supabase : {e}")

# Vérifier si la table existe
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = %s
    );
""", (TABLE_NAME,))
table_exists = cursor.fetchone()[0]

if table_exists:
    # Vérifier les colonnes de la table
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = %s;
    """, (TABLE_NAME,))
    columns = cursor.fetchall()
    print(f"Colonnes de la table {TABLE_NAME} : {columns}")

    # Vérifier si 'id' existe et est de type integer
    if 'id' not in [col[0] for col in columns]:
        raise ValueError(f"La colonne 'id' n'existe pas dans la table {TABLE_NAME}.")
    id_type = next(col[1] for col in columns if col[0] == 'id')
    if id_type != 'integer':
        print(f"Attention : la colonne 'id' est de type {id_type}, mais le script suppose un type integer.")

# Si la table n'existe pas, la créer
if not table_exists:
    df.to_sql(TABLE_NAME, f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}", 
              index=False, if_exists='fail', method='multi')
    # Ajouter la contrainte de clé primaire sur id
    cursor.execute(f"""
        ALTER TABLE {TABLE_NAME}
        ADD CONSTRAINT {TABLE_NAME}_pkey PRIMARY KEY (id);
    """)
    conn.commit()
    print(f"Table '{TABLE_NAME}' créée avec id comme clé primaire (type integer) et données insérées.")
else:
    # Créer une table temporaire pour les données du CSV
    temp_table = f'{TABLE_NAME}_temp'
    df.to_sql(temp_table, f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}", 
              index=False, if_exists='replace', method='multi')

    # Supprimer les lignes de verifications_chargement qui ne sont pas dans le CSV
    cursor.execute(f"""
        DELETE FROM {TABLE_NAME}
        WHERE id NOT IN (
            SELECT id FROM {temp_table}
        );
    """)

    # Upsert : insérer ou mettre à jour basé sur id
    cursor.execute(f"""
        INSERT INTO {TABLE_NAME} (
            id, heure_de_debut, heure_de_fin, date, lieu_de_la_verification, 
            appartenance_du_conducteur, type_de_verification, 
            region, presence_licence_transport, numero_licence, presentation_permis_conduire, 
            verification_liste_nominative, anomalie, anomalie_de_chargement, 
            anomalie_de_vehicule, is_surete, anomalie_suivi_de_tournee, 
            agences_antennes, tournee, pda, jour, heure_arrondie
        )
        SELECT 
            id, heure_de_debut, heure_de_fin, date, lieu_de_la_verification, 
            appartenance_du_conducteur, type_de_verification, 
            region, presence_licence_transport, numero_licence, presentation_permis_conduire, 
            verification_liste_nominative, anomalie, anomalie_de_chargement, 
            anomalie_de_vehicule, is_surete, anomalie_suivi_de_tournee, 
            agences_antennes, tournee, pda, jour, heure_arrondie
        FROM {temp_table}
        ON CONFLICT (id)
        DO UPDATE SET
            heure_de_debut = EXCLUDED.heure_de_debut,
            heure_de_fin = EXCLUDED.heure_de_fin,
            date = EXCLUDED.date,
            lieu_de_la_verification = EXCLUDED.lieu_de_la_verification,
            appartenance_du_conducteur = EXCLUDED.appartenance_du_conducteur,
            type_de_verification = EXCLUDED.type_de_verification,
            region = EXCLUDED.region,
            presence_licence_transport = EXCLUDED.presence_licence_transport,
            numero_licence = EXCLUDED.numero_licence,
            presentation_permis_conduire = EXCLUDED.presentation_permis_conduire,
            verification_liste_nominative = EXCLUDED.verification_liste_nominative,
            anomalie = EXCLUDED.anomalie,
            anomalie_de_chargement = EXCLUDED.anomalie_de_chargement,
            anomalie_de_vehicule = EXCLUDED.anomalie_de_vehicule,
            is_surete = EXCLUDED.is_surete,
            anomalie_suivi_de_tournee = EXCLUDED.anomalie_suivi_de_tournee,
            agences_antennes = EXCLUDED.agences_antennes,
            tournee = EXCLUDED.tournee,
            pda = EXCLUDED.pda,
            jour = EXCLUDED.jour,
            heure_arrondie = EXCLUDED.heure_arrondie;
    """)
        
    # Supprimer la table temporaire
    cursor.execute(f"DROP TABLE {temp_table};")
    conn.commit()

    print(f"Données mises à jour dans la table '{TABLE_NAME}' : lignes absentes supprimées et nouvelles lignes insérées/mises à jour.")

# Vérification : lire les premières lignes de la table
try:
    df_check = pd.read_sql(f"SELECT * FROM {TABLE_NAME} LIMIT 5;", 
                           f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("\nAperçu des 5 premières lignes de la table après mise à jour :")
    print(df_check)
except Exception as e:
    print("Erreur lors de la lecture de la table :", e)

# Fermer la connexion
cursor.close()
conn.close()