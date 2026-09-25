import { useQuery } from '@tanstack/react-query';
import { Briefcase, Send, TrendingUp, Clock } from 'lucide-react';
import { dashboardApi } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import { MetricCard } from '@/components/ui/MetricCard';
import { ActivityChart } from '@/components/ui/ActivityChart';
import { FollowUpsList } from '@/components/ui/FollowUpsList';

export default function Dashboard() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: queryKeys.dashboard.summary(),
    queryFn: dashboardApi.getSummary,
  });

  const { data: activity, isLoading: activityLoading } = useQuery({
    queryKey: queryKeys.dashboard.activity(14),
    queryFn: () => dashboardApi.getActivity(14),
  });

  const { data: followUps, isLoading: followUpsLoading } = useQuery({
    queryKey: queryKeys.dashboard.followUps(),
    queryFn: dashboardApi.getFollowUps,
  });

  const isLoading = summaryLoading || activityLoading || followUpsLoading;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary">
          Dashboard
        </h1>
        <p className="mt-1 text-sm text-text-secondary">
          Your job search at a glance
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Active Jobs"
          value={isLoading ? '—' : summary?.active_jobs ?? 0}
          icon={<Briefcase size={20} />}
          accent="indigo"
        />
        <MetricCard
          label="Applications This Week"
          value={isLoading ? '—' : summary?.applications_this_week ?? 0}
          icon={<Send size={20} />}
          accent="violet"
        />
        <MetricCard
          label="Response Rate"
          value={isLoading ? '—' : `${summary?.response_rate ?? 0}%`}
          icon={<TrendingUp size={20} />}
          accent="emerald"
        />
        <MetricCard
          label="Total Applications"
          value={isLoading ? '—' : summary?.total_applications ?? 0}
          icon={<Clock size={20} />}
          accent="amber"
        />
      </div>

      {/* Activity Chart */}
      {!activityLoading && activity && activity.length > 0 && (
        <ActivityChart data={activity} />
      )}

      {/* Follow-ups */}
      {!followUpsLoading && followUps && (
        <FollowUpsList items={followUps} />
      )}
    </div>
  );
}
