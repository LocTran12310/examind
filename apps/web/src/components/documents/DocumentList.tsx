"use client";

import Link from "next/link";
import { ToneBadge } from "@/components/app/ToneBadge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
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

export function DocumentList({ docs, taxonomy }: { docs: SourceDocument[]; taxonomy?: Taxonomy | null }) {
  return (
    <div className="rounded-lg border bg-card">
<Table>
      <TableHeader>
        <TableRow>
          <TableHead>File</TableHead>
          <TableHead>Thông tin</TableHead>
          <TableHead>Trạng thái</TableHead>
          <TableHead>Tải lên</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {docs.map((d) => (
          <TableRow key={d.id} data-testid={`doc-${d.filename}`}>
            <TableCell>
              <Link className="font-medium text-primary hover:underline" href={`/org/documents/${d.id}`}>
                {d.filename}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">{metaLabel(d, taxonomy)}</TableCell>
            <TableCell>
              <StatusBadge doc={d} />
            </TableCell>
            <TableCell>{new Date(d.created_at).toLocaleString("vi-VN")}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
</div>
  );
}
