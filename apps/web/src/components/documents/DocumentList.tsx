"use client";

import Link from "next/link";
import { Badge, Table, td, th } from "@/components/ui";
import { DOC_STATUS_LABEL, type SourceDocument, type Taxonomy } from "@/lib/types";

export function StatusBadge({ doc }: { doc: SourceDocument }) {
  const tone = doc.status === "parsed" ? "green" : doc.status === "failed" ? "red" : "amber";
  return (
    <Badge tone={tone}>
      {DOC_STATUS_LABEL[doc.status]}
      {doc.status === "parsed" ? ` · ${doc.question_count} câu` : ""}
    </Badge>
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
    <Table>
      <thead className="bg-gray-50">
        <tr>
          <th className={th}>File</th>
          <th className={th}>Thông tin</th>
          <th className={th}>Trạng thái</th>
          <th className={th}>Tải lên</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {docs.map((d) => (
          <tr key={d.id} data-testid={`doc-${d.filename}`}>
            <td className={td}>
              <Link className="font-medium text-brand-700 hover:underline" href={`/org/documents/${d.id}`}>
                {d.filename}
              </Link>
            </td>
            <td className={`${td} text-gray-600`}>{metaLabel(d, taxonomy)}</td>
            <td className={td}>
              <StatusBadge doc={d} />
            </td>
            <td className={td}>{new Date(d.created_at).toLocaleString("vi-VN")}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
