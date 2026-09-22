// moved to interfaces/ and constants/ (architecture-refactor); re-exported for the screens not moved yet
export type { BankFacets, FlagEvidence, ParsedQuestion, Question, QuestionOption, QuestionStatus, QuestionType } from "@/interfaces/question.interface";
export type { DetectedHeader, DocStatus, DocumentMeta, ProcessingConfig, SourceDocument } from "@/interfaces/document.interface";
export type { ReviewDocument } from "@/interfaces/review.interface";
export { DIFFICULTY_LABEL, STATUS_LABEL, TYPE_LABEL } from "@/constants/question.constant";
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

export type { BlueprintResult, BlueprintRow, BlueprintShortfall, Exam, ExamQuestion, ExamSettings } from "@/interfaces/exam.interface";
export type { Assignment, AssignmentReport, AttemptBrief, MyAssignment } from "@/interfaces/assignment.interface";
export type { AttemptQuestion, AttemptResult, AttemptView, ResultQuestion } from "@/interfaces/attempt.interface";
export type { ResultsPolicy } from "@/types/assignment.type";

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

