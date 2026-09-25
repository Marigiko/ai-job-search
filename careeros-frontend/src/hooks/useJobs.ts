import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jobsApi } from "@/api/client";
import { queryKeys } from "@/api/query-keys";
import type { JobFilters, JobPosting, JobPostingUpdate, PaginatedResponse } from "@/types";

export function useJobs(filters: JobFilters = {}) {
  return useQuery<PaginatedResponse<JobPosting>>({
    queryKey: queryKeys.jobs.list(filters),
    queryFn: () => jobsApi.list(filters),
    placeholderData: (previousData) => previousData,
  });
}

export function useJobDetail(id: number | null) {
  return useQuery<JobPosting>({
    queryKey: queryKeys.jobs.detail(id ?? 0),
    queryFn: () => jobsApi.get(id ?? 0),
    enabled: id !== null,
  });
}

export function useUpdateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: JobPostingUpdate }) =>
      jobsApi.update(id, payload),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
      queryClient.setQueryData(queryKeys.jobs.detail(data.id), data);
    },
  });
}

export function useDeleteJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => jobsApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
    },
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { title: string; url?: string | null; description?: string | null; company_id?: number | null }) =>
      jobsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs.all });
    },
  });
}
