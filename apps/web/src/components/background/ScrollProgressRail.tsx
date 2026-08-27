"use client";

import React, { useEffect, useState } from "react";

const STAGES = [
  { id: "detect", num: "01", label: "DETECT", targetId: "section-detect" },
  { id: "analyze", num: "02", label: "ANALYZE", targetId: "section-analyze" },
  { id: "patch", num: "03", label: "PATCH", targetId: "section-patch" },
  { id: "verify", num: "04", label: "VERIFY", targetId: "section-verify" },
  { id: "proof", num: "05", label: "PROOF", targetId: "section-proof" },
  { id: "write", num: "06", label: "WRITE", targetId: "section-write" },
];

export function ScrollProgressRail() {
  const [activeStage, setActiveStage] = useState<string>("detect");

  useEffect(() => {
    if (typeof window === "undefined" || !window.IntersectionObserver) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            const stage = STAGES.find((s) => s.targetId === id);
            if (stage) {
              setActiveStage(stage.id);
            }
          }
        });
      },
      { rootMargin: "-40% 0px -40% 0px", threshold: 0 } // Triggers when section is near middle of screen
    );

    STAGES.forEach((stage) => {
      const el = document.getElementById(stage.targetId);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div className="hidden lg:flex fixed left-6 xl:left-12 top-0 bottom-0 flex-col justify-center z-50 pointer-events-none">
      {/* Telemetry Rail Container */}
      <div className="flex flex-col relative py-8">
        {/* Continuous background rail line */}
        <div className="absolute left-[5px] top-0 bottom-0 w-[2px] bg-zinc-900/60" />
        
        <div className="flex flex-col gap-10">
          {STAGES.map((stage, index) => {
            const isActive = activeStage === stage.id;
            const isPassed = STAGES.findIndex((s) => s.id === activeStage) >= index;
            
            return (
              <div key={stage.id} className="relative flex items-center group">
                {/* Connector Line Fill - overlay on top of the background line */}
                {index !== 0 && (
                  <div 
                    className={`absolute bottom-full left-[5px] w-[2px] h-10 transition-colors duration-700 origin-bottom
                      ${isPassed ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]" : "bg-transparent"}`}
                  />
                )}
                
                {/* Node Box */}
                <div 
                  className={`w-3 h-3 z-10 transition-all duration-500 border
                    ${isActive ? "bg-emerald-400 border-emerald-300 shadow-[0_0_12px_rgba(52,211,153,0.8)] rotate-45 scale-125" 
                    : isPassed ? "bg-emerald-950 border-emerald-800 rotate-45 scale-100" 
                    : "bg-zinc-950 border-zinc-700 rotate-45 scale-75"}`}
                />
                
                {/* Label & Metadata */}
                <div 
                  className={`absolute left-8 flex flex-col justify-center transition-all duration-500
                    ${isActive ? "opacity-100 translate-x-0" : "opacity-40 -translate-x-2"}`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-mono font-bold text-zinc-500 tracking-widest">[{stage.num}]</span>
                    <span className={`text-[10px] font-mono tracking-widest font-bold ${isActive ? "text-emerald-400" : "text-zinc-600"}`}>
                      {stage.label}
                    </span>
                  </div>
                  {/* Active telemetry reading */}
                  {isActive && (
                    <div className="text-[8px] font-mono text-emerald-500/60 mt-0.5 whitespace-nowrap">
                      SECTOR_ONLINE_OK
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
