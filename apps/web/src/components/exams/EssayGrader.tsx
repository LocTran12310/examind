"use client";

import { useState } from "react";
import { Alert, Button, Input, Textarea } from "@/components/ui";
import { api, ApiError } from "@/lib/api";

export function EssayGrader({ attemptId, questionId, max, points, comment, onSaved }: {
  attemptId: string; questionId: string; max: number; points: number | null; comment: string | null; onSaved: () => void;
}) {
  const [p, setP] = useState(points === null ? "" : String(points));
  const [c, setC] = useState(comment ?? "");
  const [error, setError] = useState<string | null>(null);
  return (
    <div className="mt-3 space-y-2 rounded-lg border border-amber-200 bg-amber-50 p-3" data-testid="essay-grader">
      <div className="flex items-center gap-2 text-sm">
        <span>Chấm điểm</span>
        <Input aria-label="Điểm tự luận" type="number" step="0.25" min={0} max={max} className="h-8 w-24" value={p} onChange={(e) => setP(e.target.value)} />
        <span className="text-gray-500">/ {max}</span>
      </div>
      <Textarea aria-label="Nhận xét" rows={2} placeholder="Nhận xét cho học sinh" value={c} onChange={(e) => setC(e.target.value)} />
      {error && <Alert>{error}</Alert>}
      <Button
        size="sm"
        variant="primary"
        onClick={async () => {
          setError(null);
          try {
            await api(`/attempts/${attemptId}/answers/${questionId}/grade`, { method: "PATCH", body: { points: Number(p), comment: c || null } });
            onSaved();
          } catch (e) {
            setError(e instanceof ApiError ? e.message : "Không lưu được");
          }
        }}
      >
        Lưu điểm
      </Button>
    </div>
  );
}
