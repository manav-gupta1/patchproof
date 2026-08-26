import sqlite3
from app.db import get_user


def test_sql_injection_is_blocked():
    conn = sqlite3.connect(":memory:")
    conn.execute("create table users (id integer, name text)")
    conn.execute("insert into users values (1, 'alice')")
    conn.commit()

    # A successful exploit returns all rows. The patched parameterized query
    # treats the payload as literal data and returns no rows.
    payload = "' OR '1'='1"
    rows = get_user(conn, payload)
    assert rows == []
