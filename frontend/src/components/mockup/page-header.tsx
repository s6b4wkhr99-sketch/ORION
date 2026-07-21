import { cn } from "@/lib/utils";

type PageHeaderProps = {
  title?: string;
  subtitle: string;
  actions?: React.ReactNode;
  className?: string;
};

export function PageHeader({ title, subtitle, actions, className }: PageHeaderProps) {
  return (
    <div className={cn("flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between", className)}>
      <div>
        {title && <h1 className="text-2xl font-bold text-gray-900">{title}</h1>}
        <p className={cn("text-sm text-[var(--cios-secondary)]", title && "mt-1")}>{subtitle}</p>
      </div>
      {actions}
    </div>
  );
}
