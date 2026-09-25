import { useState, useCallback, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Search as SearchIcon,
  Loader2,
  AlertCircle,
  Globe,
  ExternalLink,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { searchApi, settingsApi, jobsApi } from "@/api/client";
import { queryKeys } from "@/api/query-keys";
import type { PortalToggle, JobPosting } from "@/types";

interface SearchResponse {
  task_id: string;
  total: number;
  counts: Record<string, number>;
}

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [activePortals, setActivePortals] = useState<Set<string>>(new Set());
  const [lastSearchTotal, setLastSearchTotal] = useState<number | null>(null);

  const { data: portals } = useQuery<PortalToggle[]>({
    queryKey: ["settings", "portals"],
    queryFn: settingsApi.getPortals,
  });

  const { data: searchResponse, isLoading, isError, error } = useQuery<SearchResponse>({
    queryKey: ["search", "trigger", query, Array.from(activePortals).sort()],
    queryFn: async () => {
      const result = await searchApi.trigger(query, Array.from(activePortals));
      setLastSearchTotal(result.total);
      return result;
    },
    enabled: false,
    retry: false,
  });

  // Fetch recent jobs after search to display them
  const { data: recentJobs, isLoading: jobsLoading } = useQuery({
    queryKey: queryKeys.jobs.list({}),
    queryFn: () => jobsApi.list({ per_page: lastSearchTotal ?? 50 }),
    enabled: lastSearchTotal !== null && lastSearchTotal > 0,
  });

  const handleSearch = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (query.trim().length === 0) return;
      setSearchParams({ q: query.trim() });
      setLastSearchTotal(null);
      // Trigger search manually
      void searchApi.trigger(query, Array.from(activePortals)).then((r) => {
        setLastSearchTotal(r.total);
      });
    },
    [query, activePortals, setSearchParams],
  );

  const togglePortal = useCallback((id: string) => {
    setActivePortals((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const displayJobs = recentJobs?.data?.slice(0, lastSearchTotal ?? 20) ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary">
          Job Search
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Search across multiple job portals in real-time
        </p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for roles, skills, companies..."
              className="input pl-11 pr-4 py-3 text-base"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || query.trim().length === 0}
            className="btn-primary px-6"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <SearchIcon className="w-5 h-5" />
            )}
            <span>Search</span>
          </button>
        </div>

        {/* Portal Toggles */}
        {portals && portals.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {portals.map((portal) => {
              const isActive = activePortals.size === 0 || activePortals.has(portal.id);
              return (
                <button
                  key={portal.id}
                  type="button"
                  onClick={() => togglePortal(portal.id)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                    isActive
                      ? "border-accent-primary bg-accent-primary/10 text-accent-primary"
                      : "border-border text-text-muted hover:text-text-secondary"
                  }`}
                >
                  <Globe className="w-3 h-3" />
                  {portal.name}
                </button>
              );
            })}
          </div>
        )}
      </form>

      {/* Status */}
      {isLoading && (
        <div className="flex items-center gap-3 p-4 rounded-lg bg-accent-primary/10 text-accent-primary">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Searching across portals...</span>
        </div>
      )}

      {isError && (
        <div className="flex items-center gap-3 p-4 rounded-lg border border-accent-danger/30 bg-accent-danger/10 text-accent-danger">
          <AlertCircle className="w-5 h-5" />
          <span>{error instanceof Error ? error.message : "Search failed"}</span>
        </div>
      )}

      {/* Results */}
      {lastSearchTotal !== null && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-text-secondary">
              Found <span className="text-text-primary font-semibold">{lastSearchTotal}</span> jobs
            </h2>
          </div>

          {jobsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-accent-primary animate-spin" />
            </div>
          ) : displayJobs.length > 0 ? (
            <div className="rounded-lg border border-border overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-bg-secondary text-text-muted text-xs uppercase tracking-wider">
                    <th className="px-4 py-3 text-left font-medium">Job Title</th>
                    <th className="px-4 py-3 text-left font-medium">Portal</th>
                    <th className="px-4 py-3 text-left font-medium">Location</th>
                    <th className="px-4 py-3 text-left font-medium w-[100px]">Link</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {displayJobs.map((job) => (
                    <tr key={job.id} className="hover:bg-surface-hover/50 transition-colors">
                      <td className="px-4 py-3">
                        <span className="font-medium text-text-primary">{job.title}</span>
                      </td>
                      <td className="px-4 py-3 text-text-secondary text-xs">
                        {job.portal_source ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-text-secondary text-xs">
                        {job.location ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        {job.url && (
                          <a
                            href={job.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-accent-primary hover:underline"
                          >
                            View <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 text-text-muted">
              Results saved. Check the Jobs tab to view them.
            </div>
          )}
        </div>
      )}

      {/* Tips */}
      {lastSearchTotal === null && !isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { title: "Multi-portal", desc: "Search across RemoteOK, Arbeitnow, Landing.jobs and more simultaneously" },
            { title: "Real-time", desc: "Results are fetched live from each portal's API" },
            { title: "Auto-persist", desc: "Discovered jobs are saved to your database automatically" },
          ].map((tip) => (
            <div key={tip.title} className="p-4 rounded-lg border border-border bg-surface">
              <h3 className="text-sm font-medium text-text-primary">{tip.title}</h3>
              <p className="text-xs text-text-muted mt-1">{tip.desc}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
