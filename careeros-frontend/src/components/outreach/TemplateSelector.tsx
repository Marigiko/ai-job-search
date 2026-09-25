import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, GitBranch, BarChart3, Check, Plus, Trash2 } from 'lucide-react';
import { templatesApi } from '@/api/client';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { EmailTemplate, EmailTemplateCreate } from '@/types';
import { cn } from '@/utils/format';

interface TemplateSelectorProps {
  readonly onSelect: (template: EmailTemplate) => void;
  readonly selectedId: number | null;
}

const itemVariants = {
  hidden: { opacity: 0, x: -8 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { delay: i * 0.04, duration: 0.2 },
  }),
};

function AbBadge({ variant }: { readonly variant: string | null }) {
  if (!variant) return null;
  const color = variant === 'A' ? 'text-accent-primary' : 'text-accent-secondary';
  return (
    <span className={cn('badge bg-bg-tertiary font-mono text-[10px] uppercase', color)}>
      v{variant}
    </span>
  );
}

function ReplyRateBar({ rate }: { readonly rate: number | null }) {
  if (rate === null) return <span className="text-text-muted text-xs">No data</span>;
  const pct = Math.round(rate * 100);
  return (
    <div className="flex items-center gap-2 w-full max-w-[120px]">
      <div className="flex-1 h-1.5 bg-surface rounded-full overflow-hidden" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-accent-primary to-accent-secondary"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
      <span className="text-xs text-text-muted font-mono">{pct}%</span>
    </div>
  );
}

export function TemplateSelector({ onSelect, selectedId }: TemplateSelectorProps) {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: templatesApi.list,
  });

  const createMutation = useMutation({
    mutationFn: (payload: EmailTemplateCreate) => templatesApi.create(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['templates'] });
      setShowCreate(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => templatesApi.remove(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['templates'] });
    },
  });

  const handleCreate = useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      const form = e.currentTarget;
      const fd = new FormData(form);
      const payload: EmailTemplateCreate = {
        name: fd.get('name') as string,
        subject_template: fd.get('subject') as string,
        body_template: fd.get('body') as string,
        language: (fd.get('language') as string) || 'en',
        is_ab_test: fd.get('is_ab_test') === 'on',
        ab_variant: (fd.get('ab_variant') as string) || null,
      };
      createMutation.mutate(payload);
    },
    [createMutation],
  );

  const abTests = templates.filter((t) => t.is_ab_test);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="glass-card p-6 space-y-4"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
          <FileText className="w-5 h-5 text-accent-secondary" />
          Templates
        </h2>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowCreate((p) => !p)}
          className="btn-ghost text-sm"
        >
          <Plus className="w-4 h-4" />
          New
        </motion.button>
      </div>

      {/* A/B Test Summary */}
      {abTests.length > 0 && (
        <div className="rounded-md border border-accent-secondary/20 bg-accent-secondary/5 p-3 space-y-2">
          <div className="flex items-center gap-2 text-xs font-medium text-accent-secondary uppercase tracking-wide">
            <GitBranch className="w-3.5 h-3.5" />
            Active A/B Tests
          </div>
          <div className="flex flex-wrap gap-2">
            {abTests.map((t) => (
              <span key={t.id} className="badge bg-bg-tertiary text-text-secondary">
                {t.name}
                <AbBadge variant={t.ab_variant} />
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Template List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-8 text-text-muted">
          <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}>
            <BarChart3 className="w-5 h-5" />
          </motion.div>
        </div>
      ) : templates.length === 0 ? (
        <p className="text-sm text-text-muted text-center py-6">
          No templates yet. Create one to get started.
        </p>
      ) : (
        <ul className="space-y-2 max-h-[360px] overflow-y-auto pr-1" role="listbox" aria-label="Email templates">
          {templates.map((template, i) => (
            <motion.li
              key={template.id}
              custom={i}
              variants={itemVariants}
              initial="hidden"
              animate="visible"
            >
              <button
                onClick={() => onSelect(template)}
                className={cn(
                  'w-full text-left rounded-md border p-3 transition-all glow-hover group',
                  selectedId === template.id
                    ? 'border-accent-primary/50 bg-accent-primary/10'
                    : 'border-border-subtle bg-surface hover:border-border',
                )}
                role="option"
                aria-selected={selectedId === template.id}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-text-primary truncate">
                        {template.name}
                      </span>
                      <AbBadge variant={template.ab_variant} />
                    </div>
                    <p className="text-xs text-text-muted mt-1 truncate">
                      {template.subject_template}
                    </p>
                    <div className="flex items-center gap-3 mt-2">
                      <ReplyRateBar rate={template.reply_rate} />
                      <span className="text-[10px] text-text-muted font-mono">
                        {template.usage_count} uses
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    {selectedId === template.id && (
                      <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
                        <Check className="w-4 h-4 text-accent-primary" />
                      </motion.div>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        void deleteMutation.mutateAsync(template.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-accent-danger/20 text-text-muted hover:text-accent-danger"
                      aria-label={`Delete template ${template.name}`}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </button>
            </motion.li>
          ))}
        </ul>
      )}

      {/* Create Form */}
      <AnimatePresence>
        {showCreate && (
          <motion.form
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            onSubmit={handleCreate}
            className="space-y-3 pt-3 border-t border-border-subtle overflow-hidden"
          >
            <input name="name" placeholder="Template name" required className="input" />
            <input name="subject" placeholder="Subject template" required className="input" />
            <textarea
              name="body"
              placeholder="Body template (use {{variable}} for interpolation)"
              rows={5}
              required
              className="input resize-y font-mono text-sm"
            />
            <div className="flex items-center gap-3">
              <input name="language" placeholder="en" defaultValue="en" className="input w-20" />
              <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
                <input name="is_ab_test" type="checkbox" className="accent-accent-primary" />
                A/B Test
              </label>
              <input name="ab_variant" placeholder="A" className="input w-16" />
            </div>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={createMutation.isPending}
              className="btn-primary w-full"
            >
              {createMutation.isPending ? 'Creating…' : 'Create Template'}
            </motion.button>
          </motion.form>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
