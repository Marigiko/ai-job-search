import axios, { type AxiosError, type AxiosInstance } from 'axios';
import type {
  AbTestPerformance,
  ApiKeys,
  ApiKeysUpdate,
  Application,
  ApplicationCreate,
  ApplicationUpdate,
  Company,
  CompanyCreate,
  CompanyUpdate,
  DocumentGenerateRequest,
  DocumentGenerateResponse,
  DocumentListItem,
  DocumentStats,
  EmailTemplate,
  EmailTemplateCreate,
  EmailTemplateUpdate,
  JobFilters,
  JobPosting,
  JobPostingCreate,
  JobPostingUpdate,
  KanbanResponse,
  MessageResponse,
  OutreachEmailCreate,
  OutreachLimits,
  OutreachLimitsUpdate,
  OutreachQueueItem,
  PaginatedResponse,
  PipelineCounts,
  PortalToggle,
  SettingsBundle,
  SmtpConfig,
  SmtpConfigUpdate,
} from '@/types';
import type {
  FunnelResponse,
  OutreachAbResponse,
  OutreachMetrics,
  SalaryInsights,
} from '@/types/analytics';

// ── Dashboard types (local to client until backend lands) ─────────────────────

export interface DashboardSummary {
  active_jobs: number;
  applications_this_week: number;
  response_rate: number;
  total_applications: number;
}

export interface ActivityPoint {
  date: string;
  applications: number;
  discoveries: number;
}

export interface FollowUpItem {
  application_id: number;
  job_title: string;
  company_name: string | null;
  follow_up_date: string;
  status: string;
  days_overdue: number;
}

const API_BASE = import.meta.env.VITE_API_URL ?? '/api/v1';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function createClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: API_BASE,
    headers: { 'Content-Type': 'application/json' },
  });

  instance.interceptors.response.use(
    (response) => response,
    (error: AxiosError<MessageResponse>) => {
      const message =
        error.response?.data?.detail ??
        error.response?.data?.message ??
        error.message;
      throw new ApiError(message, error.response?.status ?? 500);
    },
  );

  return instance;
}

export const api = createClient();

// ── Jobs ─────────────────────────────────────────────────────────────────────

export const jobsApi = {
  list: async (filters: JobFilters = {}): Promise<PaginatedResponse<JobPosting>> => {
    const { data } = await api.get<PaginatedResponse<JobPosting>>('/jobs', {
      params: filters,
    });
    return data;
  },

  get: async (id: number): Promise<JobPosting> => {
    const { data } = await api.get<JobPosting>(`/jobs/${id}`);
    return data;
  },

  create: async (payload: JobPostingCreate): Promise<JobPosting> => {
    const { data } = await api.post<JobPosting>('/jobs', payload);
    return data;
  },

  update: async (id: number, payload: JobPostingUpdate): Promise<JobPosting> => {
    const { data } = await api.patch<JobPosting>(`/jobs/${id}`, payload);
    return data;
  },

  remove: async (id: number): Promise<void> => {
    await api.delete(`/jobs/${id}`);
  },
};

// ── Companies ────────────────────────────────────────────────────────────────

export const companiesApi = {
  list: async (): Promise<Company[]> => {
    const { data } = await api.get<PaginatedResponse<Company>>('/companies');
    return data.data;
  },

  create: async (payload: CompanyCreate): Promise<Company> => {
    const { data } = await api.post<Company>('/companies', payload);
    return data;
  },

  update: async (id: number, payload: CompanyUpdate): Promise<Company> => {
    const { data } = await api.patch<Company>(`/companies/${id}`, payload);
    return data;
  },

  remove: async (id: number): Promise<void> => {
    await api.delete(`/companies/${id}`);
  },
};

// ── Applications / Pipeline ──────────────────────────────────────────────────

export const applicationsApi = {
  list: async (): Promise<Application[]> => {
    const { data } = await api.get<Application[]>('/pipeline/applications');
    return data;
  },

  create: async (payload: ApplicationCreate): Promise<Application> => {
    const { data } = await api.post<Application>('/pipeline/applications', payload);
    return data;
  },

  update: async (id: number, payload: ApplicationUpdate): Promise<Application> => {
    const { data } = await api.patch<Application>(`/pipeline/applications/${id}`, payload);
    return data;
  },

  getKanban: async (): Promise<KanbanResponse> => {
    const { data } = await api.get<KanbanResponse>('/pipeline/kanban');
    return data;
  },

  getPipelineCounts: async (): Promise<PipelineCounts> => {
    const { data } = await api.get<PipelineCounts>('/pipeline');
    return data;
  },
};

// ── Outreach ─────────────────────────────────────────────────────────────────

export const outreachApi = {
  compose: async (payload: OutreachEmailCreate): Promise<{ preview: string; variant: string }> => {
    const { data } = await api.post<{ preview: string; variant: string }>(
      '/outreach/compose',
      payload,
    );
    return data;
  },

  queue: async (payload: OutreachEmailCreate): Promise<{ queued_id: number }> => {
    const { data } = await api.post<{ queued_id: number }>('/outreach/queue', payload);
    return data;
  },

  send: async (payload: OutreachEmailCreate): Promise<MessageResponse> => {
    const { data } = await api.post<MessageResponse>('/outreach/send', payload);
    return data;
  },

  getQueue: async (): Promise<OutreachQueueItem[]> => {
    const { data } = await api.get<OutreachQueueItem[]>('/outreach/queue');
    return data;
  },

  removeFromQueue: async (id: number): Promise<void> => {
    await api.delete(`/outreach/queue/${id}`);
  },
};

// ── Templates ────────────────────────────────────────────────────────────────

