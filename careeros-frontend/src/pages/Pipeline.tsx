import { KanbanBoard } from "@/components/kanban";
import { mockKanbanData } from "@/data/mockPipeline";
import type { KanbanResponse } from "@/types";

export default function Pipeline() {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Pipeline</h1>
          <p className="text-sm text-text-secondary mt-1">
            Drag cards across stages to track your job search
          </p>
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <KanbanBoard initialData={mockKanbanData as KanbanResponse} />
      </div>
    </div>
  );
}
