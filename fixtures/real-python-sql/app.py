import sqlite3

DB = ":memory:"


def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("create table users (name text, role text)")
    conn.execute("insert into users values ('alice', 'user')")
    conn.commit()
    return conn


def lookup_user(conn, name):
    query = "select role from users where name = '%s'" % name
    return conn.execute(query).fetchone()
