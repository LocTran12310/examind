export type QuestionType = "mcq" | "true_false" | "short_answer" | "essay";

export type QuestionStatus = "draft" | "auto_approved" | "needs_review" | "approved" | "rejected" | "duplicate" | "flagged";

export interface QuestionOption {
  label: string;
  content: string;
  is_true?: boolean | null;
}

export interface Question {
  id: string;
  type: QuestionType;
  stem: string;
  options: QuestionOption[];
  answer: { key?: string; value?: string; text?: string; [k: string]: unknown } | null;
  solution: string;
  difficulty: string | null;
  grade: number | null;
  status: string;
}

/** Why a key is suspected wrong (statistics of the answers). */
export interface FlagEvidence {
  reason: string;
  answers: number;
  key: string;
  overall_correct: number;
  top_quartile: { size: number; choice: string; share: number };
  option_counts: Record<string, number>;
  dismissed?: boolean;
}

/** A question of the bank (parsed from a document or written by hand). */
export interface ParsedQuestion extends Question {
  number: number | null;
  part: string | null;
  confidence: number | null;
  issues: string[];
  parse_method: string | null;
  parse_model: string | null;
  answer_source: string | null;
  subject_id: string | null;
  semester_code: string | null;
  exam_kind: string | null;
  topics: { id: string; name: string; is_primary: boolean; source: string; score: number | null }[];
  tags: { id: string; group: string; name: string }[];
  page?: number | null;
  spot_check?: boolean;
  duplicate_of?: string | null;
  source_document_id?: string | null;
  /** review queue: why the question is in the queue */
  group?: string | null;
  flag_evidence?: FlagEvidence | null;
}

/** POST /questions/facets — counts per value; each facet ignores its own filter (subject-scoped-bank ADR-02). */
export interface BankFacets {
  subjects: Record<string, number>; // subject id or "none"
  topics: Record<string, number>; // subtree totals
  types: Record<string, number>;
  difficulties: Record<string, number>;
  grades: Record<string, number>;
  periods: Record<string, number>; // "hk1|Giữa kỳ"
  school_years: Record<string, number>;
  tags: Record<string, number>;
}

export interface BulkResult {
  updated: number;
}
