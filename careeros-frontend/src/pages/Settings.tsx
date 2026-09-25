import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Settings as SettingsIcon,
  Mail,
  Key,
  SlidersHorizontal,
  LayoutTemplate,
  Globe,
  Save,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Sparkles,
  TrendingUp,
  Trophy,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { settingsApi } from "@/api/client";
import type {
  SmtpConfig,
  ApiKeys,
  OutreachLimits,
  PortalToggle,
} from "@/types";

// ── Types ───────────────────────────────────────────────────────────────────

type TabId = "smtp" | "api-keys" | "outreach" | "templates" | "portals";

interface TabDef {
  readonly id: TabId;
  readonly label: string;
  readonly icon: LucideIcon;
  readonly description: string;
}

// ── Constants ───────────────────────────────────────────────────────────────

const TABS: readonly TabDef[] = [
  {
    id: "smtp",
    label: "SMTP",
    icon: Mail,
    description: "Email server configuration",
  },
  {
    id: "api-keys",
    label: "API Keys",
    icon: Key,
    description: "Third-party service credentials",
  },
  {
    id: "outreach",
    label: "Outreach Limits",
    icon: SlidersHorizontal,
    description: "Sending rate controls",
  },
  {
    id: "templates",
    label: "A/B Tests",
    icon: LayoutTemplate,
    description: "Template performance",
  },
  {
    id: "portals",
    label: "Portals",
    icon: Globe,
    description: "Job board integrations",
  },
];

const PORTAL_CATEGORY_META: Record<
  PortalToggle["category"],
  { label: string; color: string }
> = {
  remote: { label: "Remote", color: "bg-emerald-500/20 text-emerald-400" },
  local: { label: "Local", color: "bg-blue-500/20 text-blue-400" },
  aggregator: { label: "Aggregator", color: "bg-violet-500/20 text-violet-400" },
};

// ── Animation variants ──────────────────────────────────────────────────────

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0 },
};

// ── Reusable UI atoms ───────────────────────────────────────────────────────

function SectionCard({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}): JSX.Element {
  return (
    <div
      className={`rounded-xl border border-border bg-surface p-6 ${className}`}
    >
      {children}
    </div>
  );
}

function FieldLabel({
  htmlFor,
  children,
  hint,
}: {
  htmlFor: string;
  children: React.ReactNode;
  hint?: string;
}): JSX.Element {
  return (
    <label htmlFor={htmlFor} className="block">
      <span className="text-sm font-medium text-text-primary">{children}</span>
      {hint && <span className="ml-2 text-xs text-text-muted">{hint}</span>}
    </label>
  );
}

function TextInput({
  id,
  value,
  onChange,
  type = "text",
  placeholder,
  disabled = false,
}: {
  id: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
  disabled?: boolean;
}): JSX.Element {
  return (
    <input
      id={id}
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      disabled={disabled}
      className="mt-1.5 w-full rounded-lg border border-border bg-bg-tertiary px-3 py-2 text-sm text-text-primary placeholder:text-text-muted transition-colors focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary disabled:opacity-50"
    />
  );
}

function NumberInput({
  id,
  value,
  onChange,
  min,
  max,
  disabled = false,
}: {
  id: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  disabled?: boolean;
}): JSX.Element {
  return (
    <input
      id={id}
      type="number"
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      min={min}
      max={max}
      disabled={disabled}
      className="mt-1.5 w-full rounded-lg border border-border bg-bg-tertiary px-3 py-2 text-sm text-text-primary transition-colors focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary disabled:opacity-50"
    />
  );
}

function Toggle({
  checked,
  onChange,
  disabled = false,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  disabled?: boolean;
}): JSX.Element {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2 focus:ring-offset-bg-primary disabled:cursor-not-allowed disabled:opacity-50 ${
        checked ? "bg-accent-primary" : "bg-bg-tertiary"
      }`}
    >
      <span
        aria-hidden="true"
        className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
          checked ? "translate-x-5" : "translate-x-0"
        }`}
      />
    </button>
  );
}

