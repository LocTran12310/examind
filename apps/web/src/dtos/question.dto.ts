import type { SearchBody } from "@/dtos/search.dto";
import type { QuestionOption, QuestionType } from "@/interfaces/question.interface";

/** Body of `POST /questions/search` and `/questions/facets`: the common search body plus the bank parameters. */
export interface QuestionSearchBody extends SearchBody {
  /** false = only questions with no topic (the tagging queue, topic-coverage AC-01) */
  has_topic?: boolean;
  /** subject id or "none" */
  subject_id?: string;
  grade?: number;
  semester_code?: string;
  exam_kind?: string;
  type?: string;
  difficulty?: string;
  /** default "usable"; "all" or one status */
  status?: string;
  topic_id?: string;
  topic_ids?: string[];
  tag_ids?: string[];
  document_id?: string;
  school_year?: string;
}

/** Create (`POST /questions`) and full edit (`PATCH /questions/{id}`) of a question. */
export interface QuestionBody {
  type: QuestionType;
  stem: string;
  options: QuestionOption[];
  answer: Record<string, unknown>;
  solution: string;
  difficulty: string;
  grade: number;
  subject_id: string | null;
  primary_topic_id: string | null;
  tag_ids: string[];
  topic_ids: string[];
}

export type UpdateQuestionBody = Partial<QuestionBody>;

/** `POST /questions/suggest-topics`: at most 50 questions per request. */
export interface SuggestTopicsBody {
  question_ids: string[];
  /** ask the tagging model for what the rules could not place; slow (tens of seconds a page) */
  use_model?: boolean;
}

/** `POST /questions/bulk`: the same change on every question. */
export interface BulkQuestionsBody {
  ids: string[];
  set: Record<string, unknown>;
}

/** `POST /questions/bulk/topics`: one topic per question, at most 200 pairs (pickers-builder ADR-02). */
export interface BulkTopicsBody {
  pairs: { question_id: string; topic_id: string }[];
}

/** `POST /questions/bulk/undo`: every question of that batch goes back to what it was (bulk-safety AC-01). */
export interface UndoBatchBody {
  batch_id: string;
}
