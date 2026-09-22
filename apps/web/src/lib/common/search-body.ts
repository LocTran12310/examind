import type { SearchBody, SearchFilter } from "@/dtos/search.dto";

/** How a URL filter param is read: the column's filter kind (see DataTable `meta.filter`). */
export type FilterKind = "text" | "select" | "number" | "date" | "param";

export const LIMIT_ALL = 1000;

/**
 * Table state in the URL → search body. The URL keeps `q`, `sort=a,-b`, `page`, `page_size` and per
 * column `<key>`, `<key>_op`, `<key>_from` / `_to` (dates), `<key>_min` / `_max` (numbers); only
 * columns listed in `kinds` become filters (kind `param` = a resource parameter at the top of the body).
 * `extra` adds fixed resource parameters (e.g. `{ class_id }`).
 */
export function toSearchBody(params: URLSearchParams, kinds: Record<string, FilterKind>, extra: Record<string, unknown> = {}): SearchBody {
  const size = params.get("page_size");
  const body: SearchBody = {
    page: Math.max(1, Number(params.get("page")) || 1),
    limit: size === "all" ? LIMIT_ALL : Number(size) || 20,
  };
  const q = params.get("q")?.trim();
  if (q) body.q = q;
  const sort = params.get("sort");
  if (sort)
    body.sort = sort
      .split(",")
      .filter(Boolean)
      .map((s) => (s.startsWith("-") ? { field: s.slice(1), desc: true } : { field: s.replace(/^\+/, "") }));
  const filters: Record<string, SearchFilter> = {};
  for (const [key, kind] of Object.entries(kinds)) {
    const value = params.get(key) ?? "";
    const op = params.get(`${key}_op`) ?? "";
    const f: SearchFilter = {};
    if (kind === "param") {
      if (value) body[key] = value;
      continue;
    }
    if (kind === "text" || kind === "select") {
      if (value) f.value = value;
      if (kind === "text" && value && op) f.operator = op;
    } else {
      const [lo, hi] = kind === "date" ? [`${key}_from`, `${key}_to`] : [`${key}_min`, `${key}_max`];
      if (value) {
        f.value = kind === "number" ? Number(value) : value;
        if (op) f.operator = op;
      }
      const from = params.get(lo);
      const to = params.get(hi);
      if (from) f.from = kind === "number" ? Number(from) : from;
      if (to) f.to = kind === "number" ? Number(to) : to;
    }
    if (Object.keys(f).length) filters[key] = f;
  }
  if (Object.keys(filters).length) body.filters = filters;
  for (const [k, v] of Object.entries(extra)) if (v !== undefined && v !== null && v !== "") body[k] = v;
  return body;
}
