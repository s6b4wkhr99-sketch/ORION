import { cn } from "@/lib/utils";

type EmptyStateProps = {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
};

export function EmptyState({ title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn("cios-card flex flex-col items-center justify-center p-16 text-center", className)}>
      <p className="text-lg text-gray-800">{title}</p>
      {description && <p className="mt-2 text-sm text-[var(--cios-secondary)]">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}
