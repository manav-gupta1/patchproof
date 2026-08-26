import React from "react";
import type { Metadata } from "next";
import { ContactForm } from "@/components/marketing/ContactForm";
import { Shield, Mail, Clock, Lock } from "lucide-react";

export const metadata: Metadata = {
  title: "Contact & Support | PatchProof",
  description: "Get in touch with the PatchProof security engineering team for technical support, security inquiries, or enterprise VPC deployments.",
};

export default function ContactPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-12">
      {/* Header */}
      <div className="space-y-4 max-w-2xl">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-300">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>Security Engineering Support</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-100 font-sans">
          Contact Engineering & Support
        </h1>
        <p className="text-zinc-400 text-sm sm:text-base font-sans leading-relaxed">
          Submit technical support requests, report security findings, or discuss enterprise air-gapped VPC deployments directly with our team.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Support Expectation & Info */}
        <div className="space-y-4 font-mono text-xs text-zinc-400">
          <div className="p-4 rounded-lg border border-border-subtle bg-surface-300 space-y-2">
            <div className="flex items-center gap-2 text-zinc-200 font-sans font-semibold text-sm">
              <Clock className="w-4 h-4 text-emerald-400" />
              <span>Response Time</span>
            </div>
            <p className="text-zinc-400 font-sans text-xs">
              All inquiries are reviewed directly by our core engineering team. We typically respond within <strong>1 business day</strong>.
            </p>
          </div>

          <div className="p-4 rounded-lg border border-border-subtle bg-surface-300 space-y-2">
            <div className="flex items-center gap-2 text-zinc-200 font-sans font-semibold text-sm">
              <Lock className="w-4 h-4 text-emerald-400" />
              <span>Security Reports</span>
            </div>
            <p className="text-zinc-400 font-sans text-xs">
              To report potential security vulnerabilities in PatchProof itself, please select &quot;Security Architecture &amp; Auditing&quot;.
            </p>
          </div>

          <div className="p-4 rounded-lg border border-border-subtle bg-surface-300 space-y-2">
            <div className="flex items-center gap-2 text-zinc-200 font-sans font-semibold text-sm">
              <Shield className="w-4 h-4 text-emerald-400" />
              <span>VPC Deployments</span>
            </div>
            <p className="text-zinc-400 font-sans text-xs">
              We provide AWS, GCP, and Azure Helm charts for air-gapped on-premise environments.
            </p>
          </div>
        </div>

        {/* Contact Form */}
        <div className="md:col-span-2 p-6 rounded-lg border border-border-subtle bg-surface-300">
          <ContactForm />
        </div>
      </div>
    </div>
  );
}
