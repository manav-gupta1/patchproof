from app import lookup_user

rows = lookup_user("' OR '1'='1")
if rows:
    raise SystemExit(0)
print("patched exploit blocked")
raise SystemExit(1)
