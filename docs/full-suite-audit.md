# Full-suite audit

Pytest return code: 2

The complete suite was executed without suppressing failures. Collection output was also captured separately so remaining failures can be classified as collection/import errors versus runtime tests.

## Collection output

```
   ImportError: cannot import name 'ContextExtractionError' from 'packages.context' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/context/__init__.py)[0m[0m
[31m[1m_______________ ERROR collecting tests/test_semgrep_matching.py ________________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_semgrep_matching.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-live-e2e/patchproof/tests/test_semgrep_matching.py[0m:2: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mverification[39;49;00m[90m [39;49;00m[94mimport[39;49;00m VerificationPlan, VerificationRunner[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'VerificationPlan' from 'packages.verification' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/verification/__init__.py). Did you mean: 'verification'?[0m[0m
[31m[1m_______________ ERROR collecting tests/test_semgrep_verifier.py ________________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_semgrep_verifier.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-semgrep-verifier/patchproof/tests/test_semgrep_verifier.py[0m:5: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96msandbox[39;49;00m[90m [39;49;00m[94mimport[39;49;00m CommandResult, SandboxExecutor, SandboxRequest[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'CommandResult' from 'packages.sandbox' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/sandbox/__init__.py)[0m[0m
[31m[1m___________ ERROR collecting tests/test_verification_semgrep_gate.py ___________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_verification_semgrep_gate.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-semgrep-verifier-fixed/patchproof/tests/test_verification_semgrep_gate.py[0m:5: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96msandbox[39;49;00m[90m [39;49;00m[94mimport[39;49;00m CommandResult, SandboxExecutor, SandboxRequest[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'CommandResult' from 'packages.sandbox' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/sandbox/__init__.py)[0m[0m
[31m[1m___________ ERROR collecting tests/test_verified_publication_e2e.py ____________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_verified_publication_e2e.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-production-db-ci/patchproof/tests/test_verified_publication_e2e.py[0m:4: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mgithub[39;49;00m[04m[96m.[39;49;00m[04m[96me2e[39;49;00m[90m [39;49;00m[94mimport[39;49;00m VerifiedPublicationService[90m[39;49;00m
[1m[31mpackages/github/e2e.py[0m:3: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mgithub[39;49;00m[04m[96m.[39;49;00m[04m[96mpublisher[39;49;00m[90m [39;49;00m[94mimport[39;49;00m PublicationDenied, VerificationEvidence[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'PublicationDenied' from 'packages.github.publisher' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/github/publisher.py)[0m[0m
[31m[1m________________ ERROR collecting tests/test_verified_to_pr.py _________________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_verified_to_pr.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-production-db-ci/patchproof/tests/test_verified_to_pr.py[0m:2: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mgithub[39;49;00m[04m[96m.[39;49;00m[04m[96mpublisher[39;49;00m[90m [39;49;00m[94mimport[39;49;00m GitHubPublisher, VerificationEvidence[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'VerificationEvidence' from 'packages.github.publisher' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/github/publisher.py)[0m[0m
[31m[1m________________ ERROR collecting tests/test_vertical_slice.py _________________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_vertical_slice.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-production-db-ci/patchproof/tests/test_vertical_slice.py[0m:6: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mremediation[39;49;00m[04m[96m.[39;49;00m[04m[96mvertical_slice[39;49;00m[90m [39;49;00m[94mimport[39;49;00m VerticalSlice[90m[39;49;00m
[1m[31mpackages/remediation/vertical_slice.py[0m:10: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mexecution[39;49;00m[04m[96m.[39;49;00m[04m[96mrunner[39;49;00m[90m [39;49;00m[94mimport[39;49;00m LocalExecutionRunner[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'LocalExecutionRunner' from 'packages.execution.runner' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/execution/runner.py)[0m[0m
[31m[1m________________ ERROR collecting tests/test_worker_and_sql.py _________________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_worker_and_sql.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-worker-5steps/patchproof/tests/test_worker_and_sql.py[0m:5: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96morchestration[39;49;00m[04m[96m.[39;49;00m[04m[96mremediation[39;49;00m[90m [39;49;00m[94mimport[39;49;00m InMemoryEvidenceSink, RemediationOrchestrator[90m[39;49;00m
[1m[31mpackages/orchestration/remediation.py[0m:8: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mpatching[39;49;00m[90m [39;49;00m[94mimport[39;49;00m PatchEngine, PatchProposal[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'PatchEngine' from 'packages.patching' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/patching/__init__.py)[0m[0m
[33m=============================== warnings summary ===============================[0m
packages/evidence/execution.py:14
  /mnt/data/patchproof-full-suite-audit/patchproof/packages/evidence/execution.py:14: PytestCollectionWarning: cannot collect test class 'TestResult' because it has a __init__ constructor (from: tests/test_execution_evidence.py)
    @dataclass(frozen=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
[36m[1m=========================== short test summary info ============================[0m
[31mERROR[0m fixtures/real-python-sql/tests/test_app.py
[31mERROR[0m fixtures/sql_injection/tests -   File "/mnt/data/patchproof-full-suite-audit/patchproof/fixtures/sql_injection/tests/conftest.py", line 1
    import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parents[1]))\n
               ^
SyntaxError: unexpected character after line continuation character
[31mERROR[0m fixtures/vulnerable-python-app/tests/test_app.py
[31mERROR[0m tests/test_analyst_service.py
[31mERROR[0m tests/test_celery.py
[31mERROR[0m tests/test_durable_verification.py
[31mERROR[0m tests/test_e2e_fixture.py
[31mERROR[0m tests/test_evidence_bundle.py
[31mERROR[0m tests/test_exploit.py
[31mERROR[0m tests/test_github_publisher.py
[31mERROR[0m tests/test_github_verified_gate.py
[31mERROR[0m tests/test_infra.py
[31mERROR[0m tests/test_orchestration.py
[31mERROR[0m tests/test_patch_protocol.py
[31mERROR[0m tests/test_pipeline.py
[31mERROR[0m tests/test_pipeline_sandbox_integration.py
[31mERROR[0m tests/test_real_execution_pipeline.py
[31mERROR[0m tests/test_repository.py
[31mERROR[0m tests/test_semgrep_matching.py
[31mERROR[0m tests/test_semgrep_verifier.py
[31mERROR[0m tests/test_verification_semgrep_gate.py
[31mERROR[0m tests/test_verified_publication_e2e.py
[31mERROR[0m tests/test_verified_to_pr.py
[31mERROR[0m tests/test_vertical_slice.py
[31mERROR[0m tests/test_worker_and_sql.py
!!!!!!!!!!!!!!!!!!! Interrupted: 25 errors during collection !!!!!!!!!!!!!!!!!!!
[31m[32m264 tests collected[0m, [31m25 errors[0m[31m in 0.77s[0m[0m
Spreadsheet runtime warmup failed during python startup
Traceback (most recent call last):
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/patches/warm_spreadsheet_runtime_on_startup.py", line 26, in warm_spreadsheet_runtime_on_startup
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/spreadsheet_warmup.py", line 785, in warm_spreadsheet_runtime
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/spreadsheet_warmup.py", line 720, in _warm_feature_flows
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/spreadsheet_warmup.py", line 704, in _warm_collaboration_flows
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/generated/interface/models.py", line 32317, in hydrate_crdt_from_proto
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/rpc/remote.py", line 749, in __call__
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/rpc/client.py", line 150, in call
artifact_tool.rpc.client.RemoteError: hydrateCrdtFromProto requires an empty collaborative document.

```

