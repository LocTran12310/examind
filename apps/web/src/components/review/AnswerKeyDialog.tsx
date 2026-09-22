"use client";

import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { api, ApiError } from "@/lib/api";

export function AnswerKeyDialog({ docId, onDone }: { docId: string; onDone: () => void }) {
  const [text, setText] = useState("");
  const [result, setResult] = useState<{ applied: number; approved: number; unmatched: number[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">Dán bảng đáp án dạng <code>1A 2C 3B</code>, <code>1.A, 2.C</code>, hoặc mỗi dòng một chữ cái. Câu đã duyệt không bị thay đổi.</p>
      <Textarea aria-label="Bảng đáp án" rows={5} value={text} onChange={(e) => setText(e.target.value)} className="font-mono" />
      {error && <FormAlert>{error}</FormAlert>}
      {result && (
        <FormAlert kind="success">
          Đã áp dụng {result.applied} đáp án, duyệt {result.approved} câu.
          {result.unmatched.length > 0 && ` Không khớp: câu ${result.unmatched.join(", ")}.`}
        </FormAlert>
      )}
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onDone}>Đóng</Button>
        <Button
         
          onClick={async () => {
            setError(null);
            try {
              setResult(await api(`/review/documents/${docId}/answer-key`, { body: { text } }));
            } catch (e) {
              setError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
            }
          }}
        >
          Áp dụng
        </Button>
      </div>
    </div>
  );
}
