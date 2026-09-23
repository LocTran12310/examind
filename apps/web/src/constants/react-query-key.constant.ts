/** Query keys, one group per resource (architecture-refactor ADR-06). The first element is the resource,
 *  so invalidating `<ENTITY>_KEYS.ALL` refreshes every query of that resource. */
export const TAG_KEYS = {
  ALL: ["tags"] as const,
  SEARCH: (body: unknown) => ["tags", "search", body] as const,
  OPTIONS: (subject: string | null) => ["tags", "options", subject] as const,
};

export const TAXONOMY_KEYS = {
  ALL: ["taxonomy"] as const,
};

export const TOPIC_KEYS = {
  ALL: ["topics"] as const,
  LIST: (subjectId: string | null) => ["topics", "list", subjectId] as const,
};

export const SCHOOL_YEAR_KEYS = {
  ALL: ["school-years"] as const,
  SEARCH: (body: unknown) => ["school-years", "search", body] as const,
  SEARCH_ALL: ["school-years", "search"] as const,
  OPTIONS: ["school-years", "options"] as const,
  ROLLOVER: (id: string, targetCode: string | null) => ["school-years", "rollover", id, targetCode] as const,
};

export const CLASS_KEYS = {
  ALL: ["classes"] as const,
  SEARCH: (body: unknown) => ["classes", "search", body] as const,
  OPTIONS: (yearId: string | null) => ["classes", "options", yearId] as const,
  DETAIL: (id: string) => ["classes", "detail", id] as const,
  OVERVIEW: (id: string) => ["classes", "overview", id] as const,
};

export const STRUCTURE_KEYS = {
  ALL: ["structure"] as const,
  TREE: (yearId: string | null) => ["structure", "tree", yearId] as const,
};

export const SCHOOL_LEVEL_KEYS = {
  ALL: ["school-levels"] as const,
  SEARCH: (body: unknown) => ["school-levels", "search", body] as const,
  OPTIONS: ["school-levels", "options"] as const,
};

export const GRADE_KEYS = {
  ALL: ["grades"] as const,
  SEARCH: (body: unknown) => ["grades", "search", body] as const,
  OPTIONS: ["grades", "options"] as const,
};

export const STUDENT_KEYS = {
  ALL: ["students"] as const,
  RECORD: (id: string) => ["students", "record", id] as const,
};

/** The signed-in user's own data (the orgs of the header selector). */
export const ME_KEYS = {
  ALL: ["me"] as const,
  ORGS: ["me", "orgs"] as const,
};

export const USER_KEYS = {
  ALL: ["users"] as const,
  SEARCH: (body: unknown) => ["users", "search", body] as const,
  OPTIONS: (body: unknown) => ["users", "options", body] as const,
};

export const ORG_KEYS = {
  ALL: ["orgs"] as const,
  SEARCH: (body: unknown) => ["orgs", "search", body] as const,
  OPTIONS: ["orgs", "options"] as const,
};

export const ACCOUNT_KEYS = {
  ALL: ["accounts"] as const,
  SEARCH: (body: unknown) => ["accounts", "search", body] as const,
};

/** Both sides of a membership (an org's members, an account's orgs) share one resource. */
export const MEMBERSHIP_KEYS = {
  ALL: ["memberships"] as const,
  SEARCH: (body: unknown) => ["memberships", "search", body] as const,
};

/** Questions of the bank; review screens show questions too, so their mutations refresh both. */
export const QUESTION_KEYS = {
  ALL: ["questions"] as const,
  SEARCH: (body: unknown) => ["questions", "search", body] as const,
  FACETS: (body: unknown) => ["questions", "facets", body] as const,
  /** questions per topic of one subject — what a picker shows beside a topic (pickers-builder ADR-01) */
  TOPIC_COUNTS: (subjectId: string) => ["questions", "facets", "topics", subjectId] as const,
  DETAIL: (id: string) => ["questions", "detail", id] as const,
  STATS: (id: string) => ["questions", "stats", id] as const,
  SUGGESTIONS: (ids: readonly string[], useModel: boolean) => ["questions", "suggestions", useModel, ids] as const,
  DEMO: ["questions", "demo"] as const,
};

/** "Thay đổi gần đây": every change of the bank lands here, so every bank mutation refreshes it (bulk-safety AC-04). */
export const QUESTION_EVENT_KEYS = {
  ALL: ["question-events"] as const,
  SEARCH: (body: unknown) => ["question-events", "search", body] as const,
};

export const REVIEW_KEYS = {
  ALL: ["review"] as const,
  DOCUMENTS: (body: unknown) => ["review", "documents", body] as const,
  FLAGGED: (body: unknown) => ["review", "flagged", body] as const,
  DOCUMENT: (id: string) => ["review", "document", id] as const,
  QUEUE: (id: string) => ["review", "queue", id] as const,
  QUESTIONS: (id: string, body: unknown) => ["review", "questions", id, body] as const,
};

/** Uploaded source documents; parsing creates questions, so their mutations refresh the bank and review too. */
export const DOCUMENT_KEYS = {
  ALL: ["documents"] as const,
  SEARCH: (body: unknown) => ["documents", "search", body] as const,
  DETAIL: (id: string) => ["documents", "detail", id] as const,
  QUESTIONS: (id: string) => ["documents", "questions", id] as const,
};

export const AI_MODEL_KEYS = {
  ALL: ["ai-models"] as const,
  SEARCH: (body: unknown) => ["ai-models", "search", body] as const,
  OPTIONS: ["ai-models", "options"] as const,
};

export const INGESTION_SETTINGS_KEYS = {
  ALL: ["ingestion-settings"] as const,
};

/** Exams and their questions; the list never embeds questions. */
export const EXAM_KEYS = {
  ALL: ["exams"] as const,
  SEARCH: (body: unknown) => ["exams", "search", body] as const,
  DETAIL: (id: string) => ["exams", "detail", id] as const,
  QUESTIONS: (id: string, body: unknown) => ["exams", "questions", id, body] as const,
};

/** Assignments (exams given to classes), their reports and the student's own list. */
export const ASSIGNMENT_KEYS = {
  ALL: ["assignments"] as const,
  SEARCH: (body: unknown) => ["assignments", "search", body] as const,
  REPORT: (id: string) => ["assignments", "report", id] as const,
  MINE: ["assignments", "mine"] as const,
};

/** Attempts: the runner's view and the result. */
export const ATTEMPT_KEYS = {
  ALL: ["attempts"] as const,
  DETAIL: (id: string) => ["attempts", "detail", id] as const,
  RESULT: (id: string) => ["attempts", "result", id] as const,
};

/** Reports over the graded answers. */
export const STATS_KEYS = {
  ALL: ["stats"] as const,
  TOPICS: (params: unknown) => ["stats", "topics", params] as const,
  GROUPS: (by: string, params: unknown) => ["stats", "groups", by, params] as const,
  HEATMAP: (params: unknown) => ["stats", "heatmap", params] as const,
};

/** The student's topic mastery and personal practice. */
export const PRACTICE_KEYS = {
  ALL: ["practice"] as const,
  MASTERY: ["practice", "mastery"] as const,
  HISTORY: ["practice", "history"] as const,
};

/** History entries (audit log). */
export const AUDIT_KEYS = {
  ALL: ["audit"] as const,
  SEARCH: (body: unknown) => ["audit", "search", body] as const,
};
