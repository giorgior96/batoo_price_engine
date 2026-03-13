import json
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

def prepare_and_upload():
    print("1. Caricamento dei dati dal JSON...")
    df = pd.read_json("master_boats_db.json")

    print(f"Trovati {len(df)} record. Preparazione dello schema...")

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

    # Carichiamo prima nella tabella temporanea
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

    print("4. Esecuzione del MERGE per aggiornare lo storico...")
    
    # Assicurati che la tabella principale esista con i campi timestamp e status
    create_main_table_sql = f"""
    CREATE TABLE IF NOT EXISTS `{main_table_ref}` (
        id INT64, builder STRING, model STRING, year_built INT64,
        country STRING, price_eur FLOAT64, length FLOAT64,
        image_url STRING, source STRING, broker STRING,
        url STRING, category STRING, status BOOLEAN,
        first_seen_at TIMESTAMP, updated_at TIMESTAMP
    )
    """
    client.query(create_main_table_sql).result()

    # Se la tabella principale esisteva già senza i campi 'first_seen_at' e 'updated_at',
    # il MERGE potrebbe fallire. Li aggiungiamo se mancano.
    alter_sql = f"""
    ALTER TABLE `{main_table_ref}`
    ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
    """
    try:
        client.query(alter_sql).result()
    except Exception as e:
        pass # Ignoriamo gli errori se le colonne esistono già

    merge_sql = f"""
    MERGE `{main_table_ref}` T
    USING `{temp_table_ref}` S
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
    """

    merge_job = client.query(merge_sql)
    merge_job.result()
    print("Finito! I dati sono stati uniti. Lo storico è mantenuto: le barche non più presenti sono marcate come 'status = FALSE'.")

if __name__ == "__main__":
    prepare_and_upload()
