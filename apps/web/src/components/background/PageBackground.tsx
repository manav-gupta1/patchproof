/**
 * PageBackground — The layered environmental background for PatchProof.
 *
 * This component renders the complete visual environment BEHIND all page content.
 * It is intentionally a single, fixed/absolute layer system rather than
 * per-section decoration.
 *
 * Layer order (bottom to top):
 *   0. Page vignette (fixed, outer-edge darkening)
 *   1. Full-page architectural guide rails (fixed verticals)
 *   2. Global engineering grid (absolute, full page)
 *   3. Global scanline texture
 *   4. Section-level atmospheric radial fields  ← per-section wrappers handle this
 *   5. Structural large geometry (rings, diagonals, shafts)
 *
 * ALL layers are pointer-events: none and aria-hidden.
 * NO Three.js / canvas / image assets used.
 */

import React from "react";

export function PageBackground() {
  return (
    <>
      {/* ── VIGNETTE — outer-edge darkening for depth ── */}
      <div className="page-vignette" aria-hidden="true" />

      {/* ── FULL-PAGE ARCHITECTURAL GUIDE RAILS ── */}
      {/* Left content boundary rail */}
      <div className="page-rail-left" aria-hidden="true" />
      {/* Right content boundary rail */}
      <div className="page-rail-right" aria-hidden="true" />

      {/*
        ── GLOBAL ENGINEERING GRID ──
        Covers the entire page. Masked more strongly toward edges.
        5.5% opacity — registers clearly as "infrastructure" against near-black.
      */}
      <div
        className="fixed inset-0 bg-grid pointer-events-none -z-10"
        aria-hidden="true"
        style={{
          maskImage:
            "radial-gradient(ellipse 90% 80% at 55% 40%, #000 20%, rgba(0,0,0,0.5) 60%, transparent 100%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 90% 80% at 55% 40%, #000 20%, rgba(0,0,0,0.5) 60%, transparent 100%)",
        }}
      />

      {/*
        ── GLOBAL SCANLINE TEXTURE ──
        Breaks up flat gradient surfaces. 0.8% — material without brightness.
      */}
      <div
        className="fixed inset-0 bg-scanlines pointer-events-none -z-10 opacity-80"
        aria-hidden="true"
      />

      {/*
        ── HERO-ZONE PRIMARY MACHINE ILLUMINATION ──
        The 3D chamber is the light source. This radial field extends well beyond
        the object to make the environment feel physically large.
        Origin: right side of the hero (~right: -5%, top: -10%).
      */}
      <div
        className="fixed pointer-events-none -z-10"
        aria-hidden="true"
        style={{
          top: "-10%",
          right: "-5%",
          width: "min(1100px, 80vw)",
          height: "min(1100px, 80vw)",
          background: `radial-gradient(
            ellipse 65% 70% at 60% 40%,
            rgba(16,185,129,0.17) 0%,
            rgba(16,185,129,0.07) 35%,
            rgba(6,78,59,0.03)   60%,
            transparent 82%
          )`,
        }}
      />

      {/*
        ── HERO-ZONE HUGE INSPECTION RING ──
        A large faint circle suggesting the 3D chamber is one component
        in a much larger containment / inspection system.
        This ring is cropped by the viewport — you only see an arc.
      */}
      <div
        className="fixed pointer-events-none -z-10"
        aria-hidden="true"
        style={{
          top: "50%",
          right: "-20%",
          transform: "translateY(-50%)",
          width: "min(900px, 65vw)",
          height: "min(900px, 65vw)",
          borderRadius: "50%",
          border: "1px solid rgba(16,185,129,0.065)",
        }}
      />

      {/*
        ── HERO-ZONE SECONDARY OUTER RING ──
        Larger, fainter ring — depth layering behind the chamber.
      */}
      <div
        className="fixed pointer-events-none -z-10"
        aria-hidden="true"
        style={{
          top: "50%",
          right: "-35%",
          transform: "translateY(-50%)",
          width: "min(1300px, 90vw)",
          height: "min(1300px, 90vw)",
          borderRadius: "50%",
          border: "1px solid rgba(16,185,129,0.028)",
        }}
      />

      {/*
        ── VERTICAL EMERALD SHAFT ──
        A single thin vertical accent line behind the right column.
        Aligns with ~65% of the page width — the center of the 3D chamber.
        Communicates: "there is a vertical system axis here".
      */}
      <div
        className="bg-v-shaft fixed pointer-events-none -z-10"
        aria-hidden="true"
        style={{ left: "63%", top: 0, bottom: 0 }}
      />

      {/*
        ── LARGE STRUCTURAL BAND — mid-page ──
        A very faint horizontal line at ~50vh connecting the hero
        to the sections below. Works as an invisible separator
        that the eye uses to orient within the page.
      */}
      <div
        className="fixed left-0 right-0 pointer-events-none -z-10"
        aria-hidden="true"
        style={{
          top: "92vh",
          height: "1px",
          background:
            "linear-gradient(to right, transparent 5%, rgba(255,255,255,0.06) 25%, rgba(255,255,255,0.06) 75%, transparent 95%)",
        }}
      />
    </>
  );
}
