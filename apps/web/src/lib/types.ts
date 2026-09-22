// moved to interfaces/ and constants/ (architecture-refactor); re-exported for the screens not moved yet
export type { BankFacets, FlagEvidence, ParsedQuestion, Question, QuestionOption, QuestionStatus, QuestionType } from "@/interfaces/question.interface";
export type { DetectedHeader, DocStatus, DocumentMeta, ProcessingConfig, SourceDocument } from "@/interfaces/document.interface";
export type { ReviewDocument } from "@/interfaces/review.interface";
export { DIFFICULTY_LABEL, STATUS_LABEL, TYPE_LABEL } from "@/constants/question.constant";
import type { ParsedQuestion, Question, QuestionType } from "@/interfaces/question.interface";
export type { Tag, TagGroup } from "@/interfaces/tag.interface";
export type { Taxonomy } from "@/interfaces/taxonomy.interface";
export { TAG_GROUP_LABEL } from "@/constants/tag.constant";
export type { ClassDetail, SchoolClass } from "@/interfaces/class.interface";
export type { SchoolTerm, SchoolYear, YearStatus } from "@/interfaces/school-year.interface";
export type { GradeRow, SchoolLevel, Structure, TreeClass, TreeGrade, TreeLevel } from "@/interfaces/structure.interface";
export type { LevelKind, Topic } from "@/interfaces/topic.interface";
export { LEVEL_LABEL } from "@/constants/topic.constant";
export { YEAR_STATUS_LABEL } from "@/constants/school-year.constant";
import type { Tag } from "@/interfaces/tag.interface";

export type { Me, MyOrg, OrgRef, Role } from "@/interfaces/auth.interface";
export type { Credential, ImportPreview, ImportRow, User } from "@/interfaces/user.interface";
export type { Account, Membership, Org, OrgCreated } from "@/interfaces/org.interface";
export { ROLE_LABEL } from "@/constants/role.constant";

/** The old list answer (`GET` lists not moved to search yet). */
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export const EXAM_KINDS = ["Giữa kỳ", "Cuối kỳ", "Khảo sát", "Thi thử", "Ôn tập", "Khác"];

export { DOC_STATUS_LABEL } from "@/constants/document.constant";
export type { AiModel, Provider } from "@/interfaces/ai-model.interface";
export { PROVIDER_LABEL } from "@/constants/ai-model.constant";

export interface BlueprintRow {
  topic_id?: string | null;
  tag_id?: string | null;
  type: QuestionType;
  difficulty?: string | null;
  count: number;
}

export interface ExamQuestion extends ParsedQuestion {
  position: number;
  section: string;
  points: number;
  row: number | null;
}

export interface Exam {
  id: string;
  title: string;
  subject_id: string | null;
  grade: number | null;
  description: string;
  settings: { points_by_type: Record<QuestionType, number>; scale_to: number };
  blueprint: BlueprintRow[];
  source: string;
  question_count: number;
  total_points: number;
  created_at: string;
  questions: ExamQuestion[];
}

export type ResultsPolicy = "after_submit" | "after_close" | "never";

export interface Assignment {
  id: string;
  exam_id: string;
  title: string;
  open_at: string;
  close_at: string;
  duration_minutes: number;
  max_attempts: number;
  shuffle_questions: boolean;
  shuffle_options: boolean;
  results_policy: ResultsPolicy;
  students: number;
  submitted: number;
  classes: string[];
}

export interface AttemptBrief {
  id: string;
  status: "in_progress" | "submitted";
  started_at: string;
  deadline_at: string;
  submitted_at: string | null;
  score: number | null;
  max_score: number | null;
  score10: number | null;
  needs_grading: boolean;
}

export interface MyAssignment {
  assignment: Assignment;
  state: "open" | "upcoming" | "closed";
  attempts: AttemptBrief[];
  attempts_left: number;
}

export interface AttemptQuestion extends Question {
  number: number;
  section: string;
  points: number;
  response: Record<string, unknown> | null;
}

export interface AttemptView {
  id: string;
  title: string;
  status: "in_progress" | "submitted";
  started_at: string;
  deadline_at: string;
  submitted_at: string | null;
  server_now: string;
  tab_switches: number;
  student: { id: string; full_name: string; username: string };
  assignment_id: string | null;
  questions: AttemptQuestion[];
}

export interface ResultQuestion extends ParsedQuestion {
  section: string;
  response: Record<string, unknown> | null;
  points: number | null;
  max_points: number;
  is_correct: boolean | null;
  comment: string | null;
}

export interface AttemptResult {
  id: string;
  title: string;
  status: string;
  submitted_at: string | null;
  needs_grading: boolean;
  tab_switches: number;
  hidden: boolean;
  reason?: string;
  available_at?: string | null;
  score?: number;
  max_score?: number;
  score10?: number;
  questions?: ResultQuestion[];
  sections?: { section: string; points: number; max_points: number }[];
  topics?: { topic: string; points: number; max_points: number; count: number }[];
}

export interface TopicStat {
  id: string | null;
  parent_id: string | null;
  name: string;
  path: string;
  depth: number;
  level_kind: string;
  points: number;
  max_points: number;
  answered: number;
  ratio: number | null;
}

export interface GroupStat {
  key: string;
  label: string;
  points: number;
  max_points: number;
  answered: number;
  ratio: number | null;
}

export interface AssignmentReport {
  assignment_id: string;
  title: string;
  submitted: number;
  total_students: number;
  average: number | null;
  distribution: { from: number; to: number; count: number }[];
  students: { student_id: string; full_name: string; username: string; status: string; attempt_id: string | null; score10: number | null; needs_grading: boolean; tab_switches: number }[];
  questions: { question_id: string; position: number; type: QuestionType; stem: string; answered: number; ratio: number | null; top_wrong: { label: string; count: number } | null }[];
}

export interface MasteryRow {
  topic_id: string;
  parent_id: string | null;
  name: string;
  path: string;
  depth: number;
  mastery: number | null;
  answers: number;
  tracked: boolean;
}

export interface ClassOverviewRow {
  student_id: string;
  full_name: string;
  username: string;
  weakest: { name: string; mastery: number; answers: number }[];
  review: { assignment_id: string; title: string; status: string } | null;
}

export interface PracticeItem {
  attempt_id: string;
  title: string;
  status: "in_progress" | "submitted";
  started_at: string;
  submitted_at: string | null;
  score10: number | null;
  note: string | null;
  groups: { reason: string; topic: string | null; count: number }[];
}

export interface AuditEntry {
  id: string;
  created_at: string;
  organization_id: string;
  organization_code: string | null;
  actor_id: string | null;
  actor_name: string | null;
  action: string;
  target_type: string;
  target_id: string | null;
  data: Record<string, unknown>;
}

