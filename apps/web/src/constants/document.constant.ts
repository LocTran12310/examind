import type { DocStatus } from "@/interfaces/document.interface";

export const DOC_STATUS_LABEL: Record<DocStatus, string> = {
  queued: "Đang chờ",
  processing: "Đang xử lý",
  parsed: "Đã tách",
  failed: "Lỗi",
};

export const DOC_STATUS_OPTIONS = Object.entries(DOC_STATUS_LABEL).map(([value, label]) => ({ value, label }));

/** Files the upload accepts. */
export const UPLOAD_ACCEPT = ".docx,.pdf,.png,.jpg,.jpeg";
export const UPLOAD_ACCEPTED = /\.(docx|pdf|png|jpe?g)$/i;

/** Confidence from which a question is approved by itself, when the document has no config. */
export const DEFAULT_THRESHOLD = 0.85;

/** ms between refreshes while a document is still being processed */
export const PROCESSING_POLL_MS = 2000;
