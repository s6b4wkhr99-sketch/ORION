"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

type LazyWhenVisibleProps = {
  children: ReactNode;
  fallback?: ReactNode;
  /** IntersectionObserver rootMargin — load slightly before entering viewport. */
  rootMargin?: string;
  className?: string;
  minHeight?: number | string;
};

function DefaultFallback({ minHeight }: { minHeight: number | string }) {
  return (
    <div
      className="animate-pulse rounded-xl bg-gray-100/80"
      style={{ minHeight: typeof minHeight === "number" ? `${minHeight}px` : minHeight }}
      aria-hidden
    />
  );
}

/** Renders children only after the placeholder enters (or nears) the viewport. */
export function LazyWhenVisible({
  children,
  fallback,
  rootMargin = "240px 0px",
  className,
  minHeight = 280,
}: LazyWhenVisibleProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (visible) return;
    const el = ref.current;
    if (!el) return;

    if (typeof IntersectionObserver === "undefined") {
      setVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin, threshold: 0.01 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [visible, rootMargin]);

  return (
    <div ref={ref} className={cn(className)}>
      {visible ? children : (fallback ?? <DefaultFallback minHeight={minHeight} />)}
    </div>
  );
}
