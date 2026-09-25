import { useCallback, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragStartEvent,
  type DragEndEvent,
} from "@dnd-kit/core";
import { motion } from "framer-motion";
import { StageColumn } from "./StageColumn";
import { JobCard } from "./JobCard";
import {
  PIPELINE_STAGES,
  normalizeStages,
  type KanbanItem,
  type KanbanResponse,
  type StageColumnId,
} from "@/types/pipeline";

interface KanbanBoardProps {
  initialData: KanbanResponse;
}

type StageMap = Record<string, KanbanItem[]>;

const findStageContainingItem = (
  stages: StageMap,
  jobId: number,
): StageColumnId | null => {
  for (const [stageId, items] of Object.entries(stages)) {
    if (items.some((i) => i.job_id === jobId)) {
      return stageId as StageColumnId;
    }
  }
  return null;
};

export const KanbanBoard = ({ initialData }: KanbanBoardProps) => {
  const [stages, setStages] = useState<StageMap>(() =>
    normalizeStages(initialData),
  );
  const [activeItem, setActiveItem] = useState<KanbanItem | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor),
  );

  const handleDragStart = useCallback(
    (event: DragStartEvent) => {
      const { active } = event;
      const jobId = Number(String(active.id).replace("job-", ""));
      const sourceStage = findStageContainingItem(stages, jobId);
      if (sourceStage) {
        const item = stages[sourceStage].find((i) => i.job_id === jobId);
        if (item) setActiveItem(item);
      }
    },
    [stages],
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      setActiveItem(null);

      if (!over) return;

      const jobId = Number(String(active.id).replace("job-", ""));
      const sourceStage = findStageContainingItem(stages, jobId);
      if (!sourceStage) return;

      // Determine target stage: either a stage drop zone or another card's stage
      let targetStage: StageColumnId | null = null;
      const overId = String(over.id);

      if ((PIPELINE_STAGES as readonly string[]).includes(overId)) {
        targetStage = overId as StageColumnId;
      } else {
        // Dropped over another card — find that card's stage
        const overJobId = Number(overId.replace("job-", ""));
        targetStage = findStageContainingItem(stages, overJobId);
      }

      if (!targetStage || sourceStage === targetStage) return;

      setStages((prev) => {
        const sourceItems = [...prev[sourceStage]];
        const targetItems = [...prev[targetStage]];

        const itemIndex = sourceItems.findIndex((i) => i.job_id === jobId);
        if (itemIndex === -1) return prev;

        const [movedItem] = sourceItems.splice(itemIndex, 1);
        movedItem.status = targetStage;

        // Insert at end (or compute index if dropping over specific card)
        const overJobId = Number(overId.replace("job-", ""));
        const overIndex = targetItems.findIndex((i) => i.job_id === overJobId);
        if (overIndex >= 0) {
          targetItems.splice(overIndex, 0, movedItem);
        } else {
          targetItems.push(movedItem);
        }

        return {
          ...prev,
          [sourceStage]: sourceItems,
          [targetStage]: targetItems,
        };
      });

      // TODO: POST /api/v1/applications/{id} with new status
    },
    [stages],
  );

  const handleDragCancel = useCallback(() => {
    setActiveItem(null);
  }, []);

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className="flex gap-4 overflow-x-auto pb-4 px-1 h-full">
        {PIPELINE_STAGES.map((stageId) => (
          <StageColumn
            key={stageId}
            stageId={stageId}
            items={stages[stageId] ?? []}
            isDragActive={activeItem !== null}
          />
        ))}
      </div>

      <DragOverlay dropAnimation={{ duration: 200 }}>
        {activeItem ? (
          <motion.div
            initial={{ scale: 0.95, opacity: 0.8 }}
            animate={{ scale: 1.03, opacity: 1 }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
            className="rotate-3 shadow-glow-lg"
          >
            <JobCard item={activeItem} />
          </motion.div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
};

export type { KanbanBoardProps };
