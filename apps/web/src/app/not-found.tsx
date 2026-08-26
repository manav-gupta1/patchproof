import React from "react";
import Link from "next/link";
import { AlertCircle, ArrowRight, Shield, Home, Terminal } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4">
      <div className="max-w-md w-full p-8 rounded-lg border border-border-subtle bg-surface-300 text-center space-y-6 font-mono text-xs shadow-2xl">
        <div className="w-12 h-12 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto text-amber-400">
          <AlertCircle className="w-6 h-6" />
        </div>

        <div className="space-y-2">
          <div className="text-[11px] text-zinc-500 uppercase tracking-wider">
            HTTP 404 // RESOURCE_NOT_FOUND
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-zinc-100 font-sans">
            Page Not Found
          </h1>
          <p className="text-zinc-400 text-xs font-sans leading-relaxed">
            The requested path does not exist in the PatchProof routing table or has been relocated.
          </p>
        </div>

        <div className="p-3 bg-zinc-950 rounded border border-zinc-800 text-left text-zinc-400 text-[11px] space-y-1">
          <div className="text-zinc-500 uppercase">Available Core Endpoints:</div>
          <div className="text-emerald-400">/jobs · Remediations Explorer</div>
          <div className="text-zinc-300">/security · Trust & Invariants</div>
          <div className="text-zinc-300">/docs · Developer Guides</div>
        </div>

        <div className="pt-2 flex flex-wrap justify-center gap-3">
          <Link
            href="/"
            className="px-4 py-2 rounded bg-zinc-100 hover:bg-white text-zinc-950 font-semibold transition-colors inline-flex items-center gap-1.5"
          >
            <Home className="w-3.5 h-3.5" /> Return Home
          </Link>
          <Link
            href="/jobs"
            className="px-4 py-2 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 transition-colors inline-flex items-center gap-1.5"
          >
            <Terminal className="w-3.5 h-3.5" /> Open Console
          </Link>
        </div>
      </div>
    </div>
  );
}
