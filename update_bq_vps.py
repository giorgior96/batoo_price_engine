import paramiko

host = '65.108.208.5'
user = 'root'
password = 'ciao2112'

new_upload_script = """import json
import pandas as pd
from google.cloud import bigquery
from datetime import datetime

# ==========================================
# CONFIGURAZIONE BIGQUERY
# ==========================================
PROJECT_ID = "vast-ascent-457111-r0"
DATASET_ID = "batoo_analytics"
TABLE_ID = "boats_staging"
TEMP_TABLE_ID = "boats_temp"
HISTORY_TABLE_ID = "price_changes_log"

def prepare_and_upload():
    print("1. Caricamento dei dati dal JSON...")
    df = pd.read_json("master_boats_db.json")

    print(f"Trovati {len(df)} record. Rimozione dei duplicati per URL...")
    df.drop_duplicates(subset=['url'], keep='first', inplace=True)
    print(f"Rimasti {len(df)} record unici. Preparazione dello schema...")

    if 'category' not in df.columns:
        df['category'] = None
    if 'status' not in df.columns:
        df['status'] = True

    df['id'] = df['id'].astype('Int64')
    df['year_built'] = df['year_built'].astype('Int64')
    df['price_eur'] = df['price_eur'].astype('float64')
    df['length'] = df['length'].astype('float64')
    df['status'] = df['status'].astype('boolean')

    string_columns = ['builder', 'model', 'country', 'image_url', 'source', 'broker', 'url', 'category']
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('<NA>', None).replace('nan', None).where(pd.notnull(df[col]), None)

    print("2. Connessione a BigQuery...")
    client = bigquery.Client(project=PROJECT_ID)

    temp_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TEMP_TABLE_ID}"
    main_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    history_table_ref = f"{PROJECT_ID}.{DATASET_ID}.{HISTORY_TABLE_ID}"

    # 1. Caricamento temporaneo
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("id", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("builder", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("model", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("year_built", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("country", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("price_eur", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("length", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("image_url", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("broker", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("url", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("category", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("status", "BOOLEAN", mode="NULLABLE"),
        ],
        write_disposition="WRITE_TRUNCATE",
    )

    print(f"3. Caricamento dei dati nella tabella TEMPORANEA {temp_table_ref}...")
    job = client.load_table_from_dataframe(df, temp_table_ref, job_config=job_config)
    job.result()
    print(f"Tabella temporanea aggiornata con {job.output_rows} righe.")

    # 2. Setup tabelle
    print("4. Setup tabelle e storicizzazione prezzi...")
    create_main_table_sql = f\"\"\"
    CREATE TABLE IF NOT EXISTS `{main_table_ref}` (
        id INT64, builder STRING, model STRING, year_built INT64,
        country STRING, price_eur FLOAT64, length FLOAT64,
        image_url STRING, source STRING, broker STRING,
        url STRING, category STRING, status BOOLEAN,
        first_seen_at TIMESTAMP, updated_at TIMESTAMP
    )
    \"\"\"
    client.query(create_main_table_sql).result()

    create_history_table_sql = f\"\"\"
    CREATE TABLE IF NOT EXISTS `{history_table_ref}` (
        url STRING,
        old_price_eur FLOAT64,
        new_price_eur FLOAT64,
        change_date TIMESTAMP
    )
    \"\"\"
    client.query(create_history_table_sql).result()

    alter_sql = f\"\"\"
    ALTER TABLE `{main_table_ref}`
    ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
    \"\"\"
    try: client.query(alter_sql).result()
    except Exception: pass

    # 3. Logica Storico Prezzi (Inseriamo in log prima di sovrascrivere)
    log_changes_sql = f\"\"\"
    INSERT INTO `{history_table_ref}` (url, old_price_eur, new_price_eur, change_date)
    SELECT 
        T.url, 
        T.price_eur as old_price_eur, 
        S.price_eur as new_price_eur, 
        CURRENT_TIMESTAMP() as change_date
    FROM `{main_table_ref}` T
    JOIN (
        SELECT * EXCEPT(row_num)
        FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY url ORDER BY id DESC) as row_num FROM `{temp_table_ref}`)
        WHERE row_num = 1
    ) S
    ON T.url = S.url
    WHERE T.price_eur != S.price_eur 
      AND T.price_eur IS NOT NULL 
      AND S.price_eur IS NOT NULL
    \"\"\"
    client.query(log_changes_sql).result()
    print("Variazioni di prezzo registrate nella tabella price_changes_log.")

    # 4. MERGE della tabella principale
    print("5. Esecuzione del MERGE per aggiornare lo snapshot principale...")
    merge_sql = f\"\"\"
    MERGE `{main_table_ref}` T
    USING (
        SELECT * EXCEPT(row_num)
        FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY url ORDER BY id DESC) as row_num FROM `{temp_table_ref}`)
        WHERE row_num = 1
    ) S
    ON T.url = S.url
    WHEN MATCHED THEN
      UPDATE SET 
        price_eur = S.price_eur,
        status = TRUE,
        updated_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
      INSERT (id, builder, model, year_built, country, price_eur, length, image_url, source, broker, url, category, status, first_seen_at, updated_at)
      VALUES (S.id, S.builder, S.model, S.year_built, S.country, S.price_eur, S.length, S.image_url, S.source, S.broker, S.url, S.category, TRUE, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
    WHEN NOT MATCHED BY SOURCE THEN
      UPDATE SET status = FALSE, updated_at = CURRENT_TIMESTAMP()
    \"\"\"

    merge_job = client.query(merge_sql)
    merge_job.result()
    print("Finito! I dati sono stati uniti e aggiornati.")

if __name__ == "__main__":
    prepare_and_upload()
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(host, username=user, password=password)
    sftp = client.open_sftp()
    with sftp.file('/root/scraper/upload_to_bq.py', 'w') as f:
        f.write(new_upload_script)
    sftp.close()
    print("Nuovo script di upload salvato sul VPS. La prossima domenica creerà/userà la tabella price_changes_log.")
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
