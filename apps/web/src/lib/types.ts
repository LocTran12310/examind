export type Role = "super_admin" | "org_admin" | "teacher" | "student";

export interface OrgRef {
  id: string;
  code: string;
  name: string;
}

export interface Me {
  id: string;
  username: string;
  full_name: string;
  role: Role;
  must_change_password: boolean;
  org: OrgRef;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export const ROLE_LABEL: Record<Role, string> = {
  super_admin: "Quản trị hệ thống",
  org_admin: "Quản trị trung tâm",
  teacher: "Giáo viên",
  student: "Học sinh",
};

export interface Org {
  id: string;
  code: string;
  name: string;
  status: "active" | "suspended";
  is_system: boolean;
  user_count: number;
  created_at: string;
  deleted_at: string | null;
}

export interface OrgCreated {
  org: Org;
  admin: { username: string; temp_password: string };
}

export interface User {
  id: string;
  username: string;
  full_name: string;
  email: string | null;
  role: Role;
  is_active: boolean;
  must_change_password: boolean;
  last_login_at: string | null;
  created_at: string;
  class_ids: string[];
}

export interface Credential {
  user_id: string;
  username: string;
  full_name: string;
  temp_password: string;
  role?: Role;
  class?: string;
}

export interface SchoolClass {
  id: string;
  name: string;
  grade: number | null;
  school_year: string;
  member_count: number;
  created_at: string;
}

export interface ClassDetail extends SchoolClass {
  members: User[];
}

export interface ImportRow {
  row: number;
  full_name: string;
  username: string;
  role: Role;
  class: string;
  errors: string[];
  generated_username: boolean;
}

export type QuestionType = "mcq" | "true_false" | "short_answer" | "essay";

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

export type LevelKind = "strand" | "topic" | "subtopic" | "type";

export const LEVEL_LABEL: Record<LevelKind, string> = {
  strand: "Mạch kiến thức",
  topic: "Chuyên đề",
  subtopic: "Chủ đề con",
  type: "Dạng bài",
};

export interface Topic {
  id: string;
  subject_id: string;
  parent_id: string | null;
  name: string;
  level_kind: LevelKind;
  grade: number | null;
  path: string;
  depth: number;
  sort: number;
  child_count: number;
}

export interface Taxonomy {
  subjects: { id: string; code: string; name: string }[];
  grades: { id: string; level: number; name: string }[];
  semesters: { id: string; code: string; name: string }[];
}

export interface Tag {
  id: string;
  group: "method" | "skill" | "source" | "custom";
  name: string;
}

export const TAG_GROUP_LABEL: Record<Tag["group"], string> = {
  method: "Phương pháp",
  skill: "Kỹ năng",
  source: "Nguồn đề",
  custom: "Khác",
};

export type DocStatus = "queued" | "processing" | "parsed" | "failed";

export interface DocumentMeta {
  subject_id?: string;
  grade?: number;
  semester_code?: string;
  exam_kind?: string;
  school_year?: string;
  source_name?: string;
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
  group?: string | null;
}

export const EXAM_KINDS = ["Giữa kỳ", "Cuối kỳ", "Khảo sát", "Thi thử", "Ôn tập", "Khác"];

export const DOC_STATUS_LABEL: Record<DocStatus, string> = {
  queued: "Đang chờ",
  processing: "Đang xử lý",
  parsed: "Đã tách",
  failed: "Lỗi",
};

export type Provider = "ollama" | "openai" | "anthropic";

export interface AiModel {
  id: string;
  name: string;
  provider: Provider;
  model: string;
  base_url: string | null;
  capabilities: ("text" | "vision")[];
  is_free: boolean;
  enabled: boolean;
  system: boolean;
  has_key: boolean;
  editable: boolean;
}

export const PROVIDER_LABEL: Record<Provider, string> = {
  ollama: "Ollama (máy chủ riêng)",
  openai: "Tương thích OpenAI",
  anthropic: "Anthropic",
};

export type QuestionStatus = "draft" | "auto_approved" | "needs_review" | "approved" | "rejected" | "duplicate";

export const STATUS_LABEL: Record<QuestionStatus, string> = {
  draft: "Nháp",
  auto_approved: "Tự duyệt",
  needs_review: "Cần xem",
  approved: "Đã duyệt",
  rejected: "Đã loại",
  duplicate: "Trùng",
};

export interface ReviewDocument {
  document: SourceDocument;
  total: number;
  counts: Record<"auto_approved" | "needs_review" | "approved" | "rejected" | "duplicate", number>;
  spot_pending: number;
  progress: number;
  assigned_to: string | null;
  assigned_name: string | null;
}

export const DIFFICULTY_LABEL: Record<string, string> = { nb: "Nhận biết", th: "Thông hiểu", vd: "Vận dụng", vdc: "Vận dụng cao" };
export const TYPE_LABEL: Record<QuestionType, string> = { mcq: "Trắc nghiệm", true_false: "Đúng/Sai", short_answer: "Trả lời ngắn", essay: "Tự luận" };

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
