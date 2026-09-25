import type { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface MetricCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  accent?: 'indigo' | 'violet' | 'emerald' | 'amber';
}

const accentMap: Record<string, string> = {
  indigo: 'from-indigo-500/20 to-indigo-500/5 border-indigo-500/30',
  violet: 'from-violet-500/20 to-violet-500/5 border-violet-500/30',
  emerald: 'from-emerald-500/20 to-emerald-500/5 border-emerald-500/30',
  amber: 'from-amber-500/20 to-amber-500/5 border-amber-500/30',
};

const iconAccentMap: Record<string, string> = {
  indigo: 'text-indigo-400 bg-indigo-500/10',
  violet: 'text-violet-400 bg-violet-500/10',
  emerald: 'text-emerald-400 bg-emerald-500/10',
  amber: 'text-amber-400 bg-amber-500/10',
};

export function MetricCard({
  label,
  value,
  icon,
  trend,
  accent = 'indigo',
}: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className={`
        relative overflow-hidden rounded-xl border bg-gradient-to-br p-5
        backdrop-blur-sm transition-shadow hover:shadow-glow
        ${accentMap[accent]}
      `}
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-text-secondary">{label}</p>
          <p className="text-3xl font-bold tracking-tight text-text-primary">
            {value}
          </p>
          {trend && (
            <p
              className={`text-xs font-medium ${
                trend.isPositive ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}% vs last week
            </p>
          )}
        </div>
        {icon && (
          <div
            className={`rounded-lg p-2.5 ${iconAccentMap[accent]}`}
            aria-hidden="true"
          >
            {icon}
          </div>
        )}
      </div>
      {/* Decorative glow */}
      <div
        className="pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full bg-accent-primary/5 blur-2xl"
        aria-hidden="true"
      />
    </motion.div>
  );
}
