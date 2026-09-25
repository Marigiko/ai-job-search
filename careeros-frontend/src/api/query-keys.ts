// Centralized TanStack Query key factory — colocate invalidation logic.

export const queryKeys = {
  jobs: {
    all: ['jobs'] as const,
    list: (filters: object = {}) =>
      ['jobs', 'list', filters] as const,
    detail: (id: number) => ['jobs', 'detail', id] as const,
  },

  companies: {
    all: ['companies'] as const,
    list: () => ['companies', 'list'] as const,
    detail: (id: number) => ['companies', 'detail', id] as const,
  },

  pipeline: {
    all: ['pipeline'] as const,
    kanban: () => ['pipeline', 'kanban'] as const,
    counts: () => ['pipeline', 'counts'] as const,
    applications: () => ['pipeline', 'applications'] as const,
  },

  outreach: {
    all: ['outreach'] as const,
    queue: () => ['outreach', 'queue'] as const,
  },

  templates: {
    all: ['templates'] as const,
    list: () => ['templates', 'list'] as const,
    detail: (id: number) => ['templates', 'detail', id] as const,
  },

  analytics: {
    all: ['analytics'] as const,
    funnel: () => ['analytics', 'funnel'] as const,
    outreach: () => ['analytics', 'outreach'] as const,
    abTest: () => ['analytics', 'outreach', 'ab-test'] as const,
    salary: () => ['analytics', 'salary'] as const,
  },

  search: {
    all: ['search'] as const,
    status: (taskId: string) => ['search', 'status', taskId] as const,
  },

  dashboard: {
    all: ['dashboard'] as const,
    summary: () => ['dashboard', 'summary'] as const,
    activity: (days = 14) => ['dashboard', 'activity', days] as const,
    followUps: () => ['dashboard', 'follow-ups'] as const,
  },

  documents: {
    all: ['documents'] as const,
    list: () => ['documents', 'list'] as const,
    detail: (id: number) => ['documents', 'detail', id] as const,
    stats: () => ['documents', 'stats'] as const,
  },
} as const;
