from pathlib import Path
import os
from packages.persistence.db import Database

def main():
    db=Database(os.environ.get("POSTGRES_DSN"))
    schema=Path(__file__).resolve().parents[1]/"packages/persistence/schema.sql"
    with db.connection() as conn:
        conn.execute(schema.read_text())
    print("PostgreSQL schema: applied")

if __name__=="__main__": main()
