"use client";

import React, { useState } from "react";
import { CheckCircle2, Send, AlertCircle, ArrowRight } from "lucide-react";
import Link from "next/link";

export function ContactForm() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    category: "technical_support",
    repository: "",
    message: "",
  });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.message) {
      setError("Please complete all required fields.");
      return;
    }
    setError(null);
    setLoading(true);

    // Simulate reliable dispatch
    await new Promise((r) => setTimeout(r, 600));
    setLoading(false);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="p-8 border border-emerald-900/50 bg-emerald-950/20 rounded-lg text-center space-y-4 font-mono text-xs animate-fadeIn">
        <div className="w-12 h-12 rounded-full bg-emerald-900/40 border border-emerald-700 flex items-center justify-center mx-auto text-emerald-400">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-semibold text-zinc-100 font-sans">Inquiry Received</h3>
          <p className="text-zinc-400 text-xs font-sans max-w-md mx-auto">
            Thank you, {formData.name}. Your inquiry has been routed to our security engineering team.
          </p>
        </div>
        <div className="p-3 bg-zinc-900/80 rounded border border-zinc-800 text-zinc-300 text-left max-w-md mx-auto space-y-1">
          <div className="text-[11px] text-zinc-500 uppercase">Expectation</div>
          <div className="text-xs">Direct response typically within 1 business day.</div>
        </div>
        <div className="pt-2 flex justify-center gap-3">
          <button
            onClick={() => {
              setSubmitted(false);
              setFormData({ name: "", email: "", category: "technical_support", repository: "", message: "" });
            }}
            className="px-4 py-2 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-mono transition-colors"
          >
            Send Another Message
          </button>
          <Link
            href="/jobs"
            className="px-4 py-2 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-mono font-semibold transition-colors"
          >
            Open Security Console
          </Link>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
      {error && (
        <div className="p-3 rounded bg-rose-950/40 border border-rose-900 text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <label className="text-[11px] text-zinc-400 uppercase tracking-wider block">
            Full Name <span className="text-rose-400">*</span>
          </label>
          <input
            type="text"
            required
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Ada Lovelace"
            className="w-full px-3 py-2 rounded bg-surface-300 border border-border-subtle text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-500 font-sans"
          />
        </div>

        <div className="space-y-1.5">
          <label className="text-[11px] text-zinc-400 uppercase tracking-wider block">
            Work Email <span className="text-rose-400">*</span>
          </label>
          <input
            type="email"
            required
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="ada@company.com"
            className="w-full px-3 py-2 rounded bg-surface-300 border border-border-subtle text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-500 font-sans"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <label className="text-[11px] text-zinc-400 uppercase tracking-wider block">Category</label>
          <select
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
            className="w-full px-3 py-2 rounded bg-surface-300 border border-border-subtle text-zinc-200 focus:outline-none focus:border-zinc-500 font-sans"
          >
            <option value="technical_support">Technical Support / Bug Report</option>
            <option value="security_inquiry">Security Architecture & Auditing</option>
            <option value="enterprise_deployment">Enterprise Self-Hosted VPC</option>
            <option value="general_inquiry">General Inquiry</option>
          </select>
        </div>

        <div className="space-y-1.5">
          <label className="text-[11px] text-zinc-400 uppercase tracking-wider block">
            Target Repository <span className="text-zinc-600">(Optional)</span>
          </label>
          <input
            type="text"
            value={formData.repository}
            onChange={(e) => setFormData({ ...formData, repository: e.target.value })}
            placeholder="org/repository-name"
            className="w-full px-3 py-2 rounded bg-surface-300 border border-border-subtle text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-500 font-mono"
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="text-[11px] text-zinc-400 uppercase tracking-wider block">
          Message & Context <span className="text-rose-400">*</span>
        </label>
        <textarea
          required
          rows={4}
          value={formData.message}
          onChange={(e) => setFormData({ ...formData, message: e.target.value })}
          placeholder="Describe your question, environment, or security requirement..."
          className="w-full px-3 py-2 rounded bg-surface-300 border border-border-subtle text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-500 font-sans"
        />
      </div>

      <div className="pt-2 flex items-center justify-between gap-4">
        <span className="text-[11px] text-zinc-500 font-sans">
          Engineering review response: typically 1 business day.
        </span>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 rounded bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-mono font-semibold transition-colors disabled:opacity-50 inline-flex items-center gap-1.5"
        >
          {loading ? "Sending..." : "Submit Inquiry"} <Send className="w-3.5 h-3.5" />
        </button>
      </div>
    </form>
  );
}
