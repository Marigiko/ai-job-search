import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Download,
  Eye,
  Sparkles,
  History,
  Loader2,
  CheckCircle2,
  AlertCircle,
  File,
  TrendingUp,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, documentsApi } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import { mockDocuments, mockDocumentStats } from '@/data/mockDocuments';
import { formatDate, formatFileSize, formatRelative, cn } from '@/utils/format';
import type {
  DocumentType,
  DocumentListItem,
  DocumentStatus,
  DocumentGenerateRequest,
} from '@/types';

// ── Constants ────────────────────────────────────────────────────────────────

const DOCUMENT_TYPE_OPTIONS: readonly { value: DocumentType; label: string }[] = [
  { value: 'cv', label: 'CV / Resume' },
  { value: 'cover_letter', label: 'Cover Letter' },
];

const STATUS_CONFIG: Record<
  DocumentStatus,
  { icon: typeof CheckCircle2; color: string; label: string }
> = {
  ready: { icon: CheckCircle2, color: 'text-accent-success', label: 'Ready' },
  generating: { icon: Loader2, color: 'text-accent-warning', label: 'Generating…' },
  failed: { icon: AlertCircle, color: 'text-accent-danger', label: 'Failed' },
};

const TYPE_LABELS: Record<DocumentType, string> = {
  cv: 'CV',
  cover_letter: 'Cover Letter',
};

const CHART_GRADIENT_ID = 'documentsAreaGradient';

const containerVariants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
};

const itemVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
};

// ── Helpers ──────────────────────────────────────────────────────────────────

const isMock = import.meta.env.VITE_USE_MOCK === 'true';

function useDocumentsList(): { data: DocumentListItem[]; isLoading: boolean } {
  const query = useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: () => documentsApi.list(),
    enabled: !isMock,
    staleTime: 30_000,
  });

  if (isMock) {
    return { data: mockDocuments, isLoading: false };
  }
  return { data: query.data ?? [], isLoading: query.isLoading };
}