export const templatesApi = {
  list: async (): Promise<EmailTemplate[]> => {
    const { data } = await api.get<PaginatedResponse<EmailTemplate>>('/templates');
    return data.data;
  },

  create: async (payload: EmailTemplateCreate): Promise<EmailTemplate> => {
    const { data } = await api.post<EmailTemplate>('/templates', payload);
    return data;
  },

  update: async (id: number, payload: EmailTemplateUpdate): Promise<EmailTemplate> => {
    const { data } = await api.patch<EmailTemplate>(`/templates/${id}`, payload);
    return data;
  },

  remove: async (id: number): Promise<void> => {
    await api.delete(`/templates/${id}`);
  },
};

// ── Search ───────────────────────────────────────────────────────────────────

export const searchApi = {
  trigger: async (query: string, portals: string[]): Promise<{ task_id: string; total: number; counts: Record<string, number> }> => {
    const { data } = await api.post<{ task_id: string; total: number; counts: Record<string, number> }>(
      "/search",
      null,
      { params: { query, portals } },
    );
    return data;
  },

  status: async (taskId: string): Promise<{ status: string; task_id: string }> => {
    const { data } = await api.get<{ status: string; task_id: string }>(
      `/search/status/${taskId}`,
    );
    return data;
  },
};

// ── Analytics ────────────────────────────────────────────────────────────────

export const analyticsApi = {
  funnel: async (): Promise<FunnelResponse> => {
    const { data } = await api.get<FunnelResponse>('/analytics/funnel');
    return data;
  },

  outreach: async (): Promise<OutreachMetrics> => {
    const { data } = await api.get<OutreachMetrics>('/analytics/outreach');
    return data;
  },

  abTest: async (): Promise<OutreachAbResponse> => {
    const { data } = await api.get<OutreachAbResponse>('/analytics/outreach/ab-test');
    return data;
  },

  salary: async (): Promise<SalaryInsights> => {
    const { data } = await api.get<SalaryInsights>('/analytics/salary');
    return data;
  },
};

// ── Dashboard ─────────────────────────────────────────────────────────────────

export const dashboardApi = {
  getSummary: async (): Promise<DashboardSummary> => {
    const { data } = await api.get<DashboardSummary>('/dashboard/summary');
    return data;
  },

  getActivity: async (days = 14): Promise<ActivityPoint[]> => {
    const { data } = await api.get<ActivityPoint[]>('/dashboard/activity', {
      params: { days },
    });
    return data;
  },

  getFollowUps: async (): Promise<FollowUpItem[]> => {
    const { data } = await api.get<FollowUpItem[]>('/dashboard/follow-ups');
    return data;
  },
};

// ── Settings ────────────────────────────────────────────────────────────────

export const settingsApi = {
  getAll: async (): Promise<SettingsBundle> => {
    const { data } = await api.get<SettingsBundle>('/settings');
    return data;
  },

  getSmtp: async (): Promise<SmtpConfig> => {
    const { data } = await api.get<SmtpConfig>('/settings/smtp');
    return data;
  },

  updateSmtp: async (payload: SmtpConfigUpdate): Promise<SmtpConfig> => {
    const { data } = await api.patch<SmtpConfig>('/settings/smtp', payload);
    return data;
  },

  testSmtp: async (): Promise<{ success: boolean; message: string }> => {
    const { data } = await api.post<{ success: boolean; message: string }>(
      '/settings/smtp/test',
    );
    return data;
  },

  getApiKeys: async (): Promise<ApiKeys> => {
    const { data } = await api.get<ApiKeys>('/settings/api-keys');
    return data;
  },

  updateApiKeys: async (payload: ApiKeysUpdate): Promise<ApiKeys> => {
    const { data } = await api.patch<ApiKeys>('/settings/api-keys', payload);
    return data;
  },

  getOutreachLimits: async (): Promise<OutreachLimits> => {
    const { data } = await api.get<OutreachLimits>('/settings/outreach-limits');
    return data;
  },

  updateOutreachLimits: async (
    payload: OutreachLimitsUpdate,
  ): Promise<OutreachLimits> => {
    const { data } = await api.patch<OutreachLimits>('/settings/outreach-limits', payload);
    return data;
  },

  getPortals: async (): Promise<PortalToggle[]> => {
    const { data } = await api.get<PortalToggle[]>('/settings/portals');
    return data;
  },

  updatePortal: async (
    portalId: string,
    enabled: boolean,
  ): Promise<PortalToggle> => {
    const { data } = await api.patch<PortalToggle>(
      `/settings/portals/${portalId}`,
      { enabled },
    );
    return data;
  },

  getAbTestPerformance: async (): Promise<AbTestPerformance[]> => {
    const { data } = await api.get<AbTestPerformance[]>('/settings/ab-tests/performance');
    return data;
  },
};

// ── Documents ────────────────────────────────────────────────────────────────

export const documentsApi = {
  list: async (): Promise<DocumentListItem[]> => {
    const { data } = await api.get<PaginatedResponse<DocumentListItem>>('/documents');
    return data.data;
  },

  generate: async (payload: DocumentGenerateRequest): Promise<DocumentGenerateResponse> => {
    const { data } = await api.post<DocumentGenerateResponse>('/documents/generate', payload);
    return data;
  },

  getStats: async (): Promise<DocumentStats> => {
    const { data } = await api.get<DocumentStats>('/documents/stats');
    return data;
  },

  /** Returns the PDF preview URL for an iframe/embed. */
  previewUrl: (id: number): string => `${API_BASE}/documents/${id}/preview`,

  /** Returns the PDF download URL. */
  downloadUrl: (id: number): string => `${API_BASE}/documents/${id}/download`,
};
