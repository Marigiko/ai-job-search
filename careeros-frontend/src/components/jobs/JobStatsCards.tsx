import { useMemo } from "react";
import { motion } from "framer-motion";
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
} from "recharts";
import { Briefcase, Globe, Plane, TrendingUp, Inbox } from "lucide-react";
import { STAGE_LABELS, STAGE_CONFIG, PIPELINE_STAGES } from "@/types/pipeline";
import type { JobPosting } from "@/types";

interface JobStatsCardsProps {
  jobs: JobPosting[];
}

const tooltipStyle = {
  contentStyle: {
    backgroundColor: "#1a1a26",
    border: "1px solid #2a2a3a",
    borderRadius: "8px",
    fontSize: "12px",
    color: "#f1f5f9",
  },
  itemStyle: { color: "#94a3b8" },
  labelStyle: { color: "#f1f5f9", fontWeight: 500, marginBottom: 4 },
};

export function JobStatsCards({ jobs }: JobStatsCardsProps) {
  const stats = useMemo(() => {
    const total = jobs.length;
    const remoteCount = jobs.filter((j) => j.remote_type === "remote").length;
    const visaCount = jobs.filter((j) => j.visa_sponsorship).length;
    const appliedCount = jobs.filter(
      (j) => !["discovered", "interested"].includes(j.status),
    ).length;

    // Status distribution for bar chart
    const statusData = PIPELINE_STAGES.map((stage) => ({
      stage: STAGE_LABELS[stage],
      count: jobs.filter((j) => j.status === stage).length,
      color: STAGE_CONFIG[stage].color,
    })).filter((d) => d.count > 0);

    // Remote type distribution for pie chart
    const remoteData = [
      {
        name: "Remote",
        value: jobs.filter((j) => j.remote_type === "remote").length,
        color: "#10b981",
      },
      {
        name: "Hybrid",
        value: jobs.filter((j) => j.remote_type === "hybrid").length,
        color: "#f59e0b",
      },
      {
        name: "On-site",
        value: jobs.filter((j) => j.remote_type === "onsite").length,
        color: "#64748b",
      },
      {
        name: "Unspecified",
        value: jobs.filter((j) => !j.remote_type).length,
        color: "#374151",
      },
    ].filter((d) => d.value > 0);

    return {
      total,
      remoteCount,
      visaCount,
      appliedCount,
      statusData,
      remoteData,
    };
  }, [jobs]);

  const statCards = [
    {
      label: "Total Jobs",
      value: stats.total,
      icon: Briefcase,
      color: "text-accent-primary",
      bg: "bg-accent-primary/10",
    },
    {
      label: "Remote",
      value: stats.remoteCount,
      icon: Globe,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
    },
    {
      label: "Visa Sponsorship",
      value: stats.visaCount,
      icon: Plane,
      color: "text-violet-400",
      bg: "bg-violet-500/10",
    },
    {
      label: "In Progress",
      value: stats.appliedCount,
      icon: TrendingUp,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
    },
  ];

  return (
    <div className="space-y-4">
      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {statCards.map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05, duration: 0.2 }}
            className="rounded-lg border border-border bg-surface p-4 hover:border-accent-primary/30 transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-text-muted font-medium uppercase tracking-wider">
                {card.label}
              </span>
              <div className={`p-1.5 rounded-md ${card.bg}`}>
                <card.icon className={`w-3.5 h-3.5 ${card.color}`} />
              </div>
            </div>
            <p className="text-2xl font-bold text-text-primary">{card.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Status distribution bar chart */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.2 }}
          className="rounded-lg border border-border bg-surface p-4"
        >
          <h3 className="text-sm font-medium text-text-primary mb-4 flex items-center gap-2">
            <Inbox className="w-4 h-4 text-text-muted" />
            By Status
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.statusData} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
                <XAxis
                  dataKey="stage"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  axisLine={{ stroke: "#2a2a3a" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip
                  {...tooltipStyle}
                  cursor={{ fill: "rgba(99, 102, 241, 0.08)" }}
                  content={<CustomTooltip />}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={40}>
                  {stats.statusData.map((entry) => (
                    <Cell key={entry.stage} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Remote distribution pie chart */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.2 }}
          className="rounded-lg border border-border bg-surface p-4"
        >
          <h3 className="text-sm font-medium text-text-primary mb-4 flex items-center gap-2">
            <Globe className="w-4 h-4 text-text-muted" />
            By Location Type
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.remoteData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={3}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {stats.remoteData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip {...tooltipStyle} content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          {/* Legend */}
          <div className="flex items-center justify-center gap-4 mt-2">
            {stats.remoteData.map((entry) => (
              <span
                key={entry.name}
                className="inline-flex items-center gap-1.5 text-xs text-text-secondary"
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                {entry.name} ({entry.value})
              </span>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}

interface TooltipPayloadEntry {
  name?: string;
  stage?: string;
  value?: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  const data = payload[0];
  const label = data?.stage ?? data?.name ?? "";
  const count = data?.value ?? 0;
  return (
    <div className="rounded-lg bg-surface-elevated border border-border px-3 py-2 shadow-lg">
      <p className="text-xs font-medium text-text-primary">{label}</p>
      <p className="text-xs text-text-muted">
        {count} job{count === 1 ? "" : "s"}
      </p>
    </div>
  );
}


