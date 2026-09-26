/** Rows of one section, split under the subject they belong to.
 *
 *  One group and no heading while everything on screen is the same subject: a heading repeated on every group
 *  names something that tells nothing apart, and a centre teaching one subject should see the list it saw before
 *  (the rule the report tree and the class overview already follow). A row whose exam has no subject goes last,
 *  under a heading that says so rather than being adopted by whichever subject happens to be first. */
export function groupBySubject<T extends { subject_id?: string | null }>(
  rows: T[],
  names: Map<string, string>,
): { key: string; name: string | null; rows: T[] }[] {
  const seen = new Set(rows.map((r) => r.subject_id ?? ""));
  if (seen.size < 2) return rows.length ? [{ key: "all", name: null, rows }] : [];
  const groups = new Map<string, T[]>();
  for (const r of rows) {
    const key = r.subject_id ?? "";
    groups.set(key, [...(groups.get(key) ?? []), r]);
  }
  const named = [...groups.entries()].filter(([k]) => k).sort((a, b) => (names.get(a[0]) ?? "").localeCompare(names.get(b[0]) ?? ""));
  const loose = groups.get("");
  return [
    ...named.map(([key, rows]) => ({ key, name: names.get(key) ?? "Môn khác", rows })),
    ...(loose ? [{ key: "none", name: "Chưa rõ môn", rows: loose }] : []),
  ];
}
