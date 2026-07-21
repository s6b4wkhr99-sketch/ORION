import { cn } from "@/lib/utils";

export function SystemStatusPanel({
  items,
}: {
  items?: { name: string; status: string }[];
}) {
  const systems = items?.length
    ? items
    : [
        { name: "Data Pipeline", status: "Operational" },
        { name: "Intelligence Engine", status: "Operational" },
        { name: "Recommendation Engine", status: "Operational" },
      ];
  return (
    <section className="cios-card p-5">
      <h2 className="mb-4 text-base font-semibold text-gray-900">System Status</h2>
      <ul className="space-y-3">
        {systems.map((s) => (
          <li key={s.name} className="flex items-center justify-between text-sm">
            <span className="text-gray-700">{s.name}</span>
            <span className="flex items-center gap-2">
              <span
                className={cn(
                  "h-2 w-2 rounded-full",
                  s.status === "Operational" ? "bg-[var(--cios-success)]" : "bg-amber-500",
                )}
              />
              <span
                className={cn(
                  "font-medium",
                  s.status === "Operational" ? "text-[var(--cios-success)]" : "text-amber-600",
                )}
              >
                {s.status}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
