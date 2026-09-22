"use client";

import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAnswerKey } from "@/hooks/page-hooks/review-document/use-answer-key";

export function AnswerKeyDialog({ docId, onDone }: { docId: string; onDone: () => void }) {
  const a = useAnswerKey(docId);
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">Dán bảng đáp án dạng <code>1A 2C 3B</code>, <code>1.A, 2.C</code>, hoặc mỗi dòng một chữ cái. Câu đã duyệt không bị thay đổi.</p>
      <Textarea aria-label="Bảng đáp án" rows={5} value={a.text} onChange={(e) => a.setText(e.target.value)} className="font-mono" />
      {a.error && <FormAlert>{a.error}</FormAlert>}
      {a.result && (
        <FormAlert kind="success">
          Đã áp dụng {a.result.applied} đáp án, duyệt {a.result.approved} câu.
          {a.result.unmatched.length > 0 && ` Không khớp: câu ${a.result.unmatched.join(", ")}.`}
        </FormAlert>
      )}
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onDone}>Đóng</Button>
        <Button onClick={() => void a.submit()}>Áp dụng</Button>
      </div>
    </div>
  );
}
