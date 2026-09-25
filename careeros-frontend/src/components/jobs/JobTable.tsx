import { useState, useMemo, forwardRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  ExternalLink,
  MapPin,
  Globe,
  Plane,
  Archive,
  Send,
  Trash2,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { STAGE_LABELS } from "@/types/pipeline";
import { REMOTE_LABELS, PORTAL_LABELS } from "@/utils/constants";
import { formatSalary, formatRelative, cn } from "@/utils/format";
import type { JobPosting, PaginatedResponse } from "@/types";

type SortField = "title" | "status" | "salary_max" | "discovered_at" | "location";
type SortDirection = "asc" | "desc";

interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

interface JobTableProps {
  data: PaginatedResponse<JobPosting>;
  onSelectJob: (job: JobPosting) => void;
  onApply: (job: JobPosting) => void;
  onArchive: (job: JobPosting) => void;
  onDelete: (job: JobPosting) => void;
  onPageChange: (page: number) => void;
}

const PAGE_SIZE = 15;

export function JobTable({
  data,
  onSelectJob,
  onApply,
  onArchive,
  onDelete,
  onPageChange,
}: JobTableProps) {
  const [sort, setSort] = useState<SortConfig>({ field: "discovered_at", direction: "desc" });

  const sortedJobs = useMemo(() => {
    const jobs = [...data.data];
    jobs.sort((a, b) => {
      const { field, direction } = sort;
      const multiplier = direction === "asc" ? 1 : -1;

      switch (field) {
        case "title":
          return multiplier * a.title.localeCompare(b.title);
        case "status":
          return multiplier * a.status.localeCompare(b.status);
        case "salary_max":
          return multiplier * ((a.salary_max ?? 0) - (b.salary_max ?? 0));
        case "discovered_at":
          return (
            multiplier *
            (new Date(a.discovered_at ?? 0).getTime() -
              new Date(b.discovered_at ?? 0).getTime())
          );
        case "location":
          return multiplier * (a.location ?? "").localeCompare(b.location ?? "");
        default:
          return 0;
      }
    });
    return jobs;
  }, [data.data, sort]);

  const handleSort = (field: SortField) => {
    setSort((prev) => ({
      field,
      direction: prev.field === field && prev.direction === "asc" ? "desc" : "asc",
    }));
  };

  const totalPages = Math.ceil(data.meta.total / (data.meta.per_page || PAGE_SIZE));
  const currentPage = data.meta.page;

  return (
    <div className="space-y-0">
      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm" role="grid" aria-label="Job listings">
          <thead>
            <tr className="bg-bg-secondary text-text-muted text-xs uppercase tracking-wider">
              <SortableHeader
                field="title"
                label="Job Title"
                current={sort}
                onSort={handleSort}
                className="min-w-[250px]"
              />
              <SortableHeader
                field="status"
                label="Status"
                current={sort}
                onSort={handleSort}
                className="w-[130px]"
              />
              <th className="px-4 py-3 text-left font-medium">Details</th>
              <SortableHeader
                field="location"
                label="Location"
                current={sort}
                onSort={handleSort}
                className="w-[150px]"
              />
              <SortableHeader
                field="salary_max"
                label="Salary"
                current={sort}
                onSort={handleSort}
                className="w-[160px]"
              />
              <th className="px-4 py-3 text-left font-medium w-[100px]">Portal</th>
              <SortableHeader
                field="discovered_at"
                label="Discovered"
                current={sort}
                onSort={handleSort}
                className="w-[120px]"
              />
              <th className="px-4 py-3 text-right font-medium w-[140px]">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            <AnimatePresence mode="popLayout">
              {sortedJobs.map((job) => (
                <JobRow
                  key={job.id}
                  job={job}
                  onSelect={onSelectJob}
                  onApply={onApply}
                  onArchive={onArchive}
                  onDelete={onDelete}
                />
              ))}
            </AnimatePresence>
            {sortedJobs.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-text-muted">
                  No jobs match your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-4 text-sm text-text-secondary">
          <span>
            Showing {(currentPage - 1) * PAGE_SIZE + 1}–
            {Math.min(currentPage * PAGE_SIZE, data.meta.total)} of {data.meta.total}
          </span>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="p-2 rounded-md hover:bg-surface-hover disabled:opacity-40 disabled:pointer-events-none"
              aria-label="Previous page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              let page: number;
              if (totalPages <= 5) {
                page = i + 1;
              } else if (currentPage <= 3) {
                page = i + 1;
              } else if (currentPage >= totalPages - 2) {
                page = totalPages - 4 + i;
              } else {
                page = currentPage - 2 + i;
              }
              return (
                <button
                  key={page}
                  type="button"
                  onClick={() => onPageChange(page)}
                  className={cn(
                    "w-8 h-8 rounded-md text-xs font-medium transition-colors",
                    page === currentPage
                      ? "bg-accent-primary text-white"
                      : "hover:bg-surface-hover text-text-secondary",
                  )}
                  aria-label={`Page ${page}`}
                  aria-current={page === currentPage ? "page" : undefined}
                >
                  {page}
                </button>
              );
            })}
            <button
              type="button"
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="p-2 rounded-md hover:bg-surface-hover disabled:opacity-40 disabled:pointer-events-none"
              aria-label="Next page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function SortableHeader({
  field,
  label,
  current,
  onSort,
  className,
}: {
  field: SortField;
  label: string;
  current: SortConfig;
  onSort: (field: SortField) => void;
  className?: string;
}) {
  const isActive = current.field === field;
  return (
    <th className={cn("px-4 py-3 text-left font-medium", className)}>
      <button
        type="button"
        onClick={() => onSort(field)}
        className={cn(
          "inline-flex items-center gap-1 rounded hover:text-text-primary transition-colors",
          isActive ? "text-text-primary" : "",
        )}
        aria-sort={
          isActive ? (current.direction === "asc" ? "ascending" : "descending") : "none"
        }
      >
        {label}
        {isActive ? (
          current.direction === "asc" ? (
            <ArrowUp className="w-3 h-3 text-accent-primary" />
          ) : (
            <ArrowDown className="w-3 h-3 text-accent-primary" />
          )
        ) : (
          <ArrowUpDown className="w-3 h-3 opacity-40" />
        )}
      </button>
    </th>
  );
}

