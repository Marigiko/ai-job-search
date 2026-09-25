import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { createPortal } from "react-dom";
import {
  X,
  ExternalLink,
  MapPin,
  Globe,
  Plane,
  DollarSign,
  Building2,
  Clock,
  Calendar,
  Send,
  Archive,
  FileText,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { STAGE_LABELS, PIPELINE_STAGES, STAGE_CONFIG } from "@/types/pipeline";
import { REMOTE_LABELS, PORTAL_LABELS } from "@/utils/constants";
import { formatSalary, formatDate, cn } from "@/utils/format";
import type { JobPosting, ApplicationStatus } from "@/types";

interface JobDetailDrawerProps {
  job: JobPosting | null;
  onClose: () => void;
  onStatusChange: (job: JobPosting, status: ApplicationStatus) => void;
  onArchive: (job: JobPosting) => void;
}

const drawerVariants = {
  hidden: { x: "100%", opacity: 0 },
  visible: { x: 0, opacity: 1 },
};

const overlayVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

export function JobDetailDrawer({
  job,
  onClose,
  onStatusChange,
  onArchive,
}: JobDetailDrawerProps) {
  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (job) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [job, onClose]);

  if (typeof document === "undefined") return null;

  return createPortal(
    <AnimatePresence>
      {job && (
        <>
          {/* Backdrop */}
          <motion.div
            variants={overlayVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Drawer */}
          <motion.aside
            variants={drawerVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-lg bg-bg-secondary border-l border-border shadow-2xl overflow-y-auto"
            role="dialog"
            aria-modal="true"
            aria-label={`Job details: ${job.title}`}
          >
            <DrawerContent
              job={job}
              onClose={onClose}
              onStatusChange={onStatusChange}
              onArchive={onArchive}
            />
          </motion.aside>
        </>
      )}
    </AnimatePresence>,
    document.body,
  );
}

function DrawerContent({
  job,
  onClose,
  onStatusChange,
  onArchive,
}: {
  job: JobPosting;
  onClose: () => void;
  onStatusChange: (job: JobPosting, status: ApplicationStatus) => void;
  onArchive: (job: JobPosting) => void;
}) {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="sticky top-0 z-10 flex items-start justify-between p-6 bg-bg-secondary/95 backdrop-blur-sm border-b border-border">
        <div className="flex-1 min-w-0 pr-4">
          <h2 className="text-lg font-semibold text-text-primary leading-tight">
            {job.title}
          </h2>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant={job.status as never} dot>
              {STAGE_LABELS[job.status as keyof typeof STAGE_LABELS] ?? job.status}
            </Badge>
            {job.portal_source && (
              <span className="text-xs text-text-muted">
                via {PORTAL_LABELS[job.portal_source] ?? job.portal_source}
              </span>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-surface-hover text-text-muted hover:text-text-primary transition-colors"
          aria-label="Close drawer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        {/* Quick metadata grid */}
        <div className="grid grid-cols-2 gap-3">
          <MetaCard
            icon={MapPin}
            label="Location"
            value={job.location ?? "Not specified"}
          />
          <MetaCard
            icon={Globe}
            label="Remote"
            value={
              job.remote_type ? REMOTE_LABELS[job.remote_type] : "Not specified"
            }
          />
          <MetaCard
            icon={DollarSign}
            label="Salary"
            value={formatSalary(job.salary_min, job.salary_max, job.currency)}
          />
          <MetaCard
            icon={job.visa_sponsorship ? Plane : Building2}
            label="Visa"
            value={job.visa_sponsorship ? "Sponsorship available" : "No sponsorship"}
          />
        </div>

        {/* Dates */}
        <div className="flex items-center gap-6 text-sm text-text-secondary">
          {job.discovered_at && (
            <span className="inline-flex items-center gap-1.5">
              <Calendar className="w-4 h-4" />
              Discovered {formatDate(job.discovered_at)}
            </span>
          )}
          {job.applied_at && (
            <span className="inline-flex items-center gap-1.5">
              <Clock className="w-4 h-4" />
              Applied {formatDate(job.applied_at)}
            </span>
          )}
        </div>

        {/* Description */}
        {job.description && (
          <div>
            <h3 className="text-sm font-medium text-text-primary mb-2">
              Description
            </h3>
            <div className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap rounded-lg bg-surface p-4 max-h-64 overflow-y-auto">
              {job.description}
            </div>
          </div>
        )}

        {/* Notes */}
        {job.notes && (
          <div>
            <h3 className="text-sm font-medium text-text-primary mb-2">Notes</h3>
            <p className="text-sm text-text-secondary bg-surface rounded-lg p-4">
              {job.notes}
            </p>
          </div>
        )}

        {/* Stage progression */}
        <div>
          <h3 className="text-sm font-medium text-text-primary mb-3">
            Pipeline stage
          </h3>
          <div className="flex items-center gap-1.5 flex-wrap">
            {PIPELINE_STAGES.map((stage) => {
              const isCurrent = stage === job.status;
              const isPast =
                PIPELINE_STAGES.indexOf(stage) <=
                PIPELINE_STAGES.indexOf(job.status as (typeof PIPELINE_STAGES)[number]);
              return (
                <button
                  key={stage}
                  type="button"
                  onClick={() => onStatusChange(job, stage)}
                  className={cn(
                    "px-2.5 py-1 rounded-full text-xs font-medium border transition-all",
                    isCurrent
                      ? "border-transparent text-white shadow-sm"
                      : isPast
                        ? "opacity-60 hover:opacity-100 border-transparent"
                        : "border-border bg-bg-tertiary text-text-muted hover:text-text-secondary hover:border-text-muted",
                  )}
                  style={
                    isCurrent || isPast
                      ? {
                          backgroundColor: STAGE_CONFIG[stage].color,
                        }
                      : undefined
                  }
                  aria-label={`Move to ${STAGE_LABELS[stage]}`}
                  aria-pressed={isCurrent}
                >
                  {STAGE_CONFIG[stage].icon} {STAGE_LABELS[stage]}
                </button>
              );
            })}
          </div>
        </div>

        {/* Original URL */}
        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-primary/10 text-accent-primary text-sm font-medium hover:bg-accent-primary/20 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            View original posting
          </a>
        )}
      </div>

      {/* Footer actions */}
      <div className="sticky bottom-0 p-6 bg-bg-secondary/95 backdrop-blur-sm border-t border-border">
        <div className="flex items-center gap-3">
          {(job.status === "discovered" || job.status === "interested") && (
            <button
              type="button"
              onClick={() => onStatusChange(job, "applied")}
              className="btn-primary flex-1"
            >
              <Send className="w-4 h-4" />
              Mark as Applied
            </button>
          )}
          {job.status !== "rejected" && job.status !== "withdrawn" && (
            <button
              type="button"
              onClick={() => onArchive(job)}
              className="btn-secondary"
            >
              <Archive className="w-4 h-4" />
              Archive
            </button>
          )}
          <button type="button" className="btn-ghost" disabled>
            <FileText className="w-4 h-4" />
            Generate CL
          </button>
        </div>
      </div>
    </div>
  );
}

function MetaCard({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg bg-surface border border-border-subtle p-3">
      <div className="flex items-center gap-1.5 text-text-muted mb-1">
        <Icon className="w-3.5 h-3.5" />
        <span className="text-xs font-medium uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-sm text-text-primary font-medium line-clamp-1">{value}</p>
    </div>
  );
}
