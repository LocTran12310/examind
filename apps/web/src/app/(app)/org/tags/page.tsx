"use client";

import { ListLayout } from "@/components/app/ListLayout";
import type { ColumnDef } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
import { ToneBadge } from "@/components/app/ToneBadge";
import { DataTable } from "@/components/data-table/DataTable";
import { GROUPS, TagForm } from "@/components/tags/TagForm";
import { api } from "@/lib/api";
import { type Tag, TAG_GROUP_LABEL } from "@/lib/types";

export default function TagsPage() {
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Tag | null>(null);
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((v) => v + 1);
  const columns = useMemo<ColumnDef<Tag, unknown>[]>(
    () => [
      { accessorKey: "name", header: "Tên tag", cell: ({ row }) => <span className="font-medium">{row.original.name}</span>, meta: { filter: { kind: "text" }, sort: "name" } },
      { accessorKey: "group", header: "Nhóm", cell: ({ row }) => <ToneBadge tone="blue">{TAG_GROUP_LABEL[row.original.group]}</ToneBadge>, meta: { filter: { kind: "select", options: GROUPS }, sort: "group" } },
    ],
    [],
  );
  return (
    <>
      <ListLayout header={<PageHeader title="Tags" description="Nhãn tự do, gắn nhiều nhãn cho một câu hỏi (phương pháp, kỹ năng, nguồn đề…)" />}>
        <DataTable
          path="/tags"
          columns={columns}
          getRowId={(t) => t.id}
          reloadKey={version}
          onAdd={() => setCreating(true)}
          addLabel="Thêm tag"
          onEdit={setEditing}
          onDelete={async (rows) => {
            for (const t of rows) await api(`/tags/${t.id}`, { method: "DELETE" });
          }}
          deleteLabel={(rows) => `Xóa ${rows.length} tag? Câu hỏi sẽ bỏ các tag này.`}
        />
      </ListLayout>
      <FormDialog open={creating} onOpenChange={setCreating} title="Thêm tag">
        <TagForm onDone={() => (setCreating(false), refresh())} />
      </FormDialog>
      <FormDialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)} title="Sửa tag">
        {editing && <TagForm tag={editing} onDone={() => (setEditing(null), refresh())} />}
      </FormDialog>
    </>
  );
}