interface JobRowProps {
  job: JobPosting;
  onSelect: (job: JobPosting) => void;
  onApply: (job: JobPosting) => void;
  onArchive: (job: JobPosting) => void;
  onDelete: (job: JobPosting) => void;
}

const JobRow = forwardRef<HTMLTableRowElement, JobRowProps>(
  ({ job, onSelect, onApply, onArchive, onDelete }, ref) => {
  return (
    <motion.tr
      ref={ref}
      layout
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: 0.15 }}
      className="group hover:bg-surface-hover/50 transition-colors cursor-pointer"
      onClick={() => onSelect(job)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(job);
        }
      }}
      tabIndex={0}
      role="row"
      aria-label={`${job.title}`}
    >
      {/* Title + Company */}
      <td className="px-4 py-3">
        <div className="flex flex-col gap-0.5">
          <span className="font-medium text-text-primary group-hover:text-accent-primary transition-colors line-clamp-1">
            {job.title}
          </span>
          {job.url && (
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="inline-flex items-center gap-1 text-xs text-text-muted hover:text-accent-primary"
            >
              View posting
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </td>

      {/* Status */}
      <td className="px-4 py-3">
        <Badge variant={job.status as never} dot>
          {STAGE_LABELS[job.status as keyof typeof STAGE_LABELS] ?? job.status}
        </Badge>
      </td>

      {/* Details: remote + visa */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {job.remote_type && (
            <span className="inline-flex items-center gap-1 text-xs text-text-secondary">
              {job.remote_type === "remote" ? (
                <Globe className="w-3 h-3 text-emerald-400" />
              ) : job.remote_type === "hybrid" ? (
                <MapPin className="w-3 h-3 text-amber-400" />
              ) : (
                <MapPin className="w-3 h-3 text-text-muted" />
              )}
              {REMOTE_LABELS[job.remote_type]}
            </span>
          )}
          {job.visa_sponsorship && (
            <span
              className="inline-flex items-center gap-1 text-xs text-violet-400"
              title="Visa sponsorship available"
            >
              <Plane className="w-3 h-3" />
              Visa
            </span>
          )}
        </div>
      </td>

      {/* Location */}
      <td className="px-4 py-3 text-text-secondary">
        <span className="line-clamp-1">{job.location ?? "—"}</span>
      </td>

      {/* Salary */}
      <td className="px-4 py-3 text-text-secondary font-mono text-xs">
        {formatSalary(job.salary_min, job.salary_max, job.currency)}
      </td>

      {/* Portal */}
      <td className="px-4 py-3">
        {job.portal_source ? (
          <span className="text-xs text-text-muted">
            {PORTAL_LABELS[job.portal_source] ?? job.portal_source}
          </span>
        ) : (
          <span className="text-xs text-text-muted">Manual</span>
        )}
      </td>

      {/* Discovered */}
      <td className="px-4 py-3 text-xs text-text-muted">
        {formatRelative(job.discovered_at)}
      </td>

      {/* Actions */}
      <td className="px-4 py-3">
        <div
          className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => e.stopPropagation()}
        >
          {(job.status === "discovered" || job.status === "interested") && (
            <ActionButton
              icon={Send}
              label="Apply"
              onClick={() => onApply(job)}
              variant="primary"
            />
          )}
          {job.status !== "rejected" && job.status !== "withdrawn" && (
            <ActionButton
              icon={Archive}
              label="Archive"
              onClick={() => onArchive(job)}
              variant="secondary"
            />
          )}
          <ActionButton
            icon={Trash2}
            label="Delete"
            onClick={() => onDelete(job)}
            variant="danger"
          />
        </div>
      </td>
    </motion.tr>
  );
});

function ActionButton({
  icon: Icon,
  label,
  onClick,
  variant,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  onClick: () => void;
  variant: "primary" | "secondary" | "danger";
}) {
  const variantClasses = {
    primary: "hover:bg-accent-primary/20 hover:text-accent-primary",
    secondary: "hover:bg-surface-hover hover:text-text-primary",
    danger: "hover:bg-red-500/20 hover:text-red-400",
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "p-1.5 rounded-md text-text-muted transition-colors",
        variantClasses[variant],
      )}
      aria-label={label}
      title={label}
    >
      <Icon className="w-3.5 h-3.5" />
    </button>
  );
}
