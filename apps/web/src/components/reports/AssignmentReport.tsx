"use client";

import Link from "next/link";
import { Markdown } from "@/components/question/Markdown";
import { Badge, Card, Table, td, th } from "@/components/ui";
import { TYPE_LABEL, type AssignmentReport as Report } from "@/lib/types";

const STATUS: Record<string, string> = { submitted: "Đã nộp", in_progress: "Đang làm", not_started: "Chưa làm" };

export function pct(r: number | null | undefined): string {
  return r === null || r === undefined ? "—" : `${Math.round(r * 100)}%`;
}

export function AssignmentReport({ report }: { report: Report }) {
  const maxBucket = Math.max(1, ...report.distribution.map((b) => b.count));
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <div className="text-sm text-gray-500">Đã nộp</div>
          <div className="text-2xl font-semibold" data-testid="submitted">
            {report.submitted}/{report.total_students}
          </div>
        </Card>
        <Card>
          <div className="text-sm text-gray-500">Điểm trung bình</div>
          <div className="text-2xl font-semibold" data-testid="average">
            {report.average ?? "—"}
          </div>
        </Card>
        <Card>
          <div className="mb-1 text-sm text-gray-500">Phổ điểm</div>
          <div className="flex h-16 items-end gap-1" data-testid="distribution">
            {report.distribution.map((b) => (
              <div key={b.from} className="flex-1" title={`${b.from}–${b.to}: ${b.count}`}>
                <div className="rounded-t bg-brand-500" style={{ height: `${(b.count / maxBucket) * 56}px` }} />
                <div className="text-center text-[10px] text-gray-400">{b.from}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
      <Card>
        <h2 className="mb-2 font-medium">Học sinh</h2>
        <Table>
          <thead className="bg-gray-50">
            <tr>
              <th className={th}>Học sinh</th>
              <th className={th}>Trạng thái</th>
              <th className={th}>Điểm</th>
              <th className={th}>Rời tab</th>
              <th className={th} />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {report.students.map((s) => (
              <tr key={s.student_id} data-testid={`st-${s.username}`}>
                <td className={td}>
                  {s.full_name} <span className="font-mono text-xs text-gray-500">{s.username}</span>
                </td>
                <td className={td}>
                  <Badge tone={s.status === "submitted" ? "green" : s.status === "in_progress" ? "amber" : "gray"}>{STATUS[s.status]}</Badge>
                  {s.needs_grading && <span className="ml-1"><Badge tone="amber">Cần chấm tự luận</Badge></span>}
                </td>
                <td className={td}>{s.score10 ?? "—"}</td>
                <td className={td}>{s.tab_switches || ""}</td>
                <td className={td}>
                  {s.attempt_id && s.status === "submitted" && (
                    <Link href={`/results/${s.attempt_id}`} className="text-brand-700 hover:underline">
                      Xem bài
                    </Link>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
      <Card>
        <h2 className="mb-2 font-medium">Theo câu hỏi</h2>
        <ul className="divide-y divide-gray-100">
          {report.questions.map((q) => (
            <li key={q.question_id} className="flex gap-3 py-2 text-sm" data-testid={`qs-${q.position}`}>
              <span className="w-8 font-semibold">{q.position}.</span>
              <div className="line-clamp-2 min-w-0 flex-1">
                <Markdown>{q.stem}</Markdown>
              </div>
              <span className="w-24 text-xs text-gray-500">{TYPE_LABEL[q.type]}</span>
              <span className="w-12 text-right font-medium">{pct(q.ratio)}</span>
              <span className="w-32 text-xs text-red-700">{q.top_wrong ? `Hay chọn sai: ${q.top_wrong.label} (${q.top_wrong.count})` : ""}</span>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
