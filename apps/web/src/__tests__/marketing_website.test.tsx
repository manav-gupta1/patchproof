import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Header } from "@/components/marketing/Header";
import { Footer } from "@/components/marketing/Footer";
import { InteractiveDemo } from "@/components/marketing/InteractiveDemo";
import { FAQAccordion } from "@/components/marketing/FAQAccordion";
import { ContactForm } from "@/components/marketing/ContactForm";
import HowItWorksPage from "@/app/how-it-works/page";
import SecurityPage from "@/app/security/page";
import DocsPage from "@/app/docs/page";
import PricingPage from "@/app/pricing/page";
import FAQPage from "@/app/faq/page";
import ContactPage from "@/app/contact/page";
import PrivacyPage from "@/app/privacy/page";
import TermsPage from "@/app/terms/page";
import NotFound from "@/app/not-found";

describe("Marketing & Public Website Components", () => {
  it("renders Header navigation and responds to mobile menu toggle", () => {
    render(<Header />);
    expect(screen.getByText("PATCHPROOF")).toBeInTheDocument();
    expect(screen.getAllByText("How It Works")[0]).toBeInTheDocument();
    expect(screen.getAllByText("Security & Trust")[0]).toBeInTheDocument();
    expect(screen.getAllByText("Docs")[0]).toBeInTheDocument();
    expect(screen.getAllByText("Pricing")[0]).toBeInTheDocument();

    const mobileToggle = screen.getByLabelText("Open navigation menu");
    fireEvent.click(mobileToggle);
    expect(screen.getByText("Open Security Console")).toBeInTheDocument();
  });

  it("renders Footer with copyright and security invariant indicator", () => {
    render(<Footer />);
    expect(screen.getByText(/PatchProof Technologies Inc/i)).toBeInTheDocument();
    expect(screen.getByText(/0 Unverified Writes/i)).toBeInTheDocument();
    expect(screen.getByText("Terms of Service")).toBeInTheDocument();
    expect(screen.getByText("Privacy Policy")).toBeInTheDocument();
  });

  it("renders InteractiveDemo and allows switching between pipeline stages", () => {
    render(<InteractiveDemo />);
    expect(screen.getByTestId("interactive-demo")).toBeInTheDocument();

    // Default stage is AST Patch ("02. AST Patch")
    expect(screen.getByText(/AST Synthesis Output/i)).toBeInTheDocument();

    // Click on 03. Sandbox Gates
    fireEvent.click(screen.getByText("03. Sandbox Gates"));
    expect(screen.getByText(/gVisor Sandbox Telemetry/i)).toBeInTheDocument();

    // Click on 04. Cryptographic Proof
    fireEvent.click(screen.getByText("04. Cryptographic Proof"));
    expect(screen.getByText(/Ed25519 Signed Verification Evidence/i)).toBeInTheDocument();

    // Click on 05. Verified PR
    fireEvent.click(screen.getByText("05. Verified PR"));
    expect(screen.getByText(/Verified Pull Request #1 Delivered/i)).toBeInTheDocument();
  });

  it("renders FAQAccordion and toggles open/close state", () => {
    const items = [
      { question: "What is PatchProof?", answer: "An automated security patch synthesis agent." },
      { question: "Is network egress blocked?", answer: "Yes, gVisor sandboxes have 0 egress." },
    ];
    render(<FAQAccordion items={items} />);

    expect(screen.getByText("What is PatchProof?")).toBeInTheDocument();
    expect(screen.getByText("An automated security patch synthesis agent.")).toBeInTheDocument();

    // Click on second question to open it
    fireEvent.click(screen.getByText("Is network egress blocked?"));
    expect(screen.getByText("Yes, gVisor sandboxes have 0 egress.")).toBeInTheDocument();
  });

  it("validates ContactForm and displays thank-you confirmation state on submission", async () => {
    render(<ContactForm />);

    const submitBtn = screen.getByText("Submit Inquiry");
    fireEvent.click(submitBtn);

    // Fill form
    fireEvent.change(screen.getByPlaceholderText("Ada Lovelace"), {
      target: { value: "Linus Torvalds" },
    });
    fireEvent.change(screen.getByPlaceholderText("ada@company.com"), {
      target: { value: "linus@kernel.org" },
    });
    fireEvent.change(screen.getByPlaceholderText(/Describe your question/i), {
      target: { value: "Interested in self-hosting PatchProof in our private VPC." },
    });

    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Inquiry Received")).toBeInTheDocument();
      expect(screen.getByText(/Thank you, Linus Torvalds/i)).toBeInTheDocument();
      expect(screen.getByText(/typically within 1 business day/i)).toBeInTheDocument();
    });
  });

  it("renders all public pages without errors", () => {
    render(<HowItWorksPage />);
    expect(screen.getByText("How PatchProof Works")).toBeInTheDocument();

    render(<SecurityPage />);
    expect(screen.getByText("Security Architecture & Trust Guarantees")).toBeInTheDocument();

    render(<DocsPage />);
    expect(screen.getByText("PatchProof Developer Documentation")).toBeInTheDocument();

    render(<PricingPage />);
    expect(screen.getByText("Predictable Pricing. Zero Hidden Fees.")).toBeInTheDocument();

    render(<FAQPage />);
    expect(screen.getByText("Technical Answers & Security FAQ")).toBeInTheDocument();

    render(<ContactPage />);
    expect(screen.getByText("Contact Engineering & Support")).toBeInTheDocument();

    render(<PrivacyPage />);
    expect(screen.getByText("Privacy Policy")).toBeInTheDocument();

    render(<TermsPage />);
    expect(screen.getByText("Terms of Service")).toBeInTheDocument();

    render(<NotFound />);
    expect(screen.getByText("Page Not Found")).toBeInTheDocument();
  });
});
