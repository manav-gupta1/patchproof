"use client";

import React, { useEffect, useState, useRef } from "react";

export function PageEnvironment() {
  const [scrollY, setScrollY] = useState(0);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [reducedMotion, setReducedMotion] = useState(false);
  const requestRef = useRef<number | null>(null);
  const latestScrollY = useRef(0);
  const latestMousePos = useRef({ x: 0, y: 0 });

  useEffect(() => {
    // Check prefers-reduced-motion
    let mediaQuery: MediaQueryList | null = null;
    const handleMotionChange = (e: MediaQueryListEvent) => {
      setReducedMotion(e.matches);
    };

    if (typeof window !== "undefined" && typeof window.matchMedia === "function") {
      mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
      setReducedMotion(mediaQuery.matches);
      mediaQuery.addEventListener("change", handleMotionChange);
    }

    // Track scroll
    const handleScroll = () => {
      latestScrollY.current = window.scrollY;
    };

    // Track mouse position relative to viewport center
    const handleMouseMove = (e: MouseEvent) => {
      const { innerWidth, innerHeight } = window;
      const x = e.clientX - innerWidth / 2;
      const y = e.clientY - innerHeight / 2;
      latestMousePos.current = { x, y };
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("mousemove", handleMouseMove, { passive: true });

    // Loop for smooth CSS updates
    const updateMotion = () => {
      setScrollY(latestScrollY.current);
      setMousePos(latestMousePos.current);
      requestRef.current = requestAnimationFrame(updateMotion);
    };

    requestRef.current = requestAnimationFrame(updateMotion);

    return () => {
      if (mediaQuery) {
        mediaQuery.removeEventListener("change", handleMotionChange);
      }
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("mousemove", handleMouseMove);
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, []);

  // Calculate layer translations (parallax)
  // If reducedMotion is true, all translations are 0.
  const getLayerStyle = (depthFactor: number, scrollFactor: number) => {
    if (reducedMotion) return {};
    const tx = mousePos.x * depthFactor * 0.04;
    const ty = mousePos.y * depthFactor * 0.04;
    const sy = scrollY * scrollFactor;
    return {
      transform: `translate3d(${tx}px, calc(${ty}px - ${sy}px), 0)`,
      transition: "transform 0.15s cubic-bezier(0.25, 1, 0.5, 1)",
    };
  };

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden select-none z-0">
      {/* ── LAYER 1: FAR BACKGROUND (Depth Factor: 0.05, Scroll Factor: 0.05) ── */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={getLayerStyle(0.05, 0.05)}
      >
        {/* Massive Far-Aperture Ring behind Hero / Problem */}
        <div
          className="absolute rounded-full border-[2px] border-zinc-900/30"
          style={{
            top: "-10vh",
            right: "-200px",
            width: "1800px",
            height: "1800px",
            maskImage: "radial-gradient(circle at center, #000 20%, transparent 80%)",
            WebkitMaskImage: "radial-gradient(circle at center, #000 20%, transparent 80%)",
          }}
        />
        <div
          className="absolute rounded-full border border-zinc-900/20"
          style={{
            top: "5vh",
            right: "-50px",
            width: "1500px",
            height: "1500px",
            maskImage: "radial-gradient(circle at center, #000 20%, transparent 80%)",
            WebkitMaskImage: "radial-gradient(circle at center, #000 20%, transparent 80%)",
          }}
        />

        {/* Far Background Structural Wall Plate (Occlusion Layer) */}
        <div
          className="absolute bg-[#08080a] border border-zinc-950/80 shadow-[0_0_80px_rgba(0,0,0,0.8)]"
          style={{
            top: "140vh",
            left: "8%",
            width: "450px",
            height: "700px",
          }}
        />

        {/* Far Background Support Columns */}
        <div
          className="absolute w-[60px] bg-gradient-to-b from-zinc-950/20 via-zinc-900/10 to-zinc-950/20 border-r border-zinc-900/30"
          style={{ left: "15%", top: 0, bottom: 0 }}
        />
        <div
          className="absolute w-[40px] bg-gradient-to-b from-zinc-950/20 via-zinc-900/10 to-zinc-950/20 border-l border-zinc-900/30"
          style={{ right: "12%", top: 0, bottom: 0 }}
        />
      </div>

      {/* ── LAYER 2: PERSPECTIVE FLOOR (In Midground but distinct) ── */}
      {/*
        Perspective Converging Floor Grid (Blueprint grid floor)
        Located between Hero and Problem Sections (extends down into the page)
      */}
      <div
        className="absolute w-[200vw] h-[150vh] origin-top pointer-events-none"
        style={{
          top: "45vh",
          left: "-50vw",
          perspective: "1000px",
          perspectiveOrigin: "50% 20%",
          maskImage: "radial-gradient(ellipse 60% 80% at 50% 30%, #000 20%, transparent 80%)",
          WebkitMaskImage: "radial-gradient(ellipse 60% 80% at 50% 30%, #000 20%, transparent 80%)",
          ...getLayerStyle(0.12, 0.1)
        }}
      >
        <div
          className="w-full h-full bg-grid"
          style={{
            transform: "rotateX(75deg) translateZ(0)",
            backgroundSize: "72px 72px",
            backgroundImage: `
              linear-gradient(to right, rgba(255, 255, 255, 0.055) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(255, 255, 255, 0.055) 1px, transparent 1px)
            `,
          }}
        />
      </div>

      {/* ── LAYER 3: MIDGROUND STRUCTURES (Depth Factor: 0.15, Scroll Factor: 0.12) ── */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={getLayerStyle(0.15, 0.12)}
      >
        {/* Giant Structural Aperture frame behind Hero */}
        <div
          className="absolute border-[2px] border-zinc-900/70 bg-zinc-950/30 rounded-xl"
          style={{
            top: "10vh",
            right: "4%",
            width: "min(950px, 55vw)",
            height: "85vh",
          }}
        >
          {/* Subtle status tag on the frame */}
          <div className="absolute top-4 left-6 font-mono text-xs text-zinc-600 tracking-widest">
            FACILITY_FRAME // C-ZONE_42
          </div>
          {/* Internal architectural lines within the frame */}
          <div className="absolute inset-10 border border-zinc-900/30 rounded-lg" />
        </div>

        {/* ── TECHNICAL WORLD MAP / TOPOLOGY (Behind Hero Left) ── */}
        <div
          className="absolute pointer-events-none opacity-30"
          style={{
            top: "10vh",
            left: "-10vw",
            width: "60vw",
            height: "80vh",
            maskImage: "radial-gradient(ellipse 50% 50% at 50% 50%, #000 30%, transparent 80%)",
            WebkitMaskImage: "radial-gradient(ellipse 50% 50% at 50% 50%, #000 30%, transparent 80%)",
          }}
        >
          <svg className="w-full h-full" viewBox="0 0 1000 1000" fill="none" xmlns="http://www.w3.org/2000/svg">
            <g stroke="rgba(14, 165, 233, 0.4)" strokeWidth="1" opacity="0.6">
              {/* Abstract connected topology */}
              <circle cx="300" cy="400" r="4" fill="rgba(14, 165, 233, 0.8)" />
              <circle cx="500" cy="200" r="3" fill="rgba(14, 165, 233, 0.8)" />
              <circle cx="700" cy="500" r="5" fill="rgba(14, 165, 233, 0.8)" />
              <circle cx="200" cy="700" r="3" fill="rgba(14, 165, 233, 0.8)" />
              <circle cx="800" cy="800" r="4" fill="rgba(14, 165, 233, 0.8)" />
              <path d="M300 400 Q400 300 500 200" strokeDasharray="4 4" />
              <path d="M500 200 Q600 350 700 500" />
              <path d="M300 400 Q500 450 700 500" strokeWidth="0.5" />
              <path d="M300 400 Q250 550 200 700" />
              <path d="M700 500 Q750 650 800 800" strokeDasharray="2 4" />
              <path d="M200 700 Q500 750 800 800" strokeWidth="0.5" />
            </g>
            <g stroke="rgba(255, 255, 255, 0.08)" strokeWidth="0.5">
              {/* Concentric scanning regions */}
              <circle cx="500" cy="500" r="200" />
              <circle cx="500" cy="500" r="350" />
              <circle cx="500" cy="500" r="450" />
            </g>
          </svg>
        </div>

        {/* ── HERO SPECIFIC VIEWPORT RINGS ── */}
        <div
          className="absolute rounded-full border-[1.5px] border-emerald-950/40"
          style={{
            top: "42vh",
            right: "12%",
            width: "800px",
            height: "800px",
            maskImage: "radial-gradient(circle at center, #000 40%, transparent 100%)",
            WebkitMaskImage: "radial-gradient(circle at center, #000 40%, transparent 100%)",
          }}
        />
        <div
          className="absolute rounded-full border border-emerald-900/20"
          style={{
            top: "38vh",
            right: "8%",
            width: "950px",
            height: "950px",
            maskImage: "radial-gradient(circle at center, #000 40%, transparent 100%)",
            WebkitMaskImage: "radial-gradient(circle at center, #000 40%, transparent 100%)",
          }}
        />

        {/* ── PROBLEM SECTION: SPLIT STRUCTURAL ENVIRONMENT ── */}
        {/* Left Side: Unstable/broken structural field */}
        <div className="absolute left-[5%] top-[125vh] w-[40vw] space-y-6">
          <div className="w-[85%] h-px bg-rose-950/20" />
          <div className="w-[60%] h-px bg-rose-900/10 ml-[20%]" />
          {/* Offset/disconnected horizontal beam */}
          <div className="w-[80%] h-8 border border-dashed border-rose-950/30 rounded bg-zinc-950/40" style={{ transform: "rotate(-1.5deg)" }}>
            <div className="absolute inset-y-0 left-4 flex items-center font-mono text-[8px] text-rose-900/60">
              STRUCT_BOUNDARY: CORRUPTED // SEGMENT_FAIL
            </div>
          </div>
        </div>

        {/* Right Side: Controlled/stable structural field */}
        <div className="absolute right-[5%] top-[125vh] w-[40vw] space-y-6">
          <div className="w-[90%] h-px bg-emerald-950/40" />
          <div className="w-[90%] h-px bg-emerald-950/30 ml-[5%]" />
          {/* Aligned solid architectural beam */}
          <div className="w-[90%] h-8 border border-emerald-950/40 rounded bg-zinc-950/70">
            <div className="absolute inset-y-0 left-6 flex items-center font-mono text-[8px] text-emerald-500/40 font-bold">
              SYSTEM_STATE: SEALED // VERIFICATION_PASS
            </div>
          </div>
        </div>

        {/* ── ARCHITECTURE SECTION: HORIZONTAL TUNNEL BEAMS ── */}
        {/* Large steel horizontal girders behind the 4 stages */}
        <div
          className="absolute left-0 right-0 bg-gradient-to-r from-transparent via-zinc-950 to-transparent border-y border-zinc-900/40"
          style={{
            top: "230vh",
            height: "120px",
          }}
        >
          <div className="absolute inset-y-0 left-[10%] right-[10%] border-x border-zinc-900/20 flex justify-between px-10 items-center">
            <span className="font-mono text-xs text-zinc-600 tracking-wider">SEC_CHANNEL_01</span>
            <span className="font-mono text-xs text-zinc-600 tracking-wider">DATA_FLOW_VERIFIED</span>
          </div>
        </div>

        {/* ── PROOF SECTION: RECESSED APERTURE PANEL (OCCLUSION LAYER) ── */}
        {/*
          This acts as a solid dark block behind the verification showcase.
          It blocks the grids and shapes behind it, casting shadows, making the tabbed console float.
        */}
        <div
          className="absolute bg-[#08080a] border border-zinc-900/80 rounded-2xl shadow-[0_30px_100px_rgba(0,0,0,0.9)]"
          style={{
            top: "320vh",
            left: "50%",
            transform: "translateX(-50%)",
            width: "min(1450px, 92vw)",
            height: "650px",
          }}
        >
          <div className="absolute top-5 left-8 font-mono text-xs text-zinc-500">
            INSPECTION_CHAMBER_SHIELD // STATUS: SECURE
          </div>
        </div>

        {/* ── CONSOLE: COMMAND CENTER OVERHEAD BEAM ── */}
        <div
          className="absolute bg-zinc-950 border-b border-zinc-900/70"
          style={{
            top: "435vh",
            left: 0,
            right: 0,
            height: "70px",
          }}
        >
          <div className="max-w-[1520px] mx-auto h-full px-12 flex items-center justify-between font-mono text-xs text-zinc-600">
            <span>CONSOLE_NODE_ONLINE</span>
            <span>ENFORCING FAIL-CLOSED BOUNDARIES</span>
          </div>
        </div>

        {/* ── SECURITY BOUNDARY: NESTED BOUNDARY APERTURES ── */}
        <div
          className="absolute border-[3px] border-zinc-950/80 rounded-2xl"
          style={{
            top: "530vh",
            left: "8%",
            width: "300px",
            height: "300px",
          }}
        />
        <div
          className="absolute border border-dashed border-zinc-900/30 rounded-xl"
          style={{
            top: "532vh",
            left: "9%",
            width: "280px",
            height: "280px",
          }}
        />
      </div>

      {/* ── LAYER 4: FOREGROUND ELEMENTS (Depth Factor: 0.32, Scroll Factor: 0.22) ── */}
      {/*
        These objects move faster and appear to hover in front of some backgrounds,
        passing behind the actual foreground content.
      */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={getLayerStyle(0.32, 0.22)}
      >
        {/* Massive Diagonal structural frame beam crossing on the far left */}
        <div
          className="absolute bg-gradient-to-b from-zinc-900/30 via-zinc-950/10 to-zinc-900/30 border-r border-zinc-900/50"
          style={{
            top: "80vh",
            left: "2%",
            width: "8px",
            height: "90vh",
            transform: "rotate(-12deg)",
            transformOrigin: "top left",
          }}
        />

        {/* Giant architectural girder in the middle transition zone */}
        <div
          className="absolute h-[6px] bg-zinc-900/40 border-y border-zinc-800/40"
          style={{
            top: "195vh",
            left: "5%",
            width: "40vw",
          }}
        />

        {/* Foreground Telemetry Shaft on the far right */}
        <div
          className="absolute w-[4px] bg-emerald-500/10"
          style={{
            top: "270vh",
            right: "4%",
            height: "120vh",
          }}
        >
          <div className="absolute top-20 right-4 font-mono text-xs text-zinc-600 tracking-[0.2em] transform rotate-90 origin-top-right whitespace-nowrap">
            TELEMETRY_BUS // EMERALD_STATE // ZERO_EXCESS
          </div>
        </div>

        {/* Floating Telemetry Markers */}
        <div className="absolute font-mono text-[9px] text-zinc-500/60" style={{ top: "35vh", left: "42%" }}>
          [ SYS: OPTIMAL ]<br/>SEC_ID_904
        </div>
        <div className="absolute font-mono text-[9px] text-emerald-500/50" style={{ top: "60vh", right: "28%" }}>
          + VERIFYING<br/>0x0F482B
        </div>
        
        {/* Occasional floating technical lines */}
        <div className="absolute h-px w-[120px] bg-cyan-900/40" style={{ top: "45vh", left: "15%" }} />
        <div className="absolute h-[2px] w-[4px] bg-cyan-400/60" style={{ top: "44.9vh", left: "15%" }} />

        {/* Concentrated local lights have been moved to .atm- classes in globals.css */}
      </div>
    </div>
  );
}
