import { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { Mail, Eye, Reply, TrendingUp } from 'lucide-react';
import { analyticsApi } from '@/api/client';
import { useQuery } from '@tanstack/react-query';

interface MetricCardProps {
  readonly label: string;
  readonly value: string;
  readonly icon: React.ReactNode;
  readonly accent: string;
}

const cardVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.06, duration: 0.3 },
  }),
};

function MetricCard({ label, value, icon, accent }: MetricCardProps) {
  return (
    <motion.div
      custom={0}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      className="rounded-lg border border-border-subtle bg-surface p-4 glow-hover"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs text-text-muted uppercase tracking-wide">{label}</span>
        <div className={`p-2 rounded-md ${accent}`}>{icon}</div>
      </div>
      <p className="mt-3 text-2xl font-bold text-text-primary">{value}</p>
    </motion.div>
  );
}

const PIE_COLORS = ['#6366f1', '#8b5cf6', '#10b981', '#f59e0b'];

interface CustomTooltipProps {
  readonly active?: boolean;
  readonly payload?: readonly { name: string; value: number; color: string }[];
  readonly label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-border bg-bg-secondary/95 backdrop-blur-sm px-3 py-2 shadow-lg">
      {label && <p className="text-xs text-text-muted mb-1">{label}</p>}
      {payload.map((entry) => (
        <p key={entry.name} className="text-sm text-text-primary flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
          {entry.name}: <span className="font-mono font-medium">{entry.value}</span>
        </p>
      ))}
    </div>
  );
}

export function OutreachStats() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics-outreach'],
    queryFn: analyticsApi.outreach,
    staleTime: 30_000,
  });

  const pieData = useMemo(() => {
    if (!data) return [];
    return [
      { name: 'Opened', value: data.by_status.opened },
      { name: 'Replied', value: data.by_status.replied },
      { name: 'Unopened', value: Math.max(0, data.total_sent - data.by_status.opened) },
    ].filter((d) => d.value > 0);
  }, [data]);

  const barData = useMemo(() => {
    if (!data) return [];
    return [
      { name: 'Sent', count: data.by_status.sent, fill: '#6366f1' },
      { name: 'Opened', count: data.by_status.opened, fill: '#8b5cf6' },
      { name: 'Replied', count: data.by_status.replied, fill: '#10b981' },
    ];
  }, [data]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="glass-card p-6 space-y-5"
    >
      <h2 className="text-lg font-semibold text-text-primary flex items-center gap-2">
        <TrendingUp className="w-5 h-5 text-accent-success" />
        Performance
      </h2>

      {isLoading ? (
        <div className="flex items-center justify-center py-12 text-text-muted">
          <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.2, ease: 'linear' }}>
            <Mail className="w-5 h-5" />
          </motion.div>
        </div>
      ) : data ? (
        <>
          {/* Metric Cards */}
          <div className="grid grid-cols-3 gap-3">
            <MetricCard
              label="Sent"
              value={data.total_sent.toLocaleString()}
              icon={<Mail className="w-4 h-4 text-accent-primary" />}
              accent="bg-accent-primary/10"
            />
            <MetricCard
              label="Open Rate"
              value={`${Math.round(data.open_rate * 100)}%`}
              icon={<Eye className="w-4 h-4 text-accent-secondary" />}
              accent="bg-accent-secondary/10"
            />
            <MetricCard
              label="Reply Rate"
              value={`${Math.round(data.reply_rate * 100)}%`}
              icon={<Reply className="w-4 h-4 text-accent-success" />}
              accent="bg-accent-success/10"
            />
          </div>

          {/* Bar Chart */}
          <div className="space-y-2">
            <h3 className="text-xs text-text-muted uppercase tracking-wide">Volume</h3>
            <div className="h-[140px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#64748b', fontSize: 11 }}
                    axisLine={{ stroke: '#2a2a3a' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#64748b', fontSize: 11 }}
                    axisLine={{ stroke: '#2a2a3a' }}
                    tickLine={false}
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(99,102,241,0.08)' }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={48}>
                    {barData.map((entry) => (
                      <Cell key={entry.name} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Pie Chart */}
          {pieData.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs text-text-muted uppercase tracking-wide">Engagement Split</h3>
              <div className="flex items-center gap-4">
                <div className="h-[120px] w-[120px] shrink-0">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        innerRadius={32}
                        outerRadius={52}
                        paddingAngle={3}
                        dataKey="value"
                        stroke="none"
                      >
                        {pieData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <ul className="space-y-1.5 flex-1">
                  {pieData.map((entry, i) => (
                    <li key={entry.name} className="flex items-center gap-2 text-xs text-text-secondary">
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
                      />
                      {entry.name}
                      <span className="ml-auto font-mono text-text-primary">{entry.value}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </>
      ) : (
        <p className="text-sm text-text-muted text-center py-6">No analytics data yet.</p>
      )}
    </motion.div>
  );
}
