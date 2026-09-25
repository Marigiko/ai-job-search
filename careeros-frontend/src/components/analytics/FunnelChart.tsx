import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  type TooltipProps,
} from 'recharts';
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent';
import { motion } from 'framer-motion';
import {
  PIPELINE_STAGES,
  STAGE_LABELS,
  type PipelineStage,
} from '@/types/pipeline';
import type { FunnelResponse } from '@/types/analytics';

const FUNNEL_GRADIENTS: Record<PipelineStage, [string, string]> = {
  discovered: ['#64748b', '#475569'],
  interested: ['#8b5cf6', '#7c3aed'],
  applied: ['#6366f1', '#4f46e5'],
  screening: ['#f59e0b', '#d97706'],
  interview: ['#10b981', '#059669'],
  offer: ['#10b981', '#047857'],
  rejected: ['#ef4444', '#dc2626'],
};

interface FunnelChartProps {
  data: FunnelResponse;
}

function FunnelTooltip({ active, payload }: TooltipProps<ValueType, NameType>): JSX.Element | null {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload as { stage: string; count: number; rate: number | null };
  const label = STAGE_LABELS[point.stage as PipelineStage] ?? point.stage;
  return (
    <div className="glass-card px-3 py-2 text-xs">
      <p className="font-semibold text-text-primary">{label}</p>
      <p className="text-text-secondary">{point.count} postings</p>
      {point.rate !== null && point.rate !== undefined && (
        <p className="text-accent-secondary">
          {(point.rate * 100).toFixed(1)}% conversion
        </p>
      )}
    </div>
  );
}

export function FunnelChart({ data }: FunnelChartProps): JSX.Element {
  const countsByStage = new Map(data.stages.map((s) => [s.stage, s.count]));

  const chartData = PIPELINE_STAGES.map((stage) => ({
    stage,
    label: STAGE_LABELS[stage],
    count: countsByStage.get(stage) ?? 0,
    rate: null as number | null,
  }));

  return (
    <div className="flex flex-col h-full gap-4">
      <div className="flex-1 min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 8, right: 8, left: -16, bottom: 0 }}
            barCategoryGap="22%"
          >
            <XAxis
              dataKey="label"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={{ stroke: '#2a2a3a' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip
              content={<FunnelTooltip />}
              cursor={{ fill: 'rgba(99,102,241,0.08)' }}
            />
            <Bar dataKey="count" radius={[6, 6, 0, 0]} isAnimationActive maxBarSize={48}>
              {chartData.map((entry) => (
                <Cell key={entry.stage} fill={`url(#grad-${entry.stage})`} />
              ))}
            </Bar>
            <defs>
              {PIPELINE_STAGES.map((stage) => {
                const [from, to] = FUNNEL_GRADIENTS[stage];
                return (
                  <linearGradient
                    key={stage}
                    id={`grad-${stage}`}
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="0%" stopColor={from} stopOpacity={0.95} />
                    <stop offset="100%" stopColor={to} stopOpacity={0.7} />
                  </linearGradient>
                );
              })}
            </defs>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <ConversionRow conversions={data.conversions} totalPostings={data.total_postings} />
    </div>
  );
}

function ConversionRow({
  conversions,
  totalPostings,
}: {
  conversions: FunnelResponse['conversions'];
  totalPostings: number;
}): JSX.Element {
  if (totalPostings === 0) {
    return (
      <p className="text-xs text-text-muted text-center">
        No applications tracked yet.
      </p>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
      {conversions.map((c, i) => {
        const drop = i === 0
          ? ((totalPostings - c.count) / totalPostings) * 100
          : null;
        return (
          <motion.div
            key={`${c.from_stage}-${c.to_stage}`}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-center gap-1.5"
          >
            <span className="text-text-muted">
              {STAGE_LABELS[c.from_stage as PipelineStage] ?? c.from_stage}
            </span>
            <span className="text-text-muted">→</span>
            <span className="text-text-secondary">
              {STAGE_LABELS[c.to_stage as PipelineStage] ?? c.to_stage}
            </span>
            <span className="font-mono font-semibold text-accent-primary">
              {(c.rate * 100).toFixed(0)}%
            </span>
            {drop !== null && drop > 0 && (
              <span className="text-text-muted">(-{drop.toFixed(0)}%)</span>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
