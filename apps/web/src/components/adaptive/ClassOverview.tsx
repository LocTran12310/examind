"use client";

import { Badge, Table, td, th } from "@/components/ui";
import type { ClassOverviewRow } from "@/lib/types";

const STATUS: Record<string, string> = { submitted: "Đã làm", in_progress: "Đang làm", not_started: "Chưa làm" };

export function ClassOverview({ rows }: { rows: ClassOverviewRow[] }) {
  return (
    <Table>
      <thead className="bg-gray-50">
        <tr>
          <th className={th}>Học sinh</th>
          <th className={th}>Chuyên đề yếu nhất</th>
          <th className={th}>Đề ôn cá nhân</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {rows.map((r) => (
          <tr key={r.student_id} data-testid={`ov-${r.username}`}>
            <td className={td}>
              {r.full_name} <span className="font-mono text-xs text-gray-500">{r.username}</span>
            </td>
            <td className={`${td} space-x-1`}>
              {r.weakest.length === 0 ? (
                <span className="text-xs text-gray-400">chưa có dữ liệu</span>
              ) : (
                r.weakest.map((w) => (
                  <Badge key={w.name} tone={w.mastery < 0.5 ? "red" : "amber"}>
                    {w.name} {Math.round(w.mastery * 100)}%
                  </Badge>
                ))
              )}
            </td>
            <td className={td}>{r.review ? <Badge tone={r.review.status === "submitted" ? "green" : "gray"}>{STATUS[r.review.status] ?? r.review.status}</Badge> : "—"}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
