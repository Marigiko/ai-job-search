import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Eye, Save, Sparkles, Loader2 } from 'lucide-react';
import { outreachApi } from '@/api/client';
import type { OutreachEmailCreate } from '@/types';

interface EmailComposerProps {
  readonly initialRecipient?: string;
  readonly initialSubject?: string;
  readonly initialBody?: string;
  readonly onQueue?: (payload: OutreachEmailCreate) => void;
  readonly onSend?: (payload: OutreachEmailCreate) => void;
}

interface ComposerState {
  recipient: string;
  subject: string;
  body: string;
}

const containerVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.25 } },
};

export function EmailComposer({
  initialRecipient = '',
  initialSubject = '',
  initialBody = '',
  onQueue,
  onSend,
}: EmailComposerProps) {
  const [state, setState] = useState<ComposerState>({
    recipient: initialRecipient,
    subject: initialSubject,
    body: initialBody,
  });
  const [preview, setPreview] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const update = useCallback(
    (field: keyof ComposerState) =>
      (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setState((prev) => ({ ...prev, [field]: e.target.value }));
      },
    [],
  );

  const handlePreview = useCallback(async () => {
    if (!state.recipient || !state.body) return;
    setLoading(true);
    setError(null);
    try {
      const result = await outreachApi.compose({
        recipient_email: state.recipient,
        subject: state.subject,
        body: state.body,
      });
      setPreview(result.preview);
      setShowPreview(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Preview failed');
    } finally {
      setLoading(false);
    }
  }, [state]);

  const handleQueue = useCallback(async () => {
    setError(null);
    try {
      const payload: OutreachEmailCreate = {
        recipient_email: state.recipient,
        subject: state.subject,
        body: state.body,
      };
      await outreachApi.queue(payload);
      onQueue?.(payload);
      setState({ recipient: '', subject: '', body: '' });
      setPreview(null);
      setShowPreview(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to queue email');
    }
  }, [state, onQueue]);

  const handleSend = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload: OutreachEmailCreate = {
        recipient_email: state.recipient,
        subject: state.subject,
        body: state.body,
      };
      await outreachApi.send(payload);
      onSend?.(payload);
      setState({ recipient: '', subject: '', body: '' });
      setPreview(null);
      setShowPreview(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send email');
    } finally {
      setLoading(false);
    }
  }, [state, onSend]);

  const isValid = state.recipient.includes('@') && state.body.length > 0;

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="glass-card p-6 space-y-4"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-accent-primary" />
          Compose Email
        </h2>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setShowPreview((p) => !p)}
          className="btn-ghost text-sm"
          aria-label={showPreview ? 'Hide preview' : 'Show preview'}
          aria-expanded={showPreview}
        >
          <Eye className="w-4 h-4" />
          {showPreview ? 'Editor' : 'Preview'}
        </motion.button>
      </div>

      <AnimatePresence mode="wait">
        {showPreview ? (
          <motion.div
            key="preview"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-3"
          >
            <div className="rounded-md border border-border bg-surface p-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">To:</span>
                <span className="text-text-primary font-mono">{state.recipient || '—'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-text-muted">Subject:</span>
                <span className="text-text-primary">{state.subject || '—'}</span>
              </div>
            </div>
            <div
              className="rounded-md border border-border bg-bg-primary p-6 min-h-[200px] prose-invert"
              aria-live="polite"
            >
              <pre className="whitespace-pre-wrap font-sans text-sm text-text-secondary leading-relaxed">
                {preview ?? state.body}
              </pre>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="editor"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-3"
          >
            <div>
              <label htmlFor="composer-recipient" className="sr-only">
                Recipient email
              </label>
              <input
                id="composer-recipient"
                type="email"
                placeholder="recipient@company.com"
                value={state.recipient}
                onChange={update('recipient')}
                className="input"
                aria-required="true"
              />
            </div>
            <div>
              <label htmlFor="composer-subject" className="sr-only">
                Subject
              </label>
              <input
                id="composer-subject"
                type="text"
                placeholder="Subject line"
                value={state.subject}
                onChange={update('subject')}
                className="input"
              />
            </div>
            <div>
              <label htmlFor="composer-body" className="sr-only">
                Email body
              </label>
              <textarea
                id="composer-body"
                placeholder="Write your email…"
                value={state.body}
                onChange={update('body')}
                rows={10}
                className="input resize-y font-mono text-sm leading-relaxed"
                aria-required="true"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="text-sm text-accent-danger"
            role="alert"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>

      <div className="flex items-center gap-3 pt-2 border-t border-border-subtle">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handlePreview}
          disabled={!isValid || loading}
          className="btn-secondary"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Eye className="w-4 h-4" />}
          Live Preview
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleQueue}
          disabled={!isValid}
          className="btn-ghost"
        >
          <Save className="w-4 h-4" />
          Queue
        </motion.button>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSend}
          disabled={!isValid || loading}
          className="btn-primary"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          Send Now
        </motion.button>
      </div>
    </motion.div>
  );
}
