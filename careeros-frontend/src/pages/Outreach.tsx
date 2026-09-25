import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Mail } from 'lucide-react';
import { EmailComposer, TemplateSelector, QueueManager, OutreachStats } from '@/components/outreach';
import type { EmailTemplate, OutreachEmailCreate } from '@/types';

const pageVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.05 },
  },
};

const sectionVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

export default function Outreach() {
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplate | null>(null);

  const handleTemplateSelect = useCallback((template: EmailTemplate) => {
    setSelectedTemplate(template);
  }, []);

  const handleQueue = useCallback((_payload: OutreachEmailCreate) => {
    setSelectedTemplate(null);
  }, []);

  const handleSend = useCallback((_payload: OutreachEmailCreate) => {
    setSelectedTemplate(null);
  }, []);

  return (
    <motion.div
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      className="h-full overflow-y-auto"
    >
      <div className="max-w-[1400px] mx-auto p-6 space-y-6">
        {/* Header */}
        <motion.header variants={sectionVariants} className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-accent-primary/10 border border-accent-primary/20">
            <Mail className="w-5 h-5 text-accent-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Outreach</h1>
            <p className="text-sm text-text-secondary">
              Compose emails, manage templates with A/B testing, and track performance.
            </p>
          </div>
        </motion.header>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Composer */}
          <motion.div variants={sectionVariants} className="lg:col-span-5 space-y-6">
            <EmailComposer
              key={selectedTemplate?.id ?? 'blank'}
              initialSubject={selectedTemplate?.subject_template ?? ''}
              initialBody={selectedTemplate?.body_template ?? ''}
              onQueue={handleQueue}
              onSend={handleSend}
            />
            <QueueManager />
          </motion.div>

          {/* Right Column: Templates + Stats */}
          <motion.div variants={sectionVariants} className="lg:col-span-7 space-y-6">
            <TemplateSelector
              onSelect={handleTemplateSelect}
              selectedId={selectedTemplate?.id ?? null}
            />
            <OutreachStats />
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
