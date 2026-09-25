// Shared constants mirroring backend enums and defaults.
// Canonical pipeline stage metadata lives in `@/types/pipeline`.

export {
  PIPELINE_STAGES,
  STAGE_LABELS,
  STAGE_COLORS,
} from '@/types/pipeline';

export type { PipelineStage } from '@/types/pipeline';

export const REMOTE_LABELS: Record<string, string> = {
  onsite: "On-site",
  remote: "Remote",
  hybrid: "Hybrid",
};

export const PORTAL_LABELS: Record<string, string> = {
  linkedin: "LinkedIn",
  remoteok: "RemoteOK",
  weworkremotely: "We Work Remotely",
  jobicy: "Jobicy",
  getonbrd: "Get on Board",
  arbeitnow: "Arbeitnow",
  themuse: "The Muse",
  landingjobs: "Landing.jobs",
  freehire: "Freehire",
  computrabajo: "Computrabajo",
};
