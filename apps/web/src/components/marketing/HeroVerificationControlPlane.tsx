"use client";

import React from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

const SecurityChamberScene = dynamic(
  () =>
    import("@/components/marketing/SecurityChamberScene").then(
      (mod) => mod.SecurityChamberScene
    ),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full min-h-[680px] flex flex-col items-center justify-center font-mono text-sm text-zinc-500 space-y-4">
        <div className="flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse-subtle shadow-[0_0_8px_rgba(52,211,153,0.5)]" />
          <span className="text-zinc-400 font-semibold text-xs uppercase tracking-widest">
            Initializing Chamber
          </span>
        </div>
      </div>
    ),
  }
);

export function HeroSection() {
  return (
    <section
      className="relative min-h-[90vh] flex items-center overflow-hidden select-none"
      aria-label="PatchProof hero"
    >
      {/*
        The global machine illumination (emerald field, inspection rings, vertical shaft)
        is rendered by PageEnvironment via fixed layers.
        
        We add the atmospheric depth masks here for the hero.
      */}
      <div className="atm-hero-depth" aria-hidden="true" />
      <div className="atm-hero-machine animate-atm-drift" aria-hidden="true" />

      <div className="relative w-full max-w-[1800px] mx-auto px-6 sm:px-8 lg:px-12 py-20 lg:py-0">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 items-center min-h-[90vh]">

          {/* ── LEFT: TYPOGRAPHY — 5 cols ── */}
          <div className="lg:col-span-5 flex flex-col justify-center space-y-8 lg:space-y-10 py-12 lg:py-16 lg:pr-8">

            {/* Eyebrow */}
            <div
              className="flex items-center gap-3 text-xs font-mono text-zinc-500 animate-hero-fade-in"
              style={{ animationDelay: "0ms" }}
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-subtle shadow-[0_0_8px_rgba(52,211,153,0.6)]" />
              <span className="uppercase tracking-[0.2em] font-semibold">
                Fail-Closed Security Boundary
              </span>
            </div>

            {/* Headline — enormous, immediate, dominant */}
            <h1
              className="font-black tracking-tight text-zinc-100 font-sans leading-[0.92] animate-hero-slide-up"
              style={{
                fontSize: "clamp(72px, 7.5vw, 118px)",
                animationDelay: "80ms",
              }}
            >
              EVERY{" "}
              <br className="hidden xs:block" />
              PATCH
              <br />
              MUST{" "}
              <span className="text-emerald-400">
                PROVE
              </span>
              <br />
              ITSELF.
            </h1>

            {/* Supporting copy — sharp visual hierarchy */}
            <div
              className="space-y-5 max-w-[440px] animate-hero-slide-up"
              style={{ animationDelay: "180ms" }}
            >
              {/* Primary — part of the 3-second rule */}
              <p
                className="text-zinc-200 font-sans leading-snug font-medium"
                style={{ fontSize: "clamp(1.15rem, 1.6vw, 1.4rem)" }}
              >
                AI writes the patch.
                <br />
                PatchProof verifies it before GitHub.
              </p>
              {/* Technical detail — clearly secondary */}
              <p className="text-zinc-600 text-sm font-sans leading-relaxed">
                Every patch passes isolated sandboxing, regression tests, policy
                gates, and cryptographic attestation before the write is
                authorized.
              </p>
            </div>

            {/* CTA — one dominant, one subordinate */}
            <div
              className="flex flex-wrap items-center gap-4 pt-2 animate-hero-fade-in"
              style={{ animationDelay: "320ms" }}
            >
              <a
                href="#console"
                id="hero-launch-console"
                className="px-8 py-4 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 text-base font-bold font-sans transition-all duration-150 shadow-lg hover:shadow-xl inline-flex items-center gap-2.5 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
              >
                Launch Console <ArrowRight className="w-4 h-4" />
              </a>
              <Link
                href="/security"
                className="text-zinc-500 hover:text-zinc-300 text-sm font-sans font-medium transition-colors inline-flex items-center gap-1.5 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-zinc-400 rounded"
              >
                Inspect Security Architecture <ArrowRight className="w-3.5 h-3.5 opacity-70" />
              </Link>
            </div>
          </div>

          {/* ── RIGHT: 3D VERIFICATION CHAMBER WITH INTEGRATED ARCHITECTURAL BUS — 7 cols ── */}
          <div
            className="lg:col-span-7 flex items-stretch animate-chamber-fade-in relative"
            style={{ animationDelay: "200ms", minHeight: "680px" }}
          >
            {/* Subtle Horizon Floor Grid under the chamber */}
            <div 
              className="absolute bottom-0 left-[-10%] right-[-20%] h-[40%] pointer-events-none -z-10"
              style={{
                perspective: "1000px",
                perspectiveOrigin: "50% 10%",
                maskImage: "radial-gradient(ellipse 60% 80% at 50% 50%, #000 10%, transparent 80%)",
                WebkitMaskImage: "radial-gradient(ellipse 60% 80% at 50% 50%, #000 10%, transparent 80%)",
              }}
            >
              <div 
                className="w-full h-full border-t border-emerald-900/40 bg-zinc-950/20"
                style={{
                  transform: "rotateX(78deg) translateZ(0)",
                  backgroundSize: "45px 45px",
                  backgroundImage: `
                    linear-gradient(to right, rgba(16, 185, 129, 0.08) 1px, transparent 1px),
                    linear-gradient(to bottom, rgba(16, 185, 129, 0.08) 1px, transparent 1px)
                  `
                }}
              />
            </div>
            {/* Subtle technical pipeline indicator column */}
            <div className="hidden xl:flex flex-col justify-between py-12 pr-6 border-r border-zinc-800/40 text-xs font-mono text-zinc-500 space-y-4 select-none shrink-0">
              <div className="space-y-0.5">
                <div className="text-zinc-400 font-bold tracking-wider">01 PATCH</div>
                <div className="text-zinc-600">UNTRUSTED INGEST</div>
              </div>
              <div className="text-zinc-700 text-xs">↓</div>
              <div className="space-y-0.5">
                <div className="text-zinc-400 font-bold tracking-wider">02 AST</div>
                <div className="text-zinc-600">TREE-SITTER BOUND</div>
              </div>
              <div className="text-zinc-700 text-xs">↓</div>
              <div className="space-y-0.5">
                <div className="text-emerald-400 font-bold tracking-wider">03 SANDBOX</div>
                <div className="text-zinc-600">gVisor 0-EGRESS</div>
              </div>
              <div className="text-zinc-700 text-xs">↓</div>
              <div className="space-y-0.5">
                <div className="text-zinc-400 font-bold tracking-wider">04 VERIFY</div>
                <div className="text-zinc-600">TEST & RESCAN</div>
              </div>
              <div className="text-zinc-700 text-xs">↓</div>
              <div className="space-y-0.5">
                <div className="text-emerald-400 font-bold tracking-wider">05 PROOF</div>
                <div className="text-zinc-600">ED25519 SEALED</div>
              </div>
              <div className="text-zinc-700 text-xs">↓</div>
              <div className="space-y-0.5">
                <div className="text-zinc-300 font-bold tracking-wider">06 GITHUB</div>
                <div className="text-zinc-600">AUTHORIZED WRITE</div>
              </div>
            </div>

            {/* 3D Scene */}
            <div className="flex-1 flex items-center">
              <SecurityChamberScene />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
