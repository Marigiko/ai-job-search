import { Search, Filter, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { PIPELINE_STAGES, STAGE_LABELS } from "@/types/pipeline";
import { REMOTE_LABELS } from "@/utils/constants";
import type { JobFilters as JobFiltersType, RemoteType } from "@/types";
import { cn } from "@/utils/format";

interface JobFiltersProps {
  filters: JobFiltersType;
  onChange: (filters: JobFiltersType) => void;
  totalResults: number;
}

const statusOptions = PIPELINE_STAGES.map((s) => ({
  value: s,
  label: STAGE_LABELS[s],
}));

const remoteOptions: { value: string; label: string }[] = [
  { value: "", label: "All types" },
  { value: "remote", label: REMOTE_LABELS.remote },
  { value: "hybrid", label: REMOTE_LABELS.hybrid },
  { value: "onsite", label: REMOTE_LABELS.onsite },
];

type VisaFilter = "all" | "sponsored" | "no_sponsorship";

function getVisaFilter(filters: JobFiltersType): VisaFilter {
  if (filters.visa_sponsorship === true) return "sponsored";
  if (filters.visa_sponsorship === false) return "no_sponsorship";
  return "all";
}

export function JobFilters({ filters, onChange, totalResults }: JobFiltersProps) {
  const hasActiveFilters =
    filters.status ||
    filters.remote_type ||
    filters.search ||
    filters.visa_sponsorship !== undefined;

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...filters, search: e.target.value, page: 1 });
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange({
      ...filters,
      status: e.target.value || undefined,
      page: 1,
    });
  };

  const handleRemoteChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    onChange({
      ...filters,
      remote_type: (value || undefined) as RemoteType | undefined,
      page: 1,
    });
  };

  const handleVisaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value as VisaFilter;
    onChange({
      ...filters,
      visa_sponsorship:
        value === "sponsored" ? true : value === "no_sponsorship" ? false : undefined,
      page: 1,
    });
  };

  const clearFilters = () => {
    onChange({ page: 1, per_page: filters.per_page });
  };

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Search jobs, companies, keywords..."
            value={filters.search ?? ""}
            onChange={handleSearchChange}
            className="input pl-10"
            aria-label="Search jobs"
          />
          <AnimatePresence>
            {filters.search && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                type="button"
                onClick={() => onChange({ ...filters, search: undefined, page: 1 })}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-surface-hover text-text-muted hover:text-text-primary"
                aria-label="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </motion.button>
            )}
          </AnimatePresence>
        </div>

        <div className="flex items-center gap-2 text-sm text-text-muted">
          <Filter className="w-4 h-4" />
          <span>{totalResults} jobs</span>
        </div>
      </div>

      {/* Filter selects */}
      <div className="flex flex-wrap items-center gap-2">
        <select
          value={filters.status ?? ""}
          onChange={handleStatusChange}
          className="input w-auto cursor-pointer"
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          {statusOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <select
          value={filters.remote_type ?? ""}
          onChange={handleRemoteChange}
          className="input w-auto cursor-pointer"
          aria-label="Filter by remote type"
        >
          {remoteOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <select
          value={getVisaFilter(filters)}
          onChange={handleVisaChange}
          className="input w-auto cursor-pointer"
          aria-label="Filter by visa sponsorship"
        >
          <option value="all">All visa</option>
          <option value="sponsored">Visa sponsorship</option>
          <option value="no_sponsorship">No sponsorship</option>
        </select>

        <AnimatePresence>
          {hasActiveFilters && (
            <motion.button
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              type="button"
              onClick={clearFilters}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs",
                "font-medium text-text-secondary bg-surface hover:bg-surface-hover",
                "transition-colors",
              )}
            >
              <X className="w-3 h-3" />
              Clear filters
            </motion.button>
          )}
        </AnimatePresence>

        {/* Active filter chips */}
        <div className="flex items-center gap-1.5 ml-2">
          {filters.status && (
            <FilterChip
              label={STAGE_LABELS[filters.status as keyof typeof STAGE_LABELS]}
              onRemove={() => onChange({ ...filters, status: undefined, page: 1 })}
            />
          )}
          {filters.remote_type && (
            <FilterChip
              label={REMOTE_LABELS[filters.remote_type]}
              onRemove={() => onChange({ ...filters, remote_type: undefined, page: 1 })}
            />
          )}
          {filters.visa_sponsorship === true && (
            <FilterChip
              label="Visa"
              onRemove={() => onChange({ ...filters, visa_sponsorship: undefined, page: 1 })}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function FilterChip({
  label,
  onRemove,
}: {
  label: string;
  onRemove: () => void;
}) {
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="inline-flex items-center gap-1 rounded-full bg-accent-primary/15 text-accent-primary px-2.5 py-0.5 text-xs font-medium"
    >
      {label}
      <button
        type="button"
        onClick={onRemove}
        className="p-0.5 rounded hover:bg-accent-primary/20"
        aria-label={`Remove ${label} filter`}
      >
        <X className="w-3 h-3" />
      </button>
    </motion.span>
  );
}
