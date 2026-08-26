import json
import subprocess
from pathlib import Path
import pytest

from packages.patching.models import FindingContext, PatchCandidate, PatchDecision, PatchOperation
from packages.patching.protocol import build_patch_prompt, parse_patch_response
from packages.patching.providers import (
    HttpLLMError,
    StructuredPatchProvider,
    RobustLLMPatchProvider,
    OpenAIChatClient,
    AnthropicChatClient,
)
from packages.patching.provider import RuleBasedPatchModel, get_patch_provider
from packages.jobs.pipeline_factory import create_concrete_remediation_orchestrator
from packages.jobs.state import JobRecord, JobState
from packages.jobs.store import InMemoryJobStore


def sample_context() -> FindingContext:
    return FindingContext(
        fingerprint="fp-sqli-001",
        rule_id="python.sql-injection",
        path="app.py",
        start_line=4,
        end_line=4,
        severity="HIGH",
        source_excerpt="4:     query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n5:     return query",
        related_symbols=["def query_user(user_input: str):"],
        project_files=["app.py", "tests/test_app.py"],
    )


class MockChatClient:
    def __init__(self, response_text: str | Exception):
        self.response_text = response_text
        self.recorded_calls = []

    async def complete(self, *, system: str, user: str) -> str:
        self.recorded_calls.append({"system": system, "user": user})
        if isinstance(self.response_text, Exception):
            raise self.response_text
        return self.response_text


@pytest.mark.asyncio
async def test_valid_structured_llm_response():
    """Test parsing a valid structured JSON patch response from an LLM."""
    valid_json = json.dumps({
        "decision": "patch",
        "title": "fix(security): parameterize SQL query",
        "explanation": "Replaced f-string interpolation with safe parameterized queries.",
        "confidence": 0.98,
        "operations": [
            {
                "file": "app.py",
                "old_text": 'query = f"SELECT * FROM users WHERE username = \'{user_input}\'"',
                "new_text": 'query = ("SELECT * FROM users WHERE username = %s", (user_input,))',
                "reason": "Parameterize input",
            }
        ],
        "changed_files": ["app.py"],
        "expected_verification_intent": "Eliminates python.sql-injection vulnerability",
        "patch_id": "patch-openai-001",
    })

    client = MockChatClient(valid_json)
    provider = StructuredPatchProvider(client=client, provider="openai", model_name="gpt-4o")
    candidate = await provider.propose(sample_context())

    assert candidate.decision == PatchDecision.PATCH
    assert candidate.title == "fix(security): parameterize SQL query"
    assert candidate.confidence == 0.98
    assert len(candidate.operations) == 1
    assert candidate.operations[0].file == "app.py"
    assert candidate.model_provider == "openai"
    assert candidate.model_name == "gpt-4o"


@pytest.mark.asyncio
async def test_malformed_json_response_raises_error():
    """Test that malformed/non-JSON LLM responses are rejected."""
    client = MockChatClient("Not a valid JSON response from model")
    provider = StructuredPatchProvider(client=client, provider="openai", model_name="gpt-4o")

    with pytest.raises(ValueError, match="not valid JSON"):
        await provider.propose(sample_context())


@pytest.mark.asyncio
async def test_path_traversal_in_patch_is_rejected():
    """Test that path traversal in operations or changed_files is rejected."""
    traversal_json = json.dumps({
        "decision": "patch",
        "title": "malicious patch",
        "explanation": "attempts directory traversal",
        "confidence": 0.5,
        "operations": [
            {
                "file": "../../etc/passwd",
                "old_text": "root:x:0:0",
                "new_text": "root:x:0:0:hacked",
            }
        ],
        "changed_files": ["../../etc/passwd"],
        "patch_id": "patch-evil-001",
    })

    client = MockChatClient(traversal_json)
    provider = StructuredPatchProvider(client=client, provider="openai", model_name="gpt-4o")

    with pytest.raises(ValueError, match="Path traversal"):
        await provider.propose(sample_context())


@pytest.mark.asyncio
async def test_absolute_path_in_patch_is_rejected():
    """Test that absolute paths in patch operations are rejected."""
    abs_path_json = json.dumps({
        "decision": "patch",
        "title": "absolute path patch",
        "explanation": "attempts absolute path",
        "confidence": 0.5,
        "operations": [
            {
                "file": "/etc/shadow",
                "old_text": "old",
                "new_text": "new",
            }
        ],
        "changed_files": ["/etc/shadow"],
        "patch_id": "patch-abs-001",
    })

    client = MockChatClient(abs_path_json)
    provider = StructuredPatchProvider(client=client, provider="openai", model_name="gpt-4o")

    with pytest.raises(ValueError, match="Absolute file paths are forbidden"):
        await provider.propose(sample_context())


@pytest.mark.asyncio
async def test_empty_old_text_in_operation_is_rejected():
    """Test that an operation with empty old_text is rejected."""
    empty_old_json = json.dumps({
        "decision": "patch",
        "title": "ambiguous patch",
        "explanation": "empty old text",
        "confidence": 0.5,
        "operations": [
            {
                "file": "app.py",
                "old_text": "",
                "new_text": "injected code",
            }
        ],
        "changed_files": ["app.py"],
        "patch_id": "patch-empty-old",
    })

    client = MockChatClient(empty_old_json)
    provider = StructuredPatchProvider(client=client, provider="openai", model_name="gpt-4o")

    with pytest.raises(ValueError, match="old_text cannot be empty"):
        await provider.propose(sample_context())


