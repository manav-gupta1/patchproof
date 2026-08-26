"use client";

import React, { useState } from "react";
import { ChevronDown } from "lucide-react";

export interface FAQItem {
  question: string;
  answer: string;
}

export function FAQAccordion({ items }: { items: FAQItem[] }) {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggle = (idx: number) => {
    setOpenIndex(openIndex === idx ? null : idx);
  };

  return (
    <div className="divide-y divide-border-subtle border border-border-subtle rounded-lg bg-surface-300 overflow-hidden font-sans text-xs">
      {items.map((item, idx) => {
        const isOpen = openIndex === idx;
        return (
          <div key={idx} className="transition-colors">
            <button
              onClick={() => toggle(idx)}
              className="w-full py-4 px-5 text-left flex items-center justify-between gap-4 text-zinc-200 hover:text-white transition-colors focus:outline-none focus-visible:bg-zinc-900/50"
              aria-expanded={isOpen}
            >
              <span className="font-medium text-sm text-zinc-100">{item.question}</span>
              <ChevronDown
                className={`w-4 h-4 text-zinc-400 shrink-0 transition-transform duration-200 ${
                  isOpen ? "rotate-180 text-zinc-200" : ""
                }`}
              />
            </button>
            {isOpen && (
              <div className="px-5 pb-5 pt-1 text-zinc-400 text-xs leading-relaxed border-t border-border-subtle/40">
                {item.answer}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
