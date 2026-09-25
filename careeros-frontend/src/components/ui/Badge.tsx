import { cn } from "@/utils/format";

type BadgeVariant =
  | "discovered"
  | "interested"
  | "applied"
  | "screening"
  | "interview"
  | "offer"
  | "rejected"
  | "default"
  | "success"
  | "warning"
  | "danger";

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
  dot?: boolean;
}

const variantClasses: Record<BadgeVariant, string> = {
  discovered: "bg-slate-500/20 text-slate-400 border-slate-500/30",
  interested: "bg-violet-500/20 text-violet-400 border-violet-500/30",
  applied: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
  screening: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  interview: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  offer: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  rejected: "bg-red-500/20 text-red-400 border-red-500/30",
  default: "bg-bg-tertiary text-text-secondary border-border",
  success: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  warning: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  danger: "bg-red-500/20 text-red-400 border-red-500/30",
};

export function Badge({
  variant = "default",
  children,
  className,
  dot = false,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        variantClasses[variant],
        className,
      )}
    >
      {dot && (
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            variant === "discovered" && "bg-slate-400",
            variant === "interested" && "bg-violet-400",
            variant === "applied" && "bg-indigo-400",
            variant === "screening" && "bg-amber-400",
            variant === "interview" && "bg-emerald-400",
            variant === "offer" && "bg-emerald-300",
            variant === "rejected" && "bg-red-400",
            variant === "default" && "bg-text-muted",
            variant === "success" && "bg-emerald-400",
            variant === "warning" && "bg-amber-400",
            variant === "danger" && "bg-red-400",
          )}
        />
      )}
      {children}
    </span>
  );
}
