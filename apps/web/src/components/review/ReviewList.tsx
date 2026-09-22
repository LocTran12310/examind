"use client";

import Link from "next/link";
import { ToneBadge } from "@/components/app/ToneBadge";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { ReviewDocument, User } from "@/lib/types";

export function Progress({ value }: { value: number }) {
  return (
    <div className="h-2 w-28 overflow-hidden rounded bg-muted" role="progressbar" aria-valuenow={Math.round(value * 100)} aria-valuemin={0} aria-valuemax={100}>
      <div className="h-2 bg-green-500" style={{ width: `${Math.round(value * 100)}%` }} />
    </div>
  );
}

export function ReviewList({
  rows,
  teachers,
  canAssign,
  onAssign,
}: {
  rows: ReviewDocument[];
  teachers: User[];
  canAssign: boolean;
  onAssign: (docId: string, userId: string | null) => void;
}) {
  return (
    <div className="rounded-lg border bg-card">
<Table>
      <TableHeader>
        <TableRow>
          <TableHead>Đề</TableHead>
          <TableHead>Tình trạng</TableHead>
          <TableHead>Tiến độ</TableHead>
          <TableHead>Người duyệt</TableHead>
          <TableHead />
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((r) => {
          const pending = r.counts.needs_review + r.spot_pending + (r.counts.flagged ?? 0);
          return (
            <TableRow key={r.document.id} data-testid={`rev-${r.document.filename}`}>
              <TableCell>
                <div className="font-medium">{r.document.filename}</div>
                <div className="text-xs text-muted-foreground">{r.total} câu</div>
              </TableCell>
              <TableCell className="space-x-1">
                <ToneBadge tone="green">Tự duyệt {r.counts.auto_approved}</ToneBadge>
                <ToneBadge tone={r.counts.needs_review ? "amber" : "gray"}>Cần xem {r.counts.needs_review}</ToneBadge>
                {(r.counts.flagged ?? 0) > 0 && <ToneBadge tone="red">Nghi sai đáp án {r.counts.flagged}</ToneBadge>}
                {r.spot_pending > 0 && <ToneBadge tone="blue">Kiểm tra ngẫu nhiên {r.spot_pending}</ToneBadge>}
                <ToneBadge>Đã duyệt {r.counts.approved}</ToneBadge>
                {r.counts.duplicate > 0 && <ToneBadge>Trùng {r.counts.duplicate}</ToneBadge>}
                {r.counts.rejected > 0 && <ToneBadge tone="red">Loại {r.counts.rejected}</ToneBadge>}
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Progress value={r.progress} />
                  <span className="text-xs text-muted-foreground">{Math.round(r.progress * 100)}%</span>
                </div>
              </TableCell>
              <TableCell>
                {canAssign ? (
                  <NativeSelect aria-label="Người duyệt" value={r.assigned_to ?? ""} onChange={(e) => onAssign(r.document.id, e.target.value || null)}>
                    <NativeSelectOption value="">— Chưa giao —</NativeSelectOption>
                    {teachers.map((t) => (
                      <NativeSelectOption key={t.id} value={t.id}>
                        {t.full_name}
                      </NativeSelectOption>
                    ))}
                  </NativeSelect>
                ) : (
                  <span className="text-sm text-muted-foreground">{r.assigned_name ?? "—"}</span>
                )}
              </TableCell>
              <TableCell className="text-right">
                <Link href={`/org/review/${r.document.id}`} className="font-medium text-primary hover:underline">
                  {pending ? `Duyệt ${pending} câu` : "Xem"}
                </Link>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
</div>
  );
}
