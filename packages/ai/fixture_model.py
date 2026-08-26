from __future__ import annotations
import json

class FixtureSQLInjectionModel:
    def complete(self, *, system: str, user: str) -> str:
        return json.dumps({
            "explanation": "Replace SQL string concatenation with a parameterized query.",
            "diff": """diff --git a/app/db.py b/app/db.py
--- a/app/db.py
+++ b/app/db.py
@@ -1,5 +1,5 @@
 import sqlite3

 def get_user(conn: sqlite3.Connection, username: str):
-    query = "SELECT id, name FROM users WHERE name = '" + username + "'"
-    return conn.execute(query).fetchall()
+    query = "SELECT id, name FROM users WHERE name = ?"
+    return conn.execute(query, (username,)).fetchall()
""",
            "changed_files": ["app/db.py"],
            "tests_to_run": ["python -m pytest -q"],
        })
