import type { DetectedHeader, SourceDocument } from "@/interfaces/document.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import { periodLabel } from "@/lib/exam-period";

/** Môn · Lớp · Đợt · Năm học · Nguồn đề of a document. */
export function metaLabel(doc: SourceDocument, taxonomy?: Taxonomy | null): string {
  const m = doc.meta;
  const subject = taxonomy?.subjects.find((s) => s.id === m.subject_id)?.name;
  return [subject, m.grade ? `Lớp ${m.grade}` : null, periodLabel(m.semester_code, m.exam_kind), m.school_year, m.source_name].filter(Boolean).join(" · ");
}

/** What the exam header said, in one line. */
export function detectedLabel(d?: DetectedHeader): string {
  if (!d) return "";
  const kind = d.exam_kind ? `${d.exam_kind}${d.attempt ? ` lần ${d.attempt}` : ""}` : null;
  return [d.issuer, d.school_year, d.subject_name, d.grade ? `Lớp ${d.grade}` : null, kind, d.duration ? `${d.duration} phút` : null].filter(Boolean).join(" · ");
}
