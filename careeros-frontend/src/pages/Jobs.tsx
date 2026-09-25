import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Loader2, AlertCircle, LayoutGrid, BarChart3, X } from "lucide-react";
import { JobFilters } from "@/components/jobs/JobFilters";
import { JobTable } from "@/components/jobs/JobTable";
import { JobDetailDrawer } from "@/components/jobs/JobDetailDrawer";
import { JobStatsCards } from "@/components/jobs/JobStatsCards";
import { useJobs, useUpdateJob, useDeleteJob, useCreateJob } from "@/hooks/useJobs";
import type { JobFilters as JobFiltersType, JobPosting, ApplicationStatus } from "@/types";
import { cn } from "@/utils/format";

type ViewMode = "table" | "stats";

const DEFAULT_FILTERS: JobFiltersType = {
  page: 1,
  per_page: 15,
};

export default function Jobs() {
  const [filters, setFilters] = useState<JobFiltersType>(DEFAULT_FILTERS);
  const [selectedJob, setSelectedJob] = useState<JobPosting | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const [showAddModal, setShowAddModal] = useState(false);

  const { data, isLoading, isError, error } = useJobs(filters);
  const updateMutation = useUpdateJob();
  const deleteMutation = useDeleteJob();
  const createMutation = useCreateJob();

  const handlePageChange = useCallback((page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  }, []);

  const handleApply = useCallback(
    (job: JobPosting) => {
      updateMutation.mutate({
        id: job.id,
        payload: { status: "applied" },
      });
    },
    [updateMutation],
  );

  const handleArchive = useCallback(
    (job: JobPosting) => {
      updateMutation.mutate({
        id: job.id,
        payload: { status: "withdrawn" },
      });
    },
    [updateMutation],
  );

  const handleDelete = useCallback(
    (job: JobPosting) => {
      if (window.confirm(`Delete "${job.title}"? This cannot be undone.`)) {
        deleteMutation.mutate(job.id);
        if (selectedJob?.id === job.id) setSelectedJob(null);
      }
    },
    [deleteMutation, selectedJob],
  );

  const handleStatusChange = useCallback(
    (job: JobPosting, status: ApplicationStatus) => {
      updateMutation.mutate({
        id: job.id,
        payload: { status },
      });
      // Optimistically update selected job
      setSelectedJob((prev) => (prev && prev.id === job.id ? { ...prev, status } : prev));
    },
    [updateMutation],
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Jobs</h1>
          <p className="text-sm text-text-secondary mt-1">
            Manage your job opportunities — search, filter, and track applications
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex items-center rounded-lg border border-border bg-surface p-0.5">
            <button
              type="button"
              onClick={() => setViewMode("table")}
              className={cn(
                "p-2 rounded-md transition-colors",
                viewMode === "table"
                  ? "bg-accent-primary text-white"
                  : "text-text-muted hover:text-text-primary",
              )}
              aria-label="Table view"
              aria-pressed={viewMode === "table"}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode("stats")}
              className={cn(
                "p-2 rounded-md transition-colors",
                viewMode === "stats"
                  ? "bg-accent-primary text-white"
                  : "text-text-muted hover:text-text-primary",
              )}
              aria-label="Stats view"
              aria-pressed={viewMode === "stats"}
            >
              <BarChart3 className="w-4 h-4" />
            </button>
          </div>

          <button type="button" className="btn-primary" onClick={() => setShowAddModal(true)}>
            <Plus className="w-4 h-4" />
            Add Job
          </button>
        </div>
      </motion.div>

      {/* Stats (always visible in stats view, or as summary when table) */}
      {viewMode === "stats" && data && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
        >
          <JobStatsCards jobs={data.data} />
        </motion.div>
      )}

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
      >
        <JobFilters
          filters={filters}
          onChange={setFilters}
          totalResults={data?.meta.total ?? 0}
        />
      </motion.div>

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-accent-primary animate-spin" />
            <span className="ml-3 text-text-secondary">Loading jobs...</span>
          </div>
        )}

        {isError && (
          <div className="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-400">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <div>
              <p className="font-medium">Failed to load jobs</p>
              <p className="text-sm text-red-400/80 mt-0.5">
                {error instanceof Error ? error.message : "Unknown error"}
              </p>
            </div>
          </div>
        )}

        {data && !isLoading && viewMode === "table" && (
          <JobTable
            data={data}
            onSelectJob={setSelectedJob}
            onApply={handleApply}
            onArchive={handleArchive}
            onDelete={handleDelete}
            onPageChange={handlePageChange}
          />
        )}

        {data && !isLoading && data.data.length === 0 && viewMode === "table" && (
          <div className="flex flex-col items-center justify-center py-20 text-text-muted">
            <Briefcase className="w-12 h-12 mb-4 opacity-30" />
            <p className="text-lg font-medium text-text-secondary">No jobs found</p>
            <p className="text-sm mt-1">
              Try adjusting your filters or add a new job posting.
            </p>
          </div>
        )}
      </motion.div>

      {/* Detail drawer */}
      <JobDetailDrawer
        job={selectedJob}
        onClose={() => setSelectedJob(null)}
        onStatusChange={handleStatusChange}
        onArchive={(job) => {
          handleArchive(job);
          setSelectedJob(null);
        }}
      />

      {/* Add Job modal */}
      <AnimatePresence>
        {showAddModal && (
          <AddJobModal
            onClose={() => setShowAddModal(false)}
            onSubmit={(payload) => {
              createMutation.mutate(payload);
              setShowAddModal(false);
            }}
            isSubmitting={createMutation.isPending}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function Briefcase({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <rect width="20" height="14" x="2" y="7" rx="2" ry="2" />
      <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
    </svg>
  );
}

function AddJobModal({
  onClose,
  onSubmit,
  isSubmitting,
}: {
  onClose: () => void;
  onSubmit: (payload: { title: string; url: string | null; description: string | null }) => void;
  isSubmitting: boolean;
}) {
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [description, setDescription] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    onSubmit({
      title: title.trim(),
      url: url.trim() || null,
      description: description.trim() || null,
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="w-full max-w-md rounded-xl border border-border bg-surface-elevated p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-text-primary">Add Job</h2>
          <button onClick={onClose} className="p-1 rounded text-text-muted hover:text-text-primary">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">Job Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Senior Full-Stack Engineer"
              className="input"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">URL</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://..."
              className="input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description..."
              rows={3}
              className="input resize-none"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            <button
              type="submit"
              disabled={!title.trim() || isSubmitting}
              className="btn-primary"
            >
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Add Job
            </button>
          </div>
        </form>
      </motion.div>
    </motion.div>
  );
}
