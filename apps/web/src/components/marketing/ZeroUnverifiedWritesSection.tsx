"use client";

import React from "react";

export function ZeroUnverifiedWritesSection() {
  return (
    <section className="py-40 lg:py-56 border-t border-zinc-800/50">
      <div className="max-w-[1100px] mx-auto px-6 sm:px-10 lg:px-16 space-y-28 lg:space-y-40">

        {/* ── EDITORIAL STATEMENT ── */}
        <div className="max-w-[800px] space-y-6">
          <p className="text-xs font-mono uppercase tracking-[0.2em] text-zinc-600 font-semibold">
            The Problem
          </p>
          <h2
            className="font-black tracking-tight text-zinc-100 font-sans leading-[0.95]"
            style={{ fontSize: "clamp(2.8rem, 5vw, 5rem)" }}
          >
            AI can write code.
            <br />
            <span className="text-zinc-500">
              Nothing proves it&apos;s safe.
            </span>
          </h2>
          <p className="text-zinc-400 text-lg sm:text-xl font-sans leading-relaxed max-w-[600px]">
            Standard AI tooling pushes speculative patches directly to your
            repository. No sandbox. No regression tests. No cryptographic
            proof. You trust the model. You hope.
          </p>
        </div>

        {/* ── LARGE TYPOGRAPHIC COMPARISON ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 lg:gap-32">

          {/* WITHOUT */}
          <div className="space-y-0">
            <p className="text-xs font-mono uppercase tracking-[0.2em] text-rose-500/70 font-bold mb-10">
              Without Verification
            </p>
            <div className="font-sans space-y-0">
              <div
                className="font-black text-zinc-400 leading-none"
                style={{ fontSize: "clamp(2.8rem, 5.5vw, 5.5rem)" }}
              >
                AI PATCH
              </div>
              <div
                className="text-rose-500/50 font-mono leading-none select-none py-4"
                aria-hidden="true"
                style={{ fontSize: "clamp(3rem, 6vw, 7rem)" }}
              >
                ↓
              </div>
              <div
                className="font-black text-zinc-400 leading-none"
                style={{ fontSize: "clamp(2.8rem, 5.5vw, 5.5rem)" }}
              >
                WRITE
              </div>
              <div
                className="text-rose-500/50 font-mono leading-none select-none py-4"
                aria-hidden="true"
                style={{ fontSize: "clamp(3rem, 6vw, 7rem)" }}
              >
                ↓
              </div>
              <div
                className="font-black text-rose-400/70 leading-none"
                style={{ fontSize: "clamp(2.8rem, 5.5vw, 5.5rem)" }}
              >
                TRUST
                <br />
                AFTERWARD
              </div>
            </div>
            <p className="text-zinc-600 text-sm font-sans leading-relaxed max-w-[340px] border-t border-zinc-800/40 pt-8 mt-10">
              Unverified code reaches production. You discover regressions after
              the merge. No evidence trail.
            </p>
          </div>

          {/* WITH PATCHPROOF */}
          <div className="space-y-0">
            <p className="text-xs font-mono uppercase tracking-[0.2em] text-emerald-500/70 font-bold mb-10">
              With PatchProof
            </p>
            <div className="font-sans space-y-0">
              <div
                className="font-black text-zinc-300 leading-none"
                style={{ fontSize: "clamp(2.8rem, 5.5vw, 5.5rem)" }}
              >
                AI PATCH
              </div>
              <div
                className="text-emerald-500/50 font-mono leading-none select-none py-4"
                aria-hidden="true"
                style={{ fontSize: "clamp(3rem, 6vw, 7rem)" }}
              >
                ↓
              </div>
              <div
                className="font-black text-zinc-100 leading-none"
                style={{ fontSize: "clamp(2.8rem, 5.5vw, 5.5rem)" }}
              >
                VERIFY
              </div>
              <div
                className="text-emerald-500/50 font-mono leading-none select-none py-4"
                aria-hidden="true"
                style={{ fontSize: "clamp(3rem, 6vw, 7rem)" }}
              >
                ↓
              </div>
              <div
                className="font-black text-zinc-100 leading-none"
                style={{ fontSize: "clamp(2.8rem, 5.5vw, 5.5rem)" }}
              >
                PROVE
              </div>
              <div
                className="text-emerald-500/50 font-mono leading-none select-none py-4"
                aria-hidden="true"
                style={{ fontSize: "clamp(3rem, 6vw, 7rem)" }}
              >
                ↓
              </div>
              <div
                className="font-black text-emerald-400 leading-none"
                style={{ fontSize: "clamp(2.8rem, 5.5vw, 5.5rem)" }}
              >
                WRITE
              </div>
            </div>
            <p className="text-zinc-400 text-sm font-sans leading-relaxed max-w-[340px] border-t border-zinc-800/40 pt-8 mt-10">
              Sandbox-tested. Regression-verified. Cryptographically signed.
              Evidence exists before code reaches GitHub.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
