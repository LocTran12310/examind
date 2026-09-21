"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Alert, Badge, Button, Card, Empty } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { fmt } from "@/lib/dates";
import { useApi } from "@/lib/hooks";
import type { MyAssignment } from "@/lib/types";

export function StudentHome() {
  const router = useRouter();
  const { data } = useApi<MyAssignment[]>("/me/assignments");
  const [error, setError] = useState<string | null>(null);
  if (!data) return null;
  const open = data.filter((x) => x.state === "open" && (x.attempts_left > 0 || x.attempts.some((a) => a.status === "in_progress")));
  const upcoming = data.filter((x) => x.state === "upcoming");
  const done = data.filter((x) => x.attempts.some((a) => a.status === "submitted"));

  async function start(id: string) {
    setError(null);
    try {
      const r = await api<{ attempt_id: string }>(`/assignments/${id}/start`, { method: "POST" });
      router.push(`/exam/${r.attempt_id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Không bắt đầu được");
    }
  }

  return (
    <div className="space-y-6">
      {error && <Alert>{error}</Alert>}
      <section>
        <h2 className="mb-2 font-medium">Đang mở</h2>
        {open.length === 0 ? (
          <Empty>Không có bài nào đang mở.</Empty>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {open.map((x) => {
              const inProgress = x.attempts.find((a) => a.status === "in_progress");
              return (
                <Card key={x.assignment.id} data-testid={`open-${x.assignment.title}`}>
                  <div className="font-medium">{x.assignment.title}</div>
                  <p className="text-sm text-gray-500">
                    {x.assignment.duration_minutes} phút · hạn {fmt(x.assignment.close_at)}
                  </p>
                  <Button variant="primary" className="mt-3" onClick={() => void start(x.assignment.id)}>
                    {inProgress ? "Làm tiếp" : "Bắt đầu"}
                  </Button>
                </Card>
              );
            })}
          </div>
        )}
      </section>
      {upcoming.length > 0 && (
        <section>
          <h2 className="mb-2 font-medium">Sắp tới</h2>
          <ul className="space-y-1 text-sm">
            {upcoming.map((x) => (
              <li key={x.assignment.id} data-testid={`upcoming-${x.assignment.title}`}>
                {x.assignment.title} · mở lúc {fmt(x.assignment.open_at)}
              </li>
            ))}
          </ul>
        </section>
      )}
      {done.length > 0 && (
        <section>
          <h2 className="mb-2 font-medium">Đã làm</h2>
          <ul className="divide-y divide-gray-100 rounded-xl border border-gray-200 bg-white">
            {done.flatMap((x) =>
              x.attempts
                .filter((a) => a.status === "submitted")
                .map((a) => (
                  <li key={a.id} className="flex items-center justify-between px-4 py-3 text-sm" data-testid={`done-${x.assignment.title}`}>
                    <span>
                      {x.assignment.title} <span className="text-gray-500">· nộp {fmt(a.submitted_at)}</span>
                    </span>
                    <span className="flex items-center gap-2">
                      {a.score10 !== null ? <Badge tone="blue">{a.score10} điểm</Badge> : <Badge>Chưa có điểm</Badge>}
                      {a.needs_grading && <Badge tone="amber">Đang chấm tự luận</Badge>}
                      <Link href={`/results/${a.id}`} className="text-brand-700 hover:underline">
                        Xem kết quả
                      </Link>
                    </span>
                  </li>
                )),
            )}
          </ul>
        </section>
      )}
    </div>
  );
}
