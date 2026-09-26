"use client";

import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { Button } from "@/components/ui/button";
import { usePracticeButton } from "@/hooks/common/use-practice-button";

/** A student starts a personal practice exam (home, my progress).
 *
 *  `defaultSubjectId` is where the subject step starts — the progress page knows which subject the student is
 *  furthest behind in and says so; the home page has no such numbers loaded and passes nothing, which lands on
 *  the first subject. Fetching a whole stats payload just to preselect a dropdown would be a poor trade. */
export function PracticeButton({ count = 20, defaultSubjectId }: { count?: number; defaultSubjectId?: string | null }) {
  const p = usePracticeButton(count, defaultSubjectId);
  return (
    <div>
      <Button disabled={p.busy} onClick={p.start}>
        {p.busy ? "Đang tạo đề…" : "Tạo đề ôn tập"}
      </Button>
      {p.error && (
        <div className="mt-2">
          <FormAlert>{p.error}</FormAlert>
        </div>
      )}
      <FormDialog open={p.asking} onOpenChange={(o) => !o && p.close()} title="Ôn môn nào?" description="Đề sẽ chỉ gồm câu của môn bạn chọn, theo những chuyên đề bạn đang yếu.">
        <div className="grid gap-3">
          <OptionSelect aria-label="Môn ôn tập" value={p.chosen} onValueChange={p.setChosen} options={p.subjects.map((s) => ({ value: s.id, label: s.name }))} />
          <Button disabled={!p.chosen || p.busy} onClick={p.confirm}>
            Tạo đề ôn tập
          </Button>
        </div>
      </FormDialog>
    </div>
  );
}
