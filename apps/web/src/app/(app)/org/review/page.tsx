"use client";

import { ListLayout } from "@/components/app/ListLayout";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { useMe } from "@/app/(app)/AppShell";
import { PageHeader } from "@/components/app/PageHeader";
import { DataTable } from "@/components/data-table/DataTable";
import { useTableQuery } from "@/components/data-table/useTableQuery";
import { reviewColumns } from "@/components/review/ReviewList";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Page, ReviewDocument, User } from "@/lib/types";

export default function ReviewPage() {
  const me = useMe();
  const tq = useTableQuery();
  const [version, setVersion] = useState(0);
  const canAssign = me.role === "org_admin";
  const { data: staff } = useApi<Page<User>>(canAssign ? "/users?role=teacher,org_admin&page_size=all" : null);
  const columns = useMemo(
    () =>
      reviewColumns({
        teachers: staff?.items ?? [],
        canAssign,
        onAssign: async (docId, userId) => {
          try {
            await api(`/review/documents/${docId}`, { method: "PATCH", body: { assigned_to: userId } });
            setVersion((v) => v + 1);
          } catch (e) {
            toast.error(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
          }
        },
      }),
    [staff, canAssign],
  );

  return (
    <>
      <ListLayout header={<PageHeader
        title="Duyệt câu hỏi"
        description="Chỉ những câu cần mắt người mới vào hàng đợi"
        actions={
          <div className="flex items-center gap-2">
            <Switch id="mine" checked={tq.get("mine") === "true"} onCheckedChange={(v) => tq.setFilter("mine", v ? "true" : null)} />
            <Label htmlFor="mine">Của tôi</Label>
          </div>
        }
      />}>
        <DataTable<ReviewDocument>
          path="/review/documents"
          columns={columns}
          getRowId={(r) => r.document.id}
          selectable={false}
          reloadKey={version}
          emptyText="Không có đề nào cần duyệt."
        />
      </ListLayout>
    </>
  );
}
