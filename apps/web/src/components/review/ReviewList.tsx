"use client";

import Link from "next/link";
import { Badge, Select, Table, td, th } from "@/components/ui";
import type { ReviewDocument, User } from "@/lib/types";

export function Progress({ value }: { value: number }) {
  return (
    <div className="h-2 w-28 overflow-hidden rounded bg-gray-100" role="progressbar" aria-valuenow={Math.round(value * 100)} aria-valuemin={0} aria-valuemax={100}>
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
    <Table>
      <thead className="bg-gray-50">
        <tr>
          <th className={th}>Đề</th>
          <th className={th}>Tình trạng</th>
          <th className={th}>Tiến độ</th>
          <th className={th}>Người duyệt</th>
          <th className={th} />
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {rows.map((r) => {
          const pending = r.counts.needs_review + r.spot_pending + (r.counts.flagged ?? 0);
          return (
            <tr key={r.document.id} data-testid={`rev-${r.document.filename}`}>
              <td className={td}>
                <div className="font-medium">{r.document.filename}</div>
                <div className="text-xs text-gray-500">{r.total} câu</div>
              </td>
              <td className={`${td} space-x-1`}>
                <Badge tone="green">Tự duyệt {r.counts.auto_approved}</Badge>
                <Badge tone={r.counts.needs_review ? "amber" : "gray"}>Cần xem {r.counts.needs_review}</Badge>
                {(r.counts.flagged ?? 0) > 0 && <Badge tone="red">Nghi sai đáp án {r.counts.flagged}</Badge>}
                {r.spot_pending > 0 && <Badge tone="blue">Kiểm tra ngẫu nhiên {r.spot_pending}</Badge>}
                <Badge>Đã duyệt {r.counts.approved}</Badge>
                {r.counts.duplicate > 0 && <Badge>Trùng {r.counts.duplicate}</Badge>}
                {r.counts.rejected > 0 && <Badge tone="red">Loại {r.counts.rejected}</Badge>}
              </td>
              <td className={td}>
                <div className="flex items-center gap-2">
                  <Progress value={r.progress} />
                  <span className="text-xs text-gray-500">{Math.round(r.progress * 100)}%</span>
                </div>
              </td>
              <td className={td}>
                {canAssign ? (
                  <Select aria-label="Người duyệt" value={r.assigned_to ?? ""} onChange={(e) => onAssign(r.document.id, e.target.value || null)}>
                    <option value="">— Chưa giao —</option>
                    {teachers.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.full_name}
                      </option>
                    ))}
                  </Select>
                ) : (
                  <span className="text-sm text-gray-600">{r.assigned_name ?? "—"}</span>
                )}
              </td>
              <td className={`${td} text-right`}>
                <Link href={`/org/review/${r.document.id}`} className="font-medium text-brand-700 hover:underline">
                  {pending ? `Duyệt ${pending} câu` : "Xem"}
                </Link>
              </td>
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
}
