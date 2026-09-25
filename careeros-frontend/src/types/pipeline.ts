/**
 * Pipeline domain types — canonical definitions.
 * Backend reference: careeros-backend/app/schemas/application.py
 */

export const PIPELINE_STAGES = [
  "discovered",
  "interested",
  "applied",
  "screening",
  "interview",
  "offer",
  "rejected",
] as const;

export type PipelineStage = (typeof PIPELINE_STAGES)[number];

export const STAGE_CONFIG: Record<
  PipelineStage,
  { label: string; color: string; icon: string }
> = {
  discovered: { label: "Discovered", color: "#64748b", icon: "🔍" },
  interested: { label: "Interested", color: "#8b5cf6", icon: "⭐" },
  applied: { label: "Applied", color: "#6366f1", icon: "📤" },
  screening: { label: "Screening", color: "#f59e0b", icon: "📋" },
  interview: { label: "Interview", color: "#10b981", icon: "🎯" },
  offer: { label: "Offer", color: "#10b981", icon: "🎉" },
  rejected: { label: "Rejected", color: "#ef4444", icon: "✕" },
};

/** Display label per stage — convenience alias over STAGE_CONFIG. */
export const STAGE_LABELS: Record<PipelineStage, string> = Object.fromEntries(
  Object.entries(STAGE_CONFIG).map(([k, v]) => [k, v.label]),
) as Record<PipelineStage, string>;

/** Tailwind badge classes per stage. */
export const STAGE_COLORS: Record<PipelineStage, string> = {
  discovered: "bg-slate-500/20 text-slate-400",
  interested: "bg-violet-500/20 text-violet-400",
  applied: "bg-indigo-500/20 text-indigo-400",
  screening: "bg-amber-500/20 text-amber-400",
  interview: "bg-emerald-500/20 text-emerald-400",
  offer: "bg-emerald-500/20 text-emerald-400",
  rejected: "bg-red-500/20 text-red-400",
};

export interface KanbanItem {
  job_id: number;
  job_title: string;
  company_name: string | null;
  application_id: number | null;
  status: string;
  applied_date: string | null;
}

export interface KanbanResponse {
  stages: Record<string, KanbanItem[]>;
}

export interface PipelineCounts {
  stages: Record<string, number>;
}

/** Stage column identifier — must match PipelineStage. */
export type StageColumnId = PipelineStage;

/** Drag data attached to a draggable JobCard. */
export interface DragData {
  type: "job";
  item: KanbanItem;
  sourceStage: StageColumnId;
}

/** Utility: create an empty stage map. */
export const createEmptyStages = (): Record<string, KanbanItem[]> =>
  Object.fromEntries(PIPELINE_STAGES.map((s) => [s, []]));

/** Normalize a KanbanResponse into a stage map, filtering out unknown stages. */
export const normalizeStages = (data: KanbanResponse): Record<string, KanbanItem[]> => {
  const stages = createEmptyStages();
  for (const [stage, items] of Object.entries(data.stages)) {
    if (stage in stages) {
      stages[stage] = items;
    }
  }
  return stages;
};
