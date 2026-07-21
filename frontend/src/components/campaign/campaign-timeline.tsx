"use client";

import { CheckCircle2, Circle } from "lucide-react";
import { cn, formatDateTimeEST } from "@/lib/utils";

type TimelineEvent = {
  event: string;
  timestamp: string | null;
  status: string;
};

export function CampaignTimeline({ events }: { events: TimelineEvent[] }) {
  return (
    <ol className="relative space-y-0 border-l border-[var(--cios-border)] pl-6">
      {events.map((ev, i) => {
        const done = ev.status === "completed";
        return (
          <li key={ev.event} className={cn("relative pb-6", i === events.length - 1 && "pb-0")}>
            <span
              className={cn(
                "absolute -left-[1.65rem] flex h-6 w-6 items-center justify-center rounded-full bg-white",
                done ? "text-[var(--cios-success)]" : "text-gray-300",
              )}
            >
              {done ? <CheckCircle2 className="h-5 w-5" /> : <Circle className="h-5 w-5" />}
            </span>
            <p className="text-sm font-medium text-gray-900">{ev.event}</p>
            <p className="text-xs text-[var(--cios-secondary)]">
              {ev.timestamp ? formatDateTimeEST(ev.timestamp) : "Pending"}
            </p>
          </li>
        );
      })}
    </ol>
  );
}
