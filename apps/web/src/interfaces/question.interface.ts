export type QuestionType = "mcq" | "true_false" | "short_answer" | "essay";

/** Which rule proposed a topic: a keyword cue, a neighbour already tagged, or the tagging model
 *  (topic-coverage A-01, ADR-04). */
export type SuggestionSource = "keyword" | "similar" | "ai";

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

/** One option of a multiple-choice question and how many of the graded answers chose it. */
export interface QuestionOptionStat {
  label: string;
  chosen: number;
  ratio: number;
  is_key: boolean;
}

/** GET /questions/{id}/stats — what the graded answers say about a question (learning-telemetry ADR-03).
 *  Under ten answers `enough_data` is false and every number is null. */
export interface QuestionStats {
  observations: number;
  enough_data: boolean;
  correct_ratio: number | null;
  first_attempt_ratio: number | null;
  discrimination: number | null;
  median_seconds: number | null;
  options: QuestionOptionStat[];
}

/** One candidate of `POST /questions/suggest-topics` (topic-coverage ADR-01): computed per request,
 *  never stored, at most three per question. `path` is the chain the API wrote it as. */
export interface TopicSuggestion {
  topic_id: string;
  name: string;
  path: string;
  score: number;
  source: SuggestionSource;
}

/** Answer of `POST /questions/suggest-topics`: candidates per question id. */
export interface TopicSuggestions {
  suggestions: Record<string, TopicSuggestion[]>;
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
  /** questions with no topic per source document id (topic-coverage AC-05) */
  untagged_documents?: Record<string, number>;
}

export interface BulkResult {
  updated: number;
}

/** Why `POST /questions/bulk/topics` left a pair alone (pickers-builder ADR-02). */
export type BulkTopicSkipReason = "unknown_question" | "other_org" | "unknown_topic" | "no_subject" | "subject_mismatch";

export interface BulkTopicSkip {
  question_id: string;
  topic_id: string;
  reason: BulkTopicSkipReason;
  message: string;
}

/** Answer of `POST /questions/bulk/topics`: what took its topic and what did not. */
export interface BulkTopicsResult {
  updated: number;
  skipped: BulkTopicSkip[];
}

/** One question a bulk subject cannot move: its topic belongs to another subject
 *  (422 `subject_topic_conflict`, `details.fields.conflicts`; pickers-builder A-04). */
export interface SubjectTopicConflict {
  question_id: string;
  topic_id: string;
  topic_name: string;
}
