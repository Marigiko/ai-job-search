// CareerOS frontend type definitions — canonical barrel export.

import type { PipelineStage, StageColumnId, DragData } from '@/types/pipeline';

export type { PipelineStage, StageColumnId, DragData };

export {
  PIPELINE_STAGES,
  STAGE_CONFIG,
  STAGE_LABELS,
  STAGE_COLORS,
  createEmptyStages,
  normalizeStages,
} from '@/types/pipeline';

// Re-export Kanban domain types (canonical lives in @/types/pipeline)
export type {
  KanbanItem,
  KanbanResponse,
  PipelineCounts,
} from '@/types/pipeline';

// ── WebSocket ────────────────────────────────────────────────────────────────

export type WebSocketStatus = 'connecting' | 'open' | 'closed' | 'error';

export type WebSocketMessage =
  | { type: 'job.created'; payload: { id: number; title: string } }
  | { type: 'job.updated'; payload: { id: number; status: string } }
  | { type: 'application.stage_changed'; payload: { jobId: number; from: string; to: string } }
  | { type: 'outreach.queued'; payload: { emailId: number } }
  | { type: 'outreach.sent'; payload: { emailId: number } }
  | { type: 'pipeline.snapshot'; payload: Record<string, number> }
  | { type: 'search.progress'; payload: { taskId: string; portal: string; done: number; total: number } }
  | { type: 'ping'; payload: null };

// ── Domain enums ─────────────────────────────────────────────────────────────

export type RemoteType = 'onsite' | 'remote' | 'hybrid';

export type ApplicationStatus =
  | 'discovered'
  | 'interested'
  | 'applied'
  | 'screening'
  | 'interview'
  | 'offer'
  | 'rejected'
  | 'withdrawn';

export type EmailStatus =
  | 'draft'
  | 'queued'
  | 'sent'
  | 'opened'
  | 'replied'
  | 'bounced'
  | 'failed';

// ── Companies ────────────────────────────────────────────────────────────────

export interface Company {
  id: number;
  name: string;
  domain: string | null;
  industry: string | null;
  size: string | null;
}

export interface CompanyCreate {
  name: string;
  domain?: string | null;
  industry?: string | null;
  size?: string | null;
}

export interface CompanyUpdate {
  name?: string | null;
  domain?: string | null;
  industry?: string | null;
  size?: string | null;
}

// ── Job Postings ─────────────────────────────────────────────────────────────

export interface JobPosting {
  id: number;
  title: string;
  description: string | null;
  url: string | null;
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  location: string | null;
  remote_type: RemoteType | null;
  visa_sponsorship: boolean;
  portal_source: string | null;
  portal_id: string | null;
  status: string;
  discovered_at: string | null;
  applied_at: string | null;
  notes: string | null;
  raw_data: Record<string, unknown> | null;
  company_id: number | null;
}

export interface JobPostingCreate {
  title: string;
  description?: string | null;
  url?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  currency?: string | null;
  location?: string | null;
  remote_type?: RemoteType | null;
  visa_sponsorship?: boolean;
  portal_source?: string | null;
  portal_id?: string | null;
  notes?: string | null;
  raw_data?: Record<string, unknown> | null;
  company_id?: number | null;
}

export interface JobPostingUpdate {
  title?: string | null;
  description?: string | null;
  url?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  currency?: string | null;
  location?: string | null;
  remote_type?: RemoteType | null;
  visa_sponsorship?: boolean | null;
  status?: string | null;
  notes?: string | null;
}

// ── Applications ─────────────────────────────────────────────────────────────

export interface Application {
  id: number;
  job_posting_id: number;
  status: ApplicationStatus;
  applied_date: string | null;
  follow_up_date: string | null;
  cv_version: string | null;
  cover_letter_version: string | null;
  notes: string | null;
}

export interface ApplicationCreate {
  job_posting_id: number;
  status?: ApplicationStatus;
  applied_date?: string | null;
  follow_up_date?: string | null;
  cv_version?: string | null;
  cover_letter_version?: string | null;
  notes?: string | null;
}

export interface ApplicationUpdate {
  status?: ApplicationStatus | null;
  applied_date?: string | null;
  follow_up_date?: string | null;
  cv_version?: string | null;
  cover_letter_version?: string | null;
  notes?: string | null;
}

// ── Outreach ─────────────────────────────────────────────────────────────────

export interface OutreachEmail {
  id: number;
  application_id: number | null;
  template_id: number | null;
  recipient_email: string;
  subject: string;
  body: string;
  status: EmailStatus;
  sent_at: string | null;
  opened_at: string | null;
  replied_at: string | null;
  ab_variant: string | null;
}

