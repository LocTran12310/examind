"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Alert, Badge, Button, Card } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { fmt } from "@/lib/dates";
import { useApi } from "@/lib/hooks";
import type { PracticeItem } from "@/lib/types";

export function PracticeButton({ count = 20 }: { count?: number }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return (
    <div>
      <Button
        variant="primary"
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          setError(null);
          try {
            const r = await api<{ attempt_id: string }>("/me/practice", { body: { count } });
            router.push(`/exam/${r.attempt_id}`);
          } catch (e) {
            setError(e instanceof ApiError ? e.message : "Không tạo được đề");
            setBusy(false);
          }
        }}
      >
        {busy ? "Đang tạo đề…" : "Tạo đề ôn tập"}
      </Button>
      {error && <div className="mt-2"><Alert>{error}</Alert></div>}
    </div>
  );
}

export function PracticeHistory() {
  const { data } = useApi<PracticeItem[]>("/me/practice");
  if (!data || !data.length) return null;
  return (
    <Card>
      <h2 className="mb-2 font-medium">Lịch sử ôn tập</h2>
      <ul className="divide-y divide-gray-100 text-sm" data-testid="practice-history">
        {data.map((p) => (
          <li key={p.attempt_id} className="py-2">
            <div className="flex items-center justify-between gap-2">
              <span>
                {fmt(p.started_at)} {p.score10 !== null && <Badge tone="blue">{p.score10} điểm</Badge>}
              </span>
              <Link className="text-brand-700 hover:underline" href={p.status === "submitted" ? `/results/${p.attempt_id}` : `/exam/${p.attempt_id}`}>
                {p.status === "submitted" ? "Xem kết quả" : "Làm tiếp"}
              </Link>
            </div>
            <div className="mt-1 flex flex-wrap gap-1 text-xs text-gray-600">
              {p.groups.map((g) => (
                <span key={`${g.reason}-${g.topic}`} className="rounded bg-gray-100 px-2 py-0.5">
                  {g.reason}
                  {g.topic ? `: ${g.topic}` : ""} × {g.count}
                </span>
              ))}
            </div>
            {p.note && <p className="mt-1 text-xs text-gray-500">{p.note}</p>}
          </li>
        ))}
      </ul>
    </Card>
  );
}
