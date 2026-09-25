import { memo } from "react";
import { motion } from "framer-motion";
import { useDraggable } from "@dnd-kit/core";
import { type KanbanItem, STAGE_CONFIG } from "@/types/pipeline";

interface JobCardProps {
  item: KanbanItem;
}

const cardVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, scale: 0.95 },
  hover: { y: -2, scale: 1.01 },
  tap: { scale: 0.98 },
};

const JobCardInner = ({ item }: JobCardProps) => {
  const stageInfo = STAGE_CONFIG[item.status as keyof typeof STAGE_CONFIG];
  const accentColor = stageInfo?.color ?? "#64748b";

  return (
    <motion.div
      variants={cardVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      whileHover="hover"
      whileTap="tap"
      transition={{ type: "spring", stiffness: 350, damping: 25 }}
      className="glass-card p-4 cursor-grab active:cursor-grabbing glow-hover group"
      style={{ borderLeft: `3px solid ${accentColor}` }}
      role="article"
      aria-label={`${item.job_title} at ${item.company_name ?? "Unknown"}`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-text-primary leading-snug line-clamp-2">
          {item.job_title}
        </h3>
        {stageInfo && (
          <span
            className="shrink-0 text-xs px-2 py-0.5 rounded-full font-medium"
            style={{
              backgroundColor: `${accentColor}20`,
              color: accentColor,
            }}
          >
            {stageInfo.icon}
          </span>
        )}
      </div>

      {item.company_name && (
        <p className="mt-1.5 text-xs text-text-secondary truncate">
          {item.company_name}
        </p>
      )}

      <div className="mt-3 flex items-center justify-between">
        <span className="text-[10px] font-mono text-text-muted">
          #{item.job_id}
        </span>
        {item.applied_date && (
          <span className="text-[10px] text-text-muted">
            {new Date(item.applied_date).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            })}
          </span>
        )}
      </div>
    </motion.div>
  );
};

/**
 * KanbanItem wrapper that provides drag capability via @dnd-kit.
 * Must be rendered inside a DndContext.
 */
export const JobCard = ({ item }: JobCardProps) => {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({
      id: `job-${item.job_id}`,
      data: { type: "job", item },
    });

  const style: React.CSSProperties = {
    transform: transform
      ? `translate3d(${transform.x}px, ${transform.y}px, 0)`
      : undefined,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 50 : undefined,
    position: isDragging ? ("relative" as const) : undefined,
  };

  return (
    <div ref={setNodeRef} style={style} {...listeners} {...attributes}>
      <JobCardInner item={item} />
    </div>
  );
};

export const MemoizedJobCard = memo(JobCard);
