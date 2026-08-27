"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useScrollReveal } from "@/hooks/useScrollReveal";

export function CTASection() {
  const { ref, isRevealed } = useScrollReveal({ threshold: 0.2 });
  
  return (
    <section ref={ref} className="relative section-env border-t border-zinc-800/50">
      {/* Single quiet CTA field */}
      <div className="atm-cta-quiet" aria-hidden="true" />
      <div className={`max-w-4xl mx-auto px-6 sm:px-10 lg:px-16 py-48 lg:py-64 text-center space-y-10 transition-all duration-1000 ${isRevealed ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"}`}>
        <h2
          className="font-black tracking-tight text-zinc-100 font-sans leading-[0.95]"
          style={{ fontSize: "clamp(3rem, 6vw, 6rem)" }}
        >
          Ready to verify
          <br />
          your first patch?
        </h2>
        <p className="text-zinc-500 text-base sm:text-xl font-sans max-w-2xl mx-auto leading-relaxed">
          Install the PatchProof GitHub App. Configure repository policies.
          Protect your codebase with fail-closed verification.
        </p>
        <div className="pt-4 flex flex-wrap justify-center gap-5 font-sans text-base">
          <a
            href="#console"
            id="final-cta-launch-console"
            className="px-9 py-4 rounded-lg bg-zinc-100 hover:bg-white text-zinc-950 font-bold transition-all shadow-lg hover:shadow-xl inline-flex items-center gap-2.5 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
          >
            Launch Console <ArrowRight className="w-4 h-4" />
          </a>
          <Link
            href="/docs"
            className="px-7 py-4 rounded-lg bg-zinc-900/60 hover:bg-zinc-800/60 border border-zinc-800 text-zinc-400 hover:text-zinc-200 font-medium transition-colors focus-visible:ring-1 focus-visible:ring-zinc-400 focus-visible:outline-none"
          >
            Read Documentation
          </Link>
        </div>
      </div>
    </section>
  );
}
