import { memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { MemoizedJobCard } from "./JobCard";
import {
  STAGE_CONFIG,
  type KanbanItem,
  type StageColumnId,
} from "@/types/pipeline";

interface StageColumnProps {
  stageId: StageColumnId;
  items: KanbanItem[];
  isDragActive: boolean;
}

const columnVariants = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
};

const StageColumnInner = ({ stageId, items, isDragActive }: StageColumnProps) => {
  const config = STAGE_CONFIG[stageId];
  const { setNodeRef, isOver } = useDroppable({ id: stageId });

  const isEmpty = items.length === 0;
  const isDropTarget = isOver && isDragActive;

  return (
    <motion.div
      variants={columnVariants}
      initial="initial"
      animate="animate"
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="flex flex-col min-w-[280px] max-w-[320px] w-full"
    >
      {/* Column header */}
      <div className="flex items-center justify-between px-3 py-2 mb-3">
        <div className="flex items-center gap-2">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: config.color }}
            aria-hidden
          />
          <h2 className="text-sm font-semibold text-text-primary tracking-wide uppercase">
            {config.label}
          </h2>
        </div>
        <span
          className="text-xs font-mono px-2 py-0.5 rounded-md"
          style={{
            backgroundColor: `${config.color}15`,
            color: config.color,
          }}
        >
          {items.length}
        </span>
      </div>

      {/* Drop zone */}
      <div
        ref={setNodeRef}
        className={`
          flex-1 p-2 rounded-lg transition-all duration-200 ease-out
          ${isDropTarget ? "bg-accent-primary/10 ring-2 ring-accent-primary/30" : ""}
          ${isEmpty && !isDropTarget ? "border-2 border-dashed border-border-subtle/40" : ""}
        `}
        style={{
          minHeight: isEmpty ? "120px" : undefined,
        }}
      >
        <SortableContext
          items={items.map((item) => `job-${item.job_id}`)}
          strategy={verticalListSortingStrategy}
        >
          <AnimatePresence mode="popLayout" initial={false}>
            <div className="flex flex-col gap-2.5">
              {items.map((item) => (
                <MemoizedJobCard key={item.job_id} item={item} />
              ))}
            </div>
          </AnimatePresence>

          {isEmpty && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center justify-center h-full min-h-[80px] text-text-muted text-xs"
            >
              {isDropTarget ? "Drop here" : "No jobs"}
            </motion.div>
          )}
        </SortableContext>
      </div>
    </motion.div>
  );
};

export const StageColumn = memo(StageColumnInner);
