"use client";

import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { ClassOverviewRow } from "@/interfaces/mastery.interface";

const STATUS: Record<string, string> = { submitted: "Đã làm", in_progress: "Đang làm", not_started: "Chưa làm" };

export function ClassOverview({ rows }: { rows: ClassOverviewRow[] }) {
  return (
    <div className="rounded-lg border bg-card">
      <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Học sinh</TableHead>
          <TableHead>Chuyên đề yếu nhất</TableHead>
          <TableHead>Đề ôn cá nhân</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((r) => (
          <TableRow key={r.student_id} data-testid={`ov-${r.username}`}>
            <TableCell>
              {r.full_name} <span className="font-mono text-xs text-muted-foreground">{r.username}</span>
            </TableCell>
            <TableCell className="space-x-1">
              {r.weakest.length === 0 ? (
                <span className="text-xs text-muted-foreground/70">chưa đủ dữ liệu</span>
              ) : (
                r.weakest.map((w) => (
                  <ToneBadge key={w.name} tone={w.mastery < 0.5 ? "red" : "amber"}>
                    {w.name} {Math.round(w.mastery * 100)}%
                  </ToneBadge>
                ))
              )}
            </TableCell>
            <TableCell>{r.review ? <ToneBadge tone={r.review.status === "submitted" ? "green" : "gray"}>{STATUS[r.review.status] ?? r.review.status}</ToneBadge> : "—"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
      </Table>
    </div>
  );
}
