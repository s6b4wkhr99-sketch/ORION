import { cn } from "@/lib/utils";

const STATUS_STYLES: Record<string, string> = {
  Active: "bg-emerald-100 text-emerald-800",
  Scheduled: "bg-blue-100 text-blue-800",
  Draft: "bg-gray-100 text-gray-700",
  Completed: "bg-violet-100 text-violet-800",
  Archived: "bg-orange-100 text-orange-800",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium", STATUS_STYLES[status] ?? "bg-gray-100 text-gray-700")}>
      {status}
    </span>
  );
}