function useDocumentsStats() {
  const query = useQuery({
    queryKey: queryKeys.documents.stats(),
    queryFn: () => documentsApi.getStats(),
    enabled: !isMock,
    staleTime: 60_000,
  });

  return isMock ? mockDocumentStats : (query.data ?? mockDocumentStats);
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function Documents() {
  const [selectedJobId, setSelectedJobId] = useState<number | ''>('');
  const [selectedType, setSelectedType] = useState<DocumentType>('cv');
  const [previewDoc, setPreviewDoc] = useState<DocumentListItem | null>(null);

  const { data: jobs } = useQuery({
    queryKey: queryKeys.jobs.list({ status: 'interested,applied,screening,interview' }),
    queryFn: () => jobsApi.list({ status: 'applied' }),
    enabled: !isMock,
    staleTime: 30_000,
  });

  const jobOptions = isMock
    ? mockDocuments
        .filter((d) => d.job_posting_id !== null)
        .map((d) => ({
          id: d.job_posting_id as number,
          title: d.job_title ?? 'Untitled',
          company: d.company_name,
        }))
        .filter((j, i, arr) => arr.findIndex((x) => x.id === j.id) === i)
    : (jobs?.data ?? []).map((j) => ({
        id: j.id,
        title: j.title,
        company: null,
      }));

  const { data: documents, isLoading } = useDocumentsList();
  const stats = useDocumentsStats();
  const queryClient = useQueryClient();

  const generateMutation = useMutation({
    mutationFn: (payload: DocumentGenerateRequest) => documentsApi.generate(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
    },
  });

  const handleGenerate = () => {
    if (selectedJobId === '') return;
    const payload: DocumentGenerateRequest = {
      job_posting_id: Number(selectedJobId),
      company_id: null,
      document_type: selectedType,
    };
    generateMutation.mutate(payload);
  };

  const readyDocuments = useMemo(
    () => documents.filter((d) => d.status === 'ready'),
    [documents],
  );

  const selectedJobTitle =
    jobOptions.find((j) => j.id === selectedJobId)?.title ?? '—';

  return (
    <motion.div
      className="space-y-6 h-full flex flex-col"
      variants={containerVariants}
      initial="initial"
      animate="animate"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary flex items-center gap-2">
            <FileText className="w-6 h-6 text-accent-primary" />
            Documents
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Generate tailored CVs & cover letters, preview, and download
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <span className="font-mono">{stats.total_generated} generated</span>
        </div>
      </motion.div>

      {/* Stats chart */}
      <motion.div variants={itemVariants} className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-4 h-4 text-accent-secondary" />
          <h2 className="text-sm font-semibold text-text-primary">Generation Activity</h2>
        </div>
        <div className="h-40">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={stats.by_week} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id={CHART_GRADIENT_ID} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#2a2a3a" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="week"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: '#1a1a26',
                  border: '1px solid #2a2a3a',
                  borderRadius: '8px',
                  fontSize: 12,
                  color: '#f1f5f9',
                }}
                cursor={{ stroke: '#6366f1', strokeOpacity: 0.3 }}
              />
              <Area
                type="monotone"
                dataKey="count"
                stroke="#6366f1"
                strokeWidth={2}
                fill={`url(#${CHART_GRADIENT_ID})`}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Generator + Preview + History grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-0">
        {/* Generator */}
        <motion.div
          variants={itemVariants}
          className="lg:col-span-4 glass-card p-5 flex flex-col"
        >
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-4">
            <Sparkles className="w-4 h-4 text-accent-primary" />
            Generator
          </h2>

          <div className="space-y-4 flex-1">
            {/* Job selector */}
            <div>
              <label
                htmlFor="doc-job-select"
                className="block text-xs font-medium text-text-secondary mb-1.5"
              >
                Target Job
              </label>
              <select
                id="doc-job-select"
                value={selectedJobId}
                onChange={(e) =>
                  setSelectedJobId(e.target.value === '' ? '' : Number(e.target.value))
                }
                className="input"
              >
                <option value="">Select a job…</option>
                {jobOptions.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.title}
                    {job.company ? ` — ${job.company}` : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Document type */}
            <div>
              <span className="block text-xs font-medium text-text-secondary mb-1.5">
                Document Type
              </span>
              <div className="grid grid-cols-2 gap-2" role="radiogroup">
                {DOCUMENT_TYPE_OPTIONS.map((opt) => {
                  const active = selectedType === opt.value;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      role="radio"
                      aria-checked={active}
                      onClick={() => setSelectedType(opt.value)}
                      className={cn(
                        'rounded-md px-3 py-2 text-sm font-medium transition-all border',
                        active
                          ? 'bg-accent-primary/15 border-accent-primary text-accent-primary'
                          : 'border-border bg-surface text-text-secondary hover:bg-surface-hover',
                      )}
                    >
                      {opt.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Summary */}
            <div className="rounded-md bg-surface-elevated border border-border p-3 text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-text-muted">Job</span>
                <span className="text-text-primary font-medium">{selectedJobTitle}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Type</span>
                <span className="text-text-primary font-medium">
                  {TYPE_LABELS[selectedType]}
                </span>
              </div>
            </div>
          </div>

          {/* Generate button */}
          <motion.button
            onClick={handleGenerate}
            disabled={selectedJobId === '' || generateMutation.isPending}
            className="btn-primary w-full mt-4"
            whileTap={{ scale: 0.97 }}
          >
            {generateMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            {generateMutation.isPending ? 'Compiling…' : 'Generate Document'}
          </motion.button>

          {generateMutation.isSuccess && (
            <motion.p
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-2 text-xs text-accent-success text-center"
            >
              {generateMutation.data.message}
            </motion.p>
          )}
        </motion.div>

        {/* Preview */}
        <motion.div
          variants={itemVariants}
          className="lg:col-span-5 glass-card p-5 flex flex-col min-h-[420px]"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2">
              <Eye className="w-4 h-4 text-accent-secondary" />
              Preview
            </h2>
            {previewDoc && previewDoc.status === 'ready' && (
              <a
                href={documentsApi.downloadUrl(previewDoc.id)}
                className="btn-ghost text-xs py-1.5 px-3"
                aria-label={`Download ${previewDoc.document_type} for ${previewDoc.job_title}`}
              >
                <Download className="w-3.5 h-3.5" />
                Download PDF
              </a>
            )}
          </div>

          <div className="flex-1 rounded-md border border-border bg-surface overflow-hidden flex items-center justify-center">
            <AnimatePresence mode="wait">
              {previewDoc === null ? (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-center px-6"
                >
                  <File className="w-10 h-10 text-text-muted mx-auto mb-3" />
                  <p className="text-sm text-text-secondary">
                    Select a document from history to preview
                  </p>
                  <p className="text-xs text-text-muted mt-1">
                    Compiled PDFs render here
                  </p>
                </motion.div>
              ) : previewDoc.status !== 'ready' ? (
                <motion.div
                  key="processing"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="text-center px-6"
                >
                  <Loader2 className="w-10 h-10 text-accent-warning mx-auto mb-3 animate-spin" />
                  <p className="text-sm text-text-secondary">Document is being compiled…</p>
                </motion.div>
              ) : (
                <motion.iframe
                  key={`preview-${previewDoc.id}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  title={`Preview of ${previewDoc.document_type} for ${previewDoc.job_title}`}
                  src={documentsApi.previewUrl(previewDoc.id)}
                  className="w-full h-full border-0"
                />
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Version history */}
        <motion.div
          variants={itemVariants}
          className="lg:col-span-3 glass-card p-5 flex flex-col min-h-[420px]"
        >
          <h2 className="text-sm font-semibold text-text-primary flex items-center gap-2 mb-4">
            <History className="w-4 h-4 text-accent-primary" />
            Version History
            <span className="ml-auto text-[10px] font-mono text-text-muted">
              {documents.length}
            </span>
          </h2>

          <div className="flex-1 overflow-y-auto -mx-2 px-2 space-y-1.5">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-5 h-5 text-accent-primary animate-spin" />
              </div>
            ) : documents.length === 0 ? (
              <p className="text-xs text-text-muted text-center py-12">
                No documents generated yet
              </p>
            ) : (
              readyDocuments
                .concat(documents.filter((d) => d.status !== 'ready'))
                .map((doc) => (
                  <DocumentHistoryRow
                    key={doc.id}
                    doc={doc}
                    active={previewDoc?.id === doc.id}
                    onPreview={() => setPreviewDoc(doc)}
                  />
                ))
            )}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}

// ── Document History Row ─────────────────────────────────────────────────────

interface DocumentHistoryRowProps {
  readonly doc: DocumentListItem;
  readonly active: boolean;
  readonly onPreview: () => void;
}

function DocumentHistoryRow({ doc, active, onPreview }: DocumentHistoryRowProps) {
  const statusConf = STATUS_CONFIG[doc.status];
  const StatusIcon = statusConf.icon;
  const isReady = doc.status === 'ready';

  return (
    <motion.button
      type="button"
      onClick={onPreview}
      disabled={!isReady}
      variants={itemVariants}
      whileHover={isReady ? { scale: 1.01 } : undefined}
      whileTap={isReady ? { scale: 0.99 } : undefined}
      className={cn(
        'w-full text-left rounded-md border p-3 transition-colors',
        active
          ? 'bg-accent-primary/10 border-accent-primary'
          : 'bg-surface-elevated/50 border-border hover:bg-surface-hover',
        !isReady && 'opacity-70',
      )}
      aria-label={`Preview ${TYPE_LABELS[doc.document_type]} for ${doc.job_title}`}
      aria-current={active ? 'true' : undefined}
    >
      <div className="flex items-start gap-2.5">
        <StatusIcon
          className={cn(
            'w-4 h-4 mt-0.5 shrink-0',
            statusConf.color,
            doc.status === 'generating' && 'animate-spin',
          )}
        />
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-text-primary truncate">
            {doc.job_title ?? 'Untitled'}
          </p>
          {doc.company_name && (
            <p className="text-[11px] text-text-secondary truncate">{doc.company_name}</p>
          )}
          <div className="flex items-center gap-2 mt-1.5">
            <span className="badge bg-accent-primary/15 text-accent-primary text-[10px]">
              {TYPE_LABELS[doc.document_type]}
            </span>
            <span className="text-[10px] font-mono text-text-muted">{doc.version}</span>
            {doc.file_size !== null && (
              <span className="text-[10px] text-text-muted">
                {formatFileSize(doc.file_size)}
              </span>
            )}
          </div>
        </div>
        <div className="text-right shrink-0">
          <p className="text-[10px] text-text-muted">{formatRelative(doc.created_at)}</p>
          <p className="text-[10px] text-text-muted">{formatDate(doc.created_at)}</p>
        </div>
      </div>
    </motion.button>
  );
}
