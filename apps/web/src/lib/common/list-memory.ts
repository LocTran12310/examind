/**
 * The last URL of each list page in this tab (ui-polish ADR-02), so "← Ngân hàng câu hỏi" from a
 * detail page returns to the same page, sort and filters instead of page 1.
 */
const key = (path: string) => `examind.list:${path}`;

export function rememberList(path: string, search: string): void {
  try {
    sessionStorage.setItem(key(path), search ? `${path}?${search}` : path);
  } catch {}
}

/** The remembered URL of the list at `path`, or `path` itself. */
export function listHref(path: string): string {
  try {
    return sessionStorage.getItem(key(path)) ?? path;
  } catch {
    return path;
  }
}
