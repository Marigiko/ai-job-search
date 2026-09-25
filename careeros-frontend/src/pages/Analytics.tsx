import { useQuery } from '@tanstack/react-query';
import { motion, type Variants } from 'framer-motion';
import { BarChart3, RefreshCw } from 'lucide-react';
import { analyticsApi } from '@/api/client';
import { queryKeys } from '@/api/query-keys';
import { ChartCard } from '@/components/analytics/ChartCard';
import { FunnelChart } from '@/components/analytics/FunnelChart';
import { OutreachPieChart } from '@/components/analytics/OutreachPieChart';
import { SalaryHistogram } from '@/components/analytics/SalaryHistogram';
import { AbTestResults } from '@/components/analytics/AbTestResults';

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' } },
};

export default function Analytics(): JSX.Element {
  const funnelQuery = useQuery({
    queryKey: queryKeys.analytics.funnel(),
    queryFn: () => analyticsApi.funnel(),
  });

  const outreachQuery = useQuery({
    queryKey: queryKeys.analytics.outreach(),
    queryFn: () => analyticsApi.outreach(),
  });

  const abTestQuery = useQuery({
    queryKey: queryKeys.analytics.abTest(),
    queryFn: () => analyticsApi.abTest(),
  });

  const salaryQuery = useQuery({
    queryKey: queryKeys.analytics.salary(),
    queryFn: () => analyticsApi.salary(),
  });

  const isLoading =
    funnelQuery.isLoading ||
    outreachQuery.isLoading ||
    abTestQuery.isLoading ||
    salaryQuery.isLoading;

  const refetchAll = (): void => {
    void funnelQuery.refetch();
    void outreachQuery.refetch();
    void abTestQuery.refetch();
    void salaryQuery.refetch();
  };

  return (
    <div className="space-y-6">
      <PageHeader loading={isLoading} onRefresh={refetchAll} />

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 xl:grid-cols-2 gap-5"
      >
        <motion.div variants={itemVariants} className="xl:col-span-2">
          <ChartCard
            title="Application Funnel"
            subtitle="Volume and conversion across pipeline stages"
            isLoading={funnelQuery.isLoading}
          >
            {funnelQuery.data && <FunnelChart data={funnelQuery.data} />}
          </ChartCard>
        </motion.div>

        <motion.div variants={itemVariants}>
          <ChartCard
            title="Outreach Performance"
            subtitle="Sent, opened, replied and bounce breakdown"
            isLoading={outreachQuery.isLoading}
          >
            {outreachQuery.data && <OutreachPieChart data={outreachQuery.data} />}
          </ChartCard>
        </motion.div>

        <motion.div variants={itemVariants}>
          <ChartCard
            title="A/B Test Results"
            subtitle="Variant open and reply rates"
            isLoading={abTestQuery.isLoading}
          >
            {abTestQuery.data && <AbTestResults data={abTestQuery.data} />}
          </ChartCard>
        </motion.div>

        <motion.div variants={itemVariants} className="xl:col-span-2">
          <ChartCard
            title="Salary Insights"
            subtitle="Compensation distribution across tracked postings"
            isLoading={salaryQuery.isLoading}
          >
            {salaryQuery.data && <SalaryHistogram data={salaryQuery.data} />}
          </ChartCard>
        </motion.div>
      </motion.div>
    </div>
  );
}

function PageHeader({
  loading,
  onRefresh,
}: {
  loading: boolean;
  onRefresh: () => void;
}): JSX.Element {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent-primary to-accent-secondary flex items-center justify-center shadow-glow">
          <BarChart3 className="w-4.5 h-4.5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-text-primary tracking-tight">
            Analytics
          </h1>
          <p className="text-xs text-text-muted">
            Conversion funnel, outreach metrics, and salary intelligence
          </p>
        </div>
      </div>

      <button
        type="button"
        onClick={onRefresh}
        disabled={loading}
        className="btn-ghost"
        aria-label="Refresh analytics data"
      >
        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        <span className="hidden sm:inline">Refresh</span>
      </button>
    </div>
  );
}
