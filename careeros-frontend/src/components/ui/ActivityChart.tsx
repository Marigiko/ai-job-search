import { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { motion } from 'framer-motion';
import type { ActivityPoint } from '@/api/client';

interface ActivityChartProps {
  data: ActivityPoint[];
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number; dataKey: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-lg border border-border bg-bg-secondary px-3 py-2 shadow-lg">
      <p className="text-xs font-medium text-text-secondary">{label}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey} className="text-sm text-text-primary">
          {entry.dataKey === 'applications' ? 'Applications' : 'Discoveries'}:{' '}
          <span className="font-semibold">{entry.value}</span>
        </p>
      ))}
    </div>
  );
}

export function ActivityChart({ data }: ActivityChartProps) {
  const formattedData = useMemo(
    () =>
      data.map((point) => ({
        ...point,
        label: new Date(point.date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        }),
      })),
    [data],
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.15 }}
      className="rounded-xl border border-border bg-bg-secondary p-5"
    >
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-text-primary">
            Recent Activity
          </h3>
          <p className="text-sm text-text-secondary">
            Last 14 days of applications and discoveries
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-indigo-500" />
            <span className="text-text-secondary">Applications</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-violet-500" />
            <span className="text-text-secondary">Discoveries</span>
          </span>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={formattedData}
            margin={{ top: 8, right: 8, left: -16, bottom: 0 }}
          >
            <defs>
              <linearGradient id="applicationsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6366f1" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="discoveriesGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.3} />
                <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#2a2a3a"
              vertical={false}
            />
            <XAxis
              dataKey="label"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: '#2a2a3a' }}
            />
            <YAxis
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
            />
            <Tooltip content={<ChartTooltip />} />
            <Area
              type="monotone"
              dataKey="applications"
              stroke="#6366f1"
              strokeWidth={2}
              fill="url(#applicationsGradient)"
              dot={false}
              activeDot={{ r: 4, fill: '#6366f1', stroke: '#0a0a0f', strokeWidth: 2 }}
            />
            <Area
              type="monotone"
              dataKey="discoveries"
              stroke="#8b5cf6"
              strokeWidth={2}
              fill="url(#discoveriesGradient)"
              dot={false}
              activeDot={{ r: 4, fill: '#8b5cf6', stroke: '#0a0a0f', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
