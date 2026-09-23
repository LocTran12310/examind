import type { SourceDocument } from "@/interfaces/document.interface";

/** Where a document stands (review-ux ADR-01): derived from the counts, filterable and sortable. */
export type ReviewState = "pending" | "in_progress" | "done";

/** `state` of `POST /review/documents/{id}/questions/search`; the server defaults to "pending". */
export type DocumentQuestionState = "pending" | "approved" | "rejected" | "duplicate" | "all";

/** A document with its review progress (a row of the review list). */
export interface ReviewDocument {
  document: SourceDocument;
  total: number;
  counts: Record<"auto_approved" | "needs_review" | "approved" | "rejected" | "duplicate" | "flagged", number>;
  spot_pending: number;
  progress: number;
  /** what the list shows; the counts keep the breakdown behind it */
  review_state: ReviewState;
  /** questions still waiting for a human */
  pending: number;
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
