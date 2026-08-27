from __future__ import annotations
from packages.jobs.state import JobState


class RemediationOrchestrator:
    def __init__(
        self, store, state_machine,
        clone, scan, analyze, patch, verify, evidence, github,
        state=None, check_runs=None, policy_loader=None, policy_evaluator=None,
    ):
        from packages.policy.loader import PolicyLoader
        from packages.policy.evaluator import PolicyEvaluator

        self.store = store
        self.state_machine = state_machine
        self.clone = clone
        self.scan = scan
        self.analyze = analyze
        self.patch = patch
        self.verify = verify
        self.evidence = evidence
        self.github = github
        self.state = state or state_machine
        self.check_runs = check_runs
        self.policy_loader = policy_loader or PolicyLoader()
        self.policy_evaluator = policy_evaluator or PolicyEvaluator()

    def _transition(self, job_id, target, message):
        if not self.state:
            return None
        # The orchestrator owns the durable JobRecord; attach that record to
        # the state machine on first use so transitions are not lost in a
        # second, disconnected in-memory state store.
        if job_id not in self.state._jobs:
            job = self.store.get(job_id)
            if job is None:
                raise KeyError(job_id)
            self.state.create(
                job_id,
                repository=job.repository,
                delivery_id=job.delivery_id,
                commit_sha=job.commit_sha,
                state=job.state,
                attempt=getattr(job, "attempt", 1),
                error=getattr(job, "error", None),
                installation_id=getattr(job, "installation_id", None),
                check_run_id=getattr(job, "check_run_id", None),
                target_branch=getattr(job, "target_branch", None),
                policy_decision=getattr(job, "policy_decision", None),
            )
        from_state = self.state._jobs[job_id].state.value
        record = self.state.transition(self.state._jobs[job_id], target.value)
        if hasattr(self.store, "record_transition"):
            try:
                self.store.record_transition(job_id, from_state, target.value, message)
            except Exception:
                pass
        job = self.store.get(job_id)
        if job is not None:
            job.state = record.state
            job.error = record.error
            self.store.update(job)
        return record

    def run(self, job_id):
        workspace_obj = None
        job = None
        current_stage = "initialization"
        finding_decision = None
        try:
            job = self.store.get(job_id)
            if job is None:
                raise KeyError(f"job {job_id} not found in store")

            # Report check run in_progress lifecycle
            if self.check_runs:
                try:
                    cr_id = getattr(job, "check_run_id", None)
                    cr_ref = self.check_runs.report_in_progress(job, check_run_id=cr_id)
                    if cr_ref and hasattr(cr_ref, "id") and not cr_id:
                        job.check_run_id = cr_ref.id
                        if hasattr(self.store, "save_check_run_id"):
                            self.store.save_check_run_id(job_id, cr_ref.id)
                except Exception:
                    pass

            current_stage = "checkout"
            workspace_res = self.clone(job.repository, job.commit_sha)
            if hasattr(workspace_res, "path"):
                workspace_obj = workspace_res
                workspace = str(workspace_res.path)
            else:
                workspace = str(workspace_res)

            # Load and evaluate repository security policy (store configured policy or workspace .patchproof.yml)
            current_stage = "policy_evaluation"
            import yaml
            policy = None
            if hasattr(self.store, "get_repository_policy") and getattr(job, "repository", None):
                store_policy = self.store.get_repository_policy(job.repository)
                if store_policy:
                    if "policy" in store_policy:
                        policy = self.policy_loader.parse_yaml(yaml.dump(store_policy), source="store")
                    else:
                        policy = self.policy_loader.parse_yaml(yaml.dump({"version": "1.0", "policy": store_policy}), source="store")
            if policy is None or policy.source == "default":
                workspace_policy = self.policy_loader.load_from_workspace(workspace)
                if workspace_policy.source != "default" or policy is None:
                    policy = workspace_policy

            target_branch = getattr(job, "target_branch", None)
            event_type = getattr(job, "event_type", None)

            # Gate 1: Event and Branch Evaluation
            event_decision = self.policy_evaluator.evaluate_event(
                policy, event_type=event_type, branch=target_branch
            )
            if not event_decision.allowed:
                if hasattr(self.store, "save_policy_decision"):
                    self.store.save_policy_decision(job_id, event_decision.to_dict())
                self._transition(job_id, JobState.FAILED, event_decision.reason)
                if self.check_runs:
                    try:
                        self.check_runs.report_policy_block(
                            job,
                            check_run_id=getattr(job, "check_run_id", None),
                            decision=event_decision,
                        )
                    except Exception:
                        pass
                return {
                    "state": JobState.FAILED.value,
                    "job_id": job_id,
                    "verified": False,
                    "error": event_decision.reason,
                    "policy": event_decision.to_dict(),
                }

            self._transition(job_id, JobState.SCANNING, "source checkout complete")
            current_stage = "scanning"
            findings = self.scan(workspace)

            # Gate 2: Finding and Rule Evaluation
            current_stage = "policy_rule_evaluation"
            target_finding = findings[0] if findings else {"rule_id": "security-issue", "severity": "medium"}
            finding_decision = self.policy_evaluator.evaluate_finding(
                policy, target_finding, event_type=event_type, branch=target_branch
            )
            if hasattr(self.store, "save_policy_decision"):
                self.store.save_policy_decision(job_id, finding_decision.to_dict())

            if not finding_decision.allowed:
                self._transition(job_id, JobState.FAILED, finding_decision.reason)
                if self.check_runs:
                    try:
                        self.check_runs.report_policy_block(
                            job,
                            check_run_id=getattr(job, "check_run_id", None),
                            decision=finding_decision,
                        )
                    except Exception:
                        pass
                return {
                    "state": JobState.FAILED.value,
                    "job_id": job_id,
                    "verified": False,
                    "error": finding_decision.reason,
                    "policy": finding_decision.to_dict(),
                }

            self._transition(job_id, JobState.ANALYZING, "security findings collected")
            current_stage = "analyzing"
            proposal = self.analyze(workspace, findings)

            self._transition(job_id, JobState.PATCHING, "remediation proposal generated")
            current_stage = "patching"
            patch_result = self.patch(workspace, proposal)

            self._transition(job_id, JobState.VERIFYING, "patch applied; verification started")
            current_stage = "verification"
            verification = self.verify(
                workspace=workspace,
                findings=findings,
                proposal=proposal,
                patch_result=patch_result,
            )

            if not getattr(verification, "verified", False):
                self._transition(job_id, JobState.FAILED, "verification failed")
                if self.check_runs:
                    try:
                        self.check_runs.report_failure(
                            job,
                            check_run_id=getattr(job, "check_run_id", None),
                            stage="verification_gate",
                            error="verification failed",
                            verification=verification,
                        )
                    except Exception:
                        pass
                return {
                    "state": JobState.FAILED.value,
                    "job_id": job_id,
                    "verified": False,
                    "error": "verification failed",
                    "policy": finding_decision.to_dict() if finding_decision else None,
                }

            self._transition(job_id, JobState.VERIFIED, "verification passed")
            current_stage = "evidence_signing"
            try:
                try:
                    evidence = self.evidence(
                        job, findings, proposal, patch_result, verification, policy_decision=finding_decision
                    )
                except TypeError:
                    evidence = self.evidence(job, findings, proposal, patch_result, verification)

                if not isinstance(evidence, dict):
                    raise ValueError("evidence must be a dictionary")
                if not evidence.get("signature"):
                    from packages.signing import Ed25519EvidenceSigner
                    evidence = Ed25519EvidenceSigner().sign(evidence)
            except Exception as sign_err:
                self._transition(job_id, JobState.FAILED, f"evidence signing failed: {sign_err}")
                if self.check_runs:
                    try:
                        self.check_runs.report_failure(
                            job,
                            check_run_id=getattr(job, "check_run_id", None),
                            stage="evidence_signing",
                            error=f"evidence signing failed: {sign_err}",
                            verification=verification,
                        )
                    except Exception:
                        pass
                return {
                    "state": JobState.FAILED.value,
                    "job_id": job_id,
                    "verified": False,
                    "error": f"evidence signing failed: {sign_err}",
                    "policy": finding_decision.to_dict() if finding_decision else None,
                }

            if not evidence.get("signature"):
                self._transition(job_id, JobState.FAILED, "evidence signing failed: missing signature")
                if self.check_runs:
                    try:
                        self.check_runs.report_failure(
                            job,
                            check_run_id=getattr(job, "check_run_id", None),
                            stage="evidence_signing",
                            error="evidence signing failed: missing signature",
                            verification=verification,
                        )
                    except Exception:
                        pass
                return {
                    "state": JobState.FAILED.value,
                    "job_id": job_id,
                    "verified": False,
                    "error": "evidence signing failed: missing signature",
                    "policy": finding_decision.to_dict() if finding_decision else None,
                }

            if hasattr(self.store, "save_evidence") and evidence is not None:
                try:
                    self.store.save_evidence(job_id, evidence)
                except Exception:
                    pass

            pr = None
            if finding_decision.auto_create_pr:
                current_stage = "publication"
                # Prevent publication based on stale verification evidence
                if getattr(job, "is_stale", False) and getattr(job, "verified_sha", None) != getattr(job, "current_head_sha", job.commit_sha):
                    self._transition(job_id, JobState.FAILED, "Cannot publish PR based on stale verification evidence")
                    return {
                        "state": JobState.FAILED.value,
                        "job_id": job_id,
                        "verified": False,
                        "error": "Cannot publish PR based on stale verification evidence",
                        "policy": finding_decision.to_dict() if finding_decision else None,
                    }

                pr = self.github.publish_verified(
                    job=job, patch_result=patch_result, evidence=evidence
                )
                if hasattr(self.store, "save_pr") and pr is not None:
                    try:
                        self.store.save_pr(job_id, pr)
                    except Exception:
                        pass

                if isinstance(pr, dict):
                    job.pr_number = pr.get("number")
                    job.pr_url = pr.get("url") or pr.get("html_url")
                    job.remediation_branch = pr.get("branch") or pr.get("head_branch")
                    job.current_head_sha = getattr(job, "commit_sha", None)
                    job.verified_sha = getattr(job, "commit_sha", None)
                    job.is_stale = False

                self._transition(job_id, JobState.PR_CREATED, "verified remediation PR created")
            else:
                self._transition(job_id, JobState.VERIFIED, "verified remediation complete (PR publication disabled by policy)")

            # Report check run completion success
            if self.check_runs:
                try:
                    self.check_runs.report_success(
                        job,
                        check_run_id=getattr(job, "check_run_id", None),
                        pr=pr,
                        evidence=evidence,
                        verification=verification,
                    )
                except Exception:
                    pass

            final_state = JobState.PR_CREATED.value if finding_decision.auto_create_pr else JobState.VERIFIED.value
            return {
                "state": final_state,
                "job_id": job_id,
                "verified": True,
                "pr": pr,
                "evidence": evidence,
                "policy": finding_decision.to_dict() if finding_decision else None,
            }

        except Exception as exc:
            from packages.github.auth import sanitize_secret_text
            sanitized_err = sanitize_secret_text(str(exc))
            try:
                self._transition(job_id, JobState.FAILED, sanitized_err)
            except Exception:
                pass
            if self.check_runs and job:
                try:
                    self.check_runs.report_failure(
                        job,
                        check_run_id=getattr(job, "check_run_id", None),
                        stage=current_stage,
                        error=sanitized_err,
                    )
                except Exception:
                    pass
            return {
                "state": JobState.FAILED.value,
                "job_id": job_id,
                "verified": False,
                "error": sanitized_err,
                "policy": finding_decision.to_dict() if finding_decision else None,
            }
        finally:
            if workspace_obj is not None and hasattr(workspace_obj, "cleanup"):
                workspace_obj.cleanup()
