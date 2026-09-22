export type DocStatus = "queued" | "processing" | "parsed" | "failed";

/** What the exam header said (official-exam-ingestion AC-09); suggestions only. */
export interface DetectedHeader {
  issuer?: string;
  province?: string;
  school_year?: string;
  subject_name?: string;
  grade?: number;
  exam_kind?: string;
  attempt?: number;
  duration?: number;
}

export interface DocumentMeta {
  subject_id?: string;
  grade?: number;
  semester_code?: string;
  exam_kind?: string;
  school_year?: string;
  source_name?: string;
  detected?: DetectedHeader;
}

export interface ProcessingConfig {
  split_mode: "rule" | "rule_ai" | "ai";
  ocr: "auto" | "tesseract" | "vision";
  split_models: string[];
  tag_model: string | null;
  vision_model: string | null;
  threshold: number;
}

export interface SourceDocument {
  id: string;
  filename: string;
  mime: string;
  size: number;
  status: DocStatus;
  error: string | null;
  meta: DocumentMeta;
  processing_config: ProcessingConfig;
  page_count: number | null;
  question_count: number;
  log: { step: string; ms?: number; items?: string[]; [k: string]: unknown }[];
  created_at: string;
  finished_at: string | null;
}

/** A document already uploaded, as the duplicate check describes it. */
export interface DocumentBrief {
  id: string;
  filename: string;
  status: string;
  question_count: number;
  created_at: string;
}

/** Answer of `POST /documents/check`, one per probed file (same order). */
export interface DuplicateCheck {
  name?: string;
  same_file: DocumentBrief | null;
  same_name: DocumentBrief[];
}

export type DuplicateChoice = "skip" | "replace" | "keep_both";

/** Answer of `POST /documents`. */
export interface UploadResult {
  document: SourceDocument;
  duplicate: boolean;
  action?: string;
}

/** Answer of `POST /documents/{id}/exam`. */
export interface DocumentExamResult {
  exam_id: string;
  added: number;
  skipped: number;
}
