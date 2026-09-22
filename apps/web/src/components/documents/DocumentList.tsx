"use client";

import type { ColumnDef } from "@tanstack/react-table";
import Link from "next/link";
import { ToneBadge } from "@/components/app/ToneBadge";
import { DOC_STATUS_LABEL, type SourceDocument, type Taxonomy } from "@/lib/types";

export function StatusBadge({ doc }: { doc: SourceDocument }) {
  const tone = doc.status === "parsed" ? "green" : doc.status === "failed" ? "red" : "amber";
  return (
    <ToneBadge tone={tone}>
      {DOC_STATUS_LABEL[doc.status]}
      {doc.status === "parsed" ? ` · ${doc.question_count} câu` : ""}
    </ToneBadge>
  );
}

export function metaLabel(doc: SourceDocument, taxonomy?: Taxonomy | null): string {
  const m = doc.meta;
  const subject = taxonomy?.subjects.find((s) => s.id === m.subject_id)?.name;
  const semester = taxonomy?.semesters.find((s) => s.code === m.semester_code)?.name;
  return [subject, m.grade ? `Lớp ${m.grade}` : null, semester, m.exam_kind, m.school_year, m.source_name].filter(Boolean).join(" · ");
}

export function documentColumns(taxonomy?: Taxonomy | null): ColumnDef<SourceDocument, unknown>[] {
  return [
    {
      accessorKey: "filename",
      header: "File",
      cell: ({ row }) => (
        <Link className="font-medium text-primary hover:underline" href={`/org/documents/${row.original.id}`} onClick={(e) => e.stopPropagation()}>
          {row.original.filename}
        </Link>
      ),
      meta: { filter: { kind: "text" }, sort: "filename" },
    },
    { id: "source_name", header: "Thông tin", cell: ({ row }) => <span className="text-muted-foreground">{metaLabel(row.original, taxonomy)}</span>, meta: { filter: { kind: "text", placeholder: "Nguồn đề…" } } },
    {
      accessorKey: "status",
      header: "Trạng thái",
      cell: ({ row }) => <StatusBadge doc={row.original} />,
      meta: { filter: { kind: "select", options: Object.entries(DOC_STATUS_LABEL).map(([value, label]) => ({ value, label })) }, sort: "status" },
    },
    { accessorKey: "created_at", header: "Tải lên", cell: ({ row }) => new Date(row.original.created_at).toLocaleString("vi-VN"), meta: { filter: { kind: "date" }, sort: "created_at" } },
  ];
}
