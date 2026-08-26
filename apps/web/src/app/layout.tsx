import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/shell/AppShell";

export const metadata: Metadata = {
  metadataBase: new URL("https://patchproof.dev"),
  title: {
    default: "PatchProof | Autonomous Verified-Safe Security Remediation",
    template: "%s | PatchProof",
  },
  description:
    "PatchProof ingests vulnerability alerts, synthesizes AST patches, verifies them in isolated 0-egress gVisor sandboxes, and publishes Ed25519-signed pull requests. Strict invariant: Unverified patch → zero GitHub writes.",
  keywords: [
    "automated security patching",
    "vulnerability remediation",
    "AST code repair",
    "gVisor sandbox",
    "Ed25519 verification",
    "DevSecOps",
    "GitHub App",
    "Semgrep remediation",
    "CodeQL remediation",
  ],
  authors: [{ name: "PatchProof Security Engineering Team" }],
  creator: "PatchProof Technologies Inc.",
  publisher: "PatchProof Technologies Inc.",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    title: "PatchProof | Autonomous Verified-Safe Security Remediation",
    description:
      "Autonomous security patching with gVisor sandbox verification and Ed25519 cryptographic evidence. Zero unverified writes to GitHub.",
    url: "https://patchproof.dev",
    siteName: "PatchProof",
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "PatchProof | Autonomous Verified-Safe Security Remediation",
    description:
      "Autonomous security patching with gVisor sandbox verification and Ed25519 cryptographic evidence. Zero unverified writes to GitHub.",
    creator: "@patchproof_dev",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://patchproof.dev/#organization",
      name: "PatchProof Technologies Inc.",
      url: "https://patchproof.dev",
      logo: "https://patchproof.dev/icon.png",
      description: "Automated verified-safe security patch synthesis and delivery platform.",
    },
    {
      "@type": "SoftwareApplication",
      "@id": "https://patchproof.dev/#software",
      name: "PatchProof",
      applicationCategory: "SecurityApplication",
      operatingSystem: "Linux, Cloud, Self-Hosted",
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD",
      },
      description:
        "Autonomous security patch agent that ingests vulnerability alerts, synthesizes AST patches, verifies them in isolated 0-egress gVisor sandboxes, and publishes signed pull requests.",
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className="bg-background text-foreground min-h-screen">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
