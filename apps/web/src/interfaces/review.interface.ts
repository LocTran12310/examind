import type { SourceDocument } from "@/interfaces/document.interface";

/** A document with its review progress (a row of the review list). */
export interface ReviewDocument {
  document: SourceDocument;
  total: number;
  counts: Record<"auto_approved" | "needs_review" | "approved" | "rejected" | "duplicate" | "flagged", number>;
  spot_pending: number;
  progress: number;
  assigned_to: string | null;
  assigned_name: string | null;
}

export type ReviewAction = "approve" | "reject" | "skip";

/** Answer of POST /review/documents/{id}/answer-key. */
export interface AnswerKeyResult {
  applied: number;
  approved: number;
  unmatched: number[];
}

export interface ApproveConfidentResult {
  approved: number;
}
