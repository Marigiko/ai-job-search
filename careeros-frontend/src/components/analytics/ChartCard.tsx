import type { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  /** Approximate rows the chart fills — drives the loading skeleton height. */
  children: ReactNode;
  isLoading?: boolean;
  /** Optional footer region (e.g. legend, secondary metric). */
  footer?: ReactNode;
  className?: string;
}

export function ChartCard({
  title,
  subtitle,
  children,
  isLoading = false,
  footer,
  className = '',
}: ChartCardProps): JSX.Element {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className={`glass-panel rounded-lg p-5 flex flex-col ${className}`}
      aria-busy={isLoading}
      aria-label={title}
    >
      <header className="flex items-start justify-between gap-3 mb-4">
        <div>
          <h2 className="text-sm font-semibold text-text-primary tracking-tight">
            {title}
          </h2>
          {subtitle && (
            <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>
          )}
        </div>
      </header>

      <div className="flex-1 min-h-0 relative">
        {isLoading ? (
          <ChartSkeleton />
        ) : (
          children
        )}
      </div>

      {footer && (
        <div className="mt-4 pt-3 border-t border-border-subtle">{footer}</div>
      )}
    </motion.section>
  );
}

function ChartSkeleton(): JSX.Element {
  return (
    <div className="space-y-3 animate-pulse" aria-hidden="true">
      <div className="flex items-end gap-2 h-40">
        {Array.from({ length: 7 }).map((_, i) => (
          <div
            key={i}
            className="flex-1 rounded-t bg-surface-elevated"
            style={{ height: `${40 + ((i * 37) % 55)}%` }}
          />
        ))}
      </div>
      <div className="h-3 w-2/3 rounded bg-surface-elevated" />
    </div>
  );
}
