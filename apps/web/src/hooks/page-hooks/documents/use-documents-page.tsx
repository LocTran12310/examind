import type { ColumnDef } from "@tanstack/react-table";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { DocumentStatusBadge } from "@/components/common/DocumentStatusBadge/DocumentStatusBadge";
import { DOC_STATUS_OPTIONS } from "@/constants/document.constant";
import { useAiModelOptionsQuery } from "@/hooks/react-query/use-query-ai-model";
import { useDeleteDocumentsMutation } from "@/hooks/react-query/use-query-document";
import { useIngestionSettingsQuery } from "@/hooks/react-query/use-query-ingestion-settings";
import { useTaxonomyQuery } from "@/hooks/react-query/use-query-taxonomy";
import type { ProcessingConfig, SourceDocument } from "@/interfaces/document.interface";
import { formatDateTime } from "@/lib/common/datetime";
import { metaLabel } from "@/lib/common/document-label";

/** Some document still waits for the worker: keep the list refreshing. */
export const inFlight = (docs: SourceDocument[]) => docs.some((d) => d.status === "queued" || d.status === "processing");

// columns that do not depend on the taxonomy keep their identity, so its arrival does not remount their cells
const FILE_COLUMN: ColumnDef<SourceDocument, unknown> = {
  accessorKey: "filename",
  header: "File",
  cell: ({ row }) => (
    <Link
      className="block max-w-[22rem] truncate font-medium text-primary hover:underline xl:max-w-[32rem]"
      title={row.original.filename}
      href={`/org/documents/${row.original.id}`}
      onClick={(e) => e.stopPropagation()}
    >
      {row.original.filename}
    </Link>
  ),
  meta: { filter: { kind: "text" }, sort: "filename" },
};

const STATUS_COLUMN: ColumnDef<SourceDocument, unknown> = {
  accessorKey: "status",
  header: "Trạng thái",
  cell: ({ row }) => <DocumentStatusBadge doc={row.original} />,
  meta: { filter: { kind: "select", options: DOC_STATUS_OPTIONS }, sort: "status" },
};

const CREATED_COLUMN: ColumnDef<SourceDocument, unknown> = {
  accessorKey: "created_at",
  header: "Tải lên",
  cell: ({ row }) => formatDateTime(row.original.created_at),
  meta: { filter: { kind: "date" }, sort: "created_at" },
};

/** Columns, delete and the upload dialog (with the org's default processing config) of the documents page. */
export function useDocumentsPage() {
  const router = useRouter();
  const { data: taxonomy } = useTaxonomyQuery();
  const { data: defaults } = useIngestionSettingsQuery();
  const { data: models } = useAiModelOptionsQuery();
  const remove = useDeleteDocumentsMutation();
  const [edited, setConfig] = useState<ProcessingConfig | null>(null);
  const [uploading, setUploading] = useState(false);
  const config = edited ?? defaults ?? null;

  const columns = useMemo<ColumnDef<SourceDocument, unknown>[]>(
    () => [
      FILE_COLUMN,
      {
        id: "source_name",
        header: "Thông tin",
        cell: ({ row }) => <span className="line-clamp-2 min-w-48 text-muted-foreground">{metaLabel(row.original, taxonomy)}</span>,
        meta: { filter: { kind: "text", placeholder: "Nguồn đề…" } },
      },
      STATUS_COLUMN,
      CREATED_COLUMN,
    ],
    [taxonomy],
  );

  return {
    columns,
    taxonomy,
    models: models ?? [],
    config,
    setConfig,
    uploading,
    setUploading,
    open: (d: SourceDocument) => router.push(`/org/documents/${d.id}`),
    removeDocuments: (rows: SourceDocument[]) => remove.mutateAsync(rows.map((d) => d.id)),
    // one file: open it; a batch: stay here, the list (refreshed by the upload) shows every file's progress
    uploaded: (done: { doc: SourceDocument; duplicate: boolean }[]) => {
      if (done.length === 1) router.push(`/org/documents/${done[0].doc.id}${done[0].duplicate ? "?dup=1" : ""}`);
    },
  };
}
