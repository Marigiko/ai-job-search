import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
  Label,
  type TooltipProps,
} from 'recharts';
import type { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent';
import type { SalaryInsights, SalaryBucket } from '@/types/analytics';

const BAR_COLOR = '#8b5cf6';
const BAR_COLOR_HIGHLIGHT = '#6366f1';
const MEDIAN_COLOR = '#10b981';

interface SalaryHistogramProps {
  data: SalaryInsights;
}

interface HistogramDatum extends SalaryBucket {
  highlight: boolean;
}

function HistogramTooltip({
  active,
  payload,
}: TooltipProps<ValueType, NameType>): JSX.Element | null {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload as HistogramDatum;
  return (
    <div className="glass-card px-3 py-2 text-xs">
      <p className="font-semibold text-text-primary">{point.range_label}</p>
      <p className="text-text-secondary">{point.count} postings</p>
      <p className="text-text-muted font-mono">
        ${point.min_bound.toLocaleString()} – {point.max_bound === Infinity ? '∞' : `$${point.max_bound.toLocaleString()}`}
      </p>
    </div>
  );
}

export function SalaryHistogram({ data }: SalaryHistogramProps): JSX.Element {
  const { buckets, postings_with_salary, median_salary_min, currency } = data;

  const chartData: HistogramDatum[] = buckets.map((b) => ({
    ...b,
    highlight: median_salary_min !== null &&
      median_salary_min >= b.min_bound &&
      (b.max_bound === Infinity || median_salary_min < b.max_bound),
  }));

  if (postings_with_salary === 0) {
    return (
      <div className="h-full min-h-[200px] flex flex-col items-center justify-center text-center gap-2">
        <p className="text-sm text-text-muted">No salary data yet</p>
        <p className="text-xs text-text-muted max-w-[220px]">
          Salary insights appear once job postings with compensation are tracked.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full gap-3">
      <SalarySummary data={data} currency={currency} />

      <div className="flex-1 min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 12, right: 8, left: -16, bottom: 0 }}
            barCategoryGap="18%"
          >
            <XAxis
              dataKey="range_label"
              tick={{ fill: '#94a3b8', fontSize: 10 }}
              axisLine={{ stroke: '#2a2a3a' }}
              tickLine={false}
              interval={0}
              angle={-35}
              textAnchor="end"
              height={50}
            />
            <YAxis
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip
              content={<HistogramTooltip />}
              cursor={{ fill: 'rgba(139,92,246,0.08)' }}
            />
            {median_salary_min !== null && (
              <ReferenceLine
                x={chartData.find((d) => d.highlight)?.range_label}
                stroke={MEDIAN_COLOR}
                strokeDasharray="4 4"
                strokeWidth={1.5}
              >
                <Label
                  value={`median $${(median_salary_min / 1000).toFixed(0)}k`}
                  position="top"
                  fill={MEDIAN_COLOR}
                  fontSize={10}
                />
              </ReferenceLine>
            )}
            <Bar dataKey="count" radius={[6, 6, 0, 0]} isAnimationActive maxBarSize={54}>
              {chartData.map((entry) => (
                <Cell
                  key={entry.range_label}
                  fill={entry.highlight ? BAR_COLOR_HIGHLIGHT : BAR_COLOR}
                  fillOpacity={entry.count === 0 ? 0.25 : entry.highlight ? 0.95 : 0.75}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {data.by_remote_type.length > 0 && (
        <RemoteBreakdown categories={data.by_remote_type} currency={currency} />
      )}
    </div>
  );
}

function SalarySummary({
  data,
  currency,
}: {
  data: SalaryInsights;
  currency: string;
}): JSX.Element | null {
  if (data.postings_with_salary === 0) return null;

  return (
    <div className="grid grid-cols-2 gap-2 text-xs">
      <SummaryStat
        label="Postings"
        value={data.postings_with_salary.toString()}
      />
      <SummaryStat
        label="Median min"
        value={data.median_salary_min !== null ? `$${(data.median_salary_min / 1000).toFixed(0)}k` : '—'}
      />
      <SummaryStat
        label="Avg range"
        value={
          data.avg_salary_min !== null && data.avg_salary_max !== null
            ? `${(data.avg_salary_min / 1000).toFixed(0)}–${(data.avg_salary_max / 1000).toFixed(0)}k`
            : '—'
        }
      />
      <SummaryStat label="Currency" value={currency} />
    </div>
  );
}

function SummaryStat({ label, value }: { label: string; value: string }): JSX.Element {
  return (
    <div className="flex items-center justify-between px-2.5 py-1.5 rounded-md bg-surface-elevated border border-border-subtle">
      <span className="text-text-muted">{label}</span>
      <span className="font-mono font-semibold text-text-primary">{value}</span>
    </div>
  );
}

function RemoteBreakdown({
  categories,
  currency,
}: {
  categories: SalaryInsights['by_remote_type'];
  currency: string;
}): JSX.Element {
  const labelMap: Record<string, string> = {
    remote: 'Remote',
    hybrid: 'Hybrid',
    onsite: 'On-site',
  };

  return (
    <div className="space-y-1.5">
      <p className="text-[10px] uppercase tracking-wider text-text-muted">
        By work type ({currency})
      </p>
      <div className="flex flex-wrap gap-2">
        {categories.map((cat) => (
          <div
            key={cat.category}
            className="text-xs px-2 py-1 rounded-md bg-surface-elevated border border-border-subtle"
          >
            <span className="text-text-secondary">{labelMap[cat.category] ?? cat.category}</span>
            <span className="ml-1.5 font-mono text-text-primary">
              {cat.avg_max !== null ? `$${(cat.avg_max / 1000).toFixed(0)}k` : '—'}
            </span>
            <span className="ml-1 text-text-muted">({cat.sample_size})</span>
          </div>
        ))}
      </div>
    </div>
  );
}
