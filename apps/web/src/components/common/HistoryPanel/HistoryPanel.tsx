"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useMemo } from "react";
import { DataTable } from "@/components/common/DataTable/DataTable";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { ACTION_LABEL } from "@/constants/audit.constant";
import { useAuditSearchQuery } from "@/hooks/react-query/use-query-audit";
import type { AuditEntry } from "@/interfaces/audit.interface";
import { auditDetails } from "@/lib/common/audit-details";
import { formatDateTime } from "@/lib/common/datetime";

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
      { id: "details", header: "Chi tiết", cell: ({ row }) => <span className="text-muted-foreground">{auditDetails(row.original)}</span> },
    ],
    [orgId],
  );
  return <DataTable useRows={useAuditSearchQuery} prefix={prefix} params={params} columns={columns} getRowId={(e) => e.id} selectable={false} emptyText="Chưa có thay đổi nào." />;
}
