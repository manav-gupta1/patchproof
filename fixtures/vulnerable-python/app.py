import sqlite3


def lookup_user(username: str) -> list[tuple]:
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE users (name TEXT)")
    db.execute("INSERT INTO users VALUES ('alice')")
    # Intentionally vulnerable fixture for the E2E test.
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return db.execute(query).fetchall()
