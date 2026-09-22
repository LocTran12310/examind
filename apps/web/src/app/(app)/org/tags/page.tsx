"use client";

import { ListLayout } from "@/components/app/ListLayout";
import type { ColumnDef } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
import { ToneBadge } from "@/components/app/ToneBadge";
import { DataTable } from "@/components/data-table/DataTable";
import { GROUPS, TagForm } from "@/components/tags/TagForm";
import { useTableQuery } from "@/components/data-table/useTableQuery";
import { api } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import { type Tag, TAG_GROUP_LABEL, type Taxonomy } from "@/lib/types";

export default function TagsPage() {
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Tag | null>(null);
  const [version, setVersion] = useState(0);
  const refresh = () => setVersion((v) => v + 1);
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  const chosen = useTableQuery().get("subject_id");
  const columns = useMemo<ColumnDef<Tag, unknown>[]>(
    () => [
      { accessorKey: "name", header: "Tên tag", cell: ({ row }) => <span className="font-medium">{row.original.name}</span>, meta: { filter: { kind: "text" }, sort: "name" } },
      { accessorKey: "group", header: "Nhóm", cell: ({ row }) => <ToneBadge tone="blue">{TAG_GROUP_LABEL[row.original.group]}</ToneBadge>, meta: { filter: { kind: "select", options: GROUPS }, sort: "group" } },
      {
        id: "subject_id",
        header: "Môn",
        cell: ({ row }) => {
          const s = taxonomy?.subjects.find((x) => x.id === row.original.subject_id);
          return s ? s.name : <span className="text-muted-foreground">Dùng chung</span>;
        },
        meta: { filter: { kind: "select", options: [{ value: "shared", label: "Dùng chung" }, ...(taxonomy?.subjects ?? []).map((x) => ({ value: x.id, label: x.name }))] } },
      },
    ],
    [taxonomy],
  );
  return (
    <>
      <ListLayout header={<PageHeader title="Tags" description="Nhãn tự do, gắn nhiều nhãn cho một câu hỏi (phương pháp, kỹ năng, nguồn đề…)" />}>
        <DataTable
          path="/tags"
          params={{ include_shared: "false" }}
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
        <TagForm subjectId={chosen && chosen !== "shared" ? chosen : null} onDone={() => (setCreating(false), refresh())} />
      </FormDialog>
      <FormDialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)} title="Sửa tag">
        {editing && <TagForm tag={editing} onDone={() => (setEditing(null), refresh())} />}
      </FormDialog>
    </>
  );
}
