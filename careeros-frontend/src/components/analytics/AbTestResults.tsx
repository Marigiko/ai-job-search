import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
  type TooltipProps,
} from 'recharts';
import type { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent';
import { motion } from 'framer-motion';
import { TrendingUp, Trophy, type LucideIcon } from 'lucide-react';
import type { OutreachAbResponse, AbTestVariant } from '@/types/analytics';

const OPEN_COLOR = '#6366f1';
const REPLY_COLOR = '#10b981';

interface AbTestResultsProps {
  data: OutreachAbResponse;
}

interface ChartRow {
  variant: string;
  open_rate: number;
  reply_rate: number;
  sent: number;
}

function AbTooltip({ active, payload, label }: TooltipProps<ValueType, NameType>): JSX.Element | null {
  if (!active || !payload?.length) return null;
  const sent = payload[0].payload as ChartRow;
  return (
    <div className="glass-card px-3 py-2 text-xs space-y-1">
      <p className="font-semibold text-text-primary">Variant {label}</p>
      <p className="text-text-muted font-mono">{sent.sent} sent</p>
      {payload.map((entry) => (
        <p key={entry.dataKey as string} style={{ color: entry.color }}>
          {entry.name}: {((entry.value as number) * 100).toFixed(1)}%
        </p>
      ))}
    </div>
  );
}

export function AbTestResults({ data }: AbTestResultsProps): JSX.Element {
  if (!data.has_data || data.variants.length === 0) {
    return <EmptyAb />;
  }

  const chartData: ChartRow[] = data.variants.map((v) => ({
    variant: v.variant,
    open_rate: v.open_rate,
    reply_rate: v.reply_rate,
    sent: v.sent,
  }));

  const winner = data.variants.reduce<AbTestVariant | null>((best, v) => {
    if (best === null) return v;
    return v.reply_rate > best.reply_rate ? v : best;
  }, null);

  return (
    <div className="flex flex-col h-full gap-4">
      {winner && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-accent-success/10 border border-accent-success/20">
          <Trophy className="w-4 h-4 text-accent-success shrink-0" />
          <p className="text-xs text-text-primary">
            <span className="font-semibold">Variant {winner.variant}</span>
            {' '}leads with {(winner.reply_rate * 100).toFixed(1)}% reply rate
          </p>
        </div>
      )}

      <div className="flex-1 min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 8, right: 8, left: -16, bottom: 0 }}
            barGap={4}
          >
            <CartesianGrid stroke="#1e1e2e" vertical={false} />
            <XAxis
              dataKey="variant"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={{ stroke: '#2a2a3a' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
              domain={[0, 'auto']}
            />
            <Tooltip content={<AbTooltip />} cursor={{ fill: 'rgba(99,102,241,0.06)' }} />
            <Legend
              wrapperStyle={{ fontSize: 11, color: '#94a3b8' }}
              iconType="circle"
            />
            <Bar
              dataKey="open_rate"
              name="Open rate"
              fill={OPEN_COLOR}
              radius={[4, 4, 0, 0]}
              isAnimationActive
              maxBarSize={40}
            />
            <Bar
              dataKey="reply_rate"
              name="Reply rate"
              fill={REPLY_COLOR}
              radius={[4, 4, 0, 0]}
              isAnimationActive
              maxBarSize={40}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <VariantTable variants={data.variants} winnerId={winner?.variant ?? null} />
    </div>
  );
}

function VariantTable({
  variants,
  winnerId,
}: {
  variants: AbTestVariant[];
  winnerId: string | null;
}): JSX.Element {
  return (
    <div className="overflow-hidden rounded-md border border-border-subtle">
      <table className="w-full text-xs">
        <thead>
          <tr className="bg-surface-elevated text-text-muted">
            <th className="text-left px-3 py-2 font-medium">Variant</th>
            <th className="text-right px-3 py-2 font-medium">Sent</th>
            <th className="text-right px-3 py-2 font-medium">Open</th>
            <th className="text-right px-3 py-2 font-medium">Reply</th>
          </tr>
        </thead>
        <tbody>
          {variants.map((v, i) => {
            const isWinner = v.variant === winnerId;
            return (
              <motion.tr
                key={v.variant}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.06 }}
                className="border-t border-border-subtle hover:bg-surface-hover"
              >
                <td className="px-3 py-2 font-medium text-text-primary">
                  {v.variant}
                  {isWinner && (
                    <span className="ml-1.5 text-accent-success" title="Winning variant">
                      <TrendingUp className="w-3 h-3 inline" />
                    </span>
                  )}
                </td>
                <td className="px-3 py-2 text-right font-mono text-text-secondary">
                  {v.sent}
                </td>
                <td className="px-3 py-2 text-right font-mono" style={{ color: OPEN_COLOR }}>
                  {(v.open_rate * 100).toFixed(1)}%
                </td>
                <td className="px-3 py-2 text-right font-mono" style={{ color: REPLY_COLOR }}>
                  {(v.reply_rate * 100).toFixed(1)}%
                </td>
              </motion.tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function EmptyAb(): JSX.Element {
  return (
    <div className="h-full min-h-[220px] flex flex-col items-center justify-center text-center gap-2">
      <AbIcon />
      <p className="text-sm text-text-muted">No A/B tests yet</p>
      <p className="text-xs text-text-muted max-w-[240px]">
        Enable A/B testing on email templates to compare open and reply rates across variants.
      </p>
    </div>
  );
}

function AbIcon(): JSX.Element {
  const Icon: LucideIcon = TrendingUp;
  return (
    <div className="w-10 h-10 rounded-lg bg-surface-elevated border border-border-subtle flex items-center justify-center">
      <Icon className="w-5 h-5 text-text-muted" />
    </div>
  );
}
