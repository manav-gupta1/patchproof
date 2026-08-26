from pathlib import Path

class SQLInjectionFixturePatcher:
    def propose(self, repository: Path, finding: dict) -> dict:
        path = repository / "app/db.py"
        original = path.read_text()
        old = '    query = "SELECT id, name FROM users WHERE name = \'" + username + "\'"\n    return conn.execute(query).fetchall()'
        new = '    query = "SELECT id, name FROM users WHERE name = ?"\n    return conn.execute(query, (username,)).fetchall()'
        patched = original.replace(old, new)
        if patched == original:
            raise ValueError("fixture patch did not match expected vulnerable code")
        path.write_text(patched)
        return {"changed_files": ["app/db.py"], "diff": "parameterized SQL query"}