@pytest.mark.asyncio
async def test_oversized_response_is_rejected():
    """Test that oversized LLM responses exceeding size limit are rejected."""
    oversized = "a" * (3 * 1024 * 1024)  # 3MB
    client = MockChatClient(oversized)
    provider = StructuredPatchProvider(client=client, provider="openai", model_name="gpt-4o")

    with pytest.raises(ValueError, match="exceeds maximum size limit"):
        await provider.propose(sample_context())


@pytest.mark.asyncio
async def test_robust_provider_falls_back_on_llm_failure():
    """Test that RobustLLMPatchProvider safely falls back to RuleBasedPatchModel on LLM failure."""
    failing_client = MockChatClient(RuntimeError("OpenAI API rate limit exceeded (HTTP 429)"))
    primary = StructuredPatchProvider(client=failing_client, provider="openai", model_name="gpt-4o")
    fallback = RuleBasedPatchModel()

    robust_provider = RobustLLMPatchProvider(
        primary=primary,
        fallback=fallback,
        fallback_on_error=True,
    )

    candidate = await robust_provider.propose(sample_context())

    assert candidate.decision == PatchDecision.PATCH
    assert len(candidate.operations) == 1
    assert "LLM generation failed" in candidate.rationale
    assert candidate.model_provider == "patchproof-rule-engine"


@pytest.mark.asyncio
async def test_missing_api_keys_raises_clear_error(monkeypatch):
    """Test that OpenAIChatClient and AnthropicChatClient require API keys."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(HttpLLMError, match="OPENAI_API_KEY is required"):
        OpenAIChatClient(api_key=None)

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(HttpLLMError, match="ANTHROPIC_API_KEY is required"):
        AnthropicChatClient(api_key=None)


def test_get_patch_provider_factory_env_config(monkeypatch):
    """Test get_patch_provider factory respecting environment variables."""
    # When no keys configured -> RuleBasedPatchModel
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = get_patch_provider()
    assert isinstance(provider, RuleBasedPatchModel)

    # When OPENAI_API_KEY configured
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-12345")
    monkeypatch.setenv("PATCHPROOF_LLM_PROVIDER", "openai")
    monkeypatch.setenv("PATCHPROOF_LLM_MODEL", "gpt-4o-mini")
    openai_provider = get_patch_provider()
    assert isinstance(openai_provider, RobustLLMPatchProvider)
    assert openai_provider.primary.provider == "openai"
    assert openai_provider.primary.model_name == "gpt-4o-mini"

    # When ANTHROPIC_API_KEY configured
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-67890")
    monkeypatch.setenv("PATCHPROOF_LLM_PROVIDER", "anthropic")
    anthropic_provider = get_patch_provider()
    assert isinstance(anthropic_provider, RobustLLMPatchProvider)
    assert anthropic_provider.primary.provider == "anthropic"


def test_end_to_end_orchestrator_with_llm_generated_patch(tmp_path):
    """Test full remediation orchestration with an LLM-generated patch."""
    source_repo = tmp_path / "llm_app_repo"
    source_repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=source_repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test Bot"], cwd=source_repo, check=True)
    subprocess.run(["git", "config", "user.email", "bot@test.local"], cwd=source_repo, check=True)
    (source_repo / "app.py").write_text(
        "def query_user(user_input: str):\n"
        "    query = f\"SELECT * FROM users WHERE username = '{user_input}'\"\n"
        "    return query\n"
    )
    subprocess.run(["git", "add", "."], cwd=source_repo, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@test.local", "commit", "-qm", "initial"],
        cwd=source_repo,
        check=True,
    )
    head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_repo, text=True).strip()

    valid_llm_response = json.dumps({
        "decision": "patch",
        "title": "fix(security): parameterized query fix from LLM",
        "explanation": "Applied parameterized SQL query safely.",
        "confidence": 0.99,
        "operations": [
            {
                "file": "app.py",
                "old_text": 'query = f"SELECT * FROM users WHERE username = \'{user_input}\'"',
                "new_text": 'query = ("SELECT * FROM users WHERE username = %s", (user_input,))',
                "reason": "Use parameter substitution",
            }
        ],
        "changed_files": ["app.py"],
        "expected_verification_intent": "Vulnerability eliminated",
        "patch_id": "patch-llm-e2e-001",
    })

    client = MockChatClient(valid_llm_response)
    llm_provider = StructuredPatchProvider(client=client, provider="openai", model_name="gpt-4o")

    store = InMemoryJobStore()
    job = JobRecord(
        job_id="job-llm-e2e-001",
        repository=str(source_repo),
        delivery_id="deliv-llm-e2e",
        commit_sha=head_sha,
    )
    store.create(job)

    orchestrator = create_concrete_remediation_orchestrator(
        store=store,
        patch_provider=llm_provider,
    )

    result = orchestrator.run(job.job_id)

    assert result["state"] == JobState.PR_CREATED.value
    assert result["verified"] is True
    assert result["job_id"] == "job-llm-e2e-001"
    assert result["pr"]["number"] == 1
    assert "patchproof" in result["pr"]["branch"]
