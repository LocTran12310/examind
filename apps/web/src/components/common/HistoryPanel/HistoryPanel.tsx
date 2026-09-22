"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useMemo } from "react";
import { ToneBadge } from "@/components/app/ToneBadge";
import { DataTable } from "@/components/data-table/DataTable";
import type { AuditEntry } from "@/lib/types";
import { formatDateTime } from "@/lib/datetime";

export const ACTION_LABEL: Record<string, string> = {
  "year.create": "Tạo năm học",
  "year.update": "Sửa năm học",
  "year.activate": "Đặt làm năm đang học",
  "year.close": "Khóa năm học",
  "year.reopen": "Mở lại năm học",
  "year.delete": "Xóa năm học",
  "class.create": "Tạo lớp",
  "class.update": "Sửa lớp",
  "class.delete": "Xóa lớp",
  "class.members_add": "Thêm học sinh vào lớp",
  "class.members_remove": "Xóa học sinh khỏi lớp",
  "member.link": "Thêm vào tổ chức",
  "member.unlink": "Gỡ khỏi tổ chức",
  "member.update": "Đổi vai trò / trạng thái",
  "org.switch": "Chuyển tổ chức",
  "rollover.commit": "Chuyển năm học",
  "user.create": "Tạo tài khoản",
  "user.update": "Sửa tài khoản",
  "user.reset_password": "Đặt lại mật khẩu",
};

function details(e: AuditEntry): string {
  const d = e.data ?? {};
  const parts: string[] = [];
  const changes = d.changes as Record<string, [unknown, unknown]> | undefined;
  if (changes) for (const [k, [a, b]] of Object.entries(changes)) parts.push(`${k}: ${a ?? "—"} → ${b ?? "—"}`);
  for (const k of ["username", "name", "code", "school_year", "role", "home", "org_code"]) if (typeof d[k] === "string" && !changes?.[k]) parts.push(String(d[k]));
  if (Array.isArray(d.user_ids)) parts.push(`${d.user_ids.length} người`);
  return parts.join(" · ");
}

/** "Lịch sử": audit entries for one target (or anything mentioning `related`), paged on the server. */
export function HistoryPanel({ targetId, related, orgId, prefix = "h." }: { targetId?: string; related?: string; orgId?: string; prefix?: string }) {
  const params = useMemo(() => ({ target_id: targetId, related, organization_id: orgId }), [targetId, related, orgId]);
  const columns = useMemo<ColumnDef<AuditEntry, unknown>[]>(
    () => [
      { accessorKey: "created_at", header: "Thời điểm", cell: ({ row }) => formatDateTime(row.original.created_at, { withSeconds: true }), meta: { filter: { kind: "date" }, sort: "created_at" } },
      { accessorKey: "actor_name", header: "Người thực hiện", cell: ({ row }) => row.original.actor_name ?? "Hệ thống" },
      ...(orgId ? [] : [{ accessorKey: "organization_code", header: "Tổ chức" } as ColumnDef<AuditEntry, unknown>]),
      {
        accessorKey: "action",
        header: "Thao tác",
        cell: ({ row }) => (
          <span className="inline-flex items-center gap-1">
            {ACTION_LABEL[row.original.action] ?? row.original.action}
            {row.original.data?.closed_year === true && <ToneBadge tone="amber">năm đã khóa</ToneBadge>}
          </span>
        ),
        meta: { filter: { kind: "text" } },
      },
      { id: "details", header: "Chi tiết", cell: ({ row }) => <span className="text-muted-foreground">{details(row.original)}</span> },
    ],
    [orgId],
  );
  return <DataTable path="/audit" prefix={prefix} params={params} columns={columns} getRowId={(e) => e.id} selectable={false} emptyText="Chưa có thay đổi nào." />;
}
