import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import lookup_user


def test_normal_lookup():
    assert lookup_user("alice") == [("alice",)]
