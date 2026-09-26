"use client";

import Link from "next/link";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { ClassOverviewRow, ClassReviewRef } from "@/interfaces/mastery.interface";
import { formatDate } from "@/lib/common/datetime";

const STATUS: Record<string, string> = { submitted: "Đã làm", in_progress: "Đang làm", not_started: "Chưa làm" };

/** A paper whose deadline has passed and that the student never submitted. Submitted ones are left alone: once
 *  the work is in, the deadline has nothing left to warn about (A-04). */
const overdue = (r: ClassReviewRef) => r.status !== "submitted" && new Date(r.close_at).getTime() < Date.now();

/** Which paper, given when, due when, done or not — and how many the student has in all.
 *
 *  The cell used to be a single badge reading "Chưa làm", which answered none of those: three rounds of
 *  "Giao đề ôn cá nhân" looked exactly like one. It shows the newest paper in full and says how many came
 *  before it rather than listing them all — 25 students × 3 papers would be a table three times as tall for a
 *  question nobody asks that way (ADR-02). */
function ReviewCell({ review }: { review: ClassReviewRef | null }) {
  if (!review) return <span className="text-xs text-muted-foreground/70">chưa giao</span>;
  const late = overdue(review);
  return (
    <div className="space-y-0.5">
      <Link href={`/org/assignments/${review.assignment_id}`} className="text-sm hover:text-primary">
        {review.title}
      </Link>
      <p className="text-xs text-muted-foreground">
        giao {formatDate(review.open_at)} · hạn {formatDate(review.close_at)}
      </p>
      <div className="flex flex-wrap items-center gap-1">
        <ToneBadge tone={review.status === "submitted" ? "green" : late ? "red" : "gray"}>
          {late ? "Quá hạn" : (STATUS[review.status] ?? review.status)}
        </ToneBadge>
        {review.total > 1 && <span className="text-xs text-muted-foreground">còn {review.total - 1} đề trước</span>}
      </div>
    </div>
  );
}

export function ClassOverview({ rows }: { rows: ClassOverviewRow[] }) {
  return (
    <div className="rounded-lg border bg-card">
      <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Học sinh</TableHead>
          <TableHead>Mức nắm vững theo chuyên đề (thấp trước)</TableHead>
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
            <TableCell><ReviewCell review={r.review} /></TableCell>
          </TableRow>
        ))}
      </TableBody>
      </Table>
    </div>
  );
}