export interface OutreachEmailCreate {
  recipient_email: string;
  subject: string;
  body: string;
  application_id?: number | null;
  template_id?: number | null;
}

export interface OutreachQueueItem {
  email_id: number;
  recipient: string;
  subject: string;
  status: string;
  queued_at: string | null;
}

// ── Email Templates ──────────────────────────────────────────────────────────

export interface EmailTemplate {
  id: number;
  name: string;
  subject_template: string;
  body_template: string;
  language: string;
  is_ab_test: boolean;
  ab_variant: string | null;
  usage_count: number;
  reply_rate: number | null;
}

export interface EmailTemplateCreate {
  name: string;
  subject_template: string;
  body_template: string;
  language?: string;
  is_ab_test?: boolean;
  ab_variant?: string | null;
}

export interface EmailTemplateUpdate {
  name?: string | null;
  subject_template?: string | null;
  body_template?: string | null;
  language?: string | null;
  is_ab_test?: boolean | null;
  ab_variant?: string | null;
}

// ── Contacts ─────────────────────────────────────────────────────────────────

export interface Contact {
  id: number;
  company_id: number | null;
  name: string | null;
  email: string | null;
  title: string | null;
  linkedin_url: string | null;
  is_recruiter: boolean;
  source: string | null;
}

// ── Settings ────────────────────────────────────────────────────────────────

export interface SmtpConfig {
  host: string;
  port: number;
  username: string;
  password: string;
  use_tls: boolean;
  from_name: string;
  from_email: string;
  reply_to: string | null;
}

export interface SmtpConfigUpdate {
  host?: string;
  port?: number;
  username?: string;
  password?: string;
  use_tls?: boolean;
  from_name?: string;
  from_email?: string;
  reply_to?: string | null;
}

export interface ApiKeys {
  hunter: string;
  apollo: string;
  serper: string;
}

export interface ApiKeysUpdate {
  hunter?: string;
  apollo?: string;
  serper?: string;
}

export interface OutreachLimits {
  daily_max: number;
  hourly_max: number;
  delay_seconds: number;
  max_per_company: number;
  cooldown_hours: number;
}

export interface OutreachLimitsUpdate {
  daily_max?: number;
  hourly_max?: number;
  delay_seconds?: number;
  max_per_company?: number;
  cooldown_hours?: number;
}

export interface PortalToggle {
  id: string;
  name: string;
  enabled: boolean;
  description: string;
  category: 'remote' | 'local' | 'aggregator';
}

export interface SettingsBundle {
  smtp: SmtpConfig;
  api_keys: ApiKeys;
  outreach_limits: OutreachLimits;
  portals: PortalToggle[];
}

export interface AbTestPerformance {
  template_id: number;
  template_name: string;
  variant: string;
  sent_count: number;
  open_rate: number;
  reply_rate: number;
  is_winner: boolean;
}

// ── Common ───────────────────────────────────────────────────────────────────

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

export interface MessageResponse {
  message: string;
  detail?: string | null;
}

export interface JobFilters {
  status?: string | null;
  remote_type?: RemoteType | null;
  portal_source?: string | null;
  search?: string | null;
  visa_sponsorship?: boolean | null;
  page?: number;
  per_page?: number;
}

// ── Documents ────────────────────────────────────────────────────────────────

export type DocumentType = 'cv' | 'cover_letter';

export type DocumentStatus = 'generating' | 'ready' | 'failed';

export interface DocumentVersion {
  id: number;
  version: number;
  document_type: DocumentType;
  job_title: string;
  company_name: string | null;
  status: DocumentStatus;
  file_size: number | null;
  created_at: string;
  latex_template: string;
}

export interface DocumentListItem {
  id: number;
  job_posting_id: number | null;
  company_id: number | null;
  document_type: DocumentType;
  version: string;
  status: DocumentStatus;
  file_path: string | null;
  file_size: number | null;
  created_at: string;
  job_title: string | null;
  company_name: string | null;
}

export interface DocumentGenerateRequest {
  job_posting_id: number | null;
  company_id: number | null;
  document_type: DocumentType;
  template_name?: string | null;
  notes?: string | null;
}

export interface DocumentGenerateResponse {
  id: number;
  status: DocumentStatus;
  message: string;
}

export interface DocumentPreview {
  id: number;
  preview_url: string;
  page_count: number;
}

export interface DocumentStats {
  total_generated: number;
  by_type: Record<DocumentType, number>;
  by_week: { week: string; count: number }[];
}
