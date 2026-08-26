from app import init_db, lookup_user

def test_normal_lookup():
    conn = init_db()
    assert lookup_user(conn, "alice") == ("user",)

def test_injection_is_blocked():
    conn = init_db()
    malicious = "alice' OR '1'='1"
    assert lookup_user(conn, malicious) is None
