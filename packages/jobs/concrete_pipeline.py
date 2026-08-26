from __future__ import annotations


class ConcretePipeline:
    def __init__(self, scanner, context, router, patcher, sandbox, verifier):
        self.scanner = scanner
        self.context = context
        self.router = router
        self.patcher = patcher
        self.sandbox = sandbox
        self.verifier = verifier

    def scan(self, workspace):
        return self.scanner.scan(workspace)

    def analyze(self, workspace, findings):
        if not findings:
            raise ValueError("no security finding supplied")
        finding = findings[0]
        triage = self.router.triage_finding(finding)
        ctx = self.context.extract(workspace, finding)
        return {"finding": finding, "triage": triage, "context": ctx}

    def patch(self, workspace, proposal):
        return self.patcher.apply(workspace, self.router.generate_patch(
            proposal["context"], proposal["finding"]
        ))

    def verify(self, workspace, findings, proposal, patch_result):
        return self.verifier(
            workspace=workspace,
            findings=findings,
            proposal=proposal,
            patch_result=patch_result,
            sandbox=self.sandbox,
        )