## Full run output

```
[31mE   ImportError: cannot import name 'ContextExtractionError' from 'packages.context' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/context/__init__.py)[0m[0m
[31m[1m_______________ ERROR collecting tests/test_semgrep_matching.py ________________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_semgrep_matching.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-live-e2e/patchproof/tests/test_semgrep_matching.py[0m:2: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mverification[39;49;00m[90m [39;49;00m[94mimport[39;49;00m VerificationPlan, VerificationRunner[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'VerificationPlan' from 'packages.verification' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/verification/__init__.py). Did you mean: 'verification'?[0m[0m
[31m[1m_______________ ERROR collecting tests/test_semgrep_verifier.py ________________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_semgrep_verifier.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-semgrep-verifier/patchproof/tests/test_semgrep_verifier.py[0m:5: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96msandbox[39;49;00m[90m [39;49;00m[94mimport[39;49;00m CommandResult, SandboxExecutor, SandboxRequest[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'CommandResult' from 'packages.sandbox' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/sandbox/__init__.py)[0m[0m
[31m[1m___________ ERROR collecting tests/test_verification_semgrep_gate.py ___________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_verification_semgrep_gate.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-semgrep-verifier-fixed/patchproof/tests/test_verification_semgrep_gate.py[0m:5: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96msandbox[39;49;00m[90m [39;49;00m[94mimport[39;49;00m CommandResult, SandboxExecutor, SandboxRequest[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'CommandResult' from 'packages.sandbox' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/sandbox/__init__.py)[0m[0m
[31m[1m___________ ERROR collecting tests/test_verified_publication_e2e.py ____________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_verified_publication_e2e.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-production-db-ci/patchproof/tests/test_verified_publication_e2e.py[0m:4: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mgithub[39;49;00m[04m[96m.[39;49;00m[04m[96me2e[39;49;00m[90m [39;49;00m[94mimport[39;49;00m VerifiedPublicationService[90m[39;49;00m
[1m[31mpackages/github/e2e.py[0m:3: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mgithub[39;49;00m[04m[96m.[39;49;00m[04m[96mpublisher[39;49;00m[90m [39;49;00m[94mimport[39;49;00m PublicationDenied, VerificationEvidence[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'PublicationDenied' from 'packages.github.publisher' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/github/publisher.py)[0m[0m
[31m[1m________________ ERROR collecting tests/test_verified_to_pr.py _________________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_verified_to_pr.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-production-db-ci/patchproof/tests/test_verified_to_pr.py[0m:2: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mgithub[39;49;00m[04m[96m.[39;49;00m[04m[96mpublisher[39;49;00m[90m [39;49;00m[94mimport[39;49;00m GitHubPublisher, VerificationEvidence[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'VerificationEvidence' from 'packages.github.publisher' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/github/publisher.py)[0m[0m
[31m[1m________________ ERROR collecting tests/test_vertical_slice.py _________________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_vertical_slice.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-production-db-ci/patchproof/tests/test_vertical_slice.py[0m:6: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mremediation[39;49;00m[04m[96m.[39;49;00m[04m[96mvertical_slice[39;49;00m[90m [39;49;00m[94mimport[39;49;00m VerticalSlice[90m[39;49;00m
[1m[31mpackages/remediation/vertical_slice.py[0m:10: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mexecution[39;49;00m[04m[96m.[39;49;00m[04m[96mrunner[39;49;00m[90m [39;49;00m[94mimport[39;49;00m LocalExecutionRunner[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'LocalExecutionRunner' from 'packages.execution.runner' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/execution/runner.py)[0m[0m
[31m[1m________________ ERROR collecting tests/test_worker_and_sql.py _________________[0m
[31mImportError while importing test module '/mnt/data/patchproof-full-suite-audit/patchproof/tests/test_worker_and_sql.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
[1m[31m/usr/lib/python3.13/importlib/__init__.py[0m:88: in import_module
    [0m[94mreturn[39;49;00m _bootstrap._gcd_import(name[level:], package, level)[90m[39;49;00m
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^[90m[39;49;00m
[1m[31m../../patchproof-worker-5steps/patchproof/tests/test_worker_and_sql.py[0m:5: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96morchestration[39;49;00m[04m[96m.[39;49;00m[04m[96mremediation[39;49;00m[90m [39;49;00m[94mimport[39;49;00m InMemoryEvidenceSink, RemediationOrchestrator[90m[39;49;00m
[1m[31mpackages/orchestration/remediation.py[0m:8: in <module>
    [0m[94mfrom[39;49;00m[90m [39;49;00m[04m[96mpackages[39;49;00m[04m[96m.[39;49;00m[04m[96mpatching[39;49;00m[90m [39;49;00m[94mimport[39;49;00m PatchEngine, PatchProposal[90m[39;49;00m
[1m[31mE   ImportError: cannot import name 'PatchEngine' from 'packages.patching' (/mnt/data/patchproof-full-suite-audit/patchproof/packages/patching/__init__.py)[0m[0m
[33m=============================== warnings summary ===============================[0m
packages/evidence/execution.py:14
  /mnt/data/patchproof-full-suite-audit/patchproof/packages/evidence/execution.py:14: PytestCollectionWarning: cannot collect test class 'TestResult' because it has a __init__ constructor (from: tests/test_execution_evidence.py)
    @dataclass(frozen=True)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
[36m[1m=========================== short test summary info ============================[0m
[31mERROR[0m fixtures/real-python-sql/tests/test_app.py
[31mERROR[0m fixtures/sql_injection/tests -   File "/mnt/data/patchproof-full-suite-audit/patchproof/fixtures/sql_injection/tests/conftest.py", line 1
    import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parents[1]))\n
               ^
SyntaxError: unexpected character after line continuation character
[31mERROR[0m fixtures/vulnerable-python-app/tests/test_app.py
[31mERROR[0m tests/test_analyst_service.py
[31mERROR[0m tests/test_celery.py
[31mERROR[0m tests/test_durable_verification.py
[31mERROR[0m tests/test_e2e_fixture.py
[31mERROR[0m tests/test_evidence_bundle.py
[31mERROR[0m tests/test_exploit.py
[31mERROR[0m tests/test_github_publisher.py
[31mERROR[0m tests/test_github_verified_gate.py
[31mERROR[0m tests/test_infra.py
[31mERROR[0m tests/test_orchestration.py
[31mERROR[0m tests/test_patch_protocol.py
[31mERROR[0m tests/test_pipeline.py
[31mERROR[0m tests/test_pipeline_sandbox_integration.py
[31mERROR[0m tests/test_real_execution_pipeline.py
[31mERROR[0m tests/test_repository.py
[31mERROR[0m tests/test_semgrep_matching.py
[31mERROR[0m tests/test_semgrep_verifier.py
[31mERROR[0m tests/test_verification_semgrep_gate.py
[31mERROR[0m tests/test_verified_publication_e2e.py
[31mERROR[0m tests/test_verified_to_pr.py
[31mERROR[0m tests/test_vertical_slice.py
[31mERROR[0m tests/test_worker_and_sql.py
!!!!!!!!!!!!!!!!!!! Interrupted: 25 errors during collection !!!!!!!!!!!!!!!!!!!
[31m[33m1 warning[0m, [31m[1m25 errors[0m[31m in 0.78s[0m[0m
Spreadsheet runtime warmup failed during python startup
Traceback (most recent call last):
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/patches/warm_spreadsheet_runtime_on_startup.py", line 26, in warm_spreadsheet_runtime_on_startup
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/spreadsheet_warmup.py", line 785, in warm_spreadsheet_runtime
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/spreadsheet_warmup.py", line 720, in _warm_feature_flows
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/spreadsheet_warmup.py", line 704, in _warm_collaboration_flows
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/generated/interface/models.py", line 32317, in hydrate_crdt_from_proto
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/rpc/remote.py", line 749, in __call__
  File "/tmp/tmp.L2TH2Y5coc/artifact_tool_v2-2.8.22/artifact_tool/rpc/client.py", line 150, in call
artifact_tool.rpc.client.RemoteError: hydrateCrdtFromProto requires an empty collaborative document.

```
