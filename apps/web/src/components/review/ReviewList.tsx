"use client";

import type { ColumnDef } from "@tanstack/react-table";
import Link from "next/link";
import { OptionSelect } from "@/components/app/OptionSelect";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Progress as Bar } from "@/components/ui/progress";
import type { ReviewDocument, User } from "@/lib/types";

export function Progress({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <Bar value={pct} className="w-28" aria-label="Tiến độ" />
      <span className="text-xs text-muted-foreground">{pct}%</span>
    </div>
  );
}

export const pendingOf = (r: ReviewDocument) => r.counts.needs_review + r.spot_pending + (r.counts.flagged ?? 0);

export function ReviewCounts({ r }: { r: ReviewDocument }) {
  return (
    <div className="flex flex-wrap gap-1">
      <ToneBadge tone="green">Tự duyệt {r.counts.auto_approved}</ToneBadge>
      <ToneBadge tone={r.counts.needs_review ? "amber" : "gray"}>Cần xem {r.counts.needs_review}</ToneBadge>
      {(r.counts.flagged ?? 0) > 0 && <ToneBadge tone="red">Nghi sai đáp án {r.counts.flagged}</ToneBadge>}
      {r.spot_pending > 0 && <ToneBadge tone="blue">Kiểm tra ngẫu nhiên {r.spot_pending}</ToneBadge>}
      <ToneBadge>Đã duyệt {r.counts.approved}</ToneBadge>
      {r.counts.duplicate > 0 && <ToneBadge>Trùng {r.counts.duplicate}</ToneBadge>}
      {r.counts.rejected > 0 && <ToneBadge tone="red">Loại {r.counts.rejected}</ToneBadge>}
    </div>
  );
}

export function reviewColumns({ teachers, canAssign, onAssign }: { teachers: User[]; canAssign: boolean; onAssign: (docId: string, userId: string | null) => void }): ColumnDef<ReviewDocument, unknown>[] {
  const options = teachers.map((t) => ({ value: t.id, label: t.full_name }));
  return [
    {
      id: "filename",
      header: "Đề",
      cell: ({ row }) => (
        <div data-testid={`rev-${row.original.document.filename}`}>
          <div className="font-medium">{row.original.document.filename}</div>
          <div className="text-xs text-muted-foreground">{row.original.total} câu</div>
        </div>
      ),
      meta: { filter: { kind: "text" }, sort: "filename" },
    },
    { id: "counts", header: "Tình trạng", cell: ({ row }) => <ReviewCounts r={row.original} />, meta: { sort: "needs_review" } },
    { id: "progress", header: "Tiến độ", cell: ({ row }) => <Progress value={row.original.progress} /> },
    {
      id: "assigned_to",
      header: "Người duyệt",
      cell: ({ row }) =>
        canAssign ? (
          <OptionSelect
            size="sm"
            aria-label="Người duyệt"
            value={row.original.assigned_to ?? ""}
            onValueChange={(v) => onAssign(row.original.document.id, v || null)}
            options={options}
            emptyLabel="— Chưa giao —"
            className="w-44"
          />
        ) : (
          <span className="text-sm text-muted-foreground">{row.original.assigned_name ?? "—"}</span>
        ),
      meta: canAssign ? { filter: { kind: "select", options } } : undefined,
    },
    {
      id: "action",
      header: "",
      cell: ({ row }) => {
        const pending = pendingOf(row.original);
        return (
          <Link href={`/org/review/${row.original.document.id}`} className="font-medium whitespace-nowrap text-primary hover:underline" onClick={(e) => e.stopPropagation()}>
            {pending ? `Duyệt ${pending} câu` : "Xem"}
          </Link>
        );
      },
      meta: { align: "right" },
    },
  ];
}
