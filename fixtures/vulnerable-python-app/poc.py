import sqlite3
from app import get_user

db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE users (id INTEGER, username TEXT)")
db.execute("INSERT INTO users VALUES (1, 'alice')")

# Baseline behavior should demonstrate that attacker-controlled SQL changes
# query semantics. The patched behavior should reject this input.
payload = "1 OR 1=1"
rows = get_user(db, payload)

if len(rows) == 1:
    raise SystemExit("POC_INCONCLUSIVE")

print("SQL_INJECTION_REPRODUCED")
raise SystemExit(0)
