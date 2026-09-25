import { motion, AnimatePresence } from 'framer-motion';
import { Inbox, X, Clock, AlertCircle } from 'lucide-react';
import { outreachApi } from '@/api/client';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatRelative } from '@/utils/format';

interface QueueManagerProps {
  readonly onRefresh?: () => void;
}

const rowVariants = {
  hidden: { opacity: 0, y: 6 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.03, duration: 0.2 },
  }),
  exit: { opacity: 0, x: 20, transition: { duration: 0.15 } },
};

function StatusDot({ status }: { readonly status: string }) {
  const colorMap: Record<string, string> = {
    queued: 'bg-accent-warning',
    sent: 'bg-accent-success',
    failed: 'bg-accent-danger',
    draft: 'bg-text-muted',
  };
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${colorMap[status] ?? 'bg-text-muted'}`}
      aria-label={`Status: ${status}`}
    />
  );
}

export function QueueManager({ onRefresh }: QueueManagerProps) {
  const queryClient = useQueryClient();

  const { data: queue = [], isLoading, refetch } = useQuery({
    queryKey: ['outreach-queue'],
    queryFn: outreachApi.getQueue,
    refetchInterval: 15_000,
  });

  const removeMutation = useMutation({
    mutationFn: (id: number) => outreachApi.removeFromQueue(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['outreach-queue'] });
      onRefresh?.();
    },
  });

  const handleRemove = async (id: number) => {
    await removeMutation.mutateAsync(id);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="glass-card p-6 space-y-4"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
          <Inbox className="w-5 h-5 text-accent-primary" />
          Queue
          {queue.length > 0 && (
            <span className="badge bg-accent-primary/20 text-accent-primary text-xs">
              {queue.length}
            </span>
          )}
        </h2>
        <button
          onClick={() => void refetch()}
          className="btn-ghost text-xs"
          aria-label="Refresh queue"
        >
          Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8 text-text-muted">
          <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
            <AlertCircle className="w-5 h-5" />
          </motion.div>
        </div>
      ) : queue.length === 0 ? (
        <div className="text-center py-8 space-y-2">
          <Inbox className="w-8 h-8 mx-auto text-text-muted opacity-50" />
          <p className="text-sm text-text-muted">Queue is empty. Compose an email to get started.</p>
        </div>
      ) : (
        <ul className="space-y-2 max-h-[320px] overflow-y-auto pr-1" role="list" aria-label="Email queue">
          <AnimatePresence mode="popLayout">
            {queue.map((item, i) => (
              <motion.li
                key={item.email_id}
                custom={i}
                variants={rowVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                layout
                className="rounded-md border border-border-subtle bg-surface p-3 glow-hover group"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center gap-2">
                      <StatusDot status={item.status} />
                      <span className="text-sm font-medium text-text-primary truncate">
                        {item.recipient}
                      </span>
                    </div>
                    <p className="text-xs text-text-secondary truncate pl-4">
                      {item.subject}
                    </p>
                    <div className="flex items-center gap-1.5 pl-4 text-[11px] text-text-muted">
                      <Clock className="w-3 h-3" />
                      {formatRelative(item.queued_at)}
                    </div>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => void handleRemove(item.email_id)}
                    disabled={removeMutation.isPending}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-md hover:bg-accent-danger/20 text-text-muted hover:text-accent-danger"
                    aria-label={`Remove ${item.recipient} from queue`}
                  >
                    <X className="w-3.5 h-3.5" />
                  </motion.button>
                </div>
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
      )}
    </motion.div>
  );
}
