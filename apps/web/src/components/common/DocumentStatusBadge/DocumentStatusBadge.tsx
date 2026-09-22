"use client";

import { ToneBadge } from "@/components/app/ToneBadge";
import { DOC_STATUS_LABEL } from "@/constants/document.constant";
import type { SourceDocument } from "@/interfaces/document.interface";

/** Status of an uploaded document ("Đã tách · 40 câu"). */
export function DocumentStatusBadge({ doc }: { doc: SourceDocument }) {
  const tone = doc.status === "parsed" ? "green" : doc.status === "failed" ? "red" : "amber";
  return (
    <ToneBadge tone={tone}>
      {DOC_STATUS_LABEL[doc.status]}
      {doc.status === "parsed" ? ` · ${doc.question_count} câu` : ""}
    </ToneBadge>
  );
}
