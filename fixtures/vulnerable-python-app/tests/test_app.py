import sqlite3

from app import get_user


def test_get_user_normal_input():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE users (id INTEGER, username TEXT)")
    db.execute("INSERT INTO users VALUES (1, 'alice')")
    assert get_user(db, "1") == (1, "alice")


def test_get_user_rejects_non_numeric_input():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE users (id INTEGER, username TEXT)")
    db.execute("INSERT INTO users VALUES (1, 'alice')")

    try:
        get_user(db, "not-a-number")
    except ValueError:
        return

    raise AssertionError("invalid user_id should be rejected")
