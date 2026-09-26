"use client";

import { Panel } from "@/components/common/Panel/Panel";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { Label } from "@/components/ui/label";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import type { Exam } from "@/interfaces/exam.interface";

/** "Môn và lớp": what the paper is for. Saved on choice, like the points beside it — there is no draft state
 *  worth a Lưu button for two selects.
 *
 *  The subject is not a label only: it scopes the matrix's topic picker, which is why an exam created without
 *  one opens the tree of every subject. Changing it on an exam that already holds questions is allowed and the
 *  consequence is said out loud (ADR-03) — the questions stay, only the picker's range moves. */
export function ExamLabels({ exam, onChange }: { exam: Exam; onChange: (changes: { subject_id?: string | null; grade?: number | null }) => void }) {
  const { data: taxonomy } = useTaxonomyQuery();
  return (
    <Panel id="mon-va-lop">
      <h2 className="mb-2 font-medium">Môn và lớp</h2>
      <div className="grid gap-2 text-sm">
        <Label className="justify-between font-normal">
          Môn
          <OptionSelect
            aria-label="Môn của đề"
            className="w-44"
            size="sm"
            value={exam.subject_id ?? ""}
            onValueChange={(v) => onChange({ subject_id: v || null })}
            emptyLabel="Chưa chọn"
            options={(taxonomy?.subjects ?? []).map((s) => ({ value: s.id, label: s.name }))}
          />
        </Label>
        <Label className="justify-between font-normal">
          Lớp
          <OptionSelect
            aria-label="Lớp của đề"
            className="w-44"
            size="sm"
            value={exam.grade === null ? "" : String(exam.grade)}
            onValueChange={(v) => onChange({ grade: v ? Number(v) : null })}
            emptyLabel="Chưa chọn"
            options={(taxonomy?.grades ?? []).map((g) => ({ value: String(g.level), label: g.name }))}
          />
        </Label>
      </div>
      <p className="mt-2 text-sm text-muted-foreground" data-testid="labels-hint">
        Ma trận đề chỉ mở chuyên đề của môn này.
        {exam.question_count > 0 && " Đổi môn không đụng tới câu đã có trong đề — chỉ đổi phạm vi của ma trận."}
      </p>
    </Panel>
  );
}
