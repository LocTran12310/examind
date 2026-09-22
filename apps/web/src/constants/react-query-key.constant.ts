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
