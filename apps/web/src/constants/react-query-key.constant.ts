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
