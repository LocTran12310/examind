"use client";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { DOCUMENT_QUESTION_STATES } from "@/constants/review.constant";
import type { DocumentQuestionState } from "@/interfaces/review.interface";

/** Which questions of the document are shown; "Cần xem" is the keyboard queue (AC-03). */
export function ReviewStateFilter({ value, onChange }: { value: DocumentQuestionState; onChange: (v: DocumentQuestionState) => void }) {
  return (
    <div className="mb-3 flex flex-wrap items-center gap-2">
      <span className="text-sm text-muted-foreground">Hiển thị câu:</span>
      <ToggleGroup
        type="single"
        variant="outline"
        size="sm"
        spacing={0}
        value={value}
        aria-label="Lọc theo trạng thái câu hỏi"
        onValueChange={(v) => v && onChange(v as DocumentQuestionState)}
      >
        {DOCUMENT_QUESTION_STATES.map((s) => (
          <ToggleGroupItem key={s.value} value={s.value}>
            {s.label}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>
    </div>
  );
}
