class FakeGitHubClient:
    def __init__(self):
        self.prs = []
        self.pull_requests = self.prs
        self.create_calls = 0

    def find_pull_request(self, *, head, base, evidence_sha256):
        for pr in self.prs:
            if pr["head"] == head and pr["base"] == base and pr["evidence_sha256"] == evidence_sha256:
                return pr["result"]
        return None

    def create_pull_request(self, *, title, body, head, base, evidence_sha256):
        self.create_calls += 1
        result = {
            "number": len(self.prs) + 1,
            "url": f"https://github.example/pr/{len(self.prs) + 1}",
            "head_sha": head,
        }
        self.prs.append({
            "head": head,
            "base": base,
            "evidence_sha256": evidence_sha256,
            "result": result,
        })
        return result
