"use client";

import React, { useState } from "react";
import {
  Check,
  ShieldCheck,
  ShieldAlert,
  FileCode,
  Terminal,
  GitPullRequest,
  Hash,
  Copy,
  Cpu,
  ChevronRight,
  ChevronLeft,
  X,
  AlertTriangle,
  Lock,
  Unlock,
  CheckCircle2,
  XCircle,
  Play,
  RotateCcw,
} from "lucide-react";

type DemoStage = "finding" | "diff" | "sandbox" | "evidence" | "delivery";
type PatchScenario = "unsafe" | "safe";

export function InteractiveDemo() {
  const [activeStage, setActiveStage] = useState<DemoStage>("diff");
  const [scenario, setScenario] = useState<PatchScenario>("safe");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const stages: { id: DemoStage; label: string; icon: React.ReactNode }[] = [
    { id: "finding", label: "01. Alert Ingestion", icon: <FileCode className="w-3.5 h-3.5" /> },
    { id: "diff", label: "02. AST Patch", icon: <Terminal className="w-3.5 h-3.5" /> },
    { id: "sandbox", label: "03. Sandbox Gates", icon: <Cpu className="w-3.5 h-3.5" /> },
    { id: "evidence", label: "04. Cryptographic Proof", icon: <Hash className="w-3.5 h-3.5" /> },
    { id: "delivery", label: "05. Verified PR", icon: <GitPullRequest className="w-3.5 h-3.5" /> },
  ];

  const stageOrder: DemoStage[] = ["finding", "diff", "sandbox", "evidence", "delivery"];
  const currentIndex = stageOrder.indexOf(activeStage);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const nextStage = () => {
    if (currentIndex < stageOrder.length - 1) {
      setActiveStage(stageOrder[currentIndex + 1]);
    }
  };

  const prevStage = () => {
    if (currentIndex > 0) {
      setActiveStage(stageOrder[currentIndex - 1]);
    }
  };

  return (
    <div
      className="border border-border-muted bg-surface-300 rounded-xl overflow-hidden shadow-2xl font-mono text-sm select-none"
      data-testid="interactive-demo"
    >
      {/* ── TOP CONTROL BAR ── */}
      <div className="px-6 py-4 bg-surface-400 border-b border-border-subtle flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
          </div>
          <span className="text-zinc-300 text-xs sm:text-sm">
            engine-simulation // <strong className="text-zinc-100">octocat/auth-service</strong> · security-gate-eval
          </span>
        </div>

        {/* Scenario Toggle */}
        <div className="flex items-center gap-3">
          <span className="text-xs text-zinc-400 hidden sm:inline">Scenario:</span>
          <div className="inline-flex p-1 rounded-lg bg-zinc-900 border border-zinc-800 text-xs">
            <button
              onClick={() => {
                setScenario("unsafe");
                setActiveStage("diff");
              }}
              className={`px-3.5 py-1.5 rounded-md transition-all duration-150 flex items-center gap-2 font-semibold ${
                scenario === "unsafe"
                  ? "bg-rose-950/90 text-rose-300 font-bold border border-rose-800 shadow-sm ring-1 ring-rose-500/20"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              Unsafe Patch (Rejected)
            </button>

            <button
              onClick={() => {
                setScenario("safe");
                setActiveStage("diff");
              }}
              className={`px-3.5 py-1.5 rounded-md transition-all duration-150 flex items-center gap-2 font-semibold ${
                scenario === "safe"
                  ? "bg-emerald-950/90 text-emerald-300 font-bold border border-emerald-800 shadow-sm ring-1 ring-emerald-500/20"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Safe Patch (Authorized)
            </button>
          </div>
        </div>
      </div>

      {/* ── STAGE PIPELINE TABS ── */}
      <div
        className="bg-surface-400/80 px-6 py-3 border-b border-border-subtle flex items-center gap-2 overflow-x-auto"
        role="tablist"
        aria-label="Simulation pipeline stages"
      >
        {stages.map((stage) => {
          const isActive = activeStage === stage.id;
          return (
            <button
              key={stage.id}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActiveStage(stage.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all duration-150 whitespace-nowrap focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none ${
                isActive
                  ? "bg-zinc-800 text-zinc-100 border border-zinc-700 shadow-sm"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40"
              }`}
            >
              <span className={isActive ? "text-emerald-400" : "text-zinc-500"}>
                {stage.icon}
              </span>
              <span>{stage.label}</span>
            </button>
          );
        })}
      </div>

      {/* ── MAIN VERIFICATION LOG & SIMULATION VIEW ── */}
      <div className="p-4 sm:p-5 min-h-[340px]">
        {/* STAGE 1: ALERT INGESTION */}
        {activeStage === "finding" && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-border-subtle">
              <div>
                <span className="text-[10px] text-zinc-500 uppercase">Incoming SAST Webhook</span>
                <div className="text-sm font-semibold text-zinc-100 mt-0.5">
                  {scenario === "unsafe"
                    ? "python.auth-bypass:app/auth/middleware.py:38"
                    : "python.sql-injection:app/database.py:42"}
                </div>
              </div>
              <span className="px-2 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-800 text-[10px] font-bold">
                HIGH SEVERITY · {scenario === "unsafe" ? "CWE-287" : "CWE-89"}
              </span>
            </div>
            <p className="text-zinc-400 text-xs font-sans leading-relaxed">
              {scenario === "unsafe"
                ? "Security alert: Authentication token verification middleware contains speculative logic susceptible to header forgery."
                : "Semgrep scanner detected direct string formatting into a raw SQL query inside the database handler."}
            </p>
            <div className="relative">
              <pre className="p-3 bg-zinc-950 rounded border border-zinc-800 text-zinc-300 overflow-x-auto text-[11px] leading-relaxed">
                <code>{scenario === "unsafe"
                  ? `# app/auth/middleware.py:38
def authenticate_request(req: Request):
    # VULNERABLE: Direct bearer token parsing without cryptographic HMAC signature check
    token = req.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing auth header")
    return parse_jwt_unverified(token)`
                  : `# app/database.py:42
def get_user_record(user_id: str):
    # VULNERABLE: Direct f-string interpolation into raw SQL query
    query = f"SELECT id, username, email FROM users WHERE id = '{user_id}'"
    return db.execute(query).fetchone()`}</code>
              </pre>
              <button
                onClick={() =>
                  handleCopy(
                    scenario === "unsafe"
                      ? "token = req.headers.get('Authorization')"
                      : "query = f\"SELECT id, username, email FROM users WHERE id = '{user_id}'\"",
                    "finding"
                  )
                }
                className="absolute top-2 right-2 px-2 py-0.5 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white border border-zinc-800 text-[10px] inline-flex items-center gap-1"
              >
                {copiedKey === "finding" ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                {copiedKey === "finding" ? "Copied" : "Copy"}
              </button>
            </div>
          </div>
        )}

        {/* STAGE 2: AST PATCH SYNTHESIS */}
        {activeStage === "diff" && (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-border-subtle">
              <div>
                <span className="text-[10px] text-zinc-500 uppercase">AST Synthesis Output (Tree-sitter)</span>
                <div className="text-sm font-semibold text-zinc-100 mt-0.5">
                  {scenario === "unsafe"
                    ? "speculative(ai): bypass token signature verification"
                    : "fix(security): parameterized query binding"}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  scenario === "unsafe"
                    ? "bg-rose-950 text-rose-300 border border-rose-800"
                    : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                }`}>
                  {scenario === "unsafe" ? "CANDIDATE: UNVERIFIED" : "CANDIDATE: SYNTHESIZED"}
                </span>
                <button
                  onClick={() =>
                    handleCopy(
                      scenario === "unsafe"
                        ? "- if not verify_hmac_signature(token):\n+ if req.headers.get('x-bypass') == '1':"
                        : "query = 'SELECT id, username, email FROM users WHERE id = %s'\nreturn db.execute(query, (user_id,)).fetchone()",
                      "diff"
                    )
                  }
                  className="px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white border border-zinc-800 inline-flex items-center gap-1 text-xs"
                >
                  {copiedKey === "diff" ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  {copiedKey === "diff" ? "Copied" : "Copy Diff"}
                </button>
              </div>
            </div>

            {/* Code Diff Display */}
            <pre className="p-5 bg-zinc-950 rounded-lg border border-zinc-800 overflow-x-auto leading-relaxed text-zinc-300 text-xs sm:text-sm font-mono">
              {scenario === "unsafe" ? (
                <>
                  <div className="text-zinc-500">--- a/app/auth/middleware.py</div>
                  <div className="text-zinc-500">+++ b/app/auth/middleware.py</div>
                  <div className="text-zinc-500">@@ -35,5 +35,4 @@ def authenticate_request(req):</div>
                  <div className="bg-rose-950/40 text-rose-300 px-2 -mx-2 rounded">
                    -    if not verify_hmac_signature(token, secret_key):
                  </div>
                  <div className="bg-rose-950/40 text-rose-300 px-2 -mx-2 rounded">
                    -        raise HTTPException(status_code=401, detail="Invalid signature")
                  </div>
                  <div className="bg-amber-950/40 text-amber-300 px-2 -mx-2 rounded">
                    +    # SPECULATIVE INSECURE SHORTCUT: Weakens auth boundary
                  </div>
                  <div className="bg-rose-950/40 text-rose-300 px-2 -mx-2 rounded">
                    +    if req.headers.get("x-bypass") == "1":
                  </div>
                  <div className="text-zinc-400">         return parse_jwt_unverified(token)</div>
                </>
              ) : (
                <>
                  <div className="text-zinc-500">--- a/app/database.py</div>
                  <div className="text-zinc-500">+++ b/app/database.py</div>
                  <div className="text-zinc-500">@@ -40,4 +40,4 @@ def get_user_record(user_id: str):</div>
                  <div className="bg-rose-950/40 text-zinc-300 px-2 -mx-2 rounded">
                    -    query = f&quot;SELECT id, username, email FROM users WHERE id = &apos;&#123;user_id&#125;&apos;&quot;
                  </div>
                  <div className="bg-rose-950/40 text-zinc-300 px-2 -mx-2 rounded">
                    -    return db.execute(query).fetchone()
                  </div>
                  <div className="bg-emerald-950/40 text-emerald-300 px-2 -mx-2 rounded">
                    +    query = "SELECT id, username, email FROM users WHERE id = %s"
                  </div>
                  <div className="bg-emerald-950/40 text-emerald-300 px-2 -mx-2 rounded">
                    +    return db.execute(query, (user_id,)).fetchone()
                  </div>
                </>
              )}
            </pre>

            {/* Invariant Execution Simulation Box */}
            <div className={`p-3.5 rounded border space-y-2 ${
              scenario === "unsafe"
                ? "bg-rose-950/20 border-rose-900/60"
                : "bg-emerald-950/20 border-emerald-900/60"
            }`}>
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="flex items-center gap-1.5">
                  {scenario === "unsafe" ? (
                    <XCircle className="w-4 h-4 text-rose-400" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  )}
                  {scenario === "unsafe" ? (
                    <span className="text-rose-200">✕ PATCH REJECTED · WRITE BLOCKED</span>
                  ) : (
                    <span className="text-emerald-200">✓ PATCH VERIFIED · WRITE AUTHORIZED</span>
                  )}
                </span>
                <span className="text-[10px] font-mono text-zinc-400">
                  {scenario === "unsafe" ? "STATUS: FAIL-CLOSED" : "STATUS: 5/5 GATES PASS"}
                </span>
              </div>

              <p className="text-xs text-zinc-300 font-sans leading-relaxed">
                {scenario === "unsafe" ? (
                  <>
                    <strong className="text-rose-300">Reason:</strong> Authentication boundary was weakened. The proposed patch removed HMAC token verification, failing isolated regression tests and policy rules. Invariant enforced: <strong className="text-zinc-100">0 writes reach GitHub</strong>.
                  </>
                ) : (
                  <>
                    <strong className="text-emerald-300">Reason:</strong> AST syntax verified valid, isolated gVisor sandbox passed 48/48 unit tests with 0 network egress, Semgrep confirmed 0 residual findings, and cryptographic Ed25519 signature was sealed.
                  </>
                )}
              </p>
            </div>
          </div>
        )}

        {/* STAGE 3: SANDBOX GATES */}
        {activeStage === "sandbox" && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-border-subtle">
              <div>
                <span className="text-[10px] text-zinc-500 uppercase">Verification Engine</span>
                <div className="text-sm font-semibold text-zinc-100 mt-0.5">
                  gVisor Sandbox Telemetry (0 Network Egress)
                </div>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                scenario === "unsafe"
                  ? "bg-rose-950 text-rose-300 border border-rose-800"
                  : "bg-emerald-950 text-emerald-300 border border-emerald-800"
              }`}>
                {scenario === "unsafe" ? "✕ GATE FAILED" : "✓ ALL 5/5 GATES PASSED"}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="p-2.5 bg-zinc-900/60 rounded border border-zinc-800">
                <div className="text-[10px] text-zinc-500 uppercase">Provider</div>
                <div className="text-zinc-200 mt-0.5 font-semibold">gVisor runsc</div>
              </div>
              <div className="p-2.5 bg-zinc-900/60 rounded border border-zinc-800">
                <div className="text-[10px] text-zinc-500 uppercase">Network Egress</div>
                <div className="text-emerald-400 mt-0.5 font-semibold">0 bytes (DROP)</div>
              </div>
              <div className="p-2.5 bg-zinc-900/60 rounded border border-zinc-800">
                <div className="text-[10px] text-zinc-500 uppercase">Unit Tests</div>
                <div className={scenario === "unsafe" ? "text-rose-400 mt-0.5 font-semibold" : "text-emerald-400 mt-0.5 font-semibold"}>
                  {scenario === "unsafe" ? "12 Passed / 1 FAILED" : "48 Passed / 0 Failed"}
                </div>
              </div>
              <div className="p-2.5 bg-zinc-900/60 rounded border border-zinc-800">
                <div className="text-[10px] text-zinc-500 uppercase">Security Re-Scan</div>
                <div className={scenario === "unsafe" ? "text-rose-400 mt-0.5 font-semibold" : "text-emerald-400 mt-0.5 font-semibold"}>
                  {scenario === "unsafe" ? "1 Violation (CWE-287)" : "0 Findings Remaining"}
                </div>
              </div>
            </div>

            <div className="p-2.5 bg-zinc-950 rounded border border-zinc-800 text-[11px] text-zinc-400 font-mono space-y-1">
              {scenario === "unsafe" ? (
                <>
                  <div className="text-zinc-400">[gVisor] Container started with non-root user · iptables drop-all active</div>
                  <div className="text-rose-400">[test_auth] FAILED: test_unauthenticated_request_rejected (AssertionError: 200 != 401)</div>
                  <div className="text-rose-300">[policy] Violation: Security control lowered. Aborting write sequence.</div>
                </>
              ) : (
                <>
                  <div>[gVisor] Container execution complete in 2.8s · Memory: 64MB / 512MB limit</div>
                  <div>[pytest] 48/48 tests passed successfully · 0 regressions detected</div>
                  <div className="text-emerald-400">[verifier] Semgrep rescan clean: 0 findings remaining</div>
                </>
              )}
            </div>
          </div>
        )}

        {/* STAGE 4: CRYPTOGRAPHIC PROOF */}
        {activeStage === "evidence" && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-border-subtle">
              <div>
                <span className="text-[10px] text-zinc-500 uppercase">Cryptographic Audit Proof</span>
                <div className="text-sm font-semibold text-zinc-100 mt-0.5">
                  Ed25519 Signed Verification Evidence
                </div>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                scenario === "unsafe"
                  ? "bg-rose-950 text-rose-300 border border-rose-800"
                  : "bg-emerald-950 text-emerald-300 border border-emerald-800"
              }`}>
                {scenario === "unsafe" ? "✕ PROOF REFUSED" : "✓ SIGNATURE VERIFIED"}
              </span>
            </div>

            {scenario === "unsafe" ? (
              <div className="p-4 bg-rose-950/30 rounded border border-rose-800/80 space-y-2">
                <div className="text-xs font-semibold text-rose-200 flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  Cryptographic Signature Not Issued
                </div>
                <p className="text-xs text-rose-300/90 font-sans leading-relaxed">
                  PatchProof never signs unverified or failed code changes. Because sandbox testing detected a security regression, the evidence bundle was discarded and no Ed25519 signature was created.
                </p>
              </div>
            ) : (
              <div className="space-y-2 text-xs">
                <div className="p-2.5 bg-zinc-900/60 rounded border border-zinc-800">
                  <div className="text-[10px] text-zinc-500 uppercase">Canonical SHA-256 Digest</div>
                  <div className="text-emerald-400 mt-0.5 break-all font-mono text-[11px]">
                    0bab05e1ac631d2c9c344c6bcaad7adcaf4decdab15ec2f981c6b32d40eeae28
                  </div>
                </div>
                <div className="p-2.5 bg-zinc-900/60 rounded border border-zinc-800">
                  <div className="text-[10px] text-zinc-500 uppercase">Ed25519 Signature (RFC 8032)</div>
                  <div className="text-zinc-300 mt-0.5 break-all font-mono text-[11px]">
                    8804f2ef9fbd46d9d642fb5fcdba4c824e10d4363a714e70f3bdfe46ea7f6c888e641c3f1e6e76f2fe257a3f54d2345c2888a4df5794c5a3eaba9f5c12c4d400
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* STAGE 5: VERIFIED PR */}
        {activeStage === "delivery" && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-border-subtle">
              <div>
                <span className="text-[10px] text-zinc-500 uppercase">GitHub Automated Publication</span>
                <div className="text-sm font-semibold text-zinc-100 mt-0.5">
                  {scenario === "unsafe" ? "Remote Publication Cancelled" : "Verified Pull Request #1 Delivered"}
                </div>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                scenario === "unsafe"
                  ? "bg-rose-950 text-rose-300 border border-rose-800"
                  : "bg-emerald-950 text-emerald-300 border border-emerald-800"
              }`}>
                {scenario === "unsafe" ? "0 WRITES EXECUTED" : "PR #1 OPENED"}
              </span>
            </div>

            {scenario === "unsafe" ? (
              <div className="p-4 bg-zinc-950 rounded border border-rose-900/60 space-y-2">
                <div className="text-xs font-semibold text-rose-300">
                  Fail-Closed Invariant Enforced: 0 Remote Writes
                </div>
                <p className="text-xs text-zinc-400 font-sans leading-relaxed">
                  No branch was pushed, no commit was written, and no pull request was created. PatchProof quarantined the flawed patch and notified administrators without exposing your repository to risk.
                </p>
              </div>
            ) : (
              <div className="p-3.5 bg-zinc-950 rounded border border-zinc-800 space-y-2">
                <div className="text-sm font-sans font-semibold text-zinc-100">
                  fix(security): remediate python.sql-injection vulnerability #1
                </div>
                <p className="text-zinc-400 font-sans text-xs">
                  This automated PR was synthesized by PatchProof and passed isolated gVisor sandbox testing with 0 egress. Cryptographic Ed25519 proof is bound.
                </p>
                <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-zinc-800 text-[11px]">
                  <span className="text-zinc-400">
                    Branch: <strong className="text-zinc-200">patchproof/pythonsql-inject</strong>
                  </span>
                  <span className="text-zinc-600">·</span>
                  <span className="text-zinc-400">
                    Target: <strong className="text-zinc-200">main</strong>
                  </span>
                  <span className="text-zinc-600">·</span>
                  <span className="text-emerald-400 font-semibold">✓ 5/5 Verification Gates Passed</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── BOTTOM STAGE STEPPER TOOLBAR ── */}
      <div className="px-4 py-2.5 bg-surface-400 border-t border-border-subtle flex items-center justify-between text-xs font-mono">
        <button
          onClick={prevStage}
          disabled={currentIndex === 0}
          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded border transition-colors ${
            currentIndex === 0
              ? "border-zinc-800 text-zinc-600 cursor-not-allowed"
              : "border-zinc-700 bg-zinc-900 text-zinc-300 hover:text-white hover:bg-zinc-800"
          }`}
        >
          <ChevronLeft className="w-3.5 h-3.5" /> Previous Stage
        </button>

        <span className="text-zinc-500 text-[11px]">
          Stage {currentIndex + 1} of {stageOrder.length}
        </span>

        <button
          onClick={nextStage}
          disabled={currentIndex === stageOrder.length - 1}
          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded border transition-colors ${
            currentIndex === stageOrder.length - 1
              ? "border-zinc-800 text-zinc-600 cursor-not-allowed"
              : "border-zinc-700 bg-zinc-900 text-zinc-300 hover:text-white hover:bg-zinc-800"
          }`}
        >
          Next Stage <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
