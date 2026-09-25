import { motion } from 'framer-motion';
import type { FollowUpItem } from '@/api/client';
import { formatRelative } from '@/utils/format';

interface FollowUpsListProps {
  items: FollowUpItem[];
}

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, x: -8 },
  show: { opacity: 1, x: 0 },
};

function OverdueBadge({ days }: { days: number }) {
  const isUrgent = days > 3;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
        isUrgent
          ? 'bg-red-500/20 text-red-400'
          : 'bg-amber-500/20 text-amber-400'
      }`}
    >
      {days === 0 ? 'Today' : `${days}d overdue`}
    </span>
  );
}

export function FollowUpsList({ items }: FollowUpsListProps) {
  if (items.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.25 }}
        className="rounded-xl border border-border bg-bg-secondary p-5"
      >
        <h3 className="text-base font-semibold text-text-primary">
          Pending Follow-ups
        </h3>
        <p className="mt-2 text-sm text-text-secondary">
          No follow-ups pending. You're all caught up!
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.25 }}
      className="rounded-xl border border-border bg-bg-secondary p-5"
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-text-primary">
            Pending Follow-ups
          </h3>
          <p className="text-sm text-text-secondary">
            {items.length} {items.length === 1 ? 'item' : 'items'} requiring attention
          </p>
        </div>
        <span className="rounded-full bg-accent-warning/20 px-2.5 py-1 text-xs font-semibold text-accent-warning">
          {items.filter((i) => i.days_overdue > 3).length} urgent
        </span>
      </div>

      <motion.ul
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="space-y-2"
        role="list"
        aria-label="Pending follow-ups"
      >
        {items.map((item) => (
          <motion.li
            key={item.application_id}
            variants={itemVariants}
            className="flex items-center justify-between rounded-lg border border-border-subtle bg-bg-tertiary/50 px-4 py-3 transition-colors hover:bg-surface-hover"
          >
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-text-primary">
                {item.job_title}
              </p>
              <p className="text-xs text-text-muted">
                {item.company_name ?? 'Unknown company'} · Applied{' '}
                {formatRelative(item.follow_up_date)}
              </p>
            </div>
            <div className="ml-3 flex shrink-0 items-center gap-3">
              <span className="hidden text-xs text-text-muted sm:inline">
                {item.status}
              </span>
              <OverdueBadge days={item.days_overdue} />
            </div>
          </motion.li>
        ))}
      </motion.ul>
    </motion.div>
  );
}
