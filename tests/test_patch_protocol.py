import json

import pytest

from packages.patching import FindingContext
from packages.patching.mock_client import StaticChatClient
from packages.patching.protocol import build_patch_prompt, parse_patch_response
from packages.patching.providers import StructuredPatchProvider


def context():
    return FindingContext(
        fingerprint="f1",
        rule_id="python.sql-injection",
        path="app.py",
        start_line=10,
        end_line=12,
        severity="high",
        source_excerpt="10: query = 'select ' + user_input",
        related_symbols=["def find_user():"] ,
        project_files=["app.py", "tests/test_app.py"],
    )


def test_prompt_contains_security_context():
    prompt = build_patch_prompt(context())
    assert "python.sql-injection" in prompt
    assert "app.py" in prompt
    assert "ONLY a JSON object" in prompt


def test_parse_valid_patch():
    raw = json.dumps({
        "decision": "patch",
        "explanation": "Use parameterized SQL.",
        "files": {"app.py": "def x(): pass\n"},
        "changed_files": ["app.py"],
        "model_provider": "test",
        "model_name": "test-model",
        "patch_id": "p1",
    })
    candidate = parse_patch_response(raw, provider="fallback", model_name="fallback")
    assert candidate.decision.value == "patch"
    assert candidate.files["app.py"]


def test_rejects_unknown_fields():
    data = {
        "decision": "no_patch",
        "explanation": "ambiguous",
        "files": {},
        "changed_files": [],
        "model_provider": "test",
        "model_name": "test",
        "patch_id": "p1",
        "execute": "rm -rf /",
    }
    with pytest.raises(ValueError, match="unknown patch fields"):
        parse_patch_response(json.dumps(data), provider="x", model_name="y")


def test_rejects_inconsistent_changed_files():
    data = {
        "decision": "patch",
        "explanation": "fix",
        "files": {"app.py": "x"},
        "changed_files": [],
        "model_provider": "test",
        "model_name": "test",
        "patch_id": "p1",
    }
    with pytest.raises(ValueError, match="changed_files"):
        parse_patch_response(json.dumps(data), provider="x", model_name="y")


@pytest.mark.asyncio
async def test_provider_forces_external_verification():
    raw = json.dumps({
        "decision": "patch",
        "explanation": "safe fix",
        "files": {"app.py": "print('safe')"},
        "changed_files": ["app.py"],
        "model_provider": "unknown",
        "model_name": "unknown",
        "patch_id": "p1",
    })
    client = StaticChatClient(raw)
    provider = StructuredPatchProvider(client, "test-provider", "test-model")

    candidate = await provider.propose(context())

    assert candidate.model_provider == "test-provider"
    assert candidate.model_name == "test-model"
    assert "Verification" in client.calls[0]["system"]
