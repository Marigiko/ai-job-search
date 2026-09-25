/**
 * Analytics domain types — mirrors careeros-backend/app/schemas/analytics.py.
 * Keep field names aligned with the API response for lossless mapping.
 */

// ── Funnel ──────────────────────────────────────────────────────────────────

export interface FunnelStage {
  stage: string;
  count: number;
}

export interface FunnelConversion {
  from_stage: string;
  to_stage: string;
  rate: number;
  count: number;
}

export interface FunnelResponse {
  total_postings: number;
  stages: FunnelStage[];
  conversions: FunnelConversion[];
}

// ── Outreach ────────────────────────────────────────────────────────────────

export interface OutreachByStatus {
  sent: number;
  opened: number;
  replied: number;
  bounced: number;
  failed: number;
}

export interface OutreachMetrics {
  total_sent: number;
  by_status: OutreachByStatus;
  open_rate: number;
  reply_rate: number;
  bounce_rate: number;
  avg_time_to_open_hours: number | null;
}

export interface AbTestVariant {
  variant: string;
  sent: number;
  open_rate: number;
  reply_rate: number;
}

export interface OutreachAbResponse {
  has_data: boolean;
  variants: AbTestVariant[];
}

// ── Salary ──────────────────────────────────────────────────────────────────

export interface SalaryBucket {
  range_label: string;
  min_bound: number;
  max_bound: number;
  count: number;
}

export interface SalaryByCategory {
  category: string;
  avg_min: number | null;
  avg_max: number | null;
  sample_size: number;
}

export interface SalaryInsights {
  postings_with_salary: number;
  avg_salary_min: number | null;
  avg_salary_max: number | null;
  median_salary_min: number | null;
  median_salary_max: number | null;
  p25_salary_min: number | null;
  p75_salary_max: number | null;
  currency: string;
  buckets: SalaryBucket[];
  by_remote_type: SalaryByCategory[];
}