function SaveButton({
  onClick,
  isLoading,
  disabled,
  children,
}: {
  onClick: () => void;
  isLoading: boolean;
  disabled?: boolean;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      disabled={disabled || isLoading}
      whileHover={{ scale: disabled || isLoading ? 1 : 1.01 }}
      whileTap={{ scale: disabled || isLoading ? 1 : 0.98 }}
      className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-accent-primary to-accent-secondary px-4 py-2 text-sm font-medium text-white shadow-glow transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Save className="h-4 w-4" />
      )}
      {children}
    </motion.button>
  );
}

function StatusBanner({
  type,
  message,
}: {
  type: "success" | "error";
  message: string;
}): JSX.Element {
  const Icon = type === "success" ? CheckCircle2 : AlertCircle;
  const colorClasses =
    type === "success"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
      : "border-red-500/30 bg-red-500/10 text-red-400";

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className={`flex items-center gap-2 rounded-lg border px-4 py-3 text-sm ${colorClasses}`}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span>{message}</span>
    </motion.div>
  );
}

// ── SMTP Section ────────────────────────────────────────────────────────────

function SmtpSection(): JSX.Element {
  const queryClient = useQueryClient();
  const { data: initialConfig, isLoading } = useQuery({
    queryKey: ["settings", "smtp"],
    queryFn: settingsApi.getSmtp,
  });

  const [form, setForm] = useState<SmtpConfig>(
    initialConfig ?? {
      host: "",
      port: 587,
      username: "",
      password: "",
      use_tls: true,
      from_name: "",
      from_email: "",
      reply_to: null,
    },
  );
  const [showPassword, setShowPassword] = useState(false);

  // Sync form when data loads
  if (initialConfig && form.host === "" && initialConfig.host !== "") {
    setForm(initialConfig);
  }

  const mutation = useMutation({
    mutationFn: settingsApi.updateSmtp,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings", "smtp"] });
    },
  });

  const testMutation = useMutation({
    mutationFn: settingsApi.testSmtp,
  });

  const updateField = <K extends keyof SmtpConfig>(
    field: K,
    value: SmtpConfig[K],
  ) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = () => mutation.mutate(form);
  const handleTest = () => testMutation.mutate();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-accent-primary" />
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <AnimatePresence>
        {mutation.isSuccess && (
          <StatusBanner
            type="success"
            message="SMTP configuration saved successfully."
          />
        )}
        {mutation.isError && (
          <StatusBanner
            type="error"
            message="Failed to save SMTP configuration."
          />
        )}
        {testMutation.data && (
          <StatusBanner
            type={testMutation.data.success ? "success" : "error"}
            message={testMutation.data.message}
          />
        )}
      </AnimatePresence>

      <SectionCard>
        <h3 className="mb-4 text-lg font-semibold text-text-primary">
          Server Configuration
        </h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <motion.div variants={itemVariants}>
            <FieldLabel htmlFor="smtp-host">SMTP Host</FieldLabel>
            <TextInput
              id="smtp-host"
              value={form.host}
              onChange={(v) => updateField("host", v)}
              placeholder="smtp.gmail.com"
            />
          </motion.div>
          <motion.div variants={itemVariants}>
            <FieldLabel htmlFor="smtp-port">Port</FieldLabel>
            <NumberInput
              id="smtp-port"
              value={form.port}
              onChange={(v) => updateField("port", v)}
              min={1}
              max={65535}
            />
          </motion.div>
          <motion.div variants={itemVariants} className="sm:col-span-2">
            <FieldLabel htmlFor="smtp-tls" hint="Recommended for security">
              TLS Encryption
            </FieldLabel>
            <div className="mt-2 flex items-center gap-3">
              <Toggle
                checked={form.use_tls}
                onChange={(v) => updateField("use_tls", v)}
              />
              <span className="text-sm text-text-secondary">
                {form.use_tls ? "Enabled" : "Disabled"}
              </span>
            </div>
          </motion.div>
        </div>
      </SectionCard>

      <SectionCard>
        <h3 className="mb-4 text-lg font-semibold text-text-primary">
          Authentication
        </h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <motion.div variants={itemVariants}>
            <FieldLabel htmlFor="smtp-username">Username</FieldLabel>
            <TextInput
              id="smtp-username"
              value={form.username}
              onChange={(v) => updateField("username", v)}
              placeholder="you@example.com"
            />
          </motion.div>
          <motion.div variants={itemVariants}>
            <FieldLabel htmlFor="smtp-password">Password</FieldLabel>
            <div className="relative mt-1.5">
              <input
                id="smtp-password"
                type={showPassword ? "text" : "password"}
                value={form.password}
                onChange={(e) => updateField("password", e.target.value)}
                placeholder="App-specific password"
                className="w-full rounded-lg border border-border bg-bg-tertiary px-3 py-2 pr-10 text-sm text-text-primary placeholder:text-text-muted transition-colors focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
              />
              <button
                type="button"
                onClick={() => setShowPassword((p) => !p)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-text-muted hover:text-text-secondary"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </motion.div>
        </div>
      </SectionCard>

      <SectionCard>
        <h3 className="mb-4 text-lg font-semibold text-text-primary">
          Sender Identity
        </h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <motion.div variants={itemVariants}>
            <FieldLabel htmlFor="smtp-from-name">From Name</FieldLabel>
            <TextInput
              id="smtp-from-name"
              value={form.from_name}
              onChange={(v) => updateField("from_name", v)}
              placeholder="Your Name"
            />
          </motion.div>
          <motion.div variants={itemVariants}>
            <FieldLabel htmlFor="smtp-from-email">From Email</FieldLabel>
            <TextInput
              id="smtp-from-email"
              value={form.from_email}
              onChange={(v) => updateField("from_email", v)}
              placeholder="you@example.com"
            />
          </motion.div>
          <motion.div variants={itemVariants} className="sm:col-span-2">
            <FieldLabel htmlFor="smtp-reply-to" hint="Optional">
              Reply-To
            </FieldLabel>
            <TextInput
              id="smtp-reply-to"
              value={form.reply_to ?? ""}
              onChange={(v) => updateField("reply_to", v || null)}
              placeholder="replies@example.com"
            />
          </motion.div>
        </div>
      </SectionCard>

      <div className="flex items-center justify-end gap-3">
        <motion.button
          type="button"
          onClick={handleTest}
          disabled={testMutation.isPending}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:border-accent-primary hover:text-accent-primary disabled:opacity-50"
        >
          {testMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Mail className="h-4 w-4" />
          )}
          Test Connection
        </motion.button>
        <SaveButton
          onClick={handleSave}
          isLoading={mutation.isPending}
          disabled={!form.host || !form.username}
        >
          Save SMTP Settings
        </SaveButton>
      </div>
    </motion.div>
  );
}

