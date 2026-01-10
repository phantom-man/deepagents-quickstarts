import psycopg2
import os

DB_PARAMS = {
    "dbname": os.getenv("POSTGRES_DB", "postgres"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "d1204l0723"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
}

try:
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    print("Dropping agent_messages table...")
    cur.execute("DROP TABLE IF EXISTS agent_messages CASCADE;")
    conn.commit()
    print("Table dropped. Next run will recreate it.")
    conn.close()
except Exception as e:
    print(f"Error: {e}")