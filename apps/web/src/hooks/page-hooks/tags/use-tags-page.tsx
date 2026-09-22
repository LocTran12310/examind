import type { ColumnDef } from "@tanstack/react-table";
import { useMemo, useState } from "react";
import { ToneBadge } from "@/components/common/ToneBadge/ToneBadge";
import { SHARED_SUBJECT, TAG_GROUP_LABEL, TAG_GROUP_OPTIONS } from "@/constants/tag.constant";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { useDeleteTagsMutation } from "@/hooks/react-query/use-query-tag";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import type { Tag } from "@/interfaces/tag.interface";

/** Columns, dialogs and delete of the Tags page. */
export function useTagsPage() {
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<Tag | null>(null);
  const { data: taxonomy } = useTaxonomyQuery();
  const remove = useDeleteTagsMutation();
  const chosen = useTableQuery().get("subject_id");
  const columns = useMemo<ColumnDef<Tag, unknown>[]>(
    () => [
      { accessorKey: "name", header: "Tên tag", cell: ({ row }) => <span className="font-medium">{row.original.name}</span>, meta: { filter: { kind: "text" }, sort: "name" } },
      { accessorKey: "group", header: "Nhóm", cell: ({ row }) => <ToneBadge tone="blue">{TAG_GROUP_LABEL[row.original.group]}</ToneBadge>, meta: { filter: { kind: "select", options: TAG_GROUP_OPTIONS }, sort: "group" } },
      {
        id: "subject_id",
        header: "Môn",
        cell: ({ row }) => {
          const s = taxonomy?.subjects.find((x) => x.id === row.original.subject_id);
          return s ? s.name : <span className="text-muted-foreground">Dùng chung</span>;
        },
        meta: { filter: { kind: "select", param: true, options: [{ value: SHARED_SUBJECT, label: "Dùng chung" }, ...(taxonomy?.subjects ?? []).map((x) => ({ value: x.id, label: x.name }))] } },
      },
    ],
    [taxonomy],
  );
  // the subject column is a resource parameter: exactly that subject's tags (or the shared ones)
  const params = useMemo(() => ({ include_shared: false }), []);
  return {
    columns,
    params,
    creating,
    setCreating,
    editing,
    setEditing,
    newTagSubject: chosen && chosen !== SHARED_SUBJECT ? chosen : null,
    removeTags: (rows: Tag[]) => remove.mutateAsync(rows.map((t) => t.id)),
  };
}
