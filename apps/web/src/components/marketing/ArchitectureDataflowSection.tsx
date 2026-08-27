"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

interface Stage {
  number: string;
  name: string;
  description: string;
}

const STAGES: Stage[] = [
  {
    number: "01",
    name: "DETECT",
    description:
      "SAST scanner alerts arrive via webhook with exact AST coordinates and CWE classification.",
  },
  {
    number: "02",
    name: "PATCH",
    description:
      "Tree-sitter isolates the vulnerable node and synthesizes a targeted syntactic replacement.",
  },
  {
    number: "03",
    name: "VERIFY",
    description:
      "Patch executes inside a 0-egress gVisor sandbox. Regression tests and security re-scans must pass.",
  },
  {
    number: "04",
    name: "WRITE",
    description:
      "Ed25519-signed evidence bundle is attached. The authorized PR is published to GitHub.",
  },
];

export function ArchitectureDataflowSection() {
  return (
    <section className="py-40 lg:py-56 border-t border-zinc-800/50">
      <div className="max-w-[1700px] mx-auto px-6 sm:px-10 lg:px-16 xl:px-20 space-y-20 lg:space-y-28">

        {/* ── SECTION HEADER ── */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 max-w-[1200px]">
          <div className="space-y-4">
            <p className="text-xs font-mono uppercase tracking-[0.2em] text-zinc-600 font-semibold">
              How It Works
            </p>
            <h2
              className="font-black tracking-tight text-zinc-100 font-sans leading-[0.95]"
              style={{ fontSize: "clamp(2.8rem, 5vw, 5rem)" }}
            >
              Four deterministic stages.
              <br />
              <span className="text-zinc-500">Zero trust assumptions.</span>
            </h2>
          </div>

          <Link
            href="/how-it-works"
            className="text-sm font-sans text-zinc-500 hover:text-zinc-300 inline-flex items-center gap-2 transition-colors self-start md:self-auto font-medium shrink-0"
          >
            Full technical specification <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* ── 4-STAGE PIPELINE ── */}
        {/* Desktop: horizontal with arrow connectors */}
        <div className="hidden lg:grid" style={{ gridTemplateColumns: "1fr auto 1fr auto 1fr auto 1fr" }}>
          {STAGES.map((stage, idx) => (
            <React.Fragment key={stage.number}>
              {/* Stage */}
              <div className="relative pr-4">
                {/* Giant step number */}
                <div
                  className="font-black text-zinc-800/60 font-mono leading-none select-none"
                  style={{ fontSize: "clamp(5rem, 8vw, 9rem)" }}
                >
                  {stage.number}
                </div>

                {/* Stage name — tightly below the number */}
                <h3 className="text-2xl lg:text-3xl font-black text-zinc-100 font-sans tracking-tight mt-3 mb-5">
                  {stage.name}
                </h3>

                {/* Description */}
                <p className="text-zinc-500 text-sm font-sans leading-relaxed max-w-[200px]">
                  {stage.description}
                </p>
              </div>

              {/* Arrow connector (except after last) */}
              {idx < STAGES.length - 1 && (
                <div className="flex items-start pt-10 px-4">
                  <span
                    className="text-zinc-700/80 font-mono select-none leading-none"
                    aria-hidden="true"
                    style={{ fontSize: "clamp(2rem, 3vw, 3.5rem)" }}
                  >
                    →
                  </span>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Mobile: vertical stack */}
        <div className="lg:hidden space-y-0 divide-y divide-zinc-800/40">
          {STAGES.map((stage, idx) => (
            <div key={stage.number} className="py-10 space-y-4">
              <div className="flex items-baseline gap-5">
                <div
                  className="font-black text-zinc-800/70 font-mono leading-none select-none"
                  style={{ fontSize: "clamp(3.5rem, 12vw, 5rem)" }}
                >
                  {stage.number}
                </div>
                <h3 className="text-2xl font-black text-zinc-100 font-sans tracking-tight">
                  {stage.name}
                </h3>
              </div>
              <p className="text-zinc-500 text-sm font-sans leading-relaxed">
                {stage.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
