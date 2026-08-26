import sqlite3

def get_user(conn: sqlite3.Connection, username: str):
    query = "SELECT id, name FROM users WHERE name = '" + username + "'"
    return conn.execute(query).fetchall()