// ── API Keys Section ────────────────────────────────────────────────────────

function ApiKeysSection(): JSX.Element {
  const queryClient = useQueryClient();
  const { data: initialKeys, isLoading } = useQuery({
    queryKey: ["settings", "api-keys"],
    queryFn: settingsApi.getApiKeys,
  });

  const [form, setForm] = useState<ApiKeys>(
    initialKeys ?? { hunter: "", apollo: "", serper: "" },
  );
  const [visibleKeys, setVisibleKeys] = useState<Record<string, boolean>>({});

  if (initialKeys && form.hunter === "" && initialKeys.hunter !== "") {
    setForm(initialKeys);
  }

  const mutation = useMutation({
    mutationFn: settingsApi.updateApiKeys,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings", "api-keys"] });
    },
  });

  const updateField = <K extends keyof ApiKeys>(field: K, value: ApiKeys[K]) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const maskKey = (key: string): string =>
    key.length > 8 ? `${key.slice(0, 4)}${"*".repeat(12)}${key.slice(-4)}` : "••••••••";

  const keyFields: readonly {
    key: keyof ApiKeys;
    label: string;
    placeholder: string;
    description: string;
  }[] = [
    {
      key: "hunter",
      label: "Hunter.io",
      placeholder: "hunter_api_key_...",
      description: "Email verification & finder",
    },
    {
      key: "apollo",
      label: "Apollo.io",
      placeholder: "apollo_api_key_...",
      description: "Contact & company data",
    },
    {
      key: "serper",
      label: "Serper.dev",
      placeholder: "serper_api_key_...",
      description: "Search API for recruiter lookup",
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-accent-primary" />
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <AnimatePresence>
        {mutation.isSuccess && (
          <StatusBanner type="success" message="API keys saved successfully." />
        )}
        {mutation.isError && (
          <StatusBanner type="error" message="Failed to save API keys." />
        )}
      </AnimatePresence>

      <SectionCard>
        <div className="mb-4 flex items-start gap-3">
          <div className="rounded-lg bg-accent-primary/10 p-2">
            <Key className="h-5 w-5 text-accent-primary" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">
              Third-Party API Keys
            </h3>
            <p className="mt-1 text-sm text-text-secondary">
              Stored locally and encrypted. Keys are never sent to any server
              except their respective providers.
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {keyFields.map((field) => (
            <motion.div
              key={field.key}
              variants={itemVariants}
              className="rounded-lg border border-border bg-bg-tertiary/50 p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-medium text-text-primary">
                    {field.label}
                  </span>
                  <span className="ml-2 text-xs text-text-muted">
                    {field.description}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    setVisibleKeys((prev) => ({
                      ...prev,
                      [field.key]: !prev[field.key],
                    }))
                  }
                  className="text-text-muted hover:text-text-secondary"
                  aria-label={
                    visibleKeys[field.key] ? "Hide key" : "Show key"
                  }
                >
                  {visibleKeys[field.key] ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              <div className="mt-2">
                <input
                  type={visibleKeys[field.key] ? "text" : "password"}
                  value={form[field.key]}
                  onChange={(e) => updateField(field.key, e.target.value)}
                  placeholder={field.placeholder}
                  className="w-full rounded-lg border border-border bg-bg-primary px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-muted/50 transition-colors focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
                />
              </div>
              {form[field.key] && !visibleKeys[field.key] && (
                <p className="mt-1.5 text-xs font-mono text-text-muted">
                  {maskKey(form[field.key])}
                </p>
              )}
            </motion.div>
          ))}
        </div>
      </SectionCard>

      <div className="flex justify-end">
        <SaveButton
          onClick={() => mutation.mutate(form)}
          isLoading={mutation.isPending}
        >
          Save API Keys
        </SaveButton>
      </div>
    </motion.div>
  );
}

