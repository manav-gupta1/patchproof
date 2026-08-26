import React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { Check, ArrowRight, ShieldCheck, Zap, Building } from "lucide-react";

export const metadata: Metadata = {
  title: "Pricing | PatchProof Automated Security Remediation",
  description: "Transparent developer pricing for open source, team repositories, and enterprise self-hosted VPC deployments.",
};

export default function PricingPage() {
  const tiers = [
    {
      name: "Open Source",
      price: "$0",
      period: "forever",
      description: "For public open source projects needing automated, verified patch remediation.",
      icon: <Zap className="w-4 h-4 text-emerald-400" />,
      features: [
        "Unlimited public repositories",
        "Automated AST patch synthesis",
        "gVisor isolated execution sandboxes",
        "Zero network egress enforcement",
        "Ed25519 cryptographic evidence export",
        "Standard webhook rate limits",
        "Community support",
      ],
      cta: "Get Started Free",
      href: "/jobs",
      popular: false,
    },
    {
      name: "Team",
      price: "$49",
      period: "per month",
      description: "For engineering teams securing private codebases with automated PR delivery.",
      icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
      features: [
        "Up to 15 private repositories",
        "Priority sandbox remediation queue",
        "Custom repository policy rules (.patchproof.yml)",
        "Automated GitHub Check Runs",
        "Real-time SSE event streaming",
        "Multi-tenant isolation & API key tokens",
        "1 business day response support",
      ],
      cta: "Start 14-Day Trial",
      href: "/contact",
      popular: true,
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "annual billing",
      description: "For security-conscious enterprises requiring air-gapped or dedicated VPC hosting.",
      icon: <Building className="w-4 h-4 text-emerald-400" />,
      features: [
        "Unlimited private & public repositories",
        "Self-hosted / VPC air-gapped deployment",
        "Custom LLM provider & local AST engines",
        "Dedicated HSM / Ed25519 signer keys",
        "Custom SLA & dedicated security engineer",
        "SOC 2 / ISO compliance audit exports",
        "Custom single sign-on (SSO / SAML)",
      ],
      cta: "Contact Enterprise",
      href: "/contact",
      popular: false,
    },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 space-y-16">
      {/* Header */}
      <div className="space-y-4 max-w-3xl text-center mx-auto">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-[11px] font-mono text-zinc-300">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>Transparent Developer Pricing</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-100 font-sans">
          Predictable Pricing. Zero Hidden Fees.
        </h1>
        <p className="text-zinc-400 text-sm sm:text-base font-sans leading-relaxed max-w-xl mx-auto">
          Free for open source projects. Transparent monthly tiers for engineering teams.
        </p>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs">
        {tiers.map((tier) => (
          <div
            key={tier.name}
            className={`p-6 rounded-lg border flex flex-col justify-between space-y-6 ${
              tier.popular
                ? "border-emerald-700/80 bg-surface-300 ring-1 ring-emerald-500/20"
                : "border-border-subtle bg-surface-300"
            }`}
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold text-zinc-100 font-sans text-base">
                  {tier.icon}
                  <span>{tier.name}</span>
                </div>
                {tier.popular && (
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-bold">
                    RECOMMENDED
                  </span>
                )}
              </div>

              <div>
                <div className="text-3xl font-bold text-zinc-100 font-sans">{tier.price}</div>
                <div className="text-zinc-500 text-[11px]">{tier.period}</div>
              </div>

              <p className="text-zinc-400 text-xs font-sans leading-relaxed">{tier.description}</p>

              <div className="border-t border-border-subtle pt-4 space-y-2.5">
                <div className="text-[11px] font-semibold text-zinc-300 uppercase tracking-wider">Includes:</div>
                <ul className="space-y-2 text-zinc-300">
                  {tier.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      <span className="font-sans text-xs">{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <Link
              href={tier.href}
              className={`w-full py-2 rounded text-center text-xs font-semibold transition-colors block ${
                tier.popular
                  ? "bg-zinc-100 hover:bg-white text-zinc-950"
                  : "bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200"
              }`}
            >
              {tier.cta}
            </Link>
          </div>
        ))}
      </div>

      {/* Technical Allocation Matrix */}
      <div className="space-y-4 border-t border-border-subtle pt-10 font-mono text-xs">
        <div className="space-y-1">
          <h2 className="text-xl font-bold tracking-tight text-zinc-100 font-sans">
            Technical Sandbox & Compute Specifications
          </h2>
          <p className="text-zinc-400 text-xs font-sans">
            Detailed resource quotas allocated to each remediation verification pipeline.
          </p>
        </div>

        <div className="border border-border-subtle rounded-lg bg-surface-300 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-surface-400 border-b border-border-subtle text-zinc-400 text-[11px]">
                <tr>
                  <th className="p-3">Specification</th>
                  <th className="p-3">Open Source</th>
                  <th className="p-3 text-emerald-400">Team Tier</th>
                  <th className="p-3">Enterprise VPC</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle text-zinc-300">
                <tr className="hover:bg-surface-400/40 transition-colors">
                  <td className="p-3 font-semibold text-zinc-200">Sandbox Isolation</td>
                  <td className="p-3 text-zinc-400 font-sans text-xs">gVisor runsc</td>
                  <td className="p-3 text-emerald-300 font-sans text-xs font-medium">gVisor runsc</td>
                  <td className="p-3 text-zinc-200 font-sans text-xs font-medium">Air-Gapped VPC / K8s</td>
                </tr>
                <tr className="hover:bg-surface-400/40 transition-colors">
                  <td className="p-3 font-semibold text-zinc-200">Network Policy</td>
                  <td className="p-3 text-zinc-400 font-sans text-xs">0 Egress (DROP)</td>
                  <td className="p-3 text-emerald-300 font-sans text-xs font-medium">0 Egress (DROP)</td>
                  <td className="p-3 text-zinc-200 font-sans text-xs font-medium">0 Egress / Air-Gapped</td>
                </tr>
                <tr className="hover:bg-surface-400/40 transition-colors">
                  <td className="p-3 font-semibold text-zinc-200">Concurrency Limit</td>
                  <td className="p-3 text-zinc-400 font-sans text-xs">2 concurrent jobs</td>
                  <td className="p-3 text-emerald-300 font-sans text-xs font-medium">10 concurrent jobs</td>
                  <td className="p-3 text-zinc-200 font-sans text-xs font-medium">Dedicated cluster pool</td>
                </tr>
                <tr className="hover:bg-surface-400/40 transition-colors">
                  <td className="p-3 font-semibold text-zinc-200">Max Job Timeout</td>
                  <td className="p-3 text-zinc-400 font-sans text-xs">300s (5 min)</td>
                  <td className="p-3 text-emerald-300 font-sans text-xs font-medium">600s (10 min)</td>
                  <td className="p-3 text-zinc-200 font-sans text-xs font-medium">Customizable (up to 30m)</td>
                </tr>
                <tr className="hover:bg-surface-400/40 transition-colors">
                  <td className="p-3 font-semibold text-zinc-200">Ed25519 Signer</td>
                  <td className="p-3 text-zinc-400 font-sans text-xs">Default Dev Key</td>
                  <td className="p-3 text-emerald-300 font-sans text-xs font-medium">Tenant-Isolated Key</td>
                  <td className="p-3 text-zinc-200 font-sans text-xs font-medium">Customer AWS KMS / HSM</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Compute FAQ */}
      <div className="p-6 rounded-lg border border-border-subtle bg-surface-300 space-y-3 font-mono text-xs">
        <h3 className="text-sm font-semibold text-zinc-100 font-sans">
          How do sandbox compute resources work?
        </h3>
        <p className="text-zinc-400 text-xs font-sans leading-relaxed">
          Every remediation job spins up a lightweight, ephemeral gVisor container capped at 512MB RAM and 1.0 vCPU. Once tests and security re-scans complete, the container is destroyed immediately. No customer code remains in memory after PR delivery.
        </p>
      </div>
    </div>
  );
}
