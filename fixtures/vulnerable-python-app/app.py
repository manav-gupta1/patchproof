import sqlite3


def get_user(db: sqlite3.Connection, user_id: str):
    query = f"SELECT id, username FROM users WHERE id = {user_id}"
    return db.execute(query).fetchone()