// ── Outreach Limits Section ─────────────────────────────────────────────────

function OutreachLimitsSection(): JSX.Element {
  const queryClient = useQueryClient();
  const { data: initialLimits, isLoading } = useQuery({
    queryKey: ["settings", "outreach-limits"],
    queryFn: settingsApi.getOutreachLimits,
  });

  const [form, setForm] = useState<OutreachLimits>(
    initialLimits ?? {
      daily_max: 50,
      hourly_max: 10,
      delay_seconds: 30,
      max_per_company: 2,
      cooldown_hours: 72,
    },
  );

  if (
    initialLimits &&
    form.daily_max === 50 &&
    initialLimits.daily_max !== 50
  ) {
    setForm(initialLimits);
  }

  const mutation = useMutation({
    mutationFn: settingsApi.updateOutreachLimits,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings", "outreach-limits"] });
    },
  });

  const updateField = <K extends keyof OutreachLimits>(
    field: K,
    value: OutreachLimits[K],
  ) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const limitFields: readonly {
    key: keyof OutreachLimits;
    label: string;
    hint: string;
    min: number;
    max: number;
    unit: string;
  }[] = [
    {
      key: "daily_max",
      label: "Daily Maximum",
      hint: "Emails per day",
      min: 1,
      max: 500,
      unit: "emails",
    },
    {
      key: "hourly_max",
      label: "Hourly Maximum",
      hint: "Emails per hour",
      min: 1,
      max: 100,
      unit: "emails",
    },
    {
      key: "delay_seconds",
      label: "Delay Between Emails",
      hint: "Minimum gap",
      min: 5,
      max: 300,
      unit: "seconds",
    },
    {
      key: "max_per_company",
      label: "Max Per Company",
      hint: "Same company limit",
      min: 1,
      max: 10,
      unit: "emails",
    },
    {
      key: "cooldown_hours",
      label: "Company Cooldown",
      hint: "Before re-contacting",
      min: 1,
      max: 720,
      unit: "hours",
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-accent-primary" />
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <AnimatePresence>
        {mutation.isSuccess && (
          <StatusBanner
            type="success"
            message="Outreach limits saved successfully."
          />
        )}
        {mutation.isError && (
          <StatusBanner type="error" message="Failed to save limits." />
        )}
      </AnimatePresence>

      <SectionCard>
        <div className="mb-4 flex items-start gap-3">
          <div className="rounded-lg bg-accent-secondary/10 p-2">
            <SlidersHorizontal className="h-5 w-5 text-accent-secondary" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">
              Rate Limiting
            </h3>
            <p className="mt-1 text-sm text-text-secondary">
              Protect your sender reputation and avoid being flagged as spam.
            </p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {limitFields.map((field) => (
            <motion.div key={field.key} variants={itemVariants}>
              <FieldLabel htmlFor={`limit-${field.key}`} hint={field.hint}>
                {field.label}
              </FieldLabel>
              <div className="relative mt-1.5">
                <NumberInput
                  id={`limit-${field.key}`}
                  value={form[field.key]}
                  onChange={(v) => updateField(field.key, v)}
                  min={field.min}
                  max={field.max}
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-text-muted">
                  {field.unit}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </SectionCard>

      <SectionCard className="border-accent-warning/30 bg-accent-warning/5">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 shrink-0 text-accent-warning" />
          <div>
            <h4 className="text-sm font-medium text-text-primary">
              Best Practices
            </h4>
            <ul className="mt-2 space-y-1 text-sm text-text-secondary">
              <li>
                • Keep daily volume under 100 for new domains (warm up gradually)
              </li>
              <li>• Use 30+ second delays between emails for natural cadence</li>
              <li>• Limit to 2 contacts per company to avoid annoyance</li>
              <li>• Respect 72h+ cooldowns before re-engaging</li>
            </ul>
          </div>
        </div>
      </SectionCard>

      <div className="flex justify-end">
        <SaveButton
          onClick={() => mutation.mutate(form)}
          isLoading={mutation.isPending}
        >
          Save Limits
        </SaveButton>
      </div>
    </motion.div>
  );
}

// ── A/B Templates Section ───────────────────────────────────────────────────

function TemplatesSection(): JSX.Element {
  const { data: performance, isLoading } = useQuery({
    queryKey: ["settings", "ab-tests"],
    queryFn: settingsApi.getAbTestPerformance,
  });

  const chartData = performance
    ? performance.map((p) => ({
        name: `${p.template_name} (${p.variant})`,
        opens: p.open_rate * 100,
        replies: p.reply_rate * 100,
        sent: p.sent_count,
        isWinner: p.is_winner,
      }))
    : [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-accent-primary" />
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <SectionCard>
        <div className="mb-4 flex items-start gap-3">
          <div className="rounded-lg bg-accent-success/10 p-2">
            <TrendingUp className="h-5 w-5 text-accent-success" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">
              Template Performance
            </h3>
            <p className="mt-1 text-sm text-text-secondary">
              A/B test results across your email templates. Winners are
              highlighted.
            </p>
          </div>
        </div>

        {chartData.length > 0 ? (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 8, right: 8, bottom: 8, left: 0 }}
              >
                <XAxis
                  dataKey="name"
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  axisLine={{ stroke: "#2a2a3a" }}
                  tickLine={false}
                  interval={0}
                  angle={-20}
                  textAnchor="end"
                  height={50}
                />
                <YAxis
                  tick={{ fill: "#94a3b8", fontSize: 11 }}
                  axisLine={{ stroke: "#2a2a3a" }}
                  tickLine={false}
                  unit="%"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1a1a26",
                    border: "1px solid #2a2a3a",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                  labelStyle={{ color: "#f1f5f9" }}
                  itemStyle={{ color: "#94a3b8" }}
                  formatter={(value) => [`${Number(value).toFixed(1)}%`]}
                />
                <Bar
                  dataKey="opens"
                  name="Open Rate"
                  radius={[4, 4, 0, 0]}
                  fill="#8b5cf6"
                />
                <Bar
                  dataKey="replies"
                  name="Reply Rate"
                  radius={[4, 4, 0, 0]}
                  fill="#10b981"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <LayoutTemplate className="h-12 w-12 text-text-muted" />
            <p className="mt-3 text-sm text-text-secondary">
              No A/B test data yet. Run campaigns to see performance metrics.
            </p>
          </div>
        )}
      </SectionCard>

      {performance && performance.length > 0 && (
        <SectionCard>
          <h3 className="mb-4 text-lg font-semibold text-text-primary">
            Detailed Breakdown
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border text-text-muted">
                  <th className="pb-3 pr-4 font-medium">Template</th>
                  <th className="pb-3 pr-4 font-medium">Variant</th>
                  <th className="pb-3 pr-4 font-medium text-right">Sent</th>
                  <th className="pb-3 pr-4 font-medium text-right">
                    Open Rate
                  </th>
                  <th className="pb-3 pr-4 font-medium text-right">
                    Reply Rate
                  </th>
                  <th className="pb-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {performance.map((p) => (
                  <tr
                    key={`${p.template_id}-${p.variant}`}
                    className="border-b border-border/50 last:border-0"
                  >
                    <td className="py-3 pr-4 text-text-primary">
                      {p.template_name}
                    </td>
                    <td className="py-3 pr-4">
                      <span className="rounded bg-bg-tertiary px-2 py-0.5 text-xs font-medium text-text-secondary">
                        {p.variant}
                      </span>
                    </td>
                    <td className="py-3 pr-4 text-right text-text-secondary">
                      {p.sent_count}
                    </td>
                    <td className="py-3 pr-4 text-right text-text-secondary">
                      {(p.open_rate * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 pr-4 text-right text-text-secondary">
                      {(p.reply_rate * 100).toFixed(1)}%
                    </td>
                    <td className="py-3">
                      {p.is_winner ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-accent-success/10 px-2 py-0.5 text-xs font-medium text-accent-success">
                          <Trophy className="h-3 w-3" />
                          Winner
                        </span>
                      ) : (
                        <span className="text-xs text-text-muted">
                          Testing
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      )}
    </motion.div>
  );
}

// ── Portals Section ─────────────────────────────────────────────────────────

function PortalsSection(): JSX.Element {
  const queryClient = useQueryClient();
  const { data: portals, isLoading } = useQuery({
    queryKey: ["settings", "portals"],
    queryFn: settingsApi.getPortals,
  });

  const mutation = useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      settingsApi.updatePortal(id, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings", "portals"] });
    },
  });

  const togglePortal = (id: string, currentEnabled: boolean) => {
    mutation.mutate({ id, enabled: !currentEnabled });
  };

  const grouped = portals
    ? portals.reduce<Record<PortalToggle["category"], PortalToggle[]>>(
        (acc, portal) => {
          acc[portal.category].push(portal);
          return acc;
        },
        { remote: [], local: [], aggregator: [] },
      )
    : null;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-accent-primary" />
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <AnimatePresence>
        {mutation.isSuccess && (
          <StatusBanner type="success" message="Portal settings updated." />
        )}
        {mutation.isError && (
          <StatusBanner type="error" message="Failed to update portal." />
        )}
      </AnimatePresence>

      <SectionCard>
        <div className="mb-4 flex items-start gap-3">
          <div className="rounded-lg bg-accent-primary/10 p-2">
            <Globe className="h-5 w-5 text-accent-primary" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">
              Job Portal Integrations
            </h3>
            <p className="mt-1 text-sm text-text-secondary">
              Enable or disable job boards for search and auto-apply features.
            </p>
          </div>
        </div>

        {grouped && (
          <div className="space-y-6">
            {(
              ["remote", "local", "aggregator"] as const
            ).map((category) => (
              <motion.div key={category} variants={itemVariants}>
                <div className="mb-3 flex items-center gap-2">
                  <span
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${PORTAL_CATEGORY_META[category].color}`}
                  >
                    {PORTAL_CATEGORY_META[category].label}
                  </span>
                  <span className="text-xs text-text-muted">
                    {grouped[category].length} portals
                  </span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {grouped[category].map((portal) => (
                    <PortalCard
                      key={portal.id}
                      portal={portal}
                      onToggle={() =>
                        togglePortal(portal.id, portal.enabled)
                      }
                      isPending={mutation.isPending}
                    />
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </SectionCard>
    </motion.div>
  );
}

function PortalCard({
  portal,
  onToggle,
  isPending,
}: {
  portal: PortalToggle;
  onToggle: () => void;
  isPending: boolean;
}): JSX.Element {
  return (
    <motion.div
      layout
      className={`rounded-lg border p-4 transition-colors ${
        portal.enabled
          ? "border-accent-primary/30 bg-accent-primary/5"
          : "border-border bg-bg-tertiary/30"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h4 className="truncate text-sm font-medium text-text-primary">
            {portal.name}
          </h4>
          <p className="mt-0.5 line-clamp-2 text-xs text-text-muted">
            {portal.description}
          </p>
        </div>
        <Toggle
          checked={portal.enabled}
          onChange={onToggle}
          disabled={isPending}
        />
      </div>
      <div className="mt-3 flex items-center gap-2">
        <span
          className={`h-2 w-2 rounded-full ${
            portal.enabled ? "bg-accent-success" : "bg-text-muted"
          }`}
        />
        <span className="text-xs text-text-muted">
          {portal.enabled ? "Active" : "Inactive"}
        </span>
      </div>
    </motion.div>
  );
}

// ── Main Settings Page ──────────────────────────────────────────────────────

export default function Settings() {
  const [activeTab, setActiveTab] = useState<TabId>("smtp");

  const activeTabDef = TABS.find((t) => t.id === activeTab) ?? TABS[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-3"
      >
        <div className="rounded-xl bg-gradient-to-br from-accent-primary to-accent-secondary p-2.5 shadow-glow">
          <SettingsIcon className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Settings</h1>
          <p className="text-sm text-text-secondary">
            Configure integrations, limits, and templates
          </p>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-border pb-4">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <motion.button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-accent-primary/10 text-accent-primary shadow-glow"
                  : "text-text-secondary hover:bg-surface hover:text-text-primary"
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </motion.button>
          );
        })}
      </div>

      {/* Active tab description */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center gap-2 text-sm text-text-muted"
      >
        <Sparkles className="h-4 w-4" />
        <span>{activeTabDef.description}</span>
      </motion.div>

      {/* Tab content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === "smtp" && <SmtpSection />}
          {activeTab === "api-keys" && <ApiKeysSection />}
          {activeTab === "outreach" && <OutreachLimitsSection />}
          {activeTab === "templates" && <TemplatesSection />}
          {activeTab === "portals" && <PortalsSection />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
