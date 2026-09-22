"use client";

import Link from "next/link";
import { EmptyState } from "@/components/common/EmptyState/EmptyState";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { Panel } from "@/components/common/Panel/Panel";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { Button } from "@/components/ui/button";
import { useStudentHome } from "@/hooks/page-hooks/student-home/use-student-home-page";
import { formatDateTime } from "@/lib/common/datetime";

export function StudentAssignments() {
  const h = useStudentHome();
  if (!h.loaded) return null;
  return (
    <div className="space-y-6">
      {h.error && <FormAlert>{h.error}</FormAlert>}
      <section>
        <h2 className="mb-2 font-medium">Đang mở</h2>
        {h.open.length === 0 ? (
          <EmptyState>Không có bài nào đang mở.</EmptyState>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {h.open.map((x) => {
              const inProgress = x.attempts.find((a) => a.status === "in_progress");
              return (
                <Panel key={x.assignment.id} data-testid={`open-${x.assignment.title}`}>
                  <div className="font-medium">{x.assignment.title}</div>
                  <p className="text-sm text-muted-foreground">
                    {x.assignment.duration_minutes} phút · hạn {formatDateTime(x.assignment.close_at)}
                  </p>
                  <Button className="mt-3" onClick={() => h.start(x.assignment.id)}>
                    {inProgress ? "Làm tiếp" : "Bắt đầu"}
                  </Button>
                </Panel>
              );
            })}
          </div>
        )}
      </section>
      {h.upcoming.length > 0 && (
        <section>
          <h2 className="mb-2 font-medium">Sắp tới</h2>
          <ul className="space-y-1 text-sm">
            {h.upcoming.map((x) => (
              <li key={x.assignment.id} data-testid={`upcoming-${x.assignment.title}`}>
                {x.assignment.title} · mở lúc {formatDateTime(x.assignment.open_at)}
              </li>
            ))}
          </ul>
        </section>
      )}
      {h.done.length > 0 && (
        <section>
          <h2 className="mb-2 font-medium">Đã làm</h2>
          <ul className="divide-y divide-border rounded-xl border border-border bg-card">
            {h.done.flatMap((x) =>
              x.attempts
                .filter((a) => a.status === "submitted")
                .map((a) => (
                  <li key={a.id} className="flex items-center justify-between px-4 py-3 text-sm" data-testid={`done-${x.assignment.title}`}>
                    <span>
                      {x.assignment.title} <span className="text-muted-foreground">· nộp {formatDateTime(a.submitted_at)}</span>
                    </span>
                    <span className="flex items-center gap-2">
                      {a.score10 !== null ? <ToneBadge tone="blue">{a.score10} điểm</ToneBadge> : <ToneBadge>Chưa có điểm</ToneBadge>}
                      {a.needs_grading && <ToneBadge tone="amber">Đang chấm tự luận</ToneBadge>}
                      <Link href={`/results/${a.id}`} className="text-primary hover:underline">
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
