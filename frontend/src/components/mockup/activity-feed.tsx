import { cn } from "@/lib/utils";

type ActivityItem = { title: string; detail: string; time: string };

export function ActivityFeed({ items }: { items: ActivityItem[] }) {
  if (!items.length) {
    return (
      <section className="cios-card p-5">
        <h2 className="mb-4 text-base font-semibold text-gray-900">Recent Activity</h2>
        <p className="text-sm text-[var(--cios-secondary)]">No recent activity recorded.</p>
      </section>
    );
  }
  return (
    <section className="cios-card p-5">
      <h2 className="mb-4 text-base font-semibold text-gray-900">Recent Activity</h2>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {items.map((item) => (
          <div
            key={`${item.title}-${item.time}`}
            className="min-w-[220px] shrink-0 rounded-lg border border-[var(--cios-border)] bg-gradient-to-b from-white to-gray-50/80 p-3 shadow-sm"
          >
            <p className="text-xs font-semibold text-[var(--cios-primary)]">{item.title}</p>
            <p className="mt-1 text-sm text-gray-800">{item.detail}</p>
            <p className="mt-2 text-xs text-[var(--cios-secondary)]">{item.time}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
