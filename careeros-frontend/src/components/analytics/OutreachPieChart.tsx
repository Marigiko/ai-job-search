import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import type { TooltipProps } from 'recharts';
import type { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent';
import { motion } from 'framer-motion';
import type { OutreachMetrics } from '@/types/analytics';

interface PieDatum {
  key: string;
  label: string;
  value: number;
  color: string;
}

const STATUS_COLORS: Record<string, string> = {
  opened: '#6366f1',
  replied: '#10b981',
  bounced: '#ef4444',
  failed: '#f59e0b',
};

interface OutreachPieChartProps {
  data: OutreachMetrics;
}

function DonutTooltip({ active, payload }: TooltipProps<ValueType, NameType>): JSX.Element | null {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload as PieDatum;
  return (
    <div className="glass-card px-3 py-2 text-xs">
      <div className="flex items-center gap-2">
        <span
          className="w-2 h-2 rounded-full"
          style={{ backgroundColor: point.color }}
        />
        <span className="font-semibold text-text-primary">{point.label}</span>
      </div>
      <p className="text-text-secondary">{point.value} emails</p>
    </div>
  );
}

export function OutreachPieChart({ data }: OutreachPieChartProps): JSX.Element {
  const byStatus = data.by_status;

  const segments: PieDatum[] = [
    { key: 'opened', label: 'Opened', value: byStatus.opened, color: STATUS_COLORS.opened },
    { key: 'replied', label: 'Replied', value: byStatus.replied, color: STATUS_COLORS.replied },
    { key: 'bounced', label: 'Bounced', value: byStatus.bounced, color: STATUS_COLORS.bounced },
    { key: 'failed', label: 'Failed', value: byStatus.failed, color: STATUS_COLORS.failed },
  ];

  const visible = segments.filter((s) => s.value > 0);
  const isEmpty = visible.length === 0;

  return (
    <div className="flex flex-col h-full gap-4">
      <div className="flex-1 min-h-[180px] relative">
        {isEmpty ? (
          <EmptyRing />
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={visible}
                dataKey="value"
                nameKey="label"
                innerRadius="55%"
                outerRadius="85%"
                paddingAngle={3}
                isAnimationActive
                stroke="#0a0a0f"
                strokeWidth={2}
              >
                {visible.map((entry) => (
                  <Cell key={entry.key} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<DonutTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        )}

        {/* Center label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-2xl font-bold text-text-primary font-mono">
            {data.total_sent}
          </span>
          <span className="text-[10px] uppercase tracking-wider text-text-muted">
            Sent
          </span>
        </div>
      </div>

      <MetricLegend data={data} segments={visible} />
    </div>
  );
}

function EmptyRing(): JSX.Element {
  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <div className="w-[150px] h-[150px] rounded-full border-4 border-dashed border-border flex items-center justify-center">
        <span className="text-xs text-text-muted">No data</span>
      </div>
    </div>
  );
}

function MetricLegend({
  data,
  segments,
}: {
  data: OutreachMetrics;
  segments: PieDatum[];
}): JSX.Element {
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-3 gap-2 text-center">
        <RatePill label="Open" rate={data.open_rate} color={STATUS_COLORS.opened} />
        <RatePill label="Reply" rate={data.reply_rate} color={STATUS_COLORS.replied} />
        <RatePill label="Bounce" rate={data.bounce_rate} color={STATUS_COLORS.bounced} />
      </div>

      {segments.length > 0 && (
        <div className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 pt-1">
          {segments.map((s) => (
            <div key={s.key} className="flex items-center gap-1.5 text-xs">
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: s.color }}
              />
              <span className="text-text-secondary">{s.label}</span>
              <span className="font-mono text-text-primary">{s.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function RatePill({
  label,
  rate,
  color,
}: {
  label: string;
  rate: number;
  color: string;
}): JSX.Element {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center gap-0.5 px-2 py-1.5 rounded-md bg-surface-elevated border border-border-subtle"
    >
      <span className="text-[10px] uppercase tracking-wider text-text-muted">
        {label}
      </span>
      <span className="text-sm font-bold font-mono" style={{ color }}>
        {(rate * 100).toFixed(1)}%
      </span>
    </motion.div>
  );
}
