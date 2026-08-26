import sqlite3
from app.db import get_user

def make_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'alice')")
    return conn

def test_normal_lookup():
    assert get_user(make_db(), "alice") == [(1, "alice")]

def test_injection_is_blocked():
    assert get_user(make_db(), "alice' OR '1'='1") == []
