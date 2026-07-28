"use client";

import { useEffect, useMemo, useState } from "react";
import { LeFrameLogo } from "@/components/layout/le-frame-logo";
import { cn } from "@/lib/utils";

export const LOGIN_MOTION_HEIGHT = 148;

type WordPhase = "opportunity" | "recognition" | "intelligence" | "optimization" | "navigator";
type Phase = "logo" | WordPhase | "orion-final";

const WORD_LABELS: Record<WordPhase, string> = {
  opportunity: "Opportunity",
  recognition: "Recognition",
  intelligence: "Intelligence",
  optimization: "Optimization",
  navigator: "Navigator",
};

/** One-shot timeline (ms). Each step animates in → fade out; final step holds. */
const TIMELINE: Array<{ phase: Phase; duration: number }> = [
  { phase: "logo", duration: 1400 },
  { phase: "opportunity", duration: 1100 },
  { phase: "recognition", duration: 1100 },
  { phase: "intelligence", duration: 1100 },
  { phase: "optimization", duration: 1100 },
  { phase: "navigator", duration: 1100 },
  { phase: "orion-final", duration: 0 },
];

const ACRONYM_CLASS = "text-4xl font-bold tracking-tight sm:text-5xl";

function FinalOrion() {
  return (
    <div className="flex flex-col items-center justify-center gap-2">
      <p className={cn("login-acronym login-acronym-merge-in", ACRONYM_CLASS, "text-[var(--orion-accent)]")}>
        ORION
      </p>
      <p className="login-tagline-in text-xs text-[var(--cios-secondary)] sm:text-sm">Campaign Decision Intelligence</p>
    </div>
  );
}

export function LoginBrandMotion() {
  const [phase, setPhase] = useState<Phase>("logo");
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => setReducedMotion(media.matches);
    apply();
    media.addEventListener("change", apply);
    return () => media.removeEventListener("change", apply);
  }, []);

  useEffect(() => {
    if (reducedMotion) {
      setPhase("orion-final");
      return;
    }

    let cancelled = false;
    let timeoutId = 0;
    let index = 0;

    const tick = () => {
      if (cancelled) return;
      const current = TIMELINE[index];
      setPhase(current.phase);
      if (current.duration <= 0) return;

      timeoutId = window.setTimeout(() => {
        index += 1;
        if (index < TIMELINE.length) tick();
      }, current.duration);
    };

    tick();
    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [reducedMotion]);

  const ariaLabel = useMemo(() => {
    if (phase === "orion-final") return "ORION — Campaign Decision Intelligence";
    if (phase in WORD_LABELS) return WORD_LABELS[phase as WordPhase];
    return "Le Frame";
  }, [phase]);

  if (reducedMotion) {
    return (
      <div className="login-motion-stage" style={{ minHeight: LOGIN_MOTION_HEIGHT }}>
        <FinalOrion />
      </div>
    );
  }

  const wordLabel = phase in WORD_LABELS ? WORD_LABELS[phase as WordPhase] : null;

  return (
    <div
      className="login-motion-stage"
      style={{ minHeight: LOGIN_MOTION_HEIGHT }}
      aria-live="polite"
      aria-atomic="true"
    >
      <p className="sr-only">{ariaLabel}</p>

      {/* 1. Le Frame logo — dynamic in → fade out */}
      {phase === "logo" ? (
        <div className="absolute inset-0 flex items-center justify-center">
          <div key="logo" className="login-logo-dynamic">
            <LeFrameLogo height={48} />
          </div>
        </div>
      ) : null}

      {/* 2–6. ORION words — motion in → fade out (ORION size) */}
      {wordLabel ? (
        <div className="absolute inset-0 flex items-center justify-center px-4">
          <p
            key={phase}
            className={cn(ACRONYM_CLASS, "login-word-in-out text-center text-[var(--orion-accent)]")}
          >
            {wordLabel}
          </p>
        </div>
      ) : null}

      {/* 7. ORION + tagline — dynamic in, final hold */}
      {phase === "orion-final" ? (
        <div className="absolute inset-0 flex items-center justify-center">
          <FinalOrion />
        </div>
      ) : null}
    </div>
  );
}
